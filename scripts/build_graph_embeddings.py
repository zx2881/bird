"""
图嵌入生成脚本 (#15) - 采样版

用法:
  python scripts/build_graph_embeddings.py
  python scripts/build_graph_embeddings.py --sample 2000
"""

import json
import sys
import time
import argparse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PREVIEW = ROOT / "public" / "data" / "graph_preview.json"
OUT_NPZ = ROOT / "public" / "data" / "graph_embeddings.npz"
OUT_META = ROOT / "public" / "data" / "graph_embeddings_meta.json"

DIM = 64


def random_walk_embeddings(adj, id_to_idx, nodes, dim=DIM, walks_per_node=5, walk_len=8):
    """用随机游走 + SVD 近似 node2vec"""
    n = len(nodes)
    idx_to_id = {v: k for k, v in id_to_idx.items()}
    neighbors = {}
    for i in range(n):
        neighbors[i] = list(np.where(adj[i] > 0)[0])

    # 随机游走生成"句子"
    walks = []
    for start in range(n):
        if not neighbors[start]:
            continue
        for _ in range(min(walks_per_node, 3)):
            walk = [start]
            for _ in range(walk_len):
                nbrs = neighbors[walk[-1]]
                if not nbrs:
                    break
                walk.append(int(np.random.choice(nbrs)))
            walks.append(walk)

    # 构建共现矩阵
    cooc = np.zeros((n, n), dtype=np.float32)
    for walk in walks:
        for i, node_i in enumerate(walk):
            for j in range(max(0, i - 2), min(len(walk), i + 3)):
                if i != j:
                    cooc[node_i, walk[j]] += 1.0

    # SVD 降维
    print(f"  SVD {n}x{n} -> {dim}...")
    try:
        U, S, Vt = np.linalg.svd(cooc, full_matrices=False)
        emb = U[:, :dim].astype(np.float32)
        norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
        emb = emb / norms
        return emb
    except np.linalg.LinAlgError:
        return np.random.randn(n, dim).astype(np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()

    if not GRAPH_PREVIEW.exists():
        print(f"[X] 找不到 {GRAPH_PREVIEW}")
        sys.exit(1)

    with open(GRAPH_PREVIEW, "r", encoding="utf-8-sig") as f:
        gp = json.load(f)

    nodes = gp.get("nodes", [])
    links = gp.get("links", [])

    if args.sample > 0 and args.sample < len(nodes):
        # 只取前 N 个节点和相关联的边
        sampled_ids = {n["id"] for n in nodes[:args.sample]}
        nodes = nodes[:args.sample]
        links = [l for l in links if l.get("source", "") in sampled_ids and l.get("target", "") in sampled_ids]
        print(f"[采样] {len(nodes)} 节点, {len(links)} 边")
    else:
        print(f"[全部] {len(nodes)} 节点, {len(links)} 边")

    # 只对鸟和地点做嵌入
    target_nodes = [n for n in nodes if n.get("type") in ("bird", "location")]
    target_ids = {n["id"] for n in target_nodes}
    target_links = [l for l in links if l.get("source", "") in target_ids and l.get("target", "") in target_ids]
    print(f"[过滤] {len(target_nodes)} 实体 (鸟+地点), {len(target_links)} 边")

    id_to_idx = {n["id"]: i for i, n in enumerate(target_nodes)}
    n = len(target_nodes)
    adj = np.zeros((n, n), dtype=np.float32)
    for link in target_links:
        src, tgt = link.get("source", ""), link.get("target", "")
        if src in id_to_idx and tgt in id_to_idx:
            i, j = id_to_idx[src], id_to_idx[tgt]
            adj[i, j] = 1.0
            adj[j, i] = 1.0

    t0 = time.time()
    emb = random_walk_embeddings(adj, id_to_idx, target_nodes, DIM)
    print(f"  耗时: {time.time() - t0:.1f}s")

    np.savez_compressed(OUT_NPZ, embeddings=emb,
                        ids=np.array([n["id"] for n in target_nodes]))
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump({
            "dim": DIM, "count": len(target_nodes),
            "ids": [n["id"] for n in target_nodes],
            "names": [n.get("name", "") for n in target_nodes],
            "types": [n.get("type", "") for n in target_nodes],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, ensure_ascii=False)

    print(f"[OK] graph_embeddings.npz: {OUT_NPZ.stat().st_size / 1024 / 1024:.1f} MB, {len(target_nodes)} 实体, dim={DIM}")


if __name__ == "__main__":
    main()
