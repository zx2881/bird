"""
语义搜索 Flask 服务器 v4 —— 完整优化版

能力:
  - jieba 分词 + BM25 关键词检索（#1）
  - networkx PageRank 图权重排序（#2）
  - 查询扩展：搜"鹤类"自动扩为鹤科所有成员（#4）
  - 编辑距离实体纠错（#5）
  - 三因子权重调优（#7）
  - 多跳检索（#11）
  - 实体链接 + 图谱遍历 + 融合排序（保留 v3 能力）

用法:
  python scripts/search_server.py
"""

import json
import re
import time
from collections import defaultdict
from pathlib import Path

import jieba
import numpy as np
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_NPZ = ROOT / "public" / "data" / "embeddings.npz"
EMBEDDINGS_META = ROOT / "public" / "data" / "embeddings_meta.json"
NODES_DIR = ROOT / "public" / "data" / "nodes"
SUMMARY_JSON = ROOT / "public" / "data" / "summary.json"

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:7b"

app = Flask(__name__)
CORS(app)

# === 全局状态 ===
embedding_matrix: np.ndarray = None
meta: dict = {}
all_ids: list = []
all_names: list = []
all_types: list = []
entity_index: dict = {}
node_cache: dict = {}
intent_cache: dict = {}
summary_data: dict = {}

# BM25
bm25_index = None
bm25_corpus = []
bm25_id_map = []

# PageRank (简化: 度数代理)
# 分类扩展
taxonomy_members: dict = {}  # taxonomy_id -> [bird_ids]


def load_data():
    global embedding_matrix, meta, all_ids, all_names, all_types
    global entity_index, summary_data, bm25_index, bm25_corpus, bm25_id_map
    global taxonomy_members

    if not EMBEDDINGS_NPZ.exists():
        print(f"[X] 找不到: {EMBEDDINGS_NPZ}")
        return False

    data = np.load(EMBEDDINGS_NPZ, allow_pickle=True)
    embedding_matrix = data["embeddings"]
    with open(EMBEDDINGS_META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    all_ids = meta.get("ids", [])
    all_names = meta.get("names", [])
    all_types = meta.get("types", all_ids and ["bird"] * len(all_ids) or [])

    if SUMMARY_JSON.exists():
        with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

    # --- 实体索引 ---
    entity_index.clear()
    for i, name in enumerate(all_names):
        if name and len(name) >= 2:
            key = name.lower()
            entity_index.setdefault(key, [])
            entity_index[key].append({"idx": i, "id": all_ids[i], "type": all_types[i]})

    # --- BM25 索引 (#1) ---
    print("[BM25] 构建关键词索引...")
    bm25_corpus = []
    bm25_id_map = []
    for i, name in enumerate(all_names):
        eid = all_ids[i]
        etype = all_types[i] if i < len(all_types) else "bird"
        summary_text = get_entity_summary(eid, etype)
        full_text = f"{name} {summary_text}"
        tokens = list(jieba.cut(full_text.lower()))
        bm25_corpus.append(tokens)
        bm25_id_map.append(i)
    bm25_index = BM25Okapi(bm25_corpus)
    print(f"  BM25 索引: {len(bm25_corpus)} 篇文档")

    # --- PageRank (#2) --- 延迟到首次搜索时构建
    # --- 分类扩展 (#4) ---
    print("[Taxonomy] 从 taxonomy_skeleton.json 加载...")
    taxonomy_members.clear()
    taxo_path = ROOT / "public" / "data" / "taxonomy_skeleton.json"
    if taxo_path.exists():
        with open(taxo_path, "r", encoding="utf-8-sig") as f:
            skeleton = json.load(f)
        for node in skeleton.get("nodes", []):
            tid = node.get("id", "")
            if tid and node.get("memberCount", 0) > 0:
                taxonomy_members[tid] = []  # 占位，实际成员从 links 或按需加载
    # 也从 graph_preview 补充关系
    gp_path = ROOT / "public" / "data" / "graph_preview.json"
    if gp_path.exists():
        with open(gp_path, "r", encoding="utf-8-sig") as f:
            gp = json.load(f)
        for link in gp.get("links", []):
            rel = link.get("relation", "")
            if rel in ("belongs_to_family", "belongs_to_order"):
                src = link.get("source", "")
                tgt = link.get("target", "")
                if src and tgt:
                    if tgt not in taxonomy_members:
                        taxonomy_members[tgt] = []
                    if src not in taxonomy_members[tgt]:
                        taxonomy_members[tgt].append(src)

    print(f"  Taxonomy: {len(taxonomy_members)} 个分类节点")
    print(f"  分类节点: {len(taxonomy_members)} 个有成员")

    tcnt = defaultdict(int)
    for t in all_types:
        tcnt[t] += 1
    print(f"[OK] 全部就绪: {meta['count']} 向量, BM25={len(bm25_corpus)}, Taxonomy={len(taxonomy_members)}")
    return True


# ==================== 工具函数 ====================

def get_entity_summary(entity_id: str, entity_type: str = "") -> str:
    chunk = load_node_chunk(entity_id)
    if not chunk:
        return ""
    for node in chunk.get("nodes", []):
        if node["id"] == entity_id:
            return node.get("summary", "")
    return ""


def load_node_chunk(node_id: str) -> dict | None:
    if node_id in node_cache:
        return node_cache[node_id]
    chunk_path = NODES_DIR / f"{node_id}.json"
    if not chunk_path.exists():
        return None
    try:
        with open(chunk_path, "r", encoding="utf-8-sig") as f:
            chunk = json.load(f)
        node_cache[node_id] = chunk
        return chunk
    except Exception:
        return None


def node_degree(node_id: str) -> int:
    chunk = load_node_chunk(node_id)
    return len(chunk.get("links", [])) if chunk else 0


def get_query_embedding(text: str) -> np.ndarray | None:
    try:
        resp = requests.post(OLLAMA_EMBED_URL,
                             json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
        resp.raise_for_status()
        return np.array(resp.json()["embedding"], dtype=np.float32)
    except Exception as e:
        print(f"[X] 向量化失败: {e}")
        return None


def cosine_similarity(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return np.dot(matrix_norm, vec_norm)


def edit_distance(s1: str, s2: str) -> int:
    """Levenshtein 编辑距离"""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if c1 == c2 else 1)
            ))
        prev = curr
    return prev[-1]


