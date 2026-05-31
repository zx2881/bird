"""
从 Wikipedia API 批量获取鸟类页面题图 URL，更新 birds.csv 的 image_url 列。

优先从 infobox 的 image 字段提取图片文件，再回退到 prop=pageimages，
最后使用 prop=images + prop=imageinfo 兜底。支持 SSL 降级处理以兼容
Windows 证书环境。
"""

from __future__ import annotations

import csv
import json
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BIRDS_PATH = DATA_DIR / "birds.csv"
BATCH_SIZE = 50
DELAY = 2.0
THUMB_WIDTH = 800

UNUSABLE_IMAGE_PATTERNS = (
    re.compile(r"\.svg(?:\.png)?(?:\?|$)", re.IGNORECASE),
    re.compile(r"(?:^|[_/\-\s])(map|distribution|range|locator)(?:[_/\-\s.]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[_/\-\s])(icon|sprite|logo)(?:[_/\-\s.]|$)", re.IGNORECASE),
    re.compile(r"commons-logo|wiktionary|oojs_ui_icon", re.IGNORECASE),
)


def _make_request(
    url: str,
    opener,
    timeout: int = 60,
) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "bird-kg-crawler/1.0 (research prototype; contact local-user)",
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
                wait = (attempt + 1) * 10
                print(f"  [retry] 429 限流，{wait}s 后重试")
                time.sleep(wait)
                continue
            raise
        except URLError as error:
            last_error = error
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 10
                print(f"  [retry] 网络错误: {error.reason}，{wait}s 后重试")
                time.sleep(wait)
                continue
    raise last_error or RuntimeError(f"请求失败: {url}")


def _build_opener(proxy: Optional[str]):
    if not proxy:
        return None
    proxy_handler = ProxyHandler({"http": proxy, "https": proxy})
    opener = build_opener(proxy_handler)
    install_opener(opener)
    return opener


def _is_usable_image_candidate(value: str) -> bool:
    candidate = (value or "").strip()
    if not candidate:
        return False
    return not any(pattern.search(candidate) for pattern in UNUSABLE_IMAGE_PATTERNS)


def _is_dirty_image_url(image_url: str) -> bool:
    candidate = (image_url or "").strip()
    return bool(candidate) and not _is_usable_image_candidate(candidate)


def _build_requested_title_lookup(payload: dict, requested_titles: List[str]) -> Dict[str, str]:
    query = payload.get("query", {}) or {}
    requested_by_current = {title: title for title in requested_titles}

    for item in query.get("normalized", []):
        from_title = (item.get("from") or "").strip()
        to_title = (item.get("to") or "").strip()
        requested_title = requested_by_current.get(from_title)
        if requested_title and to_title:
            requested_by_current[to_title] = requested_title

    updated = True
    while updated:
        updated = False
        for item in query.get("redirects", []):
            from_title = (item.get("from") or "").strip()
            to_title = (item.get("to") or "").strip()
            requested_title = requested_by_current.get(from_title)
            if requested_title and to_title and requested_by_current.get(to_title) != requested_title:
                requested_by_current[to_title] = requested_title
                updated = True

    return requested_by_current


def _extract_revision_content(page: dict) -> str:
    revisions = page.get("revisions", [])
    if not revisions:
        return ""

    revision = revisions[0] or {}
    slots = revision.get("slots", {}) or {}
    main_slot = slots.get("main", {}) or {}
    return (main_slot.get("content") or revision.get("content") or "").strip()


