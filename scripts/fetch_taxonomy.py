"""
通过 Wikidata API 获取鸟类的完整分类信息（界门纲目科属种），回填到 birds.csv 和 relations.csv。

数据源:
  1. en.wikipedia.org API → 获取 wikibase_item (Wikidata QID)
  2. www.wikidata.org API → 沿 P171(parent taxon) 链向上遍历，获取各层级分类

输出:
  - birds.csv 新增列: order, family, order_cn, family_cn
  - relations.csv 新增 belongs_to 关系（目/科两级）

说明:
  - 界(Animalia)/门(Chordata)/纲(Aves) 对所有鸟类恒定，不写入 CSV 列
  - 属/种信息已由 latin_name 覆盖，不重复写入
  - 支持断点续跑：已处理过的鸟类自动跳过
  - 中文标签从 Wikidata 的 zh 语言标签获取

示例:
  python scripts/fetch_taxonomy.py
  python scripts/fetch_taxonomy.py --delay 0.5 --proxy http://127.0.0.1:7890
  python scripts/fetch_taxonomy.py --overwrite --build-json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
BUILD_SCRIPT = ROOT / "scripts" / "build_knowledge_json.py"

TAXONOMY_COLUMNS = ["order", "family", "order_cn", "family_cn"]

BIRDS_HEADERS = [
    "id", "name", "english_name", "latin_name", "summary", "lat", "lng", "image_url",
] + TAXONOMY_COLUMNS

RELATIONS_HEADERS = [
    "subject_id", "subject", "predicate", "object_id", "object",
    "subject_type", "object_type", "evidence", "object_summary",
]

RANK_LABELS = {
    "Q36732": "kingdom",
    "Q38348": "phylum",
    "Q37517": "class",
    "Q36602": "order",
    "Q35409": "family",
    "Q34740": "genus",
    "Q7432": "species",
}


def _api_get(url: str, opener=None, timeout: int = 25, max_retries: int = 3) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "bird-kg-taxonomy/1.0 (research prototype; contact local-user)",
            "Accept": "application/json",
        },
    )
    for attempt in range(max_retries):
        try:
            if opener:
                with opener.open(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            else:
                with urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 429 and attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  [retry] 429 限流，{wait}s 后重试 ({attempt + 1}/{max_retries - 1})")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"API 请求失败: {url}")


def get_wikidata_qid(title: str, opener=None) -> Optional[str]:
    """通过 en.wikipedia API 获取页面对应的 Wikidata QID"""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "pageprops",
        "titles": title,
    }
    url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
    payload = _api_get(url, opener=opener)
    pages = payload.get("query", {}).get("pages", [])
    if not pages:
        return None
    pageprops = pages[0].get("pageprops", {})
    return pageprops.get("wikibase_item")


def get_entity_claims(qid: str, opener=None) -> dict:
    """获取 Wikidata 实体的 claims"""
    url = (
        f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    )
    payload = _api_get(url, opener=opener)
    entities = payload.get("entities", {})
    entity = entities.get(qid, {})
    return entity.get("claims", {})


def get_entity_label(qid: str, lang: str = "en", opener=None) -> str:
    """获取 Wikidata 实体的标签"""
    url = (
        f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    )
    payload = _api_get(url, opener=opener)
    entities = payload.get("entities", {})
    entity = entities.get(qid, {})
    labels = entity.get("labels", {})
    return labels.get(lang, {}).get("value", "")


def traverse_taxonomy(start_qid: str, opener=None, delay: float = 0.3) -> Dict[str, Tuple[str, str]]:
    """从物种 QID 开始，沿 P171 向上遍历，收集各层级分类信息

    返回 {rank: (en_label, zh_label)} 的字典
    """
    taxonomy: Dict[str, Tuple[str, str]] = {}
    current_qid = start_qid
    visited = set()
    max_depth = 20

    for _ in range(max_depth):
        if current_qid in visited:
            break
        visited.add(current_qid)

        claims = get_entity_claims(current_qid, opener=opener)
        if delay:
            time.sleep(delay)

        rank_from_claims = _extract_rank(claims)
        if rank_from_claims:
            en_label = get_entity_label(current_qid, "en", opener)
            zh_label = get_entity_label(current_qid, "zh", opener)
            if delay:
                time.sleep(delay)
            if rank_from_claims not in taxonomy:
                taxonomy[rank_from_claims] = (en_label, zh_label)

        p171_claims = claims.get("P171", [])
        if not p171_claims:
            break
        datavalue = p171_claims[0].get("mainsnak", {}).get("datavalue", {})
        parent_qid = datavalue.get("value", {}).get("id")
        if not parent_qid:
            break
        current_qid = parent_qid

    return taxonomy


def _extract_rank(claims: dict) -> Optional[str]:
    """从 claims 中提取 P105 taxon rank"""
    p105 = claims.get("P105", [])
    if not p105:
        return None
    datavalue = p105[0].get("mainsnak", {}).get("datavalue", {})
    rank_qid = datavalue.get("value", {}).get("id")
    return RANK_LABELS.get(rank_qid) if rank_qid else None


def stable_id(prefix: str, name: str) -> str:
    normalized = re.sub(r"\s+", "-", name.strip().lower())
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", normalized).strip("-")
    digest = md5(name.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{normalized}-{digest}" if normalized else f"{prefix}-{digest}"


def load_csv_rows(path: Path, headers: List[str]) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            normalized = {header: (row.get(header, "") or "").strip() for header in headers}
            rows.append(normalized)
        return rows


def write_csv_rows(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    temp_path.replace(path)


def build_taxon_relations(
    bird_row: Dict[str, str],
    taxonomy: Dict[str, Tuple[str, str]],
) -> List[Dict[str, str]]:
    """根据分类信息生成 belongs_to 关系（目和科两级）"""
    relations: List[Dict[str, str]] = []
    taxa = [
        ("order", "目"),
        ("family", "科"),
    ]
    for rank, cn_label in taxa:
        en_name, zh_name = taxonomy.get(rank, ("", ""))
        if not en_name and not zh_name:
            continue
        display_name = zh_name or en_name
        object_id = stable_id("taxonomy", display_name)
        summary = f"依据 Wikidata 抽取的分类单元：{display_name}（{cn_label}）。"
        relations.append({
            "subject_id": bird_row["id"],
            "subject": bird_row["name"],
            "predicate": "belongs_to",
            "object_id": object_id,
            "object": display_name,
            "subject_type": "Bird",
            "object_type": "Taxon",
            "evidence": f"Wikidata 分类: {bird_row['name']} 属于{cn_label} {display_name}。",
            "object_summary": summary,
        })
    return relations


def already_has_taxonomy(bird_row: Dict[str, str]) -> bool:
    return bool(bird_row.get("order") or bird_row.get("family"))


def maybe_build_json(build_json: bool) -> None:
    if not build_json:
        return
    if not BUILD_SCRIPT.exists():
        print("未找到 build_knowledge_json.py，跳过 knowledge.json 构建。", file=sys.stderr)
        return
    import subprocess
    exit_code = subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=False).returncode
    if exit_code != 0:
        raise RuntimeError("执行 build_knowledge_json.py 失败")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过 Wikidata API 获取鸟类分类信息")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--overwrite", action="store_true", help="强制重取已有分类的鸟类")
    parser.add_argument("--build-json", action="store_true", help="结束后自动执行 build_knowledge_json.py")
    parser.add_argument("--delay", type=float, default=0.5, help="Wikidata 请求间隔秒数，默认 0.5")
    parser.add_argument("--proxy", type=str, default="", help="HTTPS 代理地址")
    parser.add_argument("--limit", type=int, default=0, help="限制处理数量（测试用）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    birds_path = data_dir / "birds.csv"
    relations_path = data_dir / "relations.csv"

    if not birds_path.exists():
        raise SystemExit(f"birds.csv 不存在: {birds_path}")

    opener = None
    if args.proxy:
        proxy_handler = ProxyHandler({"https": args.proxy})
        opener = build_opener(proxy_handler)
        install_opener(opener)

    birds_rows = load_csv_rows(birds_path, BIRDS_HEADERS)
    relations_rows = load_csv_rows(relations_path, RELATIONS_HEADERS)

    processed = 0
    success = 0
    skipped = 0

    for bird_row in birds_rows:
        if args.limit > 0 and processed >= args.limit:
            break

        if already_has_taxonomy(bird_row) and not args.overwrite:
            skipped += 1
            continue

        name = bird_row["name"]
        english_name = bird_row["english_name"]
        print(f"[taxonomy] {name} ({english_name})")

        if not english_name:
            print(f"  [warn] 无英文名，跳过")
            skipped += 1
            continue

        try:
            qid = get_wikidata_qid(english_name, opener=opener)
            if args.delay:
                time.sleep(args.delay)
        except Exception as e:
            print(f"  [error] 获取 Wikidata QID 失败: {e}")
            processed += 1
            continue

        if not qid:
            print(f"  [warn] 未找到 Wikidata 条目")
            processed += 1
            continue

        print(f"  QID: {qid}")

        try:
            taxonomy = traverse_taxonomy(qid, opener=opener, delay=args.delay)
        except Exception as e:
            print(f"  [error] 遍历分类链失败: {e}")
            processed += 1
            continue

        if not taxonomy:
            print(f"  [warn] 未获取到分类信息")
            processed += 1
            continue

        order_en, order_cn = taxonomy.get("order", ("", ""))
        family_en, family_cn = taxonomy.get("family", ("", ""))

        bird_row["order"] = order_en
        bird_row["family"] = family_en
        bird_row["order_cn"] = order_cn
        bird_row["family_cn"] = family_cn

        taxon_relations = build_taxon_relations(bird_row, taxonomy)
        if taxon_relations:
            existing_keys = {
                (r["subject_id"], r["predicate"], r["object_id"])
                for r in relations_rows
            }
            for rel in taxon_relations:
                key = (rel["subject_id"], rel["predicate"], rel["object_id"])
                if key not in existing_keys:
                    relations_rows.append(rel)
                    existing_keys.add(key)

        success += 1
        processed += 1

    if success > 0:
        write_csv_rows(birds_path, BIRDS_HEADERS, birds_rows)
        write_csv_rows(relations_path, RELATIONS_HEADERS, relations_rows)
        print(f"\n已更新 birds.csv 和 relations.csv")
    else:
        print(f"\n无新数据写入")

    print(f"处理总数: {processed}, 成功: {success}, 跳过: {skipped}")
    maybe_build_json(args.build_json)


if __name__ == "__main__":
    main()