# ==================== 1. BM25 关键词搜索 (#1) ====================

def bm25_search(query: str, top_k: int = 20) -> list[dict]:
    tokens = list(jieba.cut(query.lower()))
    if not tokens:
        return []
    scores = bm25_index.get_scores(tokens)
    # 归一化到 0-1
    max_s = float(scores.max())
    if max_s > 0:
        scores = scores / max_s
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        s = float(scores[idx])
        if s < 0.05:
            continue
        orig_idx = bm25_id_map[int(idx)]
        results.append({
            "idx": orig_idx, "id": all_ids[orig_idx],
            "name": all_names[orig_idx], "type": all_types[orig_idx],
            "bm25_score": s,
        })
    return results


# ==================== 2. PageRank 权重 (#2) ====================

# 简化为度数代理（避免扫描目录文件）
def get_pagerank(entity_id: str) -> float:
    return min(node_degree(entity_id) / 20.0, 0.02)


# ==================== 4. 查询扩展 (#4) ====================

RELATION_LABELS = {
    "distributed_in": "分布于", "lives_in": "栖息于",
    "has_status": "保护等级", "threatened_by": "受威胁于",
    "belongs_to": "属于", "belongs_to_family": "属于科",
    "belongs_to_order": "属于目",
}


def expand_taxonomy_query(query: str) -> list[str]:
    """如果查询提到分类名，扩展为成员 ID"""
    expanded = []
    qlower = query.lower()
    for tax_id, members in taxonomy_members.items():
        tax_name = ""
        chunk = load_node_chunk(tax_id)
        if chunk:
            for node in chunk.get("nodes", []):
                if node["id"] == tax_id:
                    tax_name = node.get("name", "")
                    break
        if tax_name and len(tax_name) >= 2 and tax_name.lower() in qlower:
            expanded.extend(members)
    return expanded


