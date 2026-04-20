"""
使用 pygbif 从 GBIF 抓取少量分布点，并输出前端可直接读取的 knowledge.json。

用法:
  pip install pygbif
  python scripts/fetch_gbif_data.py --limit 15 --output public/knowledge.generated.json

说明:
1. GBIF 更擅长提供 occurrence 坐标，不直接给出 IUCN 保护等级。
2. 因此脚本将保护等级、栖息地、威胁因素放在本地配置中，分布点从 GBIF 动态获取。
3. 输出结构与 public/knowledge.json 保持兼容，可直接替换前端读取文件。
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from pygbif import occurrences, species


@dataclass
class BirdSeed:
    id: str
    cn_name: str
    en_name: str
    latin_name: str
    status: str
    habitats: List[str]
    threats: List[str]


BIRD_SEEDS: List[BirdSeed] = [
    BirdSeed("bird-red-crowned-crane", "丹顶鹤", "Red-crowned Crane", "Grus japonensis", "VU", ["湿地"], ["湿地围垦", "气候变化"]),
    BirdSeed("bird-crested-ibis", "朱鹮", "Crested Ibis", "Nipponia nippon", "EN", ["湿地", "山地森林"], ["栖息地破坏", "污染"]),
    BirdSeed("bird-chinese-merganser", "中华秋沙鸭", "Chinese Merganser", "Mergus squamatus", "EN", ["山地河流", "山地森林"], ["栖息地破坏", "人类扰动"]),
    BirdSeed("bird-spoon-billed-sandpiper", "勺嘴鹬", "Spoon-billed Sandpiper", "Calidris pygmaea", "CR", ["潮间带泥滩"], ["湿地围垦", "非法猎捕"]),
    BirdSeed("bird-black-faced-spoonbill", "黑脸琵鹭", "Black-faced Spoonbill", "Platalea minor", "EN", ["海岸湿地"], ["污染", "栖息地破坏"]),
    BirdSeed("bird-california-condor", "加州神鹫", "California Condor", "Gymnogyps californianus", "CR", ["峡谷峭壁"], ["铅中毒", "人类扰动"]),
    BirdSeed("bird-philippine-eagle", "菲律宾鹰", "Philippine Eagle", "Pithecophaga jefferyi", "CR", ["热带雨林"], ["栖息地破坏", "非法猎捕"]),
    BirdSeed("bird-kakapo", "鸮鹦鹉", "Kakapo", "Strigops habroptilus", "CR", ["山地森林"], ["外来捕食者", "人类扰动"]),
    BirdSeed("bird-emperor-penguin", "帝企鹅", "Emperor Penguin", "Aptenodytes forsteri", "NT", ["海冰"], ["气候变化"]),
    BirdSeed("bird-grey-crowned-crane", "灰冠鹤", "Grey Crowned Crane", "Balearica regulorum", "EN", ["稀树草原", "湿地"], ["湿地围垦", "非法猎捕"])
]


def safe_name_backbone(name: str) -> int | None:
    result = species.name_backbone(name=name)
    return result.get("usageKey")


def normalize_location(record: Dict) -> Tuple[str, float, float]:
    name_parts = [record.get("country"), record.get("stateProvince"), record.get("locality")]
    name = " / ".join(part for part in name_parts if part) or "GBIF occurrence"
    return name, float(record["decimalLatitude"]), float(record["decimalLongitude"])


def sample_occurrences(usage_key: int, limit: int) -> Iterable[Dict]:
    payload = occurrences.search(taxonKey=usage_key, hasCoordinate=True, limit=limit)
    return payload.get("results", [])


def ensure_node(nodes: Dict[str, Dict], node_id: str, payload: Dict) -> None:
    if node_id not in nodes:
        nodes[node_id] = payload


def build_graph(limit: int) -> Dict:
    nodes: Dict[str, Dict] = {}
    links: List[Dict] = []

    status_ids: Dict[str, str] = {}
    habitat_ids: Dict[str, str] = {}
    threat_ids: Dict[str, str] = {}

    for seed in BIRD_SEEDS:
        usage_key = safe_name_backbone(seed.latin_name)
        if not usage_key:
            continue

        bird_locations: List[str] = []
        representative_lat = None
        representative_lng = None

        for index, occurrence in enumerate(sample_occurrences(usage_key, limit)):
            if "decimalLatitude" not in occurrence or "decimalLongitude" not in occurrence:
                continue

            location_name, lat, lng = normalize_location(occurrence)
            location_id = f"loc-{seed.id}-{index}"
            ensure_node(
                nodes,
                location_id,
                {
                    "id": location_id,
                    "name": location_name,
                    "type": "location",
                    "summary": "由 GBIF occurrence 自动生成的地点节点。",
                    "lat": lat,
                    "lng": lng
                },
            )
            links.append(
                {
                    "source": seed.id,
                    "target": location_id,
                    "relation": "distributed_in",
                    "label": "分布于"
                }
            )

            bird_locations.append(location_name)
            if representative_lat is None:
                representative_lat = lat
                representative_lng = lng

            if len(bird_locations) >= 3:
                break

        ensure_node(
            nodes,
            seed.id,
            {
                "id": seed.id,
                "name": seed.cn_name,
                "englishName": seed.en_name,
                "latinName": seed.latin_name,
                "type": "bird",
                "status": seed.status,
                "summary": "GBIF occurrence + 本地保育信息融合生成。",
                "locations": bird_locations,
                "habitats": seed.habitats,
                "threats": seed.threats,
                "lat": representative_lat,
                "lng": representative_lng
            },
        )

        status_id = status_ids.setdefault(seed.status, f"status-{seed.status.lower()}")
        ensure_node(
            nodes,
            status_id,
            {
                "id": status_id,
                "name": seed.status,
                "type": "status",
                "summary": "本地配置的 IUCN 保护等级节点。",
                "lat": None,
                "lng": None
            },
        )
        links.append({"source": seed.id, "target": status_id, "relation": "has_status", "label": "保护等级"})

        for habitat in seed.habitats:
            habitat_id = habitat_ids.setdefault(habitat, f"hab-{len(habitat_ids) + 1}")
            ensure_node(
                nodes,
                habitat_id,
                {
                    "id": habitat_id,
                    "name": habitat,
                    "type": "habitat",
                    "summary": "本地配置的栖息地节点。",
                    "lat": None,
                    "lng": None
                },
            )
            links.append({"source": seed.id, "target": habitat_id, "relation": "lives_in", "label": "栖息于"})

        for threat in seed.threats:
            threat_id = threat_ids.setdefault(threat, f"threat-{len(threat_ids) + 1}")
            ensure_node(
                nodes,
                threat_id,
                {
                    "id": threat_id,
                    "name": threat,
                    "type": "threat",
                    "summary": "本地配置的威胁因素节点。",
                    "lat": None,
                    "lng": None
                },
            )
            links.append({"source": seed.id, "target": threat_id, "relation": "threatened_by", "label": "受威胁于"})

    return {
        "meta": {
            "title": "全球鸟类分布与生物多样性保护知识图谱",
            "mode": "gbif-generated",
            "source": "GBIF + local curation"
        },
        "nodes": list(nodes.values()),
        "links": links
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15, help="每个物种请求的最大 occurrence 数")
    parser.add_argument("--output", type=Path, default=Path("public/knowledge.generated.json"), help="输出 JSON 文件")
    args = parser.parse_args()

    graph = build_graph(args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"knowledge graph written to {args.output}")


if __name__ == "__main__":
    main()
