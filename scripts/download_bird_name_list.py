"""
自动下载 AviList 官方 checklist，并整理成可供 crawl_from_wikipedia.py 直接使用的 bird_titles.csv。

默认行为:
1. 访问 AviList 官方 checklist 页面
2. 自动定位当前 short/extended xlsx 下载链接
3. 解析 xlsx 中 Taxon_rank=species 的行
4. 输出 data/bird_titles.csv

输出列默认包含:
  page_title, english_name, scientific_name, order, family, family_english_name,
  iucn_red_list_category, avibase_id, range, extinct_or_possibly_extinct,
  source_dataset, source_version, source_url

用法:
  python scripts/download_bird_name_list.py
  python scripts/download_bird_name_list.py --variant extended
  python scripts/download_bird_name_list.py --output data/bird_titles.csv
  npm run download:bird-names
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "bird_titles.csv"
DEFAULT_DOWNLOAD_DIR = ROOT / "tmp" / "avilist"
CHECKLIST_URL = "https://www.avilist.org/checklist/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

OUTPUT_HEADERS = [
    "page_title",
    "english_name",
    "scientific_name",
    "order",
    "family",
    "family_english_name",
    "iucn_red_list_category",
    "avibase_id",
    "range",
    "extinct_or_possibly_extinct",
    "source_dataset",
    "source_version",
    "source_url",
]

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def fetch_text(url: str, referer: Optional[str] = None) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        curl_path = shutil.which("curl") or shutil.which("curl.exe")
        if not curl_path:
            raise
        command = [curl_path, "--fail", "--location", "--user-agent", USER_AGENT]
        if referer:
            command.extend(["--referer", referer])
        command.append(url)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise
        return result.stdout


def discover_download_link(checklist_html: str, variant: str) -> str:
    lowered_variant = variant.lower()
    links = re.findall(r'href="([^"]+\.xlsx)"', checklist_html, flags=re.IGNORECASE)
    normalized_links = [html.unescape(link) for link in links]

    variant_links = [link for link in normalized_links if lowered_variant in link.lower() and "avilist" in link.lower()]
    if not variant_links:
        raise RuntimeError(f"未在 AviList checklist 页面中找到 {variant} xlsx 下载链接。")

    # Prefer the official wp-content uploaded workbook link.
    variant_links.sort(key=lambda value: ("wp-content/uploads" not in value.lower(), len(value)))
    return variant_links[0]


def parse_version_from_url(url: str) -> str:
    filename = Path(urllib.parse.urlparse(url).path).name
    match = re.search(r"AviList[-_]?v?([0-9]{4}[-_][0-9]{1,2}[A-Za-z]{3}|v?[0-9]{4}|[0-9]{4}).*?(short|extended)", filename, re.IGNORECASE)
    if match:
        return match.group(0).replace(".xlsx", "")
    filename_no_ext = re.sub(r"\.xlsx$", "", filename, flags=re.IGNORECASE)
    return filename_no_ext or "AviList"


def download_file(url: str, output_path: Path, referer: Optional[str] = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    curl_path = shutil.which("curl") or shutil.which("curl.exe")
    if curl_path:
        command = [curl_path, "--fail", "--location", "--user-agent", USER_AGENT]
        if referer:
            command.extend(["--referer", referer])
        command.extend(["--output", str(output_path), url])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
    }
    if referer:
        headers["Referer"] = referer

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response, output_path.open("wb") as file:
        file.write(response.read())


def column_letters_to_index(ref: str) -> int:
    letters = re.match(r"([A-Z]+)", ref).group(1)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def load_shared_strings(workbook: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    values: List[str] = []
    for si in root:
        text = "".join(node.text or "" for node in si.iter(f"{{{NS_MAIN}}}t"))
        values.append(text)
    return values


def workbook_sheet_path(workbook: zipfile.ZipFile, preferred_sheet_name: Optional[str] = None) -> str:
    ns = {"a": NS_MAIN, "r": NS_REL}
    workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_xml = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_map = {node.attrib["Id"]: node.attrib["Target"] for node in rels_xml}

    target_id = None
    for sheet in workbook_xml.find("a:sheets", ns):
        sheet_name = sheet.attrib["name"]
        rid = sheet.attrib[f"{{{NS_REL}}}id"]
        if preferred_sheet_name and preferred_sheet_name.lower() == sheet_name.lower():
            target_id = rid
            break
        if preferred_sheet_name is None and "avilist" in sheet_name.lower():
            target_id = rid
            break
    if target_id is None:
        first_sheet = next(iter(workbook_xml.find("a:sheets", ns)))
        target_id = first_sheet.attrib[f"{{{NS_REL}}}id"]

    return "xl/" + rel_map[target_id].lstrip("/")


def read_xlsx_rows(path: Path, preferred_sheet_name: Optional[str] = None) -> List[Dict[str, str]]:
    ns = {"a": NS_MAIN}
    with zipfile.ZipFile(path) as workbook:
        sheet_path = workbook_sheet_path(workbook, preferred_sheet_name=preferred_sheet_name)
        shared_strings = load_shared_strings(workbook)
        sheet_xml = ET.fromstring(workbook.read(sheet_path))
        rows = []
        for row in sheet_xml.find("a:sheetData", ns):
            values_by_index: Dict[int, str] = {}
            for cell in row:
                ref = cell.attrib.get("r", "")
                index = column_letters_to_index(ref)
                value_node = cell.find("a:v", ns)
                if value_node is None:
                    value = ""
                else:
                    value = value_node.text or ""
                    if cell.attrib.get("t") == "s":
                        value = shared_strings[int(value)]
                values_by_index[index] = value
            rows.append(values_by_index)

    if not rows:
        return []

    max_index = max(max(row.keys(), default=-1) for row in rows)
    matrix = [[row.get(index, "") for index in range(max_index + 1)] for row in rows]
    headers = [str(item).strip() for item in matrix[0]]
    data_rows: List[Dict[str, str]] = []
    for values in matrix[1:]:
        record = {}
        for index, header in enumerate(headers):
            if not header:
                continue
            record[header] = str(values[index]).strip() if index < len(values) else ""
        if any(record.values()):
            data_rows.append(record)
    return data_rows


def select_species_rows(rows: Iterable[Dict[str, str]], include_extinct: bool) -> List[Dict[str, str]]:
    selected = []
    for row in rows:
        rank = row.get("Taxon_rank", "").strip().lower()
        if rank != "species":
            continue
        english_name = row.get("English_name_AviList", "").strip()
        scientific_name = row.get("Scientific_name", "").strip()
        if not english_name or not scientific_name:
            continue
        extinct_value = row.get("Extinct_or_possibly_extinct", "").strip()
        if extinct_value and not include_extinct:
            continue
        selected.append(row)
    return selected


def build_output_rows(rows: Iterable[Dict[str, str]], source_url: str, source_version: str) -> List[Dict[str, str]]:
    output = []
    for row in rows:
        english_name = row.get("English_name_AviList", "").strip()
        output.append(
            {
                "page_title": english_name,
                "english_name": english_name,
                "scientific_name": row.get("Scientific_name", "").strip(),
                "order": row.get("Order", "").strip(),
                "family": row.get("Family", "").strip(),
                "family_english_name": row.get("Family_English_name", "").strip(),
                "iucn_red_list_category": row.get("IUCN_Red_List_Category", "").strip(),
                "avibase_id": row.get("AvibaseID", "").strip(),
                "range": row.get("Range", "").strip(),
                "extinct_or_possibly_extinct": row.get("Extinct_or_possibly_extinct", "").strip(),
                "source_dataset": "AviList",
                "source_version": source_version,
                "source_url": source_url,
            }
        )
    return output


def write_csv(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write UTF-8 BOM so Excel/WPS on Windows opens Chinese text correctly.
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载 AviList 并整理为 bird_titles.csv")
    parser.add_argument("--variant", choices=["short", "extended"], default="short", help="下载 AviList short 或 extended 版本")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 CSV 路径，默认 data/bird_titles.csv")
    parser.add_argument("--download-dir", default=str(DEFAULT_DOWNLOAD_DIR), help="下载缓存目录，默认 tmp/avilist/")
    parser.add_argument("--keep-download", action="store_true", help="保留下载的 xlsx 文件")
    parser.add_argument("--include-extinct", action="store_true", help="包含已灭绝或可能灭绝物种，默认排除")
    parser.add_argument("--sheet-name", default="", help="可选，指定 workbook sheet 名称")
    parser.add_argument("--metadata-json", default="", help="可选，额外输出下载元数据 json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    download_dir = Path(args.download_dir)

    try:
        checklist_html = fetch_text(CHECKLIST_URL)
    except urllib.error.URLError as error:
        raise SystemExit(f"无法访问 AviList checklist 页面: {error}") from error

    download_url = discover_download_link(checklist_html, args.variant)
    version = parse_version_from_url(download_url)

    filename = Path(urllib.parse.urlparse(download_url).path).name or f"avilist-{args.variant}.xlsx"
    download_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = download_dir / filename
    download_file(download_url, xlsx_path, referer=CHECKLIST_URL)

    rows = read_xlsx_rows(xlsx_path, preferred_sheet_name=args.sheet_name or None)
    species_rows = select_species_rows(rows, include_extinct=args.include_extinct)
    output_rows = build_output_rows(species_rows, source_url=download_url, source_version=version)
    write_csv(output_path, OUTPUT_HEADERS, output_rows)

    metadata = {
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "variant": args.variant,
        "source_url": download_url,
        "source_version": version,
        "input_rows": len(rows),
        "species_rows": len(species_rows),
        "output_path": str(output_path),
        "include_extinct": args.include_extinct,
    }
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    if args.metadata_json:
        metadata_path = Path(args.metadata_json)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.keep_download and xlsx_path.exists():
        xlsx_path.unlink()


if __name__ == "__main__":
    main()