# ==================== 5. 实体纠错 (#5) ====================

def correct_entity_name(name: str, max_distance: int = 2) -> str | None:
    """编辑距离纠错：'丹顶赫' → '丹顶鹤'"""
    if len(name) < 3:
        return None
    best = None
    best_dist = max_distance + 1
    for known_name in all_names:
        if not known_name or len(known_name) < 2:
            continue
        if abs(len(known_name) - len(name)) > max_distance:
            continue
        dist = edit_distance(name, known_name)
        if dist < best_dist and dist <= max_distance:
            best_dist = dist
            best = known_name
    return best if best_dist <= max_distance else None


# ==================== 7. 融合排序 (权重调优版) (#7) ====================

def fused_score_v4(item: dict, vector_score: float, query_text: str = "") -> float:
    """
    四因子排序（调优后权重）:
      - 向量语义分: 25%
      - BM25 关键词分: 30%
      - PageRank 图权重: 20%
      - 结构匹配分: 25%
    """
    score = vector_score * 0.25

    # BM25 分
    score += item.get("bm25_score", 0) * 0.30

    # PageRank 分 (归一化到 0-1)
    pr = get_pagerank(item.get("id", ""))
    score += min(pr * 50, 0.20)

    # 结构匹配分
    struct = 0.0
    if item.get("isAnchor"):
        struct += 0.15
    if item.get("via"):
        struct += 0.07
    if item.get("degree", 0) > 5:
        struct += 0.03
    name = item.get("name", "").lower()
    if name and len(name) >= 2 and name in query_text.lower():
        struct += 0.10
        if query_text.lower().startswith(name):
            struct += 0.03
    score += min(struct, 0.25)

    return round(score, 4)


# ==================== 实体链接 (#1 增强) ====================

def extract_known_entities(query: str) -> list[dict]:
    found = []
    query_lower = query.lower()
    for name_key, entries in entity_index.items():
        if name_key in query_lower:
            for entry in entries:
                found.append({
                    "id": entry["id"], "name": all_names[entry["idx"]],
                    "type": entry["type"], "match_text": name_key,
                })
    seen = set()
    unique = []
    for f in found:
        if f["id"] not in seen:
            seen.add(f["id"])
            unique.append(f)
    unique.sort(key=lambda x: len(x["match_text"]), reverse=True)
    return unique


def extract_with_correction(query: str) -> list[dict]:
    """实体链接（含纠错）：先精确匹配，不行再逐词纠错"""
    result = extract_known_entities(query)
    if result:
        return result

    # 对每个词做纠错
    words = list(jieba.cut(query))
    corrected = []
    for w in words:
        if len(w) >= 3:
            fix = correct_entity_name(w)
            if fix and fix not in corrected:
                corrected.append(fix)
                result.extend(extract_known_entities(fix))
    return result


# ==================== 图谱扩展 (含多跳 #11) ====================

def expand_graph(entity_id: str, max_hops: int = 2) -> list[dict]:
    chunk = load_node_chunk(entity_id)
    if not chunk:
        return []
    related = []
    seen_ids = {entity_id}

    for link in chunk.get("links", []):
        other_id = link["target"] if link["source"] == entity_id else link["source"]
        if other_id in seen_ids:
            continue
        seen_ids.add(other_id)
        other_name = other_id
        other_type = ""
        for node in chunk.get("nodes", []):
            if node["id"] == other_id:
                other_name = node.get("name", other_id)
                other_type = node.get("type", "")
                break
        related.append({
            "id": other_id, "name": other_name, "type": other_type,
            "relation": link.get("relation", ""),
            "relationLabel": RELATION_LABELS.get(link.get("relation", ""), link.get("relation", "")),
            "via": entity_id,
            "viaName": all_names[all_ids.index(entity_id)] if entity_id in all_ids else entity_id,
            "hop": 1,
        })

    if max_hops >= 2:
        for hop1 in list(related):
            if hop1["type"] in ("bird", "location", "taxonomy"):
                h2c = load_node_chunk(hop1["id"])
                if h2c:
                    for link in h2c.get("links", []):
                        other_id = link["target"] if link["source"] == hop1["id"] else link["source"]
                        if other_id in seen_ids:
                            continue
                        seen_ids.add(other_id)
                        other_name = other_id
                        other_type = ""
                        for node in h2c.get("nodes", []):
                            if node["id"] == other_id:
                                other_name = node.get("name", other_id)
                                other_type = node.get("type", "")
                                break
                        related.append({
                            "id": other_id, "name": other_name, "type": other_type,
                            "relation": link.get("relation", ""),
                            "relationLabel": RELATION_LABELS.get(link.get("relation", ""), link.get("relation", "")),
                            "via": hop1["id"], "viaName": hop1["name"], "hop": 2,
                        })
    return related


