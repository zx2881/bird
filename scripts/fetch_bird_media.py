"""
从 Wikipedia / Wikidata 抓取鸟类图片、摘要与分类信息，回填 birds.csv 与 relations.csv。

规则:
1) 图片优先取 table.infobox 内首图；无图则回退 mw-parser-output 中首个可用图片
2) 摘要取 mw-parser-output 中首个有效段落文本
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
from typing import Dict, List, Set, Tuple
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
    TaxonomyClient,
    already_has_taxonomy,
    build_taxon_relations,
    configure_csv_field_size_limit,
    load_csv_rows,
    maybe_build_json,
    populate_taxonomy_fields,
    prune_wikidata_taxon_relations,
    write_csv_rows,
)

DATA_DIR = ROOT / "data"
BIRDS_PATH = DATA_DIR / "birds.csv"
RELATIONS_PATH = DATA_DIR / "relations.csv"


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
                print(f"  [retry] 429 限流，{wait}s 后重试")
                time.sleep(wait)
                continue
            raise
        except URLError as error:
            last_error = error
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 8
                print(f"  [retry] 网络错误: {error.reason}，{wait}s 后重试")
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


def _strip_html_to_text(html_text: str) -> str:
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", "", html_text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\[[0-9]+\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_summary(html_text: str) -> str:
    parser_match = re.search(
        r'<div[^>]*class="[^"]*\bmw-parser-output\b[^"]*"[^>]*>(.*?)</div>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    parser_html = parser_match.group(1) if parser_match else html_text
    parser_html = re.sub(r"<table\b[^>]*>.*?</table>", "", parser_html, flags=re.IGNORECASE | re.DOTALL)
    parser_html = re.sub(
        r'<div[^>]*class="[^"]*(hatnote|shortdescription|metadata|navbox)[^"]*"[^>]*>.*?</div>',
        "",
        parser_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", parser_html, flags=re.IGNORECASE | re.DOTALL)
    for paragraph in paragraphs:
        text = _strip_html_to_text(paragraph)
        if len(text) >= 20:
            return text
    return _strip_html_to_text(parser_html)


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

    summary = _extract_summary(page_html)
    if delay > 0:
        time.sleep(delay)
    return image_url, summary


def needs_media(row: Dict[str, str], overwrite: bool) -> bool:
    if overwrite:
        return True
    return not ((row.get("image_url") or "").strip() and (row.get("summary") or "").strip())


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
    birds_rows: List[Dict[str, str]],
    relations_rows: List[Dict[str, str]],
) -> None:
    write_csv_rows(BIRDS_PATH, BIRDS_HEADERS, birds_rows)
    write_csv_rows(RELATIONS_PATH, RELATIONS_HEADERS, relations_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取鸟类图片、摘要与分类信息")
    parser.add_argument("--proxy", type=str, default="", help="HTTPS 代理地址")
    parser.add_argument("--delay", type=float, default=0.8, help="Wikipedia 页面请求间隔秒数")
    parser.add_argument("--taxonomy-delay", type=float, default=0.1, help="Wikidata 请求间隔秒数")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前 N 条（测试用）")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 image_url / summary / 分类字段")
    parser.add_argument("--only-media", action="store_true", help="仅抓取图片与摘要")
    parser.add_argument("--only-taxonomy", action="store_true", help="仅抓取分类信息")
    parser.add_argument("--build-json", action="store_true", help="结束后自动执行 build_knowledge_json.py")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.only_media and args.only_taxonomy:
        raise SystemExit("--only-media 与 --only-taxonomy 不能同时使用")

    opener = None
    if args.proxy:
        proxy_handler = ProxyHandler({"https": args.proxy})
        opener = build_opener(proxy_handler)
        install_opener(opener)

    if not BIRDS_PATH.exists():
        print(f"未找到 {BIRDS_PATH}，请先准备 birds.csv。")
        sys.exit(1)

    configure_csv_field_size_limit()
    birds_rows = load_csv_rows(BIRDS_PATH, BIRDS_HEADERS)
    relations_rows = load_csv_rows(RELATIONS_PATH, RELATIONS_HEADERS)
    existing_relation_keys: Set[Tuple[str, str, str]] = {
        (row["subject_id"], row["predicate"], row["object_id"])
        for row in relations_rows
    }
    taxonomy_client = TaxonomyClient(opener=opener, delay=max(0.0, args.taxonomy_delay))

    pending: List[int] = []
    for idx, row in enumerate(birds_rows):
        english_name = (row.get("english_name") or "").strip()
        latin_name = (row.get("latin_name") or "").strip()
        if not english_name and not latin_name:
            continue
        if should_process_row(row, args):
            pending.append(idx)
        if args.limit > 0 and len(pending) >= args.limit:
            break

    if not pending:
        print("无需抓取：目标记录已具备所需字段。")
        maybe_build_json(args.build_json)
        return

    print(f"准备处理 {len(pending)} 条记录...")
    updated_image = 0
    updated_summary = 0
    updated_taxonomy = 0
    saved = 0

    try:
        for i, idx in enumerate(pending, start=1):
            row = birds_rows[idx]
            english_name = (row.get("english_name") or "").strip()
            latin_name = (row.get("latin_name") or "").strip()
            title = english_name or latin_name
            name = (row.get("name") or "").strip() or title
            print(f"[{i}/{len(pending)}] {name} ({title})")

            changed = False
            fetch_media = args.only_taxonomy is False and needs_media(row, args.overwrite)
            fetch_taxonomy_flag = args.only_media is False and needs_taxonomy(row, args.overwrite)

            if fetch_media and title:
                try:
                    image_url, summary = fetch_page_media_and_summary(
                        title,
                        opener=opener,
                        delay=max(0.0, args.delay),
                    )
                except Exception as error:
                    print(f"  [error] 页面抓取失败: {error}")
                    image_url, summary = "", ""

                if image_url and (args.overwrite or not (row.get("image_url") or "").strip()):
                    row["image_url"] = image_url
                    updated_image += 1
                    changed = True
                    print("  [ok] image_url 已更新")

                if summary and (args.overwrite or not (row.get("summary") or "").strip()):
                    row["summary"] = summary
                    updated_summary += 1
                    changed = True
                    print("  [ok] summary 已更新")

            if fetch_taxonomy_flag:
                if not english_name and not latin_name:
                    print("  [warn] 无英文名也无学名，跳过分类抓取")
                else:
                    try:
                        qid, source = taxonomy_client.resolve_wikidata_qid(english_name, latin_name)
                    except Exception as error:
                        print(f"  [error] 获取 Wikidata QID 失败: {error}")
                        qid, source = "", ""

                    if not qid:
                        print("  [warn] 未找到 Wikidata 条目")
                    else:
                        print(f"  QID: {qid} ({source})")
                        try:
                            taxonomy = taxonomy_client.traverse_taxonomy(qid)
                        except Exception as error:
                            print(f"  [error] 遍历分类链失败: {error}")
                            taxonomy = {}

                        if not taxonomy:
                            print("  [warn] 未获取到分类信息")
                        else:
                            populate_taxonomy_fields(row, taxonomy)
                            relations_rows = prune_wikidata_taxon_relations(
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
                                print(f"  [warn] 已拿到条目，但缺少 {'、'.join(missing_ranks)} 字段")

                            for relation in build_taxon_relations(row, taxonomy):
                                key = (relation["subject_id"], relation["predicate"], relation["object_id"])
                                if key in existing_relation_keys:
                                    continue
                                existing_relation_keys.add(key)
                                relations_rows.append(relation)

                            updated_taxonomy += 1
                            changed = True
                            print("  [ok] 分类字段已更新")

            if changed:
                persist_progress(birds_rows, relations_rows)
                saved += 1
                print("  [saved] 已写入 birds.csv 和 relations.csv")

    except KeyboardInterrupt:
        print("\n[interrupt] 已停止运行，正在保存当前进度...")
        persist_progress(birds_rows, relations_rows)
        print("  [saved] 已保存当前进度")

    print(
        f"完成：image_url {updated_image} 条，summary {updated_summary} 条，"
        f"分类 {updated_taxonomy} 条，落盘 {saved} 次，总处理 {len(pending)} 条。"
    )
    maybe_build_json(args.build_json)


if __name__ == "__main__":
    main()
