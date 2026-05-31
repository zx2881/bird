"""
从 Wikipedia / Wikidata 抓取鸟类图片、摘要与分类信息，回填 birds.csv 与 relations.csv。

规则:
1) 图片优先取 table.infobox 内首图；无图则回退 mw-parser-output 中首个可用图片
2) summary 字段抓取 Wikipedia 正文全文纯文本，不再只取首段摘要
3) 分类通过 Wikidata P171 链获取目 / 科 / 属 / 种，并补充 belongs_to 关系（目 / 科）
"""

from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_taxonomy import (  # noqa: E402
    BIRDS_HEADERS,
    RANK_DISPLAY,
    RELATIONS_HEADERS,
    TAXONOMY_COLUMNS,
    TaxonomyClient,
    already_has_taxonomy,
    build_taxon_relations,
    configure_csv_field_size_limit,
    load_csv_rows,
    maybe_build_json,
    populate_taxonomy_fields,
    prune_wikidata_taxon_relations,
    read_csv_headers,
    write_csv_rows,
)

DATA_DIR = ROOT / "data"
BIRDS_PATH = DATA_DIR / "birds.csv"
RELATIONS_PATH = DATA_DIR / "relations.csv"
DEFAULT_CHECKPOINT_PATH = DATA_DIR / "fetch_bird_media_checkpoint.json"
CHECKPOINT_VERSION = 1


