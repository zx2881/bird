"""
校验 data/ 目录中 CSV 主数据源的一致性和完整性。

检查项:
  1. 各 CSV 必需的列是否存在
  2. birds.csv / locations.csv ID 是否唯一
  3. relations.csv 的 subject_id 是否在 birds.csv 中存在
  4. relations.csv 的 object_id (Location/Bird 类型) 是否存在对应实体
  5. predicate 是否在 RELATION_LABELS 范围内
  6. 坐标是否在合理范围内
  7. 核心必填字段是否有空值
  8. 可选字段缺失情况汇总

用法:
  python scripts/validate_data.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

RELATION_LABELS = {
    "distributed_in", "lives_in", "has_status",
    "threatened_by", "belongs_to",
    "belongs_to_kingdom", "belongs_to_phylum", "belongs_to_class",
    "belongs_to_order", "belongs_to_family", "belongs_to_genus",
    "belongs_to_species",
}

ENTITY_TYPES = {"Bird", "Location", "Habitat", "Status", "Threat", "Taxon"}

BIRDS_REQUIRED = ["id", "name", "english_name"]
BIRDS_OPTIONAL_TRACKED = ["latin_name"]
LOCATIONS_REQUIRED = ["id", "name"]
LOCATIONS_OPTIONAL_TRACKED = ["lat", "lng"]
RELATIONS_REQUIRED = [
    "subject_id", "subject", "predicate", "object_id",
    "object", "subject_type", "object_type",
]


def read_csv(path: Path) -> tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = [row for row in reader]
    return headers, rows


def check_required_headers(path: Path, headers: List[str], required: List[str]) -> List[str]:
    missing = [col for col in required if col not in headers]
    if missing:
        return [f"{path.name}: 缺少必要列 {missing}"]
    return []


def check_unique_ids(path: Path, rows: List[Dict[str, str]], id_field: str) -> List[str]:
    seen: Dict[str, int] = {}
    errors = []
    for idx, row in enumerate(rows, start=2):
        rid = row.get(id_field, "").strip()
        if not rid:
            errors.append(f"{path.name} 第 {idx} 行: {id_field} 为空")
            continue
        if rid in seen:
            errors.append(f"{path.name} 第 {idx} 行: {id_field} '{rid}' 重复（首次出现于第 {seen[rid]} 行）")
        else:
            seen[rid] = idx
    return errors


def check_coordinates(path: Path, rows: List[Dict[str, str]]) -> List[str]:
    errors = []
    for idx, row in enumerate(rows, start=2):
        lat_raw = row.get("lat", "").strip()
        lng_raw = row.get("lng", "").strip()
        if not lat_raw and not lng_raw:
            continue
        if not lat_raw or not lng_raw:
            errors.append(f"{path.name} 第 {idx} 行: 坐标不完整 (lat={lat_raw}, lng={lng_raw})")
            continue
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except ValueError:
            errors.append(f"{path.name} 第 {idx} 行: 坐标不是有效数字 (lat={lat_raw}, lng={lng_raw})")
            continue
        if lat is not None and (lat < -90 or lat > 90):
            errors.append(f"{path.name} 第 {idx} 行: lat 超出范围 [-90, 90]: {lat}")
        if lng is not None and (lng < -180 or lng > 180):
            errors.append(f"{path.name} 第 {idx} 行: lng 超出范围 [-180, 180]: {lng}")
    return errors


def summarize_missing_values(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    warnings = []
    for field in fields:
        missing_count = sum(1 for row in rows if not row.get(field, "").strip())
        if missing_count:
            warnings.append(f"{path.name}: 可选字段 '{field}' 有 {missing_count} 行为空")
    return warnings


def check_required_values(path: Path, rows: List[Dict[str, str]], required: List[str]) -> List[str]:
    errors = []
    for idx, row in enumerate(rows, start=2):
        for field in required:
            if not row.get(field, "").strip():
                errors.append(f"{path.name} 第 {idx} 行: 必填字段 '{field}' 为空")
    return errors


def validate_birds() -> Tuple[List[str], List[str]]:
    path = DATA_DIR / "birds.csv"
    if not path.exists():
        return [f"{path.name} 不存在"], []
    headers, rows = read_csv(path)
    errors = []
    warnings = []
    errors.extend(check_required_headers(path, headers, BIRDS_REQUIRED + BIRDS_OPTIONAL_TRACKED + ["lat", "lng"]))
    errors.extend(check_unique_ids(path, rows, "id"))
    errors.extend(check_coordinates(path, rows))
    errors.extend(check_required_values(path, rows, BIRDS_REQUIRED))
    warnings.extend(summarize_missing_values(path, rows, BIRDS_OPTIONAL_TRACKED + ["lat", "lng"]))
    return errors, warnings


def validate_locations() -> Tuple[List[str], List[str]]:
    path = DATA_DIR / "locations.csv"
    if not path.exists():
        return [f"{path.name} 不存在"], []
    headers, rows = read_csv(path)
    errors = []
    warnings = []
    errors.extend(check_required_headers(path, headers, LOCATIONS_REQUIRED + LOCATIONS_OPTIONAL_TRACKED))
    errors.extend(check_unique_ids(path, rows, "id"))
    errors.extend(check_coordinates(path, rows))
    errors.extend(check_required_values(path, rows, LOCATIONS_REQUIRED))
    warnings.extend(summarize_missing_values(path, rows, LOCATIONS_OPTIONAL_TRACKED))
    return errors, warnings


def validate_relations() -> Tuple[List[str], List[str]]:
    path = DATA_DIR / "relations.csv"
    if not path.exists():
        return [f"{path.name} 不存在"], []

    birds_path = DATA_DIR / "birds.csv"
    locations_path = DATA_DIR / "locations.csv"

    birds_ids: Dict[str, str] = {}
    if birds_path.exists():
        _, birds_rows = read_csv(birds_path)
        for row in birds_rows:
            rid = row.get("id", "").strip()
            name = row.get("name", "").strip()
            if rid:
                birds_ids[rid] = name

    locations_ids: Dict[str, str] = {}
    if locations_path.exists():
        _, loc_rows = read_csv(locations_path)
        for row in loc_rows:
            rid = row.get("id", "").strip()
            name = row.get("name", "").strip()
            if rid:
                locations_ids[rid] = name

    headers, rows = read_csv(path)
    errors = []
    errors.extend(check_required_headers(path, headers, RELATIONS_REQUIRED))

    for idx, row in enumerate(rows, start=2):
        subject_id = row.get("subject_id", "").strip()
        subject = row.get("subject", "").strip()
        predicate = row.get("predicate", "").strip()
        object_id = row.get("object_id", "").strip()
        object_name = row.get("object", "").strip()
        subject_type = row.get("subject_type", "").strip()
        object_type = row.get("object_type", "").strip()

        if not subject_id:
            errors.append(f"relations.csv 第 {idx} 行: subject_id 为空")
        elif subject_id not in birds_ids:
            errors.append(f"relations.csv 第 {idx} 行: subject_id '{subject_id}' 在 birds.csv 中不存在")

        if not predicate:
            errors.append(f"relations.csv 第 {idx} 行: predicate 为空")
        elif predicate not in RELATION_LABELS:
            errors.append(f"relations.csv 第 {idx} 行: 不支持的 predicate '{predicate}'")

        if not subject_type:
            errors.append(f"relations.csv 第 {idx} 行: subject_type 为空")
        elif subject_type != "Bird":
            errors.append(f"relations.csv 第 {idx} 行: subject_type 应为 Bird，当前为 '{subject_type}'")

        if not object_type:
            errors.append(f"relations.csv 第 {idx} 行: object_type 为空")
        elif object_type not in ENTITY_TYPES:
            errors.append(f"relations.csv 第 {idx} 行: 不支持的 object_type '{object_type}'")

        if not object_name:
            errors.append(f"relations.csv 第 {idx} 行: object 为空")

        if object_type == "Location" and object_id:
            if object_id not in locations_ids:
                errors.append(f"relations.csv 第 {idx} 行: Location object_id '{object_id}' 在 locations.csv 中不存在")

        if object_type == "Bird" and object_id:
            if object_id not in birds_ids:
                errors.append(f"relations.csv 第 {idx} 行: Bird object_id '{object_id}' 在 birds.csv 中不存在")

    return errors, []


def main() -> int:
    all_errors: List[str] = []
    all_warnings: List[str] = []

    for errors, warnings in (validate_birds(), validate_locations(), validate_relations()):
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if not all_errors:
        print("所有硬性校验通过 OK")
        if all_warnings:
            print("\n可选字段提示:")
            for warning in all_warnings:
                print(f"  - {warning}")
        return 0

    print(f"发现 {len(all_errors)} 个问题:\n")
    for error in all_errors[:100]:
        print(f"  - {error}")
    if len(all_errors) > 100:
        print(f"  ... 还有 {len(all_errors) - 100} 个问题未显示")

    return 1


if __name__ == "__main__":
    sys.exit(main())