# ==================== 搜索结果构建 ====================

def build_entity_card(idx: int, **extra) -> dict:
    card = {
        "id": all_ids[idx],
        "name": all_names[idx],
        "type": all_types[idx] if idx < len(all_types) else "bird",
    }
    if card["type"] == "bird" and summary_data:
        items = summary_data.get("items", [])
        cols = summary_data.get("columns", [])
        imap = {col: i for i, col in enumerate(cols)}
        for item in items:
            if item[imap.get("id", 0)] == card["id"]:
                card["englishName"] = item[imap.get("englishName", 2)] or ""
                card["latinName"] = item[imap.get("latinName", 3)] or ""
                break
    card.update(extra)
    return card


# ==================== 混合搜索 (#1) ====================

def hybrid_search(query: str, known_entities: list, query_vec, top_k: int, max_hops: int = 1) -> list:
    results = []
    seen = set()

    # 1. BM25 召回
    bm25_results = bm25_search(query, top_k * 2)

    # 2. 向量召回
    vec_results = []
    if query_vec is not None:
        sims = cosine_similarity(query_vec, embedding_matrix)
        top_indices = np.argsort(sims)[::-1][:top_k * 2]
        for idx in top_indices:
            vec_results.append({
                "idx": int(idx), "id": all_ids[int(idx)],
                "name": all_names[int(idx)], "type": all_types[int(idx)],
                "vec_score": float(sims[int(idx)]),
                "bm25_score": 0.0,
            })

    # 3. 扩展 ID（查询扩展）
    expanded_ids = expand_taxonomy_query(query)

    # 4. 融合：合并 BM25 + Vector 结果
    merged = {}
    for r in bm25_results:
        merged[r["id"]] = r
    for r in vec_results:
        if r["id"] in merged:
            merged[r["id"]]["vec_score"] = r["vec_score"]
        else:
            merged[r["id"]] = r

    # 5. 锚点加分 + 图谱扩展
    for ent in known_entities[:6]:
        if ent["id"] in seen:
            continue
        seen.add(ent["id"])
        aidx = all_ids.index(ent["id"]) if ent["id"] in all_ids else -1
        vs = float(cosine_similarity(query_vec, embedding_matrix)[aidx]) if aidx >= 0 and query_vec is not None else 0.85
        bm25_s = merged.get(ent["id"], {}).get("bm25_score", 0.0)
        card = build_entity_card(aidx if aidx >= 0 else 0,
                                 isAnchor=True, degree=node_degree(ent["id"]),
                                 bm25_score=bm25_s, vec_score=vs,
                                 score=fused_score_v4({"name": ent["name"], "id": ent["id"],
                                                       "isAnchor": True, "degree": node_degree(ent["id"]),
                                                       "bm25_score": bm25_s},
                                                      vs, query))
        results.append(card)

        for rel in expand_graph(ent["id"], max_hops=max_hops)[:8]:
            if rel["id"] in seen:
                continue
            seen.add(rel["id"])
            ridx = all_ids.index(rel["id"]) if rel["id"] in all_ids else -1
            if ridx < 0:
                results.append({
                    "id": rel["id"], "name": rel["name"], "type": rel["type"],
                    "isAnchor": False, "via": rel["via"], "viaName": rel["viaName"],
                    "relation": rel["relation"], "relationLabel": rel["relationLabel"],
                    "hop": rel["hop"], "degree": node_degree(rel["id"]),
                    "score": fused_score_v4({"name": rel["name"], "id": rel["id"],
                                            "via": rel["via"], "degree": node_degree(rel["id"])},
                                            0.5, query),
                })
                continue
            rvec = float(cosine_similarity(query_vec, embedding_matrix)[ridx]) if query_vec is not None else 0.5
            rcard = build_entity_card(ridx, isAnchor=False, via=rel["via"],
                                       viaName=rel["viaName"], relation=rel["relation"],
                                       relationLabel=rel["relationLabel"], hop=rel["hop"],
                                       degree=node_degree(rel["id"]),
                                       bm25_score=merged.get(rel["id"], {}).get("bm25_score", 0.0),
                                       vec_score=rvec,
                                       score=fused_score_v4({"name": rel["name"], "id": rel["id"],
                                                             "via": rel["via"], "degree": node_degree(rel["id"])},
                                                            rvec, query))
            results.append(rcard)

    # 6. 补充不重复的融合结果
    for eid, mr in merged.items():
        if eid in seen or len(results) >= top_k + 8:
            continue
        seen.add(eid)
        vs = mr.get("vec_score", 0.5)
        bm25_s = mr.get("bm25_score", 0.0)
        card = build_entity_card(mr["idx"], bm25_score=bm25_s, vec_score=vs,
                                 degree=node_degree(eid),
                                 score=fused_score_v4({"name": mr["name"], "id": eid,
                                                       "degree": node_degree(eid), "bm25_score": bm25_s},
                                                      vs, query))
        results.append(card)

    # 7. 扩展 ID 的额外加分
    for eid in expanded_ids:
        if eid in seen:
            continue
        seen.add(eid)
        results.append({
            "id": eid, "name": eid, "type": "bird",
            "expandedFrom": True, "score": 0.45,
        })

    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 去重 (保留第一次出现的)
    seen_ids = set()
    deduped = []
    for r in results:
        rid = r.get("id", "")
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            deduped.append(r)
    return deduped[:top_k + 8]