def log(*args, **kwargs) -> None:
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def write_json_payload(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def load_resume_checkpoint(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"checkpoint JSON 解析失败: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"checkpoint 顶层结构必须为对象: {path}")
    version = payload.get("version")
    if version not in (None, CHECKPOINT_VERSION):
        raise RuntimeError(f"不支持的 checkpoint 版本: {path}")
    return payload


def clear_resume_checkpoint(path: Path) -> None:
    if path.exists():
        path.unlink()


def build_resume_signature(args: argparse.Namespace) -> Dict[str, bool]:
    return {
        "only_media": bool(args.only_media),
        "only_taxonomy": bool(args.only_taxonomy),
        "overwrite": bool(args.overwrite),
    }


def checkpoint_matches_run(payload: Dict, args: argparse.Namespace) -> bool:
    return payload.get("signature") == build_resume_signature(args)


def resolve_resume_start_index(payload: Dict, birds_rows: Sequence[Dict[str, str]]) -> int:
    if not payload:
        return 0

    last_index = payload.get("last_completed_index")
    last_row_id = str(payload.get("last_completed_row_id") or "").strip()
    last_title = str(payload.get("last_completed_title") or "").strip()

    if isinstance(last_index, int) and 0 <= last_index < len(birds_rows):
        row = birds_rows[last_index]
        row_id = (row.get("id") or "").strip()
        title = (row.get("english_name") or "").strip() or (row.get("latin_name") or "").strip()
        if (last_row_id and row_id == last_row_id) or (not last_row_id and last_title and title == last_title):
            return last_index + 1

    for index, row in enumerate(birds_rows):
        row_id = (row.get("id") or "").strip()
        title = (row.get("english_name") or "").strip() or (row.get("latin_name") or "").strip()
        if last_row_id and row_id == last_row_id:
            return index + 1
        if not last_row_id and last_title and title == last_title:
            return index + 1

    return 0


def build_row_title(row: Dict[str, str]) -> str:
    return (row.get("english_name") or "").strip() or (row.get("latin_name") or "").strip()


def build_row_key(row: Dict[str, str], title: str = "") -> str:
    return (row.get("id") or "").strip() or (title or "").strip()


def failed_item_key(item: Dict) -> str:
    return str(item.get("row_id") or "").strip() or str(item.get("title") or "").strip()


def build_failed_item(
    row: Dict[str, str],
    row_index: int,
    title: str,
    error: Exception,
    stage: str,
    previous: Optional[Dict] = None,
) -> Dict:
    updated_at = int(time.time())
    attempts = int((previous or {}).get("attempts") or 0) + 1
    first_failed_at = int((previous or {}).get("first_failed_at") or updated_at)
    return {
        "row_index": row_index,
        "row_id": (row.get("id") or "").strip(),
        "title": title.strip(),
        "stage": stage,
        "error": str(error),
        "attempts": attempts,
        "first_failed_at": first_failed_at,
        "updated_at": updated_at,
    }


def upsert_failed_item(
    failed_items: List[Dict],
    row: Dict[str, str],
    row_index: int,
    title: str,
    error: Exception,
    stage: str,
) -> List[Dict]:
    key = build_row_key(row, title)
    updated_items: List[Dict] = []
    previous: Optional[Dict] = None
    for item in failed_items:
        if failed_item_key(item) == key:
            previous = item
            continue
        updated_items.append(item)
    updated_items.append(build_failed_item(row, row_index, title, error, stage, previous=previous))
    return updated_items


def remove_failed_item(failed_items: List[Dict], row: Dict[str, str], title: str) -> List[Dict]:
    key = build_row_key(row, title)
    return [item for item in failed_items if failed_item_key(item) != key]


def resolve_failed_item_index(item: Dict, birds_rows: Sequence[Dict[str, str]]) -> Optional[int]:
    row_index = item.get("row_index")
    row_id = str(item.get("row_id") or "").strip()
    title = str(item.get("title") or "").strip()

    if isinstance(row_index, int) and 0 <= row_index < len(birds_rows):
        row = birds_rows[row_index]
        if build_row_key(row, build_row_title(row)) == (row_id or title):
            return row_index

    for index, row in enumerate(birds_rows):
        if row_id and (row.get("id") or "").strip() == row_id:
            return index
        if not row_id and title and build_row_title(row) == title:
            return index
    return None


def normalize_failed_items(payload: Dict, birds_rows: Sequence[Dict[str, str]]) -> List[Dict]:
    normalized: List[Dict] = []
    seen: Set[str] = set()
    for item in payload.get("failed_items", []) or []:
        if not isinstance(item, dict):
            continue
        key = failed_item_key(item)
        if not key or key in seen:
            continue
        if resolve_failed_item_index(item, birds_rows) is None:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def is_retryable_network_error(error: Exception) -> bool:
    if isinstance(error, (HTTPError, URLError, TimeoutError)):
        return True

    text = f"{type(error).__name__}: {error}".casefold()
    retryable_tokens = (
        "请求失败",
        "api 请求失败",
        "网络错误",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "connection",
        "ssl",
        "429",
        "502",
        "503",
        "504",
    )
    return any(token in text for token in retryable_tokens)


def build_resume_checkpoint_payload(
    args: argparse.Namespace,
    last_completed: Optional[Dict[str, object]],
    failed_items: List[Dict],
    processed: int,
    saved: int,
    updated_image: int,
    updated_summary: int,
    updated_taxonomy: int,
) -> Dict:
    return {
        "version": CHECKPOINT_VERSION,
        "updated_at": int(time.time()),
        "signature": build_resume_signature(args),
        "last_completed_index": None if not last_completed else last_completed.get("index"),
        "last_completed_row_id": "" if not last_completed else str(last_completed.get("row_id") or "").strip(),
        "last_completed_title": "" if not last_completed else str(last_completed.get("title") or "").strip(),
        "failed_items": failed_items,
        "processed_in_run": processed,
        "saved_in_run": saved,
        "updated_image": updated_image,
        "updated_summary": updated_summary,
        "updated_taxonomy": updated_taxonomy,
    }


def _make_request(url: str, opener, timeout: int = 60) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "bird-kg-content-fetcher/1.0 (research prototype; contact local-user)",
            "Accept": "application/json",
        },
    )
    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            if opener:
                with opener.open(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            try:
                with urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except URLError:
                ctx = ssl._create_unverified_context()
                with urlopen(request, timeout=timeout, context=ctx) as response:
                    return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 429 and attempt < max_retries - 1:
                wait = (attempt + 1) * 8
                log(f"  [retry] 429 限流，{wait}s 后重试")
                time.sleep(wait)
                continue
            raise
        except URLError as error:
            last_error = error
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 8
                log(f"  [retry] 网络错误: {error.reason}，{wait}s 后重试")
                time.sleep(wait)
                continue
    raise last_error or RuntimeError(f"请求失败: {url}")


def _normalize_image_url(src: str) -> str:
    src = (src or "").strip()
    if not src:
        return ""
    if src.startswith("//"):
        return f"https:{src}"
    if src.startswith("/"):
        return f"https://en.wikipedia.org{src}"
    return src


def _extract_first_usable_image(html_text: str) -> str:
    for src in re.findall(r'<img[^>]+src="([^"]+)"', html_text, flags=re.IGNORECASE):
        image_url = _normalize_image_url(src)
        lower = image_url.lower()
        if any(token in lower for token in ("icon", "sprite", ".svg", "wiktionary", "commons-logo")):
            continue
        return image_url
    return ""


def _extract_infobox_image(html_text: str) -> str:
    match = re.search(
        r'(<table[^>]*class="[^"]*\binfobox\b[^"]*"[^>]*>.*?</table>)',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return _extract_first_usable_image(match.group(1))


def _normalize_article_text(text: str) -> str:
    normalized = html.unescape((text or "").strip())
    if not normalized:
        return ""

    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n[ \t]+", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _fetch_full_article_text(title: str, opener) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
        "titles": title,
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "exlimit": "1",
    }
    url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
    payload = _make_request(url, opener)
    pages = payload.get("query", {}).get("pages", [])
    if not pages:
        return ""

    page = pages[0] or {}
    if page.get("missing"):
        return ""
    return _normalize_article_text(page.get("extract", "") or "")


def fetch_page_media_and_summary(title: str, opener, delay: float) -> Tuple[str, str]:
    params = {
        "action": "parse",
        "format": "json",
        "formatversion": "2",
        "prop": "text",
        "page": title,
        "redirects": "1",
    }
    url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
    payload = _make_request(url, opener)
    page_html = ((payload.get("parse", {}) or {}).get("text") or "")
    if not page_html:
        return "", ""

    image_url = _extract_infobox_image(page_html)
    if not image_url:
        parser_match = re.search(
            r'<div[^>]*class="[^"]*\bmw-parser-output\b[^"]*"[^>]*>(.*?)</div>',
            page_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        fallback_html = parser_match.group(1) if parser_match else page_html
        image_url = _extract_first_usable_image(fallback_html)

    summary = _fetch_full_article_text(title, opener)
    if delay > 0:
        time.sleep(delay)
    return image_url, summary


def needs_media(row: Dict[str, str], overwrite: bool) -> bool:
    if overwrite:
        return True
    # Summary adopts compare-and-replace semantics, so media mode needs a fresh fetch.
    return True


def needs_taxonomy(row: Dict[str, str], overwrite: bool) -> bool:
    if overwrite:
        return True
    return not already_has_taxonomy(row)


def should_process_row(row: Dict[str, str], args: argparse.Namespace) -> bool:
    if args.only_media:
        return needs_media(row, args.overwrite)
    if args.only_taxonomy:
        return needs_taxonomy(row, args.overwrite)
    return needs_media(row, args.overwrite) or needs_taxonomy(row, args.overwrite)


def persist_progress(
    birds_headers: Sequence[str],
    birds_rows: List[Dict[str, str]],
    relations_rows: List[Dict[str, str]],
) -> None:
    write_csv_rows(BIRDS_PATH, list(birds_headers), birds_rows)
    write_csv_rows(RELATIONS_PATH, RELATIONS_HEADERS, relations_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取鸟类图片、摘要与分类信息")
    parser.add_argument("--proxy", type=str, default="", help="HTTPS 代理地址")
    parser.add_argument("--delay", type=float, default=0.8, help="Wikipedia 页面请求间隔秒数")
    parser.add_argument("--taxonomy-delay", type=float, default=0.1, help="Wikidata 请求间隔秒数")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前 N 条（测试用）")
    parser.add_argument(
        "--checkpoint-file",
        default=str(DEFAULT_CHECKPOINT_PATH),
        help="断点 checkpoint 文件，默认 data/fetch_bird_media_checkpoint.json",
    )
    parser.add_argument("--reset-checkpoint", action="store_true", help="启动前清空断点 checkpoint，从头开始")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="强制覆盖已有 image_url / 分类字段；summary 只要抓取结果不同会自动覆盖",
    )
    parser.add_argument("--only-media", action="store_true", help="仅抓取图片与摘要")
    parser.add_argument("--only-taxonomy", action="store_true", help="仅抓取分类信息")
    parser.add_argument("--build-json", action="store_true", help="结束后自动执行 build_knowledge_json.py")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.only_media and args.only_taxonomy:
        raise SystemExit("--only-media 与 --only-taxonomy 不能同时使用")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)

    checkpoint_path = Path(args.checkpoint_file)
    if args.reset_checkpoint:
        clear_resume_checkpoint(checkpoint_path)
        log(f"[resume] 已清空 checkpoint: {checkpoint_path}")

    opener = None
    if args.proxy:
        proxy_handler = ProxyHandler({"https": args.proxy})
        opener = build_opener(proxy_handler)
        install_opener(opener)

    if not BIRDS_PATH.exists():
        log(f"未找到 {BIRDS_PATH}，请先准备 birds.csv。")
        sys.exit(1)

    configure_csv_field_size_limit()
    source_birds_headers = read_csv_headers(BIRDS_PATH)
    birds_write_headers = source_birds_headers or list(BIRDS_HEADERS)
    birds_load_headers = list(dict.fromkeys([*birds_write_headers, *BIRDS_HEADERS]))
    has_taxonomy_columns = all(header in birds_write_headers for header in TAXONOMY_COLUMNS)
    birds_rows = load_csv_rows(BIRDS_PATH, birds_load_headers, optional_headers=TAXONOMY_COLUMNS)
    resume_checkpoint = load_resume_checkpoint(checkpoint_path)
    resume_start_index = 0
    last_completed: Optional[Dict[str, object]] = None
    failed_items: List[Dict] = []
    if resume_checkpoint:
        if checkpoint_matches_run(resume_checkpoint, args):
            last_index = resume_checkpoint.get("last_completed_index")
            if isinstance(last_index, int) and last_index >= 0:
                last_completed = {
                    "index": last_index,
                    "row_id": str(resume_checkpoint.get("last_completed_row_id") or "").strip(),
                    "title": str(resume_checkpoint.get("last_completed_title") or "").strip(),
                }
            failed_items = normalize_failed_items(resume_checkpoint, birds_rows)
            resume_start_index = resolve_resume_start_index(resume_checkpoint, birds_rows)
            resume_label = (
                str(resume_checkpoint.get("last_completed_title") or "").strip()
                or str(resume_checkpoint.get("last_completed_row_id") or "").strip()
                or f"index={resume_checkpoint.get('last_completed_index', '?')}"
            )
            if resume_start_index > 0:
                log(f"[resume] 检测到 checkpoint，将从 {resume_label} 之后继续")
            else:
                log("[resume] 未在当前 birds.csv 中定位到 checkpoint 记录，将从头开始")
        else:
            log("[resume] checkpoint 与本次运行模式不一致，忽略旧 checkpoint 并从头开始")
    relations_rows = load_csv_rows(RELATIONS_PATH, RELATIONS_HEADERS)
    existing_relation_keys: Set[Tuple[str, str, str]] = {
        (row["subject_id"], row["predicate"], row["object_id"])
        for row in relations_rows
    }
    taxonomy_client = TaxonomyClient(opener=opener, delay=max(0.0, args.taxonomy_delay))

    if not has_taxonomy_columns:
        if args.only_taxonomy:
            raise SystemExit("检测到旧 birds.csv 表头。为保持旧表头不变，--only-taxonomy 不能在此模式下使用。")
        if not args.only_media:
            log("[compat] 检测到旧 birds.csv 表头。为保持原列结构，本次仅抓取 image_url / summary。")

    log("开始逐条处理记录，命中一条写入一条...")
    updated_image = 0
    updated_summary = 0
    updated_taxonomy = 0
    saved = 0
    processed = 0
    stopped_due_to_limit = False
    retried_keys_in_run: Set[str] = set()

    def persist_checkpoint_state() -> None:
        write_json_payload(
            checkpoint_path,
            build_resume_checkpoint_payload(
                args,
                last_completed,
                failed_items,
                processed,
                saved,
                updated_image,
                updated_summary,
                updated_taxonomy,
            ),
        )

    def process_row(idx: int, row: Dict[str, str], label: str) -> None:
        nonlocal updated_image, updated_summary, updated_taxonomy, saved, last_completed, failed_items

        english_name = (row.get("english_name") or "").strip()
        latin_name = (row.get("latin_name") or "").strip()
        title = english_name or latin_name
        name = (row.get("name") or "").strip() or title
        log(f"[{label}] {name} ({title})")

        changed = False
        retryable_failure: Optional[Tuple[Exception, str]] = None
        fetch_media = args.only_taxonomy is False and needs_media(row, args.overwrite)
        fetch_taxonomy_flag = (
            args.only_media is False
            and has_taxonomy_columns
            and needs_taxonomy(row, args.overwrite)
        )

        if fetch_media and title:
            try:
                image_url, summary = fetch_page_media_and_summary(
                    title,
                    opener=opener,
                    delay=max(0.0, args.delay),
                )
            except Exception as error:
                if is_retryable_network_error(error):
                    retryable_failure = (error, "media")
                    log(f"  [retry] 页面抓取出现网络错误，已加入重试队列: {error}")
                else:
                    log(f"  [error] 页面抓取失败: {error}")
                image_url, summary = "", ""

            current_image_url = (row.get("image_url") or "").strip()
            current_summary = (row.get("summary") or "").strip()
            if image_url and image_url != current_image_url:
                row["image_url"] = image_url
                updated_image += 1
                changed = True
                log("  [ok] image_url 已更新")
            elif image_url:
                log("  [skip] image_url 与现有值一致")

            if summary and summary != current_summary:
                row["summary"] = summary
                updated_summary += 1
                changed = True
                log("  [ok] summary 已更新（抓取内容有变化）")
            elif summary:
                log("  [skip] summary 与现有值一致")

        if fetch_taxonomy_flag and retryable_failure is None:
            if not english_name and not latin_name:
                log("  [warn] 无英文名也无学名，跳过分类抓取")
            else:
                try:
                    qid, source = taxonomy_client.resolve_wikidata_qid(english_name, latin_name)
                except Exception as error:
                    if is_retryable_network_error(error):
                        retryable_failure = (error, "taxonomy")
                        log(f"  [retry] 获取 Wikidata QID 出现网络错误，已加入重试队列: {error}")
                    else:
                        log(f"  [error] 获取 Wikidata QID 失败: {error}")
                    qid, source = "", ""

                if retryable_failure is None:
                    if not qid:
                        log("  [warn] 未找到 Wikidata 条目")
                    else:
                        log(f"  QID: {qid} ({source})")
                        try:
                            taxonomy = taxonomy_client.traverse_taxonomy(qid)
                        except Exception as error:
                            if is_retryable_network_error(error):
                                retryable_failure = (error, "taxonomy")
                                log(f"  [retry] 遍历分类链出现网络错误，已加入重试队列: {error}")
                            else:
                                log(f"  [error] 遍历分类链失败: {error}")
                            taxonomy = {}

                        if retryable_failure is None:
                            if not taxonomy:
                                log("  [warn] 未获取到分类信息")
                            else:
                                populate_taxonomy_fields(row, taxonomy)
                                relations_rows[:] = prune_wikidata_taxon_relations(
                                    relations_rows,
                                    existing_relation_keys,
                                    row,
                                    taxonomy,
                                )

                                missing_ranks = [
                                    RANK_DISPLAY[rank]
                                    for rank in ("order", "family")
                                    if not row.get(rank, "").strip()
                                ]
                                if missing_ranks:
                                    log(f"  [warn] 已拿到条目，但缺少 {'、'.join(missing_ranks)} 字段")

                                for relation in build_taxon_relations(row, taxonomy):
                                    key = (relation["subject_id"], relation["predicate"], relation["object_id"])
                                    if key in existing_relation_keys:
                                        continue
                                    existing_relation_keys.add(key)
                                    relations_rows.append(relation)

                                updated_taxonomy += 1
                                changed = True
                                log("  [ok] 分类字段已更新")

        if changed:
            persist_progress(birds_write_headers, birds_rows, relations_rows)
            saved += 1
            log("  [saved] 已写入 birds.csv 和 relations.csv")
        else:
            log("  [skip] 本条无字段变化，未写入 CSV")

        if retryable_failure is not None:
            error, stage = retryable_failure
            failed_items = upsert_failed_item(failed_items, row, idx, title, error, stage)
            persist_checkpoint_state()
            log("  [resume] 本条已记录到 checkpoint，后续启动会优先重试")
            return

        failed_items = remove_failed_item(failed_items, row, title)
        last_completed = {
            "index": idx,
            "row_id": (row.get("id") or "").strip(),
            "title": title,
        }
        persist_checkpoint_state()

    try:
        if failed_items:
            log(f"[resume] 发现 {len(failed_items)} 条网络失败记录，先进行重试")
        for retry_number, item in enumerate(list(failed_items), start=1):
            if args.limit > 0 and processed >= args.limit:
                stopped_due_to_limit = True
                break

            idx = resolve_failed_item_index(item, birds_rows)
            if idx is None:
                failed_items = [entry for entry in failed_items if failed_item_key(entry) != failed_item_key(item)]
                persist_checkpoint_state()
                log(f"[resume] 未找到失败记录对应行，已从重试队列移除: {failed_item_key(item)}")
                continue

            row = birds_rows[idx]
            row_key = build_row_key(row, build_row_title(row))
            retried_keys_in_run.add(row_key)
            english_name = (row.get("english_name") or "").strip()
            latin_name = (row.get("latin_name") or "").strip()
            if not english_name and not latin_name:
                failed_items = remove_failed_item(failed_items, row, "")
                persist_checkpoint_state()
                continue

            processed += 1
            process_row(idx, row, f"retry {retry_number}")

        for idx, row in enumerate(birds_rows[resume_start_index:], start=resume_start_index):
            english_name = (row.get("english_name") or "").strip()
            latin_name = (row.get("latin_name") or "").strip()
            if not english_name and not latin_name:
                continue
            if build_row_key(row, build_row_title(row)) in retried_keys_in_run:
                continue
            if not should_process_row(row, args):
                continue
            if args.limit > 0 and processed >= args.limit:
                stopped_due_to_limit = True
                break

            processed += 1
            process_row(idx, row, str(processed))

        if processed == 0:
            clear_resume_checkpoint(checkpoint_path)
            log("无需抓取：目标记录已具备所需字段。")
            maybe_build_json(args.build_json)
            return

    except KeyboardInterrupt:
        log("\n[interrupt] 已停止运行，正在保存当前进度...")
        persist_progress(birds_write_headers, birds_rows, relations_rows)
        log("  [saved] 已保存当前进度")
        if checkpoint_path.exists():
            log(f"  [resume] 下次可从 checkpoint 继续: {checkpoint_path}")
        return

    if stopped_due_to_limit:
        log(f"[resume] 已到达 --limit={args.limit}，保留 checkpoint 以便下次继续: {checkpoint_path}")
    elif failed_items:
        persist_checkpoint_state()
        log(f"[resume] 仍有 {len(failed_items)} 条网络失败记录待重试，保留 checkpoint: {checkpoint_path}")
    else:
        clear_resume_checkpoint(checkpoint_path)
        log("[resume] 已完成全部可处理记录，checkpoint 已清理")

    log(
        f"完成：image_url {updated_image} 条，summary {updated_summary} 条，"
        f"分类 {updated_taxonomy} 条，落盘 {saved} 次，总处理 {processed} 条。"
    )
    maybe_build_json(args.build_json)


if __name__ == "__main__":
    main()
