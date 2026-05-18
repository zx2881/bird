"""
从 Wikipedia API 批量获取鸟类页面题图 URL，更新 birds.csv 的 image_url 列。

主要使用 prop=pageimages 轻量请求，回退使用 prop=images + prop=imageinfo。
支持 SSL 降级处理以兼容 Windows 证书环境。
"""

from __future__ import annotations

import csv
import json
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


def fetch_images_for_titles(
    titles: List[str],
    batch_size: int = 50,
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """批量查询 Wikipedia pageimages API，返回 {英文标题: image_url} 的映射。"""
    opener = None
    if proxy:
        proxy_handler = ProxyHandler({"https": proxy})
        opener = build_opener(proxy_handler)
        install_opener(opener)

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
            "pithumbsize": "800",
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)

        pages = payload.get("query", {}).get("pages", [])
        for page in pages:
            if page.get("missing"):
                continue
            title = page.get("title", "")
            thumbnail = page.get("thumbnail", {})
            image_url = thumbnail.get("source", "") if thumbnail else ""
            if title and image_url:
                result[title] = image_url

        batch_num = i // batch_size + 1
        total_batches = (len(titles) + batch_size - 1) // batch_size
        found = len([t for t in batch if t in result])
        print(f"  批次 {batch_num}/{total_batches}: {found}/{len(batch)} 获取到图片 (pageimages)")

        if i + batch_size < len(titles):
            time.sleep(delay)

    return result


def fetch_images_fallback(
    titles: List[str],
    proxy: Optional[str] = None,
    delay: float = 2.0,
) -> Dict[str, str]:
    """回退方案：pageimages 未命中时，通过 prop=images + imageinfo 获取题图。"""
    opener = None
    if proxy:
        proxy_handler = ProxyHandler({"https": proxy})
        opener = build_opener(proxy_handler)
        install_opener(opener)

    if not titles:
        return {}

    print(f"  开始回退获取 {len(titles)} 个页面的图片...")

    image_map: Dict[str, str] = {}

    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        titles_param = "|".join(batch)
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles_param,
            "prop": "images",
            "imlimit": "1",
            "redirects": "1",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urlencode(params)}"
        payload = _make_request(url, opener)

        page_to_image: Dict[str, str] = {}
        for page in payload.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            title = page.get("title", "")
            images = page.get("images", [])
            if title and images:
                page_to_image[title] = images[0]["title"]

        if page_to_image:
            img_titles = list(page_to_image.values())
            img_params = {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "titles": "|".join(img_titles),
                "prop": "imageinfo",
                "iiprop": "url",
            }
            img_url = f"https://en.wikipedia.org/w/api.php?{urlencode(img_params)}"
            img_payload = _make_request(img_url, opener)
            title_to_actual = {}
            for img_page in img_payload.get("query", {}).get("pages", []):
                img_title = img_page.get("title", "")
                iinfo = img_page.get("imageinfo", [])
                if img_title and iinfo:
                    title_to_actual[img_title] = iinfo[0]["url"]

            for page_title, img_title in page_to_image.items():
                if img_title in title_to_actual:
                    image_map[page_title] = title_to_actual[img_title]

        if i + BATCH_SIZE < len(titles):
            time.sleep(delay)

    print(f"  回退获取到 {len(image_map)} 张图片")
    return image_map


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
    for idx, row in enumerate(rows):
        english_name = (row.get("english_name") or "").strip()
        image_url = (row.get("image_url") or "").strip()
        if english_name and not image_url:
            pending.append((idx, english_name))

    if not pending:
        print("所有鸟类已有图片，无需获取。")
        return

    print(f"共 {len(rows)} 种鸟类，其中 {len(pending)} 种尚无图片。")
    print(f"开始批量获取图片（每批 {BATCH_SIZE} 个标题，间隔 {DELAY}s）...")

    titles = [t for _, t in pending]
    image_map = fetch_images_for_titles(titles, batch_size=BATCH_SIZE, proxy=proxy, delay=DELAY)

    missing_titles = [t for t in titles if t not in image_map]
    if missing_titles:
        fallback_map = fetch_images_fallback(missing_titles, proxy=proxy, delay=DELAY)
        image_map.update(fallback_map)

    updated = 0
    for idx, english_name in pending:
        if english_name in image_map:
            rows[idx]["image_url"] = image_map[english_name]
            updated += 1

    temp_path = BIRDS_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(BIRDS_PATH)

    print(f"完成！更新了 {updated}/{len(pending)} 种鸟类的图片 URL。")
    if updated < len(pending):
        print(f"  其中 {len(pending) - updated} 种鸟类未能获取到图片。")


if __name__ == "__main__":
    main()