def _normalize_file_title(raw_value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", raw_value or "", flags=re.DOTALL).strip()
    if not value:
        return ""

    linked_file = re.search(r"\[\[(?:File|Image):([^|\]]+)", value, flags=re.IGNORECASE)
    if linked_file:
        value = linked_file.group(1).strip()
    else:
        value = value.split("|", 1)[0].strip()
        value = re.sub(r"^(?:File|Image)\s*:\s*", "", value, flags=re.IGNORECASE)

    value = value.strip("[] ").replace("_", " ")
    lower = value.lower()
    if lower in {"none", "no", "n/a", "na", "replace this image", "replace_this_image"}:
        return ""
    if not re.search(r"\.(?:jpe?g|png|gif|tiff?|webp|svg)\b", value, flags=re.IGNORECASE):
        return ""
    if not _is_usable_image_candidate(value):
        return ""
    return f"File:{value}"


def _extract_infobox_image_title(wikitext: str) -> str:
    for field in ("image", "image2"):
        match = re.search(
            rf"^\|\s*{field}\s*=\s*(.+?)\s*$",
            wikitext,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            continue
        file_title = _normalize_file_title(match.group(1))
        if file_title:
            return file_title
    return ""


def _pick_first_usable_image_title(images: List[dict]) -> str:
    for image in images:
        file_title = _normalize_file_title((image or {}).get("title", ""))
        if file_title:
            return file_title
    return ""


def _write_rows(rows: List[Dict[str, str]], headers: List[str]) -> None:
    temp_path = BIRDS_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(BIRDS_PATH)


def _fetch_image_urls_for_titles(
    titles: List[str],
    batch_size: int = 50,
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """批量解析文件标题，返回 {文件标题: image_url} 的映射。"""
    opener = _build_opener(proxy)

    result: Dict[str, str] = {}

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        titles_param = "|".join(batch)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles_param,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": str(THUMB_WIDTH),
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)
        title_lookup = _build_requested_title_lookup(payload, batch)

        pages = payload.get("query", {}).get("pages", [])
        for page in pages:
            if page.get("missing"):
                continue
            title = page.get("title", "")
            requested_title = title_lookup.get(title, title if title in batch else "")
            imageinfo = page.get("imageinfo", [])
            image_url = ""
            if imageinfo:
                info = imageinfo[0] or {}
                image_url = (info.get("thumburl") or info.get("url") or "").strip()
            if requested_title and image_url and _is_usable_image_candidate(image_url):
                result[requested_title] = image_url

        if i + batch_size < len(titles):
            time.sleep(delay)

    return result


def fetch_infobox_images_for_titles(
    titles: List[str],
    batch_size: int = 50,
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """优先从 infobox 的 image 字段提取图片，返回 {英文标题: image_url} 的映射。"""
    opener = _build_opener(proxy)
    result: Dict[str, str] = {}

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        titles_param = "|".join(batch)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles_param,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)
        title_lookup = _build_requested_title_lookup(payload, batch)

        page_to_image: Dict[str, str] = {}
        for page in payload.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            page_title = (page.get("title") or "").strip()
            requested_title = title_lookup.get(page_title, page_title if page_title in batch else "")
            if not requested_title:
                continue

            wikitext = _extract_revision_content(page)
            image_title = _extract_infobox_image_title(wikitext)
            if image_title:
                page_to_image[requested_title] = image_title

        file_urls = _fetch_image_urls_for_titles(
            list(page_to_image.values()),
            batch_size=batch_size,
            proxy=proxy,
            delay=0,
        )
        for requested_title, image_title in page_to_image.items():
            image_url = file_urls.get(image_title, "")
            if image_url:
                result[requested_title] = image_url

        batch_num = i // batch_size + 1
        total_batches = (len(titles) + batch_size - 1) // batch_size
        found = len([title for title in batch if title in result])
        print(f"  批次 {batch_num}/{total_batches}: {found}/{len(batch)} 获取到图片 (infobox)")

        if i + batch_size < len(titles):
            time.sleep(delay)

    return result


def fetch_pageimages_for_titles(
    titles: List[str],
    batch_size: int = 50,
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """回退到 Wikipedia pageimages API，返回 {英文标题: image_url} 的映射。"""
    opener = _build_opener(proxy)
    result: Dict[str, str] = {}

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        titles_param = "|".join(batch)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles_param,
            "prop": "pageimages",
            "pithumbsize": str(THUMB_WIDTH),
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)
        title_lookup = _build_requested_title_lookup(payload, batch)

        pages = payload.get("query", {}).get("pages", [])
        for page in pages:
            if page.get("missing"):
                continue
            page_title = (page.get("title") or "").strip()
            requested_title = title_lookup.get(page_title, page_title if page_title in batch else "")
            thumbnail = page.get("thumbnail", {})
            image_url = (thumbnail.get("source") or "").strip() if thumbnail else ""
            if requested_title and image_url and _is_usable_image_candidate(image_url):
                result[requested_title] = image_url

        batch_num = i // batch_size + 1
        total_batches = (len(titles) + batch_size - 1) // batch_size
        found = len([title for title in batch if title in result])
        print(f"  批次 {batch_num}/{total_batches}: {found}/{len(batch)} 获取到图片 (pageimages)")

        if i + batch_size < len(titles):
            time.sleep(delay)

    return result


def fetch_images_fallback(
    titles: List[str],
    batch_size: int = 50,
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """最终回退方案：扫描页面文件列表，挑选首张可用图片。"""
    opener = _build_opener(proxy)

    if not titles:
        return {}

    print(f"  开始回退获取 {len(titles)} 个页面的图片...")

    image_map: Dict[str, str] = {}

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        titles_param = "|".join(batch)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles_param,
            "prop": "images",
            "imlimit": "50",
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)
        title_lookup = _build_requested_title_lookup(payload, batch)

        page_to_image: Dict[str, str] = {}
        for page in payload.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            title = page.get("title", "")
            requested_title = title_lookup.get(title, title if title in batch else "")
            images = page.get("images", [])
            image_title = _pick_first_usable_image_title(images)
            if requested_title and image_title:
                page_to_image[requested_title] = image_title

        if page_to_image:
            title_to_actual = _fetch_image_urls_for_titles(
                list(page_to_image.values()),
                batch_size=batch_size,
                proxy=proxy,
                delay=0,
            )
            for page_title, img_title in page_to_image.items():
                if img_title in title_to_actual:
                    image_map[page_title] = title_to_actual[img_title]

        if i + batch_size < len(titles):
            time.sleep(delay)

    print(f"  回退获取到 {len(image_map)} 张图片")
    return image_map


def fetch_image_for_title(title: str, proxy: Optional[str] = None) -> str:
    image_map = fetch_infobox_images_for_titles([title], batch_size=1, proxy=proxy, delay=0)
    if title in image_map:
        return image_map[title]

    print("  infobox 未命中，回退到 pageimages...")
    image_map = fetch_pageimages_for_titles([title], batch_size=1, proxy=proxy, delay=0)
    if title in image_map:
        return image_map[title]

    print("  pageimages 未命中，回退到页面文件列表...")
    image_map = fetch_images_fallback([title], batch_size=1, proxy=proxy, delay=0)
    return image_map.get(title, "")


def main() -> None:
    proxy = None
    if "--proxy" in sys.argv:
        idx = sys.argv.index("--proxy")
        if idx + 1 < len(sys.argv):
            proxy = sys.argv[idx + 1]

    if not BIRDS_PATH.exists():
        print(f"未找到 {BIRDS_PATH}，请先运行 crawl_from_wikipedia.py 或确保 birds.csv 存在。")
        sys.exit(1)

    with BIRDS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    headers = reader.fieldnames or []
    if "image_url" not in headers:
        print("birds.csv 中缺少 image_url 列，正在添加。")
        headers.append("image_url")
        for row in rows:
            row["image_url"] = ""

    pending: List[tuple[int, str]] = []
    dirty_count = 0
    for idx, row in enumerate(rows):
        english_name = (row.get("english_name") or "").strip()
        image_url = (row.get("image_url") or "").strip()
        if english_name and (not image_url or _is_dirty_image_url(image_url)):
            pending.append((idx, english_name))
            if image_url:
                dirty_count += 1

    if not pending:
        print("所有鸟类已有图片，无需获取。")
        return

    empty_count = len(pending) - dirty_count
    print(f"共 {len(rows)} 种鸟类，其中 {empty_count} 种尚无图片，{dirty_count} 种图片 URL 待纠正。")
    print(f"开始逐条获取图片（优先 infobox，抓到一条写入一条，间隔 {DELAY}s）...")

    updated = 0
    for current, (idx, english_name) in enumerate(pending, start=1):
        print(f"[{current}/{len(pending)}] 处理 {english_name}")
        current_image_url = (rows[idx].get("image_url") or "").strip()
        image_url = fetch_image_for_title(english_name, proxy=proxy)
        if image_url:
            rows[idx]["image_url"] = image_url
            _write_rows(rows, headers)
            updated += 1
            print("  [ok] 已写入 birds.csv")
        else:
            if current_image_url:
                print("  [miss] 未获取到新图片，已保留原值")
            else:
                print("  [miss] 未获取到图片")

        if current < len(pending) and DELAY > 0:
            time.sleep(DELAY)

    print(f"完成！更新了 {updated}/{len(pending)} 种鸟类的图片 URL。")
    if updated < len(pending):
        print(f"  其中 {len(pending) - updated} 种鸟类未能获取到新图片，已保留原值。")


if __name__ == "__main__":
    main()
