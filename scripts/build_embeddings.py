"""
为鸟类、地点、栖息地、威胁等所有实体生成语义嵌入向量。

用法:
  python scripts/build_embeddings.py              # 生成全部
  python scripts/build_embeddings.py --limit 100  # 测试

依赖: numpy, requests
需要先运行: ollama pull nomic-embed-text
"""

import csv
import json
import sys
import time
import argparse
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent.parent
BIRDS_CSV = ROOT / "data" / "birds.csv"
LOCATIONS_CSV = ROOT / "data" / "locations.csv"
OUTPUT_NPZ = ROOT / "public" / "data" / "embeddings.npz"
OUTPUT_META = ROOT / "public" / "data" / "embeddings_meta.json"

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"


def get_embedding(text: str, retries: int = 3) -> list[float] | None:
    for attempt in range(retries):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": text[:4000]},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 2
                print(f"  [!] 重试 ({attempt + 1}/{retries})，等待 {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"  [X] 失败: {e}")
                return None


def safe_str(value) -> str:
    return (value or "").strip()


def build_bird_text(row: dict) -> str:
    parts = []
    name = safe_str(row.get("name"))
    en_name = safe_str(row.get("english_name"))
    latin = safe_str(row.get("latin_name"))
    summary = safe_str(row.get("summary"))
    order_cn = safe_str(row.get("order_cn"))
    family_cn = safe_str(row.get("family_cn"))
    order = safe_str(row.get("order"))
    family = safe_str(row.get("family"))

    if name:
        parts.append(f"鸟类：{name}")
    if en_name:
        parts.append(f"英文名：{en_name}")
    if latin:
        parts.append(f"学名：{latin}")
    if order_cn or order:
        parts.append(f"目：{order_cn or order}")
    if family_cn or family:
        parts.append(f"科：{family_cn or family}")
    if summary:
        parts.append(f"介绍：{summary}")

    return "\n".join(parts) if parts else name


def build_location_text(row: dict) -> str:
    parts = []
    name = safe_str(row.get("name"))
    summary = safe_str(row.get("summary"))
    lat = safe_str(row.get("lat"))
    lng = safe_str(row.get("lng"))

    if name:
        parts.append(f"地点：{name}")
    if summary:
        parts.append(f"介绍：{summary}")
    if lat and lng:
        parts.append(f"坐标：({lat}, {lng})")

    return "\n".join(parts) if parts else name


def process_entities(entities, build_text_fn, entity_type, limit=0):
    """处理一批实体，返回 ids, names, types, embeddings"""
    ids = []
    names = []
    types = []
    embeddings = []
    total = len(entities)

    if limit > 0 and len(entities) > limit:
        entities = entities[:limit]
        print(f"  [{entity_type}] 限制为前 {len(entities)} 条")

    start = time.time()
    success = 0

    for i, entity in enumerate(entities):
        eid = entity.get("id") or f"{entity_type}-{i}"
        name = safe_str(entity.get("name"))
        text = build_text_fn(entity)

        vec = get_embedding(text)
        if vec is not None:
            ids.append(eid)
            names.append(name)
            types.append(entity_type)
            embeddings.append(vec)
            success += 1

        if (i + 1) % 200 == 0 or i == len(entities) - 1:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(entities) - i - 1) / rate if rate > 0 else 0
            print(f"  [{entity_type} {i + 1}/{len(entities)}] "
                  f"速度: {rate:.1f} 条/秒, 预计剩余: {eta:.0f} 秒, 成功: {success}")

    elapsed = time.time() - start
    print(f"  [{entity_type}] 完成！耗时 {elapsed:.1f} 秒, 成功 {success}/{len(entities)}")
    return ids, names, types, embeddings


def main():
    parser = argparse.ArgumentParser(description="生成知识图谱实体语义嵌入向量")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条（0=全部）")
    args = parser.parse_args()

    print(f"[连接] 连接 Ollama ({MODEL}) ...")
    test = get_embedding("测试连接")
    if test is None:
        print("[X] 无法连接 Ollama，请确认 ollama serve 正在运行")
        sys.exit(1)
    dim = len(test)
    print(f"  向量维度: {dim}")

    all_ids = []
    all_names = []
    all_types = []
    all_embeddings = []

    # 1. 鸟类
    print(f"\n[读取] {BIRDS_CSV} ...")
    with open(BIRDS_CSV, "r", encoding="utf-8-sig") as f:
        birds = list(csv.DictReader(f))
    print(f"  共 {len(birds)} 只鸟")
    bid, bname, btype, bemb = process_entities(birds, build_bird_text, "bird", args.limit)
    all_ids.extend(bid); all_names.extend(bname); all_types.extend(btype); all_embeddings.extend(bemb)

    # 2. 地点
    print(f"\n[读取] {LOCATIONS_CSV} ...")
    with open(LOCATIONS_CSV, "r", encoding="utf-8-sig") as f:
        locations = list(csv.DictReader(f))
    print(f"  共 {len(locations)} 个地点")
    lid, lname, ltype, lemb = process_entities(locations, build_location_text, "location",
                                                args.limit if args.limit > 0 else 0)
    all_ids.extend(lid); all_names.extend(lname); all_types.extend(ltype); all_embeddings.extend(lemb)

    # 保存
    total = len(all_ids)
    print(f"\n[统计] 共生成 {total} 个向量 (鸟: {len(bid)}, 地点: {len(lid)})")

    print(f"\n[保存] 保存向量到 {OUTPUT_NPZ} ...")
    embedding_matrix = np.array(all_embeddings, dtype=np.float32)
    OUTPUT_NPZ.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUTPUT_NPZ, embeddings=embedding_matrix,
                        ids=np.array(all_ids), types=np.array(all_types))

    print(f"[保存] 保存元数据到 {OUTPUT_META} ...")
    meta = {
        "model": MODEL,
        "dim": dim,
        "count": total,
        "birdCount": len(bid),
        "locationCount": len(lid),
        "ids": all_ids,
        "names": all_names,
        "types": all_types,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    npz_size = OUTPUT_NPZ.stat().st_size / 1024 / 1024
    print(f"\n[统计] 文件大小: embeddings.npz = {npz_size:.1f} MB")
    print(f"   鸟: {meta['birdCount']}  地点: {meta['locationCount']}")
    print("[完成] 全部搞定！")


if __name__ == "__main__":
    main()