# ==================== 意图分类 (= v3) ====================

INTENT_PROMPT = """判断搜索意图，只回复一个标签:
ENTITY_LOOKUP | RELATION_ASK | COMPARE | FILTER | GENERAL
用户问题：{query}
标签："""


def classify_intent(query: str) -> str:
    if query in intent_cache:
        return intent_cache[query]
    q = query.strip().lower()
    if len(q) <= 6:
        intent_cache[query] = "ENTITY_LOOKUP"
        return "ENTITY_LOOKUP"
    try:
        resp = requests.post(OLLAMA_CHAT_URL, json={
            "model": CHAT_MODEL,
            "messages": [{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
            "stream": False, "options": {"temperature": 0.1, "num_predict": 10},
        }, timeout=20)
        resp.raise_for_status()
        reply = resp.json()["message"]["content"].strip().upper()
        for tag in ("ENTITY_LOOKUP", "RELATION_ASK", "COMPARE", "FILTER", "GENERAL"):
            if tag in reply:
                intent_cache[query] = tag
                return tag
    except Exception:
        pass
    intent_cache[query] = "GENERAL"
    return "GENERAL"


# ==================== API ====================

@app.route("/api/search")
def semantic_search():
    query = request.args.get("q", "").strip()
    top_k = int(request.args.get("top", 12))
    hops = int(request.args.get("hops", 1))

    if not query:
        return jsonify({"error": "请提供 q 参数"}), 400
    if embedding_matrix is None:
        return jsonify({"error": "向量数据未加载"}), 500

    start = time.time()

    known_entities = extract_with_correction(query)
    query_vec = get_query_embedding(query)
    intent = classify_intent(query)

    results = hybrid_search(query, known_entities, query_vec, top_k, max_hops=hops)

    elapsed = time.time() - start
    print(f"[搜索] {intent} '{query}' -> {len(results)} 条, {elapsed * 1000:.0f}ms")

    return jsonify({
        "query": query, "intent": intent,
        "matchedEntities": [{"name": e["name"], "type": e["type"]} for e in known_entities[:6]],
        "results": results, "time_ms": round(elapsed * 1000),
    })


@app.route("/api/ask")
def ask_question():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "请提供 q 参数"}), 400
    if embedding_matrix is None:
        return jsonify({"error": "向量数据未加载"}), 500

    known_entities = extract_with_correction(query)
    query_vec = get_query_embedding(query)
    intent = classify_intent(query)

    search_results = hybrid_search(query, known_entities, query_vec, 16, max_hops=2)

    context_parts = []
    seen = set()
    for r in search_results:
        if r.get("type") == "bird" and r["id"] not in seen and len(context_parts) < 8:
            seen.add(r["id"])
            ctx = extract_graph_context(r["id"], r["name"])
            if ctx:
                context_parts.append(ctx)
        elif r.get("type") == "location" and r["id"] not in seen and len(context_parts) < 4:
            seen.add(r["id"])
            lc = load_node_chunk(r["id"])
            if lc:
                for n in lc.get("nodes", []):
                    if n["id"] == r["id"]:
                        context_parts.append(f"【{r['name']}（地点）】{n.get('summary', '')}")
                        break

    graph_context = "\n\n".join(context_parts) if context_parts else "未找到相关信息。"

    prompt = f"""鸟类学和生态保护知识助手。基于知识图谱数据回答。

数据：
{graph_context}

问题：{query}

要求：基于数据回答，不足时诚实说明。中文 300 字内。涉及鸟类时列出分布和保护等级。"""

    try:
        resp = requests.post(OLLAMA_CHAT_URL, json={
            "model": CHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }, timeout=90)
        resp.raise_for_status()
        answer = resp.json()["message"]["content"]
    except Exception as e:
        answer = f"生成失败: {e}"

    return jsonify({"query": query, "intent": intent, "answer": answer,
                    "context_count": len(context_parts)})


