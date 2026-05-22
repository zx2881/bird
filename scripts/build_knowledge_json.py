"""
将 data/ 目录中的 CSV 主数据源重构为可被纯静态前端按需加载的数据切片。

输出目录:
  - public/data/summary.json
  - public/data/taxonomy_skeleton.json
  - public/data/nodes/[node_id].json

设计目标:
  1. summary.json 仅承载极速搜索所需的鸟类轻量索引。
  2. taxonomy_skeleton.json 仅承载目 / 科层级的分类骨架，作为首屏底图。
  3. nodes/[node_id].json 承载单个中心节点及其局部邻域，支持前端增量织入图谱。

说明:
  - 为了保证静态部署环境也能稳定渲染，本脚本会预计算节点坐标。
  - 物种节点与分类节点（order / family）都会生成切片文件，便于前端点击扩展。
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
from collections import defaultdict
from datetime import datetime
from hashlib import md5
from pathlib import Path
from statistics import mean
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "public" / "data"
NODES_DIR = OUTPUT_DIR / "nodes"
LEGACY_OUTPUT_PATH = ROOT / "public" / "knowledge.json"

RELATION_LABELS = {
    "distributed_in": "分布于",
    "lives_in": "栖息于",
    "has_status": "保护等级",
    "threatened_by": "受威胁于",
    "belongs_to": "属于",
    "belongs_to_family": "属于科",
    "belongs_to_order": "属于目",
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


def compact(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def slugify(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().lower())
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", normalized).strip("-")
    return normalized


def stable_generated_id(entity_type: str, name: str) -> str:
    prefix = TYPE_PREFIX[entity_type]
    normalized = slugify(name)
    digest = md5(name.encode("utf-8")).hexdigest()[:8]
    if normalized:
        return f"{prefix}-{normalized}-{digest}"
    return f"{prefix}-{digest}"


def taxonomy_node_id(level: str, latin_name: str, display_name: str) -> str:
    base = latin_name or display_name or f"{level}-unknown"
    normalized = slugify(base)
    digest = md5(f"{level}:{base}".encode("utf-8")).hexdigest()[:6]
    return f"taxonomy-{level}-{normalized or digest}"


def default_summary(name: str, object_type: str) -> str:
    templates = {
        "Habitat": f"依据 relations.csv 自动生成的栖息地节点：{name}。",
        "Status": f"依据 relations.csv 自动生成的保护等级节点：{name}。",
        "Threat": f"依据 relations.csv 自动生成的威胁因素节点：{name}。",
        "Taxon": f"依据 relations.csv 自动生成的分类单元节点：{name}。",
    }
    return templates.get(object_type, f"依据 relations.csv 自动生成的实体节点：{name}。")


def normalize_summary_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()
    normalized = re.sub(r"\s*([，。；：])", r"\1", normalized)
    return normalized


def preview_names(values: Iterable[str], limit: int = 3, unit: str = "项") -> str:
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


def should_preview_locations(values: Iterable[str]) -> bool:
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

    lead = f"{node['name']}（{'，'.join(aliases)}）" if aliases else node["name"]

    clauses = []
    if node.get("orderCn") or node.get("order"):
        order_text = node.get("orderCn") or node.get("order", "")
        if order_text:
            clauses.append(f"分类上属于{order_text}")
    if node.get("familyCn") or node.get("family"):
        family_text = node.get("familyCn") or node.get("family", "")
        if family_text:
            clauses.append(f"并归入{family_text}")
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
        level = node.get("taxonomyLevel")
        level_text = {"order": "目", "family": "科"}.get(level, "分类")
        latin_suffix = f"（{node['latinName']}）" if node.get("latinName") else ""
        if count:
            return f"{node['name']}{latin_suffix}是图谱中的{level_text}级分类节点，当前关联{count}种鸟类，如{examples}。"
        return f"{node['name']}{latin_suffix}是图谱中的{level_text}级分类节点，用于组织鸟类分类关系。"

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


def link_key(source: str, relation: str, target: str) -> str:
    return f"{source}__{relation}__{target}"


def numeric_position(seed: str, radius: float = 1.0) -> Tuple[float, float]:
    digest = md5(seed.encode("utf-8")).hexdigest()
    angle = int(digest[:8], 16) / 0xFFFFFFFF * math.tau
    distance = radius * (0.72 + int(digest[8:12], 16) / 0xFFFF * 0.56)
    return math.cos(angle) * distance, math.sin(angle) * distance


def numeric_depth(seed: str, amplitude: float = 1.0) -> float:
    digest = md5(f"z:{seed}".encode("utf-8")).hexdigest()
    normalized = int(digest[:8], 16) / 0xFFFFFFFF
    return (normalized * 2 - 1) * amplitude


def stable_unit_value(seed: str, salt: str = "") -> float:
    digest = md5(f"{seed}:{salt}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / 0xFFFFFFFFFFFF


def best_candidate_disk_offsets(
    item_ids: List[str],
    cluster_seed: str,
    radius: float,
    radial_power: float = 0.5,
    center_penalty_scale: float = 0.08,
    core_ratio: float = 0.0,
    core_radius_ratio: float = 0.32,
) -> Dict[str, Tuple[float, float]]:
    if not item_ids:
        return {}

    ordered_ids = sorted(item_ids, key=lambda item_id: md5(f"{cluster_seed}:{item_id}".encode("utf-8")).hexdigest())
    placed: List[Tuple[str, float, float]] = []
    attempts = max(18, min(48, len(ordered_ids) + 12))
    core_count = min(len(ordered_ids), max(0, int(round(len(ordered_ids) * core_ratio))))

    def place_items(
        current_ids: List[str],
        local_radius: float,
        local_radial_power: float,
        local_center_penalty_scale: float,
        nearest_weight: float,
    ) -> None:
        for item_id in current_ids:
            best_dx = 0.0
            best_dy = 0.0
            best_score = float("-inf")

            for attempt in range(attempts):
                candidate_radius = stable_unit_value(item_id, f"{cluster_seed}:r:{attempt}") ** local_radial_power * local_radius
                candidate_angle = stable_unit_value(item_id, f"{cluster_seed}:a:{attempt}") * math.tau
                candidate_dx = math.cos(candidate_angle) * candidate_radius
                candidate_dy = math.sin(candidate_angle) * candidate_radius

                if not placed:
                    score = local_radius - candidate_radius
                else:
                    nearest_sq = min(
                        (candidate_dx - placed_dx) ** 2 + (candidate_dy - placed_dy) ** 2
                        for _, placed_dx, placed_dy in placed
                    )
                    center_penalty = candidate_radius * candidate_radius * local_center_penalty_scale
                    score = nearest_sq * nearest_weight - center_penalty

                if score > best_score:
                    best_dx = candidate_dx
                    best_dy = candidate_dy
                    best_score = score

            placed.append((item_id, best_dx, best_dy))

    if core_count:
        place_items(
            ordered_ids[:core_count],
            radius * core_radius_ratio,
            max(1.08, radial_power + 0.24),
            center_penalty_scale * 0.3,
            0.42,
        )

    place_items(
        ordered_ids[core_count:],
        radius,
        radial_power,
        center_penalty_scale,
        1.0,
    )

    return {item_id: (dx, dy) for item_id, dx, dy in placed}


def round_position(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value, 2)


def ensure_taxonomy_node(
    nodes: Dict[str, Dict],
    taxonomy_nodes: Dict[str, Dict],
    level: str,
    latin_name: str,
    display_name: str,
) -> Dict:
    node_id = taxonomy_node_id(level, latin_name, display_name)
    existing = taxonomy_nodes.get(node_id)
    if existing:
        return existing

    node = {
        "id": node_id,
        "name": display_name or latin_name,
        "latinName": latin_name,
        "type": "taxonomy",
        "taxonomyLevel": level,
        "summary": "",
        "lat": None,
        "lng": None,
        "expandable": True,
        "memberCount": 0,
        "x": None,
        "y": None,
        "z": None,
    }
    taxonomy_nodes[node_id] = node
    nodes[node_id] = node
    return node


def add_unique_link(links: List[Dict], link_set: set[str], source: str, target: str, relation: str, label: Optional[str] = None, evidence: str = "") -> None:
    key = link_key(source, relation, target)
    if key in link_set:
        return
    links.append(
        {
            "key": key,
            "source": source,
            "target": target,
            "relation": relation,
            "label": label or RELATION_LABELS.get(relation, relation),
            "evidence": evidence,
        }
    )
    link_set.add(key)


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
    existing_link_keys: set[str] = set()

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
            "order": row.get("order", "").strip(),
            "family": row.get("family", "").strip(),
            "genus": row.get("genus", "").strip(),
            "species": row.get("species", "").strip(),
            "orderCn": row.get("order_cn", "").strip(),
            "familyCn": row.get("family_cn", "").strip(),
            "genusCn": row.get("genus_cn", "").strip(),
            "speciesCn": row.get("species_cn", "").strip(),
            "orderId": "",
            "familyId": "",
            "expandable": True,
            "x": None,
            "y": None,
            "z": None,
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
            "expandable": False,
            "x": None,
            "y": None,
            "z": None,
        }
        nodes[node["id"]] = node
        locations_by_id[node["id"]] = node
        locations_by_name[node["name"]] = node

    relation_targets: Dict[str, Dict] = {}
    incoming_birds: DefaultDict[str, List[str]] = defaultdict(list)
    grouped_values: DefaultDict[str, DefaultDict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

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
                    "expandable": False,
                    "x": None,
                    "y": None,
                    "z": None,
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

        add_unique_link(
            links,
            existing_link_keys,
            subject_node["id"],
            resolved_object_id,
            predicate,
            RELATION_LABELS[predicate],
            row["evidence"],
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

    taxonomy_nodes: Dict[str, Dict] = {}
    taxonomy_index = {
        "orders": {},
        "families": {},
        "birds_by_order": defaultdict(list),
        "birds_by_family": defaultdict(list),
        "family_children_by_order": defaultdict(list),
    }

    for bird in birds_by_id.values():
        order_latin = bird.get("order", "")
        family_latin = bird.get("family", "")
        order_name = bird.get("orderCn") or order_latin
        family_name = bird.get("familyCn") or family_latin

        order_node = None
        family_node = None

        if order_name or order_latin:
            order_node = ensure_taxonomy_node(nodes, taxonomy_nodes, "order", order_latin, order_name or order_latin)
            taxonomy_index["orders"][order_node["id"]] = order_node
            incoming_birds[order_node["id"]].append(bird["name"])
            taxonomy_index["birds_by_order"][order_node["id"]].append(bird["id"])
            bird["orderId"] = order_node["id"]

        if family_name or family_latin:
            family_node = ensure_taxonomy_node(nodes, taxonomy_nodes, "family", family_latin, family_name or family_latin)
            taxonomy_index["families"][family_node["id"]] = family_node
            incoming_birds[family_node["id"]].append(bird["name"])
            taxonomy_index["birds_by_family"][family_node["id"]].append(bird["id"])
            bird["familyId"] = family_node["id"]

        if family_node:
            add_unique_link(
                links,
                existing_link_keys,
                bird["id"],
                family_node["id"],
                "belongs_to_family",
                RELATION_LABELS["belongs_to_family"],
                "依据 birds.csv 中的 family / family_cn 字段补充。",
            )

        if family_node and order_node:
            add_unique_link(
                links,
                existing_link_keys,
                family_node["id"],
                order_node["id"],
                "belongs_to_order",
                RELATION_LABELS["belongs_to_order"],
                "依据 birds.csv 中的 order / order_cn 与 family / family_cn 字段补充。",
            )
            if family_node["id"] not in taxonomy_index["family_children_by_order"][order_node["id"]]:
                taxonomy_index["family_children_by_order"][order_node["id"]].append(family_node["id"])

    for order_node in taxonomy_index["orders"].values():
        order_node["memberCount"] = len(compact(taxonomy_index["birds_by_order"][order_node["id"]]))

    for family_node in taxonomy_index["families"].values():
        family_node["memberCount"] = len(compact(taxonomy_index["birds_by_family"][family_node["id"]]))

    complete_node_summaries(nodes, incoming_birds)

    return {
        "meta": {
            "title": "全球鸟类分布与生物多样性保护知识图谱",
            "mode": "chunked-static-data",
            "description": "由 data/birds.csv、data/locations.csv、data/relations.csv 自动构建为静态分片数据。",
            "updated_at": datetime.now().date().isoformat(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_files": [
                "data/birds.csv",
                "data/locations.csv",
                "data/relations.csv",
            ],
        },
        "nodes": nodes,
        "links": links,
        "taxonomy": taxonomy_index,
    }


def assign_taxonomy_layout(nodes: Dict[str, Dict], taxonomy: Dict) -> None:
    order_nodes = sorted(taxonomy["orders"].values(), key=lambda item: (item["name"], item["id"]))
    if not order_nodes:
        return

    order_radius = max(280.0, 160.0 * math.sqrt(len(order_nodes)))

    for order_index, order_node in enumerate(order_nodes):
        angle = -math.pi / 2 + math.tau * order_index / max(len(order_nodes), 1)
        order_x = math.cos(angle) * order_radius
        order_y = math.sin(angle) * order_radius
        order_node["x"] = order_x
        order_node["y"] = order_y
        order_node["z"] = numeric_depth(order_node["id"], amplitude=max(80.0, order_radius * 0.16))

        family_ids = sorted(taxonomy["family_children_by_order"][order_node["id"]])
        if not family_ids:
            continue

        family_radius = max(92.0, 20.0 * math.sqrt(len(family_ids)) + 48.0)
        family_offsets = best_candidate_disk_offsets(
            family_ids,
            order_node["id"],
            family_radius,
            radial_power=0.68,
            center_penalty_scale=0.11,
            core_ratio=0.18,
            core_radius_ratio=0.28,
        )

        for family_id in family_ids:
            family_node = nodes[family_id]
            offset_x, offset_y = family_offsets[family_id]
            family_node["x"] = order_x + offset_x
            family_node["y"] = order_y + offset_y
            family_node["z"] = (order_node["z"] or 0.0) + numeric_depth(
                family_node["id"],
                amplitude=max(24.0, family_radius * 0.24),
            )


def assign_bird_layout(nodes: Dict[str, Dict], birds_by_id: Dict[str, Dict], taxonomy: Dict) -> None:
    grouped_birds: DefaultDict[str, List[Dict]] = defaultdict(list)
    fallback_birds: List[Dict] = []

    for bird in birds_by_id.values():
        anchor_id = bird.get("familyId") or bird.get("orderId")
        if anchor_id:
            grouped_birds[anchor_id].append(bird)
        else:
            fallback_birds.append(bird)

    for anchor_id, birds in grouped_birds.items():
        anchor_node = nodes.get(anchor_id)
        if not anchor_node or anchor_node.get("x") is None or anchor_node.get("y") is None:
            fallback_birds.extend(birds)
            continue

        cluster_radius = max(44.0, 16.0 * math.sqrt(len(birds)) + 18.0)
        bird_offsets = best_candidate_disk_offsets(
            [bird["id"] for bird in birds],
            anchor_id,
            cluster_radius,
            radial_power=0.82,
            center_penalty_scale=0.14,
            core_ratio=0.3,
            core_radius_ratio=0.24,
        )

        for bird in sorted(birds, key=lambda item: (item["name"], item["id"])):
            offset_x, offset_y = bird_offsets[bird["id"]]
            radial_ratio = math.hypot(offset_x, offset_y) / max(cluster_radius, 1.0)
            bird["x"] = anchor_node["x"] + offset_x
            bird["y"] = anchor_node["y"] + offset_y
            bird["z"] = (anchor_node.get("z") or 0.0) + numeric_depth(
                bird["id"],
                amplitude=max(12.0, cluster_radius * (0.18 + 0.08 * (1.0 - radial_ratio))),
            )

    if fallback_birds:
        outer_radius = max(420.0, 45.0 * math.sqrt(len(fallback_birds)) + 180.0)
        fallback_offsets = best_candidate_disk_offsets(
            [bird["id"] for bird in fallback_birds],
            "fallback-birds",
            outer_radius,
        )
        for bird in sorted(fallback_birds, key=lambda item: (item["name"], item["id"])):
            offset_x, offset_y = fallback_offsets[bird["id"]]
            bird["x"] = offset_x
            bird["y"] = offset_y
            bird["z"] = numeric_depth(bird["id"], amplitude=max(80.0, outer_radius * 0.18))


def assign_context_layout(nodes: Dict[str, Dict], links: List[Dict]) -> None:
    bird_neighbor_map: DefaultDict[str, List[str]] = defaultdict(list)

    for link in links:
        source_node = nodes[link["source"]]
        target_node = nodes[link["target"]]
        if source_node["type"] == "bird" and target_node["type"] != "bird":
            bird_neighbor_map[target_node["id"]].append(source_node["id"])
        elif target_node["type"] == "bird" and source_node["type"] != "bird":
            bird_neighbor_map[source_node["id"]].append(target_node["id"])

    type_radius = {
        "location": 92.0,
        "habitat": 70.0,
        "status": 56.0,
        "threat": 78.0,
        "taxonomy": 0.0,
    }

    for node_id, bird_ids in bird_neighbor_map.items():
        node = nodes[node_id]
        if node.get("x") is not None and node.get("y") is not None:
            continue

        bird_positions = [
            (nodes[bird_id]["x"], nodes[bird_id]["y"], nodes[bird_id].get("z") or 0.0)
            for bird_id in compact(bird_ids)
            if nodes.get(bird_id)
            and nodes[bird_id].get("x") is not None
            and nodes[bird_id].get("y") is not None
        ]

        if bird_positions:
            center_x = mean(position[0] for position in bird_positions)
            center_y = mean(position[1] for position in bird_positions)
            center_z = mean(position[2] for position in bird_positions)
            offset_x, offset_y = numeric_position(node_id, radius=type_radius.get(node["type"], 64.0))
            node["x"] = center_x + offset_x
            node["y"] = center_y + offset_y
            node["z"] = center_z + numeric_depth(node_id, amplitude=max(18.0, type_radius.get(node["type"], 64.0) * 0.5))
            continue

        if node.get("lat") is not None and node.get("lng") is not None:
            node["x"] = node["lng"] * 6.0
            node["y"] = -node["lat"] * 6.0
            node["z"] = numeric_depth(node_id, amplitude=42.0)
            continue

        fallback_x, fallback_y = numeric_position(node_id, radius=520.0)
        node["x"] = fallback_x
        node["y"] = fallback_y
        node["z"] = numeric_depth(node_id, amplitude=96.0)


def finalize_positions(nodes: Dict[str, Dict]) -> None:
    for node in nodes.values():
        if node.get("x") is None or node.get("y") is None:
            fallback_x, fallback_y = numeric_position(node["id"], radius=560.0)
            node["x"] = fallback_x
            node["y"] = fallback_y
        if node.get("z") is None:
            node["z"] = numeric_depth(node["id"], amplitude=96.0)
        node["x"] = round_position(node["x"])
        node["y"] = round_position(node["y"])
        node["z"] = round_position(node["z"])


def build_adjacency(links: List[Dict]) -> Dict[str, List[Dict]]:
    adjacency: DefaultDict[str, List[Dict]] = defaultdict(list)
    for link in links:
        adjacency[link["source"]].append(link)
        adjacency[link["target"]].append(link)
    return dict(adjacency)


def serialize_node(node: Dict) -> Dict:
    data = {key: value for key, value in node.items() if value not in ("", [])}
    if data.get("lat") is None:
        data.pop("lat", None)
    if data.get("lng") is None:
        data.pop("lng", None)
    return data


def serialize_link(link: Dict) -> Dict:
    return {
        "key": link["key"],
        "source": link["source"],
        "target": link["target"],
        "relation": link["relation"],
        "label": link["label"],
        "evidence": link.get("evidence", ""),
    }


def serialize_overview_node(node: Dict) -> Dict:
    data = {
        "id": node["id"],
        "name": node["name"],
        "type": node["type"],
        "expandable": node.get("expandable", False),
        "x": round_position(node.get("x")),
        "y": round_position(node.get("y")),
        "z": round_position(node.get("z")),
    }

    if node["type"] == "bird":
        data.update(
            {
                "englishName": node.get("englishName", ""),
                "latinName": node.get("latinName", ""),
                "order": node.get("order", ""),
                "family": node.get("family", ""),
                "orderCn": node.get("orderCn", ""),
                "familyCn": node.get("familyCn", ""),
                "orderId": node.get("orderId", ""),
                "familyId": node.get("familyId", ""),
            }
        )
    elif node["type"] == "taxonomy":
        data.update(
            {
                "latinName": node.get("latinName", ""),
                "taxonomyLevel": node.get("taxonomyLevel", ""),
                "memberCount": node.get("memberCount", 0),
            }
        )

    return {key: value for key, value in data.items() if value not in ("", None)}


def serialize_overview_link(link: Dict) -> Dict:
    return {
        "source": link["source"],
        "target": link["target"],
        "relation": link["relation"],
    }


def serialize_preview_node(node: Dict) -> Dict:
    data = {
        "id": node["id"],
        "name": node["name"],
        "type": node["type"],
        "expandable": node.get("expandable", False),
        "x": round_position(node.get("x")),
        "y": round_position(node.get("y")),
        "z": round_position(node.get("z")),
    }

    if node["type"] == "bird":
        data.update(
            {
                "familyId": node.get("familyId", ""),
                "orderId": node.get("orderId", ""),
            }
        )
    elif node["type"] == "taxonomy":
        data.update(
            {
                "taxonomyLevel": node.get("taxonomyLevel", ""),
            }
        )

    return {key: value for key, value in data.items() if value not in ("", None)}


def extract_chunk(node_id: str, nodes: Dict[str, Dict], links: List[Dict], adjacency: Dict[str, List[Dict]], taxonomy: Dict) -> Optional[Dict]:
    center = nodes.get(node_id)
    if not center:
        return None

    included_node_ids = {node_id}
    included_link_keys = set()

    for link in adjacency.get(node_id, []):
        included_node_ids.add(link["source"])
        included_node_ids.add(link["target"])
        included_link_keys.add(link["key"])

    if center["type"] == "bird":
        family_id = center.get("familyId")
        order_id = center.get("orderId")
        if family_id and family_id in nodes:
            included_node_ids.add(family_id)
            for link in adjacency.get(family_id, []):
                if link["source"] == family_id or link["target"] == family_id:
                    other_id = link["target"] if link["source"] == family_id else link["source"]
                    if other_id == order_id:
                        included_node_ids.add(other_id)
                        included_link_keys.add(link["key"])
        if order_id and order_id in nodes:
            included_node_ids.add(order_id)

    if center["type"] == "taxonomy" and center.get("taxonomyLevel") == "family":
        order_id = None
        for link in adjacency.get(node_id, []):
            if link["relation"] == "belongs_to_order":
                order_id = link["target"] if link["source"] == node_id else link["source"]
                break
        if order_id:
            included_node_ids.add(order_id)

    included_nodes = [serialize_node(nodes[item_id]) for item_id in included_node_ids]
    included_links = [
        serialize_link(link)
        for link in links
        if link["key"] in included_link_keys
        and link["source"] in included_node_ids
        and link["target"] in included_node_ids
    ]

    return {
        "meta": {
            "centerNodeId": node_id,
            "centerNodeType": center["type"],
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "includedNodeCount": len(included_nodes),
            "includedLinkCount": len(included_links),
            "layoutMode": "precomputed-static",
        },
        "center": {
            "id": center["id"],
            "name": center["name"],
            "type": center["type"],
        },
        "nodes": included_nodes,
        "links": included_links,
    }


def write_output_files(graph: Dict) -> None:
    nodes = graph["nodes"]
    links = graph["links"]
    taxonomy = graph["taxonomy"]
    meta = graph["meta"]

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    if LEGACY_OUTPUT_PATH.exists():
        LEGACY_OUTPUT_PATH.unlink()

    bird_nodes = sorted(
        (node for node in nodes.values() if node["type"] == "bird"),
        key=lambda item: (item["name"], item["id"]),
    )
    family_nodes = sorted(
        (node for node in nodes.values() if node["type"] == "taxonomy" and node.get("taxonomyLevel") == "family"),
        key=lambda item: (item["name"], item["id"]),
    )
    order_nodes = sorted(
        (node for node in nodes.values() if node["type"] == "taxonomy" and node.get("taxonomyLevel") == "order"),
        key=lambda item: (item["name"], item["id"]),
    )

    summary_payload = {
        "meta": {
            **meta,
            "counts": {
                "birds": len(bird_nodes),
                "orders": len(order_nodes),
                "families": len(family_nodes),
            },
        },
        "columns": ["id", "name", "englishName", "latinName"],
        "items": [
            [bird["id"], bird["name"], bird.get("englishName", ""), bird.get("latinName", "")]
            for bird in bird_nodes
        ],
    }
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    skeleton_links = [
        serialize_link(link)
        for link in links
        if link["relation"] == "belongs_to_order"
        and nodes[link["source"]]["type"] == "taxonomy"
        and nodes[link["target"]]["type"] == "taxonomy"
    ]
    skeleton_payload = {
        "meta": {
            **meta,
            "counts": {
                "orders": len(order_nodes),
                "families": len(family_nodes),
                "links": len(skeleton_links),
            },
            "layoutMode": "precomputed-static",
        },
        "nodes": [serialize_node(node) for node in [*order_nodes, *family_nodes]],
        "links": skeleton_links,
    }
    (OUTPUT_DIR / "taxonomy_skeleton.json").write_text(json.dumps(skeleton_payload, ensure_ascii=False), encoding="utf-8")

    preview_links = [
        serialize_overview_link(link)
        for link in links
        if link["relation"] in {"belongs_to_family", "belongs_to_order"}
    ]
    preview_payload = {
        "meta": {
            **meta,
            "counts": {
                "birds": len(bird_nodes),
                "orders": len(order_nodes),
                "families": len(family_nodes),
                "nodes": len(order_nodes) + len(family_nodes) + len(bird_nodes),
                "links": len(preview_links),
            },
            "layoutMode": "precomputed-static",
            "scope": "startup-graph-preview",
        },
        "nodes": [serialize_preview_node(node) for node in [*order_nodes, *family_nodes, *bird_nodes]],
        "links": preview_links,
    }
    (OUTPUT_DIR / "graph_preview.json").write_text(
        json.dumps(preview_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    adjacency = build_adjacency(links)
    chunk_ids = [node["id"] for node in bird_nodes] + [node["id"] for node in family_nodes] + [node["id"] for node in order_nodes]
    for node_id in chunk_ids:
        payload = extract_chunk(node_id, nodes, links, adjacency, taxonomy)
        if not payload:
            continue
        (NODES_DIR / f"{node_id}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    graph = build_graph()
    nodes = graph["nodes"]
    birds_by_id = {node_id: node for node_id, node in nodes.items() if node["type"] == "bird"}

    assign_taxonomy_layout(nodes, graph["taxonomy"])
    assign_bird_layout(nodes, birds_by_id, graph["taxonomy"])
    assign_context_layout(nodes, graph["links"])
    finalize_positions(nodes)

    write_output_files(graph)
    print(f"chunked bird graph written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
