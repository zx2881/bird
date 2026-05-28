"""
Rebuild summary.json and graph_preview.json from the JSON files in nodes/ directory.
Reads all node chunk files to collect full bird/location/taxonomy data and regenerates
the summary index and preview graph with richer fields.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
NODES_DIR = ROOT / "public" / "data" / "nodes"

TAXONOMY_RANKS = ("kingdom", "phylum", "class", "order", "family", "genus", "species")
PREVIEW_TAXONOMY_LEVELS = {"kingdom", "phylum", "class", "order", "family"}

def parse_float(value):
    if value is None:
        return None
    return float(value)

def compact(values):
    seen = set()
    result = []
    for v in (values or []):
        if v and v not in seen:
            seen.add(v)
            result.append(v)
    return result

def round_position(value):
    if value is None:
        return None
    return round(float(value), 2)


def main():
    node_files = list(NODES_DIR.glob("*.json"))
    print(f"Found {len(node_files)} node chunk files")

    all_nodes: Dict[str, dict] = {}
    all_links: Dict[str, dict] = {}
    all_taxonomy_ids: Dict[str, dict] = {}

    for path in node_files:
        try:
            chunk = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        for node in chunk.get("nodes", []):
            node.setdefault("type", "bird")
            node.setdefault("expandable", node.get("type") in ("bird", "taxonomy"))
            if node["id"] not in all_nodes or node["type"] == all_nodes[node["id"]].get("type"):
                if node["id"] not in all_nodes or len(json.dumps(node, ensure_ascii=False)) > len(json.dumps(all_nodes[node["id"]], ensure_ascii=False)):
                    all_nodes[node["id"]] = {
                        k: v for k, v in node.items()
                        if v not in ("", [], None)
                    }

        for link in chunk.get("links", []):
            key = link.get("key") or f"{link['source']}__{link.get('relation','')}__{link['target']}"
            if key not in all_links:
                all_links[key] = {
                    "key": key,
                    "source": link["source"],
                    "target": link["target"],
                    "relation": link.get("relation", ""),
                    "label": link.get("label", link.get("relation", "")),
                    "evidence": link.get("evidence", ""),
                }

    print(f"Collected {len(all_nodes)} nodes, {len(all_links)} links")

    bird_nodes = sorted(
        (n for n in all_nodes.values() if n.get("type") == "bird"),
        key=lambda n: (n.get("name", ""), n["id"]),
    )
    taxonomy_nodes = sorted(
        (n for n in all_nodes.values() if n.get("type") == "taxonomy"),
        key=lambda n: (TAXONOMY_RANKS.index(n.get("taxonomyLevel", "species")), n.get("name", ""), n["id"]),
    )
    order_nodes = [n for n in taxonomy_nodes if n.get("taxonomyLevel") == "order"]
    family_nodes = [n for n in taxonomy_nodes if n.get("taxonomyLevel") == "family"]

    taxonomy_counts = {}
    for rank in TAXONOMY_RANKS:
        key_map = {
            "kingdom": "kingdoms", "phylum": "phyla", "class": "classes",
            "order": "orders", "family": "families", "genus": "genera", "species": "species",
        }
        taxonomy_counts[key_map[rank]] = len([n for n in taxonomy_nodes if n.get("taxonomyLevel") == rank])

    relation_type_counts = {}
    taxonomy_link_count = 0
    for link in all_links.values():
        relation_type_counts[link["relation"]] = relation_type_counts.get(link["relation"], 0) + 1
        if link["relation"].startswith("belongs_to_"):
            taxonomy_link_count += 1

    location_nodes = sorted(
        (n for n in all_nodes.values() if n.get("type") == "location"),
        key=lambda n: (n.get("name", ""), n["id"]),
    )

    meta = {
        "title": "全球鸟类分布与生物多样性保护知识图谱",
        "mode": "chunked-static-data",
        "description": "由 data/birds.csv、data/locations.csv、data/relations.csv 自动构建为静态分片数据。",
        "updated_at": datetime.now().date().isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    summary_payload = {
        "meta": {
            **meta,
            "counts": {
                "birds": len(bird_nodes),
                "orders": len(order_nodes),
                "families": len(family_nodes),
                "totalRelations": len(all_links),
                "taxonomyRelations": taxonomy_link_count,
                "relationTypes": relation_type_counts,
                **taxonomy_counts,
            },
        },
        "columns": ["id", "name", "englishName", "latinName"],
        "items": [
            [b["id"], b.get("name", ""), b.get("englishName", ""), b.get("latinName", "")]
            for b in bird_nodes
        ],
        "locations": [
            {"id": loc["id"], "name": loc.get("name", "")}
            for loc in location_nodes
        ],
    }

    (ROOT / "public" / "data" / "summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print("summary.json written")

    taxonomy_skeleton_links = [
        {"source": l["source"], "target": l["target"], "relation": l["relation"]}
        for l in all_links.values()
        if l["relation"].startswith("belongs_to_")
        and all_nodes.get(l["source"], {}).get("type") == "taxonomy"
        and all_nodes.get(l["target"], {}).get("type") == "taxonomy"
    ]

    skeleton_payload = {
        "meta": {**meta, "counts": {**taxonomy_counts, "links": len(taxonomy_skeleton_links)}, "layoutMode": "precomputed-static"},
        "nodes": [serialize_node(n) for n in taxonomy_nodes],
        "links": taxonomy_skeleton_links,
    }
    (ROOT / "public" / "data" / "taxonomy_skeleton.json").write_text(
        json.dumps(skeleton_payload, ensure_ascii=False), encoding="utf-8",
    )
    print("taxonomy_skeleton.json written")

    preview_links_all = [
        {"source": l["source"], "target": l["target"], "relation": l["relation"]}
        for l in all_links.values()
        if l["relation"].startswith("belongs_to_")
    ]

    preview_nodes = []
    for n in taxonomy_nodes:
        data = serialize_preview_node(n)
        if n.get("taxonomyLevel") in PREVIEW_TAXONOMY_LEVELS:
            preview_nodes.append(data)

    for b in bird_nodes:
        data = serialize_preview_node(b)
        preview_nodes.append(data)

    preview_payload = {
        "meta": {
            **meta,
            "counts": {
                "birds": len(bird_nodes),
                **taxonomy_counts,
                "nodes": len(preview_nodes),
                "links": len(preview_links_all),
            },
            "layoutMode": "precomputed-static",
            "scope": "startup-graph-preview",
        },
        "nodes": preview_nodes,
        "links": preview_links_all,
    }
    (ROOT / "public" / "data" / "graph_preview.json").write_text(
        json.dumps(preview_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print("graph_preview.json written")
    print("Done!")


def serialize_node(node):
    data = {k: v for k, v in node.items() if v not in ("", [], None)}
    if data.get("lat") is None:
        data.pop("lat", None)
    if data.get("lng") is None:
        data.pop("lng", None)
    return data

def serialize_preview_node(node):
    data = {
        "id": node["id"],
        "name": node.get("name", ""),
        "type": node.get("type", "bird"),
        "expandable": node.get("expandable", False),
        "x": round_position(node.get("x")),
        "y": round_position(node.get("y")),
        "z": round_position(node.get("z")),
    }

    if node.get("type") == "bird":
        data.update({
            "englishName": node.get("englishName", ""),
            "latinName": node.get("latinName", ""),
            "summary": (node.get("summary", "") or "")[:200],
            "lat": node.get("lat"),
            "lng": node.get("lng"),
            "status": node.get("status", ""),
            "locations": node.get("locations", []),
            "habitats": node.get("habitats", []),
            "threats": node.get("threats", []),
            "familyId": node.get("familyId", ""),
            "orderId": node.get("orderId", ""),
            "genusId": node.get("genusId", ""),
            "speciesId": node.get("speciesId", ""),
        })
    elif node.get("type") == "taxonomy":
        data.update({
            "latinName": node.get("latinName", ""),
            "taxonomyLevel": node.get("taxonomyLevel", ""),
            "memberCount": node.get("memberCount", 0),
        })

    return {k: v for k, v in data.items() if v not in ("", None, [])}


if __name__ == "__main__":
    main()