def extract_graph_context(node_id: str, node_name: str) -> str | None:
    chunk = load_node_chunk(node_id)
    if not chunk:
        return None
    center = None
    for n in chunk.get("nodes", []):
        if n["id"] == node_id:
            center = n
            break
    if not center:
        return None
    parts = [f"【{node_name}】"]
    if center.get("latinName"):
        parts.append(f"  学名：{center['latinName']}")
    if center.get("orderCn"):
        parts.append(f"  目：{center['orderCn']}")
    if center.get("familyCn"):
        parts.append(f"  科：{center['familyCn']}")
    if center.get("status"):
        parts.append(f"  保护等级：{center['status']}")
    if center.get("summary"):
        parts.append(f"  介绍：{center['summary']}")
    if center.get("locations"):
        parts.append(f"  分布地点：{'、'.join(center['locations'])}")
    if center.get("habitats"):
        parts.append(f"  栖息环境：{'、'.join(center['habitats'])}")
    if center.get("threats"):
        parts.append(f"  主要威胁：{'、'.join(center['threats'])}")
    return "\n".join(parts)


@app.route("/api/suggest")
def suggest():
    """自动补全接口"""
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify({"suggestions": []})
    matches = []
    for name in all_names:
        if name and q in name.lower() and len(matches) < 8:
            matches.append({"name": name, "type": all_types[all_names.index(name)]})
    return jsonify({"suggestions": matches})


@app.route("/api/health")
def health():
    loaded = embedding_matrix is not None
    tcnt = defaultdict(int)
    for t in all_types:
        tcnt[t] += 1
    return jsonify({
        "status": "ok" if loaded else "loading",
        "vectors": meta.get("count", 0) if loaded else 0,
        "bm25_docs": len(bm25_corpus),
        "taxonomy_groups": len(taxonomy_members),
        "types": dict(tcnt),
    })


if __name__ == "__main__":
    if not load_data():
        print("\n[!] 请先运行 python scripts/build_embeddings.py")
    print("\n[启动] 语义搜索 v4 http://localhost:5000")
    print("  GET /api/search?q=查询&top=12&hops=2  混合搜索 + PageRank + 纠错")
    print("  GET /api/ask?q=问题                    图谱增强问答")
    print("  GET /api/suggest?q=前缀                 搜索建议")
    print("  GET /api/health                         状态检查")
    app.run(host="0.0.0.0", port=5000, debug=False)
