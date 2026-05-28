"""
Build lightweight search index for the semantic search server.
Does NOT require Ollama - uses BM25-only search with graph expansion.

Generates:
  - public/data/embeddings_meta.json  (entity IDs, names, types)
  - public/data/embeddings.npz         (zero matrix, shape-compatible)

Usage:
  python scripts/build_lightweight_index.py
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_JSON = ROOT / "public" / "data" / "summary.json"
GP_JSON = ROOT / "public" / "data" / "graph_preview.json"
OUTPUT_NPZ = ROOT / "public" / "data" / "embeddings.npz"
OUTPUT_META = ROOT / "public" / "data" / "embeddings_meta.json"

DIM = 768  # nomic-embed-text dimension


def main():
    print("[读取] summary.json ...")
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        summary = json.load(f)

    all_ids = []
    all_names = []
    all_types = []

    # Birds from summary
    cols = summary.get("columns", [])
    idx_map = {c: i for i, c in enumerate(cols)}

    for item in summary.get("items", []):
        eid = item[idx_map.get("id", 0)]
        name = item[idx_map.get("name", 1)]
        all_ids.append(eid)
        all_names.append(name)
        all_types.append("bird")

    print(f"  鸟类: {len(all_ids)}")

    # Locations from summary
    locations = summary.get("locations", [])
    for loc in locations:
        all_ids.append(loc["id"])
        all_names.append(loc["name"])
        all_types.append("location")

    print(f"  地点: {len(locations)}")

    # Taxonomy from graph_preview
    if GP_JSON.exists():
        with open(GP_JSON, "r", encoding="utf-8") as f:
            gp = json.load(f)
        tax_count = 0
        for node in gp.get("nodes", []):
            if node.get("type") == "taxonomy":
                all_ids.append(node["id"])
                all_names.append(node.get("name", node["id"]))
                all_types.append("taxonomy")
                tax_count += 1
        print(f"  分类: {tax_count}")

    total = len(all_ids)
    print(f"\n[统计] 共 {total} 个实体")

    # Generate zero embeddings matrix
    print(f"\n[生成] 零向量矩阵 ({total} x {DIM}) ...")
    embedding_matrix = np.zeros((total, DIM), dtype=np.float32)

    print(f"[保存] {OUTPUT_NPZ} ...")
    np.savez_compressed(OUTPUT_NPZ, embeddings=embedding_matrix)

    print(f"[保存] {OUTPUT_META} ...")
    meta = {
        "model": "lightweight-index",
        "dim": DIM,
        "count": total,
        "birdCount": len(summary.get("items", [])),
        "locationCount": len(locations),
        "ids": all_ids,
        "names": all_names,
        "types": all_types,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    npz_size = OUTPUT_NPZ.stat().st_size / 1024 / 1024
    print(f"\n[完成] embeddings.npz = {npz_size:.1f} MB")
    print(f"  可加载实体: {total} (鸟: {len(summary.get('items',[]))}, 地点: {len(locations)})")


if __name__ == "__main__":
    main()
