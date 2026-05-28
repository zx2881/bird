"""
通过 Wikipedia / Wikidata API 获取鸟类的分类信息（界 / 门 / 纲 / 目 / 科 / 属 / 种），
回填到 birds.csv，并补充完整分类链关系。

数据源:
  1. en.wikipedia.org API → 精确标题或搜索结果 → 获取 wikibase_item (Wikidata QID)
  2. www.wikidata.org API → 沿 P171(parent taxon) 链向上遍历，收集 taxonomy ranks

输出:
  - birds.csv 新增列:
    kingdom, phylum, class, order, family, genus, species,
    kingdom_cn, phylum_cn, class_cn, order_cn, family_cn, genus_cn, species_cn
  - relations.csv 新增 belongs_to 关系（界 / 门 / 纲 / 目 / 科 / 属 / 种）

说明:
  - 非中文字段优先使用 P225（科学分类名），避免 species 列落成英文俗名
  - 查询链路带缓存，同一属 / 科 / 目不会重复拉取实体，速度显著快于串行逐层请求
  - --build-json 会继续调用 build_knowledge_json.py，生成 public/data/ 下的静态分片

示例:
  python scripts/fetch_taxonomy.py
  python scripts/fetch_taxonomy.py --delay 0.1 --proxy http://127.0.0.1:7890
  python scripts/fetch_taxonomy.py --overwrite --build-json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
BUILD_SCRIPT = ROOT / "scripts" / "build_knowledge_json.py"

TARGET_RANKS = ("kingdom", "phylum", "class", "order", "family", "genus", "species")
TAXONOMY_COLUMNS = [
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "kingdom_cn",
    "phylum_cn",
    "class_cn",
    "order_cn",
    "family_cn",
    "genus_cn",
    "species_cn",
]

BIRDS_HEADERS = [
    "id",
    "name",
    "english_name",
    "latin_name",
    "summary",
    "lat",
    "lng",
    "image_url",
] + TAXONOMY_COLUMNS

RELATIONS_HEADERS = [
    "subject_id",
    "subject",
    "predicate",
    "object_id",
    "object",
    "subject_type",
    "object_type",
    "evidence",
    "object_summary",
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

RANK_DISPLAY = {
    "kingdom": "界",
    "phylum": "门",
    "class": "纲",
    "order": "目",
    "family": "科",
    "genus": "属",
    "species": "种",
}


def configure_csv_field_size_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def _api_get(url: str, opener=None, timeout: int = 25, max_retries: int = 3) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "bird-kg-taxonomy/2.0 (research prototype; contact local-user)",
            "Accept": "application/json",
        },
    )
    for attempt in range(max_retries):
        try:
            if opener:
                with opener.open(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
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


def normalize_lookup_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def sentence_case_title(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", (value or "").strip())
    if not cleaned:
        return ""
    return cleaned[:1].upper() + cleaned[1:].lower()


def unique_non_empty(values: Sequence[str]) -> List[str]:
    result: List[str] = []
    seen: Set[str] = set()
    for value in values:
        cleaned = re.sub(r"\s+", " ", (value or "").strip())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def stable_id(prefix: str, name: str) -> str:
    normalized = re.sub(r"\s+", "-", name.strip().lower())
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", normalized).strip("-")
    digest = md5(name.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{normalized}-{digest}" if normalized else f"{prefix}-{digest}"


def slugify(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().lower())
    return re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", normalized).strip("-")


def taxonomy_relation_object_id(rank: str, scientific_name: str, chinese_name: str) -> str:
    base = (scientific_name or chinese_name or f"{rank}-unknown").strip()
    normalized = slugify(base)
    digest = md5(f"{rank}:{base}".encode("utf-8")).hexdigest()[:6]
    return f"taxonomy-{rank}-{normalized or digest}"


def load_csv_rows(path: Path, headers: List[str]) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise ValueError(f"{path.name} 为空，或无法读取 CSV 表头。")
        if any("\x00" in field for field in fieldnames):
            raise ValueError(f"{path.name} 包含 NUL 字节，文件已损坏，无法解析。")
        missing_headers = [header for header in headers if header not in fieldnames]
        if missing_headers:
            joined = ", ".join(missing_headers[:8])
            suffix = "..." if len(missing_headers) > 8 else ""
            raise ValueError(f"{path.name} 缺少必要列: {joined}{suffix}")
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


def extract_claim_target_id(entity: dict, property_id: str) -> str:
    claims = entity.get("claims", {})
    for claim in claims.get(property_id, []):
        datavalue = claim.get("mainsnak", {}).get("datavalue", {})
        value = datavalue.get("value", {})
        if isinstance(value, dict):
            target_id = value.get("id", "")
            if target_id:
                return target_id
    return ""


def extract_claim_string(entity: dict, property_id: str) -> str:
    claims = entity.get("claims", {})
    for claim in claims.get(property_id, []):
        datavalue = claim.get("mainsnak", {}).get("datavalue", {})
        value = datavalue.get("value", "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_label(entity: dict, lang: str) -> str:
    labels = entity.get("labels", {})
    return (labels.get(lang, {}) or {}).get("value", "").strip()


def extract_aliases(entity: dict, lang: str) -> List[str]:
    aliases = entity.get("aliases", {})
    return [
        (item.get("value", "") or "").strip()
        for item in aliases.get(lang, []) or []
        if (item.get("value", "") or "").strip()
    ]


def extract_description(entity: dict, lang: str) -> str:
    descriptions = entity.get("descriptions", {})
    return (descriptions.get(lang, {}) or {}).get("value", "").strip()


def extract_rank(entity: dict) -> str:
    rank_qid = extract_claim_target_id(entity, "P105")
    return RANK_LABELS.get(rank_qid, "")


def extract_parent_qid(entity: dict) -> str:
    return extract_claim_target_id(entity, "P171")


def extract_taxon_name(entity: dict) -> str:
    return extract_claim_string(entity, "P225") or extract_label(entity, "en")


def score_wikipedia_page(query: str, page_title: str) -> int:
    normalized_query = normalize_lookup_key(query)
    normalized_title = normalize_lookup_key(page_title)
    if not normalized_query or not normalized_title:
        return 0
    if normalized_query == normalized_title:
        return 200
    score = 0
    if normalized_query in normalized_title:
        score += 120
    query_words = set(normalized_query.split())
    title_words = set(normalized_title.split())
    score += 10 * len(query_words & title_words)
    if page_title and page_title[0:1] == query[0:1]:
        score += 5
    return score


def score_wikidata_entity(term: str, entity: dict, preferred_ranks: Set[str]) -> int:
    normalized_term = normalize_lookup_key(term)
    if not normalized_term:
        return 0

    score = 0
    scientific_name = normalize_lookup_key(extract_taxon_name(entity))
    en_label = normalize_lookup_key(extract_label(entity, "en"))
    aliases = {normalize_lookup_key(value) for value in extract_aliases(entity, "en")}
    rank = extract_rank(entity)
    description = extract_description(entity, "en").lower()

    if scientific_name == normalized_term:
        score += 220
    if en_label == normalized_term:
        score += 180
    if normalized_term in aliases:
        score += 160
    if normalized_term and scientific_name and normalized_term in scientific_name:
        score += 30
    if normalized_term and en_label and normalized_term in en_label:
        score += 20
    if rank and rank in preferred_ranks:
        score += 25
    if "bird" in description:
        score += 10
    return score


class TaxonomyClient:
    def __init__(self, opener=None, delay: float = 0.1) -> None:
        self.opener = opener
        self.delay = max(delay, 0.0)
        self.last_request_at = 0.0
        self.entity_cache: Dict[str, dict] = {}
        self.wikipedia_title_cache: Dict[str, str] = {}
        self.wikipedia_search_cache: Dict[str, str] = {}
        self.wikidata_search_cache: Dict[Tuple[str, Tuple[str, ...]], str] = {}

    def _get(self, url: str) -> dict:
        if self.delay > 0:
            elapsed = time.monotonic() - self.last_request_at
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        payload = _api_get(url, opener=self.opener)
        self.last_request_at = time.monotonic()
        return payload

    def get_entity(self, qid: str) -> dict:
        if not qid:
            return {}
        if qid not in self.entity_cache:
            url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
            payload = self._get(url)
            entities = payload.get("entities", {})
            self.entity_cache[qid] = entities.get(qid, {})
        return self.entity_cache.get(qid, {})

    def normalize_taxon_qid(self, qid: str) -> str:
        entity = self.get_entity(qid)
        if not entity:
            return ""
        if extract_rank(entity) in TARGET_RANKS:
            return qid
        if extract_parent_qid(entity):
            return qid
        return ""

    def get_qid_from_wikipedia_title(self, title: str) -> str:
        cleaned = re.sub(r"\s+", " ", (title or "").strip())
        if not cleaned:
            return ""
        cache_key = cleaned.casefold()
        if cache_key in self.wikipedia_title_cache:
            return self.wikipedia_title_cache[cache_key]

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "pageprops",
            "redirects": "1",
            "titles": cleaned,
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = self._get(url)
        pages = payload.get("query", {}).get("pages", [])
        qid = ""
        if pages:
            qid = pages[0].get("pageprops", {}).get("wikibase_item", "") or ""

        self.wikipedia_title_cache[cache_key] = qid
        return qid

    def search_wikipedia_qid(self, query: str) -> str:
        cleaned = re.sub(r"\s+", " ", (query or "").strip())
        if not cleaned:
            return ""
        cache_key = cleaned.casefold()
        if cache_key in self.wikipedia_search_cache:
            return self.wikipedia_search_cache[cache_key]

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "search",
            "gsrsearch": cleaned,
            "gsrlimit": "5",
            "redirects": "1",
            "prop": "pageprops",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = self._get(url)
        pages = payload.get("query", {}).get("pages", []) or []

        best_qid = ""
        best_score = -1
        for page in pages:
            qid = page.get("pageprops", {}).get("wikibase_item", "") or ""
            if not qid:
                continue
            score = score_wikipedia_page(cleaned, page.get("title", ""))
            if score > best_score:
                best_score = score
                best_qid = qid

        self.wikipedia_search_cache[cache_key] = best_qid
        return best_qid

    def search_wikidata_qid(self, term: str, preferred_ranks: Set[str]) -> str:
        cleaned = re.sub(r"\s+", " ", (term or "").strip())
        if not cleaned:
            return ""
        cache_key = (cleaned.casefold(), tuple(sorted(preferred_ranks)))
        if cache_key in self.wikidata_search_cache:
            return self.wikidata_search_cache[cache_key]

        params = {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "type": "item",
            "limit": "8",
            "search": cleaned,
        }
        url = f"https://www.wikidata.org/w/api.php?{urlencode(params)}"
        payload = self._get(url)
        candidates = payload.get("search", []) or []

        best_qid = ""
        best_score = -1
        for candidate in candidates:
            qid = (candidate or {}).get("id", "") or ""
            if not qid:
                continue
            entity = self.get_entity(qid)
            score = score_wikidata_entity(cleaned, entity, preferred_ranks)
            if score > best_score:
                best_score = score
                best_qid = qid

        self.wikidata_search_cache[cache_key] = best_qid
        return best_qid

    def resolve_wikidata_qid(self, english_name: str, latin_name: str) -> Tuple[str, str]:
        title_candidates = unique_non_empty([
            english_name,
            sentence_case_title(english_name),
            latin_name,
        ])
        for title in title_candidates:
            qid = self.normalize_taxon_qid(self.get_qid_from_wikipedia_title(title))
            if qid:
                return qid, f"enwiki-title:{title}"

        for query in unique_non_empty([english_name, latin_name]):
            qid = self.normalize_taxon_qid(self.search_wikipedia_qid(query))
            if qid:
                return qid, f"enwiki-search:{query}"

        if latin_name:
            qid = self.normalize_taxon_qid(self.search_wikidata_qid(latin_name, {"species"}))
            if qid:
                return qid, f"wikidata-search-latin:{latin_name}"

        if english_name:
            qid = self.normalize_taxon_qid(
                self.search_wikidata_qid(english_name, {"species", "genus", "family", "order"})
            )
            if qid:
                return qid, f"wikidata-search-en:{english_name}"

        return "", ""

    def traverse_taxonomy(self, start_qid: str) -> Dict[str, Dict[str, str]]:
        taxonomy: Dict[str, Dict[str, str]] = {}
        current_qid = start_qid
        visited: Set[str] = set()

        for _ in range(24):
            if not current_qid or current_qid in visited:
                break
            visited.add(current_qid)

            entity = self.get_entity(current_qid)
            if not entity:
                break

            rank = extract_rank(entity)
            if rank in TARGET_RANKS and rank not in taxonomy:
                taxonomy[rank] = {
                    "qid": current_qid,
                    "name": extract_taxon_name(entity),
                    "name_cn": extract_label(entity, "zh"),
                    "label_en": extract_label(entity, "en"),
                }

            current_qid = extract_parent_qid(entity)

        return taxonomy


def build_taxon_relations(
    bird_row: Dict[str, str],
    taxonomy: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    for rank in TARGET_RANKS:
        entry = taxonomy.get(rank, {})
        scientific_name = entry.get("name", "").strip()
        chinese_name = entry.get("name_cn", "").strip()
        display_name = chinese_name or scientific_name
        if not display_name:
            continue
        object_id = taxonomy_relation_object_id(rank, scientific_name, chinese_name)
        summary = f"依据 Wikidata 抽取的分类单元：{display_name}（{RANK_DISPLAY[rank]}）。"
        relations.append({
            "subject_id": bird_row["id"],
            "subject": bird_row["name"],
            "predicate": "belongs_to",
            "object_id": object_id,
            "object": display_name,
            "subject_type": "Bird",
            "object_type": "Taxon",
            "evidence": f"Wikidata 分类: {bird_row['name']} 属于{RANK_DISPLAY[rank]} {display_name}。",
            "object_summary": summary,
        })
    return relations


def already_has_taxonomy(bird_row: Dict[str, str]) -> bool:
    return all((bird_row.get(column, "") or "").strip() for column in TARGET_RANKS)


def populate_taxonomy_fields(bird_row: Dict[str, str], taxonomy: Dict[str, Dict[str, str]]) -> None:
    genus_fallback = (bird_row.get("latin_name", "").split(" ", 1)[0] or "").strip()
    species_fallback = bird_row.get("latin_name", "").strip()

    for rank in TARGET_RANKS:
        entry = taxonomy.get(rank, {})
        bird_row[rank] = entry.get("name", "").strip()
        bird_row[f"{rank}_cn"] = entry.get("name_cn", "").strip()

    if not bird_row["genus"] and genus_fallback:
        bird_row["genus"] = genus_fallback
    if not bird_row["species"] and species_fallback:
        bird_row["species"] = species_fallback
    if not bird_row["species_cn"] and bird_row.get("name"):
        bird_row["species_cn"] = bird_row["name"]


def persist_taxonomy_progress(
    birds_path: Path,
    relations_path: Path,
    birds_rows: List[Dict[str, str]],
    relations_rows: List[Dict[str, str]],
) -> None:
    write_csv_rows(birds_path, BIRDS_HEADERS, birds_rows)
    write_csv_rows(relations_path, RELATIONS_HEADERS, relations_rows)


def prune_wikidata_taxon_relations(
    relations_rows: List[Dict[str, str]],
    existing_relation_keys: Set[Tuple[str, str, str]],
    bird_row: Dict[str, str],
    taxonomy: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    removable_names = set()
    for rank in TARGET_RANKS:
        entry = taxonomy.get(rank, {})
        for value in (entry.get("name", "").strip(), entry.get("name_cn", "").strip()):
            if value:
                removable_names.add(value)

    if not removable_names:
        return relations_rows

    filtered_rows: List[Dict[str, str]] = []
    for row in relations_rows:
        is_target = (
            row.get("subject_id") == bird_row["id"]
            and row.get("predicate") == "belongs_to"
            and row.get("object_type") == "Taxon"
            and row.get("evidence", "").startswith("Wikidata 分类:")
            and row.get("object") in removable_names
        )
        if is_target:
            existing_relation_keys.discard((row["subject_id"], row["predicate"], row["object_id"]))
            continue
        filtered_rows.append(row)
    return filtered_rows


def maybe_build_json(build_json: bool) -> None:
    if not build_json:
        return
    if not BUILD_SCRIPT.exists():
        print("未找到 build_knowledge_json.py，跳过静态数据构建。", file=sys.stderr)
        return
    exit_code = subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=False).returncode
    if exit_code != 0:
        raise RuntimeError("执行 build_knowledge_json.py 失败")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过 Wikidata API 获取鸟类分类信息")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--overwrite", action="store_true", help="强制重取已有分类的鸟类")
    parser.add_argument("--build-json", action="store_true", help="结束后自动执行 build_knowledge_json.py")
    parser.add_argument("--delay", type=float, default=0.1, help="网络请求最小间隔秒数，默认 0.1")
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

    configure_csv_field_size_limit()
    client = TaxonomyClient(opener=opener, delay=args.delay)
    birds_rows = load_csv_rows(birds_path, BIRDS_HEADERS)
    relations_rows = load_csv_rows(relations_path, RELATIONS_HEADERS)
    existing_relation_keys = {
        (row["subject_id"], row["predicate"], row["object_id"])
        for row in relations_rows
    }

    processed = 0
    success = 0
    skipped = 0

    try:
        for bird_row in birds_rows:
            if args.limit > 0 and processed >= args.limit:
                break

            if already_has_taxonomy(bird_row) and not args.overwrite:
                skipped += 1
                continue

            name = bird_row.get("name", "").strip()
            english_name = bird_row.get("english_name", "").strip()
            latin_name = bird_row.get("latin_name", "").strip()
            print(f"[taxonomy] {name} ({english_name or latin_name or '无英文名'})")

            if not english_name and not latin_name:
                print("  [warn] 无英文名也无学名，跳过")
                skipped += 1
                continue

            try:
                qid, source = client.resolve_wikidata_qid(english_name, latin_name)
            except Exception as error:
                print(f"  [error] 获取 Wikidata QID 失败: {error}")
                processed += 1
                continue

            if not qid:
                print("  [warn] 未找到 Wikidata 条目")
                processed += 1
                continue

            print(f"  QID: {qid} ({source})")

            try:
                taxonomy = client.traverse_taxonomy(qid)
            except Exception as error:
                print(f"  [error] 遍历分类链失败: {error}")
                processed += 1
                continue

            if not taxonomy:
                print("  [warn] 未获取到分类信息")
                processed += 1
                continue

            populate_taxonomy_fields(bird_row, taxonomy)
            relations_rows = prune_wikidata_taxon_relations(relations_rows, existing_relation_keys, bird_row, taxonomy)

            missing_ranks = [
                RANK_DISPLAY[rank]
                for rank in TARGET_RANKS
                if not bird_row.get(rank, "").strip()
            ]
            if missing_ranks:
                joined = "、".join(missing_ranks)
                print(f"  [warn] 已拿到条目，但缺少 {joined} 字段")

            for relation in build_taxon_relations(bird_row, taxonomy):
                key = (relation["subject_id"], relation["predicate"], relation["object_id"])
                if key in existing_relation_keys:
                    continue
                existing_relation_keys.add(key)
                relations_rows.append(relation)

            persist_taxonomy_progress(birds_path, relations_path, birds_rows, relations_rows)
            print("  [saved] 已写入 birds.csv 和 relations.csv")

            success += 1
            processed += 1
    except KeyboardInterrupt:
        print("\n[interrupt] 已停止运行，之前成功的条目已经落盘。")

        # 每成功一只立刻落盘，中断不怕丢数据
        write_csv_rows(birds_path, BIRDS_HEADERS, birds_rows)
        write_csv_rows(relations_path, RELATIONS_HEADERS, relations_rows)
        print("  [saved] 已保存当前进度到 birds.csv 和 relations.csv")

    if success > 0:
        print("\n已更新 birds.csv 和 relations.csv")
    else:
        print("\n无新数据写入")

    print(f"处理总数: {processed}, 成功: {success}, 跳过: {skipped}")
    maybe_build_json(args.build_json)


if __name__ == "__main__":
    main()
