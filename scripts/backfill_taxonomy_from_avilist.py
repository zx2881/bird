"""
从 AviList 鸟名列表 (data/bird_titles.csv) 中读取 order/family 信息，
匹配回填到 birds.csv 的 order/family 列。

中文目名/科名无法从 AviList 获取，留空供后续 fetch_taxonomy.py 补充。

用法:
  python scripts/backfill_taxonomy_from_avilist.py
  npm run build:data  # 随后重建 knowledge.json
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BIRDS_PATH = DATA_DIR / "birds.csv"
TITLES_PATH = DATA_DIR / "bird_titles.csv"

BIRDS_HEADERS = [
    "id", "name", "english_name", "latin_name", "summary", "lat", "lng", "image_url",
    "order", "family", "order_cn", "family_cn",
]


def build_avilist_lookup(path: Path) -> Dict[str, Tuple[str, str]]:
    lookup: Dict[str, Tuple[str, str]] = {}
    if not path.exists():
        print(f"警告: {path} 不存在，无法回填。请先运行 npm run download:bird-names")
        return lookup
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            en_name = (row.get("english_name") or "").strip().lower()
            order = (row.get("order") or "").strip()
            family = (row.get("family") or "").strip()
            if en_name and (order or family):
                lookup[en_name] = (order, family)
    return lookup


def main() -> None:
    if not BIRDS_PATH.exists():
        raise SystemExit(f"birds.csv 不存在: {BIRDS_PATH}")

    lookup = build_avilist_lookup(TITLES_PATH)
    if not lookup:
        raise SystemExit("AviList 查找表为空，无法回填。")

    birds_rows: list[dict] = []
    with BIRDS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            birds_rows.append({k: (v or "").strip() for k, v in row.items()})

    filled_order = 0
    filled_family = 0
    missed = 0

    for row in birds_rows:
        en_name = (row.get("english_name") or "").strip().lower()
        if not en_name:
            missed += 1
            continue

        avi = lookup.get(en_name)
        if not avi:
            missed += 1
            continue

        order, family = avi
        if not row.get("order") and order:
            row["order"] = order
            filled_order += 1
        if not row.get("family") and family:
            row["family"] = family
            filled_family += 1

    temp_path = BIRDS_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BIRDS_HEADERS)
        writer.writeheader()
        for row in birds_rows:
            writer.writerow({h: row.get(h, "") for h in BIRDS_HEADERS})
    temp_path.replace(BIRDS_PATH)

    total = len(birds_rows)
    already = total - missed - sum(1 for r in birds_rows if not r.get("order") and not r.get("family"))
    print(f"总计 {total} 种鸟类")
    print(f"回填 order: {filled_order} / 空余: {sum(1 for r in birds_rows if not r.get('order'))}")
    print(f"回填 family: {filled_family} / 空余: {sum(1 for r in birds_rows if not r.get('family'))}")
    print(f"AviList 中未匹配: {missed}")
    if missed > 0:
        print(f"（未匹配的可能是英文名拼写差异，可后续用 fetch_taxonomy.py 通过 Wikidata 补充）")
    print(f"已保存到 {BIRDS_PATH}")


if __name__ == "__main__":
    main()
