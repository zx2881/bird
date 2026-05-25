"""
生成地点反向节点分片 (#14)

从鸟类节点分片中提取每个地点的关联鸟类和关系，
生成 locations/{loc_id}.json 格式的反向分片。

用法:
  python scripts/build_location_chunks.py
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES_DIR = ROOT / "public" / "data" / "nodes"
OUT_DIR = NODES_DIR  # 直接放在同一个目录


def main():
    print("[扫描] 鸟类节点分片，构建地点反向索引...")

    bird_files = sorted(NODES_DIR.glob("bird-*.json"))
    print(f"  找到 {len(bird_files)} 个鸟类分片")

    loc_index = defaultdict(list)  # loc_id -> [related birds with link info]

    count = 0
    for nf in bird_files:
        try:
            with open(nf, "r", encoding="utf-8-sig") as f:
                chunk = json.load(f)
        except Exception:
            continue

        center_id = chunk.get("meta", {}).get("centerNodeId", "")
        center_name = ""
        for node in chunk.get("nodes", []):
            if node["id"] == center_id:
                center_name = node.get("name", center_id)
                break

        for link in chunk.get("links", []):
            src = link.get("source", "")
            tgt = link.get("target", "")
            rel = link.get("relation", "")

            loc_id = None
            bird_id = None

            if src == center_id and rel in ("distributed_in", "lives_in"):
                loc_id = tgt
                bird_id = center_id
            elif tgt == center_id and rel in ("distributed_in", "lives_in"):
                loc_id = src
                bird_id = center_id

            if loc_id and bird_id and loc_id.startswith("loc-"):
                # 找地点名称
                loc_name = loc_id
                for node in chunk.get("nodes", []):
                    if node["id"] == loc_id:
                        loc_name = node.get("name", loc_id)
                        break

                loc_index[loc_id].append({
                    "birdId": bird_id,
                    "birdName": center_name,
                    "relation": rel,
                    "label": link.get("label", rel),
                    "evidence": link.get("evidence", ""),
                })

        count += 1
        if count % 1000 == 0:
            print(f"  已处理 {count}/{len(bird_files)}...")

    print(f"\n[生成] 地点反向分片 ({len(loc_index)} 个地点)...")

    # 第一遍扫描：收集地点 meta
    print("  [1/2] 收集地点元数据...")
    loc_meta = {}
    for nf in bird_files:
        try:
            with open(nf, "r", encoding="utf-8-sig") as f:
                chunk = json.load(f)
            for node in chunk.get("nodes", []):
                nid = node["id"]
                if nid.startswith("loc-") and nid not in loc_meta:
                    loc_meta[nid] = {
                        "name": node.get("name", nid),
                        "summary": node.get("summary", ""),
                        "lat": node.get("lat"),
                        "lng": node.get("lng"),
                    }
        except Exception:
            continue

    # 第二遍：写文件
    print(f"  [2/2] 写入 {len(loc_index)} 个分片...")
    count = 0
    for loc_id, birds in loc_index.items():
        meta = loc_meta.get(loc_id, {})
        loc_name = meta.get("name", loc_id)
        loc_summary = meta.get("summary", "")
        loc_lat = meta.get("lat")
        loc_lng = meta.get("lng")

        # 去重
        seen = set()
        unique = []
        for b in birds:
            if b["birdId"] not in seen:
                seen.add(b["birdId"])
                unique.append(b)

        chunk_data = {
            "meta": {
                "centerNodeId": loc_id,
                "centerNodeType": "location",
                "includedBirdCount": len(unique),
            },
            "center": {
                "id": loc_id, "name": loc_name, "type": "location",
                "summary": loc_summary, "lat": loc_lat, "lng": loc_lng,
            },
            "birds": unique,
            "links": [
                {
                    "key": f"{b['birdId']}__{b['relation']}__{loc_id}",
                    "source": b["birdId"],
                    "target": loc_id,
                    "relation": b["relation"],
                    "label": b["label"],
                    "evidence": b.get("evidence", ""),
                }
                for b in unique
            ],
        }

        out_path = OUT_DIR / f"{loc_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[OK] 生成 {len(loc_index)} 个地点反向分片")

    # 让 search_server 的 expand_graph 能识别
    loc_sample = list(loc_index.items())[:3]
    for loc_id, birds in loc_sample:
        print(f"  {loc_id}: {len(birds)} 只鸟")


if __name__ == "__main__":
    main()
