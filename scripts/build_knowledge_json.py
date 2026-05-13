"""
将 data/ 目录中的 CSV 主数据源整合为前端可直接使用的 public/knowledge.json。

输入文件:
  - data/birds.csv
  - data/locations.csv
  - data/relations.csv

relations.csv 兼容三元组抽取 Schema，并额外允许 subject_id / object_id / object_summary
这些工程字段，便于稳定构图与前端展示。
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_PATH = ROOT / "public" / "knowledge.json"

RELATION_LABELS = {
    "distributed_in": "分布于",
    "lives_in": "栖息于",
    "has_status": "保护等级",
    "threatened_by": "受威胁于",
    "belongs_to": "属于",
}

ENTITY_TYPE_TO_NODE_TYPE = {
    "Bird": "bird",
    "Location": "location",
    "Habitat": "habitat",
    "Status": "status",
    "Threat": "threat",
    "Taxon": "taxonomy",
}

TYPE_PREFIX = {
    "Bird": "bird",
    "Location": "loc",
    "Habitat": "hab",
    "Status": "status",
    "Threat": "threat",
    "Taxon": "taxonomy",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def parse_float(value: str) -> Optional[float]:
    if not value:
        return None
    return float(value)


def compact(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def stable_generated_id(entity_type: str, name: str) -> str:
    prefix = TYPE_PREFIX[entity_type]
    normalized = re.sub(r"\s+", "-", name.strip().lower())
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", normalized).strip("-")
    digest = md5(name.encode("utf-8")).hexdigest()[:8]
    if normalized:
        return f"{prefix}-{normalized}-{digest}"
    return f"{prefix}-{digest}"


def default_summary(name: str, object_type: str) -> str:
    templates = {
        "Habitat": f"依据 relations.csv 自动生成的栖息地节点：{name}。",
        "Status": f"依据 relations.csv 自动生成的保护等级节点：{name}。",
        "Threat": f"依据 relations.csv 自动生成的威胁因素节点：{name}。",
        "Taxon": f"依据 relations.csv 自动生成的分类单元节点：{name}。",
    }
    return templates.get(object_type, f"依据 relations.csv 自动生成的实体节点：{name}。")


STATUS_LABELS = {
    "EX": "灭绝",
    "EW": "野外灭绝",
    "CR": "极危",
    "EN": "濒危",
    "VU": "易危",
    "NT": "近危",
    "LC": "无危",
    "DD": "数据缺乏",
    "NE": "未评估",
}

SUMMARY_SECTION_MARKERS = (
    "特征",
    "特徵",
    "参考资料",
    "參考資料",
    "生平",
    "分布与栖息地",
    "分布及栖息地",
)

FOREIGN_LANGUAGE_MARKERS = (
    "英语",
    "英語",
    "法语",
    "法語",
    "西班牙语",
    "西班牙語",
    "葡萄牙语",
    "葡萄牙語",
    "德语",
    "德語",
    "阿拉伯语",
    "阿拉伯語",
)


def normalize_summary_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()
    normalized = re.sub(r"\s*([，。；：])", r"\1", normalized)
    return normalized


def preview_names(values: List[str], limit: int = 3, unit: str = "项") -> str:
    items = compact(values)
    if not items:
        return ""
    shown = "、".join(items[:limit])
    if len(items) <= limit:
        return shown
    return f"{shown}等{len(items)}{unit}"


def status_text(code: str) -> str:
    if not code:
        return ""
    label = STATUS_LABELS.get(code.upper(), code.upper())
    return f"{label}（{code.upper()}）"


def should_preview_locations(values: List[str]) -> bool:
    items = compact(values)
    if not items or len(items) > 3:
        return False
    for item in items:
        if len(item) > 18:
            return False
        if re.search(r"[A-Za-z]{10,}", item):
            return False
        if any(marker in item for marker in (",", "Act", "Protection", "Department", "edition")):
            return False
    return True


def needs_summary_completion(summary: str, node_type: str) -> bool:
    text = normalize_summary_text(summary)
    if not text:
        return True
    if text.startswith("依据 relations.csv 自动生成"):
        return True
    if re.search(r"(…|\.{3,})\s*$", text):
        return True
    if any(marker in text for marker in SUMMARY_SECTION_MARKERS):
        return True
    if node_type == "bird" and len(text) > 90:
        return True
    if node_type == "location" and (len(text) > 80 or any(marker in text for marker in FOREIGN_LANGUAGE_MARKERS)):
        return True
    if node_type in {"habitat", "status", "threat", "taxonomy"} and len(text) < 10:
        return True
    return False


def synthesize_bird_summary(node: Dict) -> str:
    aliases = []
    if node.get("englishName"):
        aliases.append(node["englishName"])
    if node.get("latinName"):
        aliases.append(f"学名 {node['latinName']}")

    if aliases:
        lead = f"{node['name']}（{'，'.join(aliases)}）"
    else:
        lead = node["name"]

    clauses = []
    if node.get("status"):
        clauses.append(f"在图谱中标记为{status_text(node['status'])}物种")
    if node.get("locations"):
        location_names = compact(node["locations"])
        if should_preview_locations(location_names):
            clauses.append(f"主要分布于{preview_names(location_names, unit='处地点')}")
        else:
            clauses.append(f"已关联{len(location_names)}个分布地点节点")
    if node.get("habitats"):
        clauses.append(f"常见栖息地包括{preview_names(node['habitats'])}")
    if node.get("threats"):
        clauses.append(f"主要威胁包括{preview_names(node['threats'])}")

    if not clauses:
        clauses.append("是图谱中的鸟类节点")
    return f"{lead}，{'，'.join(clauses)}。"


def synthesize_location_summary(node: Dict, bird_names: List[str]) -> str:
    if bird_names:
        return (
            f"{node['name']}是图谱中的地点节点，当前关联{len(compact(bird_names))}种鸟类，"
            f"包括{preview_names(bird_names, unit='种鸟类')}，主要用于表示这些物种的分布地、停歇地或观测地。"
        )

    if node.get("lat") is not None and node.get("lng") is not None:
        return (
            f"{node['name']}是图谱中的地点节点，已记录坐标"
            f"（{node['lat']:.3f}, {node['lng']:.3f}），用于承载鸟类分布关系。"
        )

    return f"{node['name']}是图谱中的地点节点，用于表示鸟类的分布地、停歇地或相关地理单元。"


def synthesize_relation_summary(node: Dict, bird_names: List[str]) -> str:
    count = len(compact(bird_names))
    examples = preview_names(bird_names, unit="种鸟类")

    if node["type"] == "habitat":
        if count:
            return f"{node['name']}是图谱中的栖息地类型节点，当前关联{count}种鸟类，如{examples}，表示这些物种常在该生境觅食、繁殖或停歇。"
        return f"{node['name']}是图谱中的栖息地类型节点，用于表示鸟类偏好的典型生境。"

    if node["type"] == "threat":
        if count:
            return f"{node['name']}是图谱中的威胁因素节点，当前关联{count}种鸟类，如{examples}，表示该因素会影响栖息地质量、繁殖成功率或种群存续。"
        return f"{node['name']}是图谱中的威胁因素节点，用于表示影响鸟类存续的生态压力。"

    if node["type"] == "status":
        label = STATUS_LABELS.get(node["name"], node["name"])
        if count:
            return f"{node['name']}表示 IUCN {label}等级，当前关联{count}种鸟类，如{examples}。"
        return f"{node['name']}表示 IUCN {label}等级，用于描述鸟类受威胁程度。"

    if node["type"] == "taxonomy":
        if count:
            return f"{node['name']}是图谱中的分类单元节点，当前关联{count}种鸟类，如{examples}。"
        return f"{node['name']}是图谱中的分类单元节点，用于组织鸟类分类关系。"

    return node["summary"]


def complete_node_summaries(nodes: Dict[str, Dict], incoming_birds: Dict[str, List[str]]) -> None:
    for node in nodes.values():
        current_summary = normalize_summary_text(node.get("summary", ""))
        bird_names = incoming_birds.get(node["id"], [])

        if node["type"] == "bird":
            if needs_summary_completion(current_summary, "bird"):
                node["summary"] = synthesize_bird_summary(node)
            else:
                node["summary"] = current_summary
            continue

        if node["type"] == "location":
            if needs_summary_completion(current_summary, "location"):
                node["summary"] = synthesize_location_summary(node, bird_names)
            else:
                node["summary"] = current_summary
            continue

        if node["type"] in {"habitat", "status", "threat", "taxonomy"}:
            if needs_summary_completion(current_summary, node["type"]):
                node["summary"] = synthesize_relation_summary(node, bird_names)
            else:
                node["summary"] = current_summary


def require_columns(path: Path, rows: List[Dict[str, str]], expected: List[str]) -> None:
    if not rows:
        raise ValueError(f"{path.name} 为空，无法生成知识图谱。")

    missing = [column for column in expected if column not in rows[0]]
    if missing:
        raise ValueError(f"{path.name} 缺少列: {', '.join(missing)}")


def build_graph() -> Dict:
    birds_rows = read_csv(DATA_DIR / "birds.csv")
    locations_rows = read_csv(DATA_DIR / "locations.csv")
    relations_rows = read_csv(DATA_DIR / "relations.csv")

    require_columns(DATA_DIR / "birds.csv", birds_rows, ["id", "name", "english_name", "latin_name", "summary", "lat", "lng"])
    require_columns(DATA_DIR / "locations.csv", locations_rows, ["id", "name", "summary", "lat", "lng"])
    require_columns(
        DATA_DIR / "relations.csv",
        relations_rows,
        ["subject_id", "subject", "predicate", "object_id", "object", "subject_type", "object_type", "evidence", "object_summary"],
    )

    nodes: Dict[str, Dict] = {}
    links: List[Dict] = []

    birds_by_id: Dict[str, Dict] = {}
    birds_by_name: Dict[str, Dict] = {}
    for row in birds_rows:
        node = {
            "id": row["id"],
            "name": row["name"],
            "englishName": row["english_name"],
            "latinName": row["latin_name"],
            "type": "bird",
            "status": "",
            "summary": row["summary"],
            "locations": [],
            "habitats": [],
            "threats": [],
            "lat": parse_float(row["lat"]),
            "lng": parse_float(row["lng"]),
            "imageUrl": row.get("image_url", "").strip(),
        }
        nodes[node["id"]] = node
        birds_by_id[node["id"]] = node
        birds_by_name[node["name"]] = node

    locations_by_id: Dict[str, Dict] = {}
    locations_by_name: Dict[str, Dict] = {}
    for row in locations_rows:
        node = {
            "id": row["id"],
            "name": row["name"],
            "type": "location",
            "summary": row["summary"],
            "lat": parse_float(row["lat"]),
            "lng": parse_float(row["lng"]),
        }
        nodes[node["id"]] = node
        locations_by_id[node["id"]] = node
        locations_by_name[node["name"]] = node

    relation_targets: Dict[str, Dict] = {}
    incoming_birds = defaultdict(list)
    grouped_values = defaultdict(lambda: defaultdict(list))

    for index, row in enumerate(relations_rows, start=2):
        predicate = row["predicate"]
        subject_type = row["subject_type"]
        object_type = row["object_type"]

        if predicate not in RELATION_LABELS:
            raise ValueError(f"relations.csv 第 {index} 行存在不支持的 predicate: {predicate}")
        if subject_type != "Bird":
            raise ValueError(f"relations.csv 第 {index} 行 subject_type 必须为 Bird，当前为 {subject_type}")
        if object_type not in ENTITY_TYPE_TO_NODE_TYPE:
            raise ValueError(f"relations.csv 第 {index} 行 object_type 不支持: {object_type}")

        subject_node = birds_by_id.get(row["subject_id"]) or birds_by_name.get(row["subject"])
        if not subject_node:
            raise ValueError(f"relations.csv 第 {index} 行无法找到鸟类实体: {row['subject_id'] or row['subject']}")
        if row["subject"] and row["subject"] != subject_node["name"]:
            raise ValueError(f"relations.csv 第 {index} 行 subject 与 birds.csv 不一致: {row['subject']} != {subject_node['name']}")

        object_id = row["object_id"]
        object_name = row["object"]
        if not object_name:
            raise ValueError(f"relations.csv 第 {index} 行 object 不能为空")

        if object_type == "Location":
            object_node = locations_by_id.get(object_id) or locations_by_name.get(object_name)
            if not object_node:
                raise ValueError(f"relations.csv 第 {index} 行无法找到地点实体: {object_id or object_name}")
            if row["object"] and row["object"] != object_node["name"]:
                raise ValueError(f"relations.csv 第 {index} 行 object 与 locations.csv 不一致: {row['object']} != {object_node['name']}")
            resolved_object_id = object_node["id"]
        elif object_type == "Bird":
            object_node = birds_by_id.get(object_id) or birds_by_name.get(object_name)
            if not object_node:
                raise ValueError(f"relations.csv 第 {index} 行无法找到鸟类实体对象: {object_id or object_name}")
            resolved_object_id = object_node["id"]
        else:
            resolved_object_id = object_id or stable_generated_id(object_type, object_name)
            object_node = relation_targets.get(resolved_object_id)
            if object_node is None:
                object_node = {
                    "id": resolved_object_id,
                    "name": object_name,
                    "type": ENTITY_TYPE_TO_NODE_TYPE[object_type],
                    "summary": row["object_summary"] or default_summary(object_name, object_type),
                    "lat": None,
                    "lng": None,
                }
                relation_targets[resolved_object_id] = object_node
                nodes[resolved_object_id] = object_node
            elif object_node["name"] != object_name:
                raise ValueError(
                    f"relations.csv 第 {index} 行 object_id {resolved_object_id} 重复，但 object 名称不一致: "
                    f"{object_node['name']} != {object_name}"
                )
            elif row["object_summary"] and object_node["summary"].startswith("依据 relations.csv 自动生成"):
                object_node["summary"] = row["object_summary"]

        links.append(
            {
                "source": subject_node["id"],
                "target": resolved_object_id,
                "relation": predicate,
                "label": RELATION_LABELS[predicate],
                "evidence": row["evidence"],
            }
        )
        incoming_birds[resolved_object_id].append(subject_node["name"])
        grouped_values[subject_node["id"]][predicate].append(object_name)

    for bird in birds_by_id.values():
        bird["locations"] = compact(grouped_values[bird["id"]]["distributed_in"])
        bird["habitats"] = compact(grouped_values[bird["id"]]["lives_in"])
        bird["threats"] = compact(grouped_values[bird["id"]]["threatened_by"])
        bird["status"] = next(iter(compact(grouped_values[bird["id"]]["has_status"])), "")

        if (bird["lat"] is None or bird["lng"] is None) and bird["locations"]:
            primary_location_name = bird["locations"][0]
            primary_location = locations_by_name.get(primary_location_name)
            if primary_location:
                bird["lat"] = primary_location["lat"]
                bird["lng"] = primary_location["lng"]

    complete_node_summaries(nodes, incoming_birds)

    return {
        "meta": {
            "title": "全球鸟类分布与生物多样性保护知识图谱",
            "mode": "csv-data",
            "description": "由 data/birds.csv、data/locations.csv、data/relations.csv 自动构建。",
            "updated_at": datetime.now().date().isoformat(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_files": [
                "data/birds.csv",
                "data/locations.csv",
                "data/relations.csv",
            ],
        },
        "nodes": list(nodes.values()),
        "links": links,
    }


def main() -> None:
    graph = build_graph()
    OUTPUT_PATH.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"knowledge graph written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
