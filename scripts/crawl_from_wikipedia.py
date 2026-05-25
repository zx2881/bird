"""
从 Wikipedia / MediaWiki API 抓取鸟类页面原始数据，并将结果写入 data/ 目录下的 CSV。

输出文件:
  - data/birds.csv
  - data/locations.csv
  - data/relations.csv
  - data/wikipedia_raw/*.json
  - data/wikipedia_checkpoint/*.json

说明:
1. birds.csv 和 locations.csv 作为实体主表。
2. relations.csv 尽量遵循“三元组提取.md”的 schema，并补充 subject_id/object_id/object_summary 工程字段。
3. wikipedia_checkpoint/ 用于断点续跑；已完成标题会自动跳过，中断后可从 checkpoint 恢复到 CSV。
4. 抽取逻辑是规则型、可复核的 best-effort 方案，适合原型阶段批量整理 Wikipedia 数据。

示例:
  python scripts/crawl_from_wikipedia.py --titles "Red-crowned Crane" "Crested Ibis" --build-json
  npm run crawl:wikipedia -- --titles "California Condor" "Philippine Eagle"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener, install_opener, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_RAW_DIR = DEFAULT_DATA_DIR / "wikipedia_raw"
DEFAULT_CHECKPOINT_DIR = DEFAULT_DATA_DIR / "wikipedia_checkpoint"
BUILD_SCRIPT = ROOT / "scripts" / "build_knowledge_json.py"
CHECKPOINT_VERSION = 1

BIRDS_HEADERS = [
    "id",
    "name",
    "english_name",
    "latin_name",
    "summary",
    "lat",
    "lng",
    "image_url",
    "order",
    "family",
    "genus",
    "species",
    "order_cn",
    "family_cn",
    "genus_cn",
    "species_cn",
]
LOCATIONS_HEADERS = ["id", "name", "summary", "lat", "lng"]
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

STATUS_SUMMARIES = {
    "CR": "IUCN 极危。",
    "EN": "IUCN 濒危。",
    "VU": "IUCN 易危。",
    "NT": "IUCN 近危。",
    "LC": "IUCN 无危。",
}

THREAT_CATALOG = {
    "栖息地破坏": ("threat-habitat-loss", "开发、采伐和围垦等活动导致适宜生境减少。"),
    "湿地退化": ("threat-wetland-degradation", "湿地水文和植被结构被改变导致适宜生境下降。"),
    "滩涂围垦": ("threat-reclamation", "滨海滩涂被转化为建设或农业用地。"),
    "迁飞地丧失": ("threat-migratory-site-loss", "迁飞链条上关键停歇地和补给地消失。"),
    "气候变化": ("threat-climate-change", "长期改变水文节律与生态系统稳定性的全球变化因素。"),
    "气候变暖": ("threat-global-warming", "长期升温改变海冰和海洋环境条件。"),
    "污染": ("threat-pollution", "农药、工业污染与水体污染影响食物链安全。"),
    "农药污染": ("threat-pesticide-pollution", "农业化学品通过水体和食物链影响鸟类生存。"),
    "非法猎捕": ("threat-illegal-hunting", "直接捕杀或非法贸易导致种群下降。"),
    "猎捕压力": ("threat-hunting-pressure", "直接猎捕或误捕造成额外死亡。"),
    "森林砍伐": ("threat-deforestation", "原生林被砍伐导致栖息地面积和连通性下降。"),
    "外来捕食者": ("threat-invasive-predators", "岛屿鸟类常受猫、鼬和鼠等外来种影响。"),
    "铅中毒": ("threat-lead-poisoning", "食腐鸟类因摄入铅弹残留而中毒。"),
    "人类活动扰动": ("threat-human-disturbance", "旅游、施工和高频活动影响繁殖或觅食。"),
    "湿地排水": ("threat-wetland-drainage", "湿地被排干转为农业或建设用地。"),
    "非法贸易": ("threat-illegal-trade", "为宠物或展示用途进行非法捕捉与交易。"),
    "食物资源下降": ("threat-food-decline", "底栖生物和小型鱼类下降带来的觅食压力。"),
    "低繁殖率": ("threat-low-reproduction", "繁殖周期长且单次成功育雏率有限。"),
    "电线碰撞": ("threat-powerline-collision", "大型鸟类在飞行中与输电设施碰撞的风险。"),
    "小种群风险": ("threat-small-population", "种群规模过小导致遗传多样性下降和脆弱性上升。"),
}

HABITAT_CATALOG = {
    "湿地": ("hab-wetland", "浅水、沼泽与植被斑块组成的高生产力生态系统。"),
    "沼泽": ("hab-marsh", "具有较高含水量和密生植被的浅水环境。"),
    "滩涂": ("hab-tidal-flat", "迁飞水鸟高度依赖的滨海觅食带。"),
    "河谷稻田": ("hab-rice-valley", "传统农田与河谷湿地交错形成的复合栖息环境。"),
    "山地森林": ("hab-mountain-forest", "以成熟阔叶林和混交林为主的山地森林系统。"),
    "成熟森林": ("hab-mature-forest", "具备成熟林冠和树洞资源的森林生境。"),
    "山地河流": ("hab-mountain-river", "冷水、清澈且流速较高的繁殖河流环境。"),
    "海岸苔原": ("hab-coastal-tundra", "高纬海岸带的低矮植被繁殖环境。"),
    "潮间带泥滩": ("hab-intertidal-mudflat", "迁飞水鸟高度依赖的滨海泥滩和浅滩系统。"),
    "海岸湿地": ("hab-coastal-wetland", "海湾、泻湖、盐沼与河口组成的复合湿地。"),
    "河口": ("hab-estuary", "淡水与海水交汇形成的高生产力边缘生态系统。"),
    "峡谷峭壁": ("hab-canyon-cliff", "大型猛禽和食腐鸟偏好的高崖栖息环境。"),
    "开阔山地": ("hab-open-mountain", "地形开阔且便于大翼展鸟类活动的山地区域。"),
    "热带雨林": ("hab-rainforest", "结构复杂且冠层完整的高生物多样性森林。"),
    "温带森林": ("hab-temperate-forest", "温带岛屿或山地森林生态系统。"),
    "灌丛": ("hab-shrubland", "低矮木本植物占优势的陆地生境。"),
    "海冰": ("hab-sea-ice", "帝企鹅等极地鸟类繁殖与育雏的平台环境。"),
    "极地海域": ("hab-polar-ocean", "海冰边缘与寒冷海域构成的极地觅食环境。"),
    "稀树草原": ("hab-savanna", "东非常见的开放草地与湿地边缘复合景观。"),
}

HABITAT_PATTERNS = [
    ("海岸苔原", [r"\bcoastal tundra\b"]),
    ("潮间带泥滩", [r"\bintertidal mudflats?\b", r"\bintertidal zone\b"]),
    ("海岸湿地", [r"\bcoastal wetlands?\b", r"\bestuar(?:y|ies)\b"]),
    ("河口", [r"\bestuar(?:y|ies)\b", r"\briver mouths?\b"]),
    ("峡谷峭壁", [r"\bcanyons?\b", r"\bcliffs?\b"]),
    ("开阔山地", [r"\bopen mountains?\b", r"\bmountainous areas\b"]),
    ("热带雨林", [r"\btropical rain ?forests?\b"]),
    ("温带森林", [r"\btemperate forests?\b"]),
    ("灌丛", [r"\bshrublands?\b", r"\bscrublands?\b"]),
    ("海冰", [r"\bsea ice\b"]),
    ("极地海域", [r"\bpolar waters?\b", r"\bantarctic waters?\b"]),
    ("稀树草原", [r"\bsavannas?\b", r"\bgrasslands?\b"]),
    ("山地河流", [r"\bmountain rivers?\b", r"\bforested rivers?\b", r"\bfast-flowing rivers?\b"]),
    ("成熟森林", [r"\bmature forests?\b", r"\bold-growth forests?\b"]),
    ("山地森林", [r"\bmountain forests?\b", r"\bmontane forests?\b"]),
    ("河谷稻田", [r"\brace padd(?:y|ies)\b", r"\bvalley rice fields?\b"]),
    ("湿地", [r"\bwetlands?\b"]),
    ("沼泽", [r"\bmarsh(?:es)?\b", r"\bswamps?\b"]),
    ("滩涂", [r"\bflats?\b", r"\btidal flats?\b"]),
]

THREAT_PATTERNS = [
    ("湿地退化", [r"\bwetland degradation\b"]),
    ("栖息地破坏", [r"\bhabitat loss\b", r"\bhabitat destruction\b", r"\bhabitat degradation\b"]),
    ("滩涂围垦", [r"\breclamation\b", r"\bland reclamation\b"]),
    ("迁飞地丧失", [r"\bstaging area loss\b", r"\bmigratory stopover loss\b"]),
    ("气候变化", [r"\bclimate change\b"]),
    ("气候变暖", [r"\bglobal warming\b"]),
    ("污染", [r"\bpollution\b", r"\bwater pollution\b", r"\bcontamination\b"]),
    ("农药污染", [r"\bpesticides?\b"]),
    ("非法猎捕", [r"\bpoaching\b", r"\billegal hunting\b"]),
    ("猎捕压力", [r"\bhunting pressure\b", r"\bhunting\b"]),
    ("森林砍伐", [r"\bdeforestation\b", r"\blogging\b"]),
    ("外来捕食者", [r"\binvasive predators?\b", r"\bintroduced predators?\b"]),
    ("铅中毒", [r"\blead poisoning\b"]),
    ("人类活动扰动", [r"\bhuman disturbance\b", r"\bdisturbance\b"]),
    ("湿地排水", [r"\bwetland drainage\b", r"\bdrainage\b"]),
    ("非法贸易", [r"\billegal trade\b"]),
    ("食物资源下降", [r"\bfood availability\b", r"\bfood decline\b"]),
    ("低繁殖率", [r"\blow reproductive rate\b", r"\blow breeding success\b"]),
    ("电线碰撞", [r"\bpower line collisions?\b", r"\bpowerline collisions?\b"]),
    ("小种群风险", [r"\bsmall population\b", r"\bpopulation bottleneck\b"]),
]

STATUS_PATTERNS = {
    "CR": [r"\bCR\b", r"critically endangered"],
    "EN": [r"\bEN\b", r"endangered"],
    "VU": [r"\bVU\b", r"vulnerable"],
    "NT": [r"\bNT\b", r"near threatened"],
    "LC": [r"\bLC\b", r"least concern"],
}

LOCATION_HINT_WORDS = {
    "wetland",
    "wetlands",
    "island",
    "islands",
    "sea",
    "bay",
    "gulf",
    "lake",
    "lakes",
    "mountain",
    "mountains",
    "province",
    "park",
    "reserve",
    "coast",
    "delta",
    "peninsula",
    "river",
    "forest",
    "valley",
    "ocean",
    "harbor",
    "harbour",
    "marsh",
    "china",
    "japan",
    "russia",
    "korea",
    "philippines",
    "uganda",
    "california",
    "antarctica",
    "new zealand",
}

COUNTRY_LOCATION_NAMES = {
    "China",
    "Japan",
    "South Korea",
    "North Korea",
    "Mongolia",
    "Russia",
    "India",
    "Nepal",
    "Bhutan",
    "Myanmar",
    "Vietnam",
    "Laos",
    "Thailand",
    "Cambodia",
    "Philippines",
    "Indonesia",
    "Malaysia",
    "Singapore",
    "Australia",
    "New Zealand",
    "United States",
    "United States of America",
    "Canada",
    "Mexico",
    "Brazil",
    "Argentina",
    "Chile",
    "Peru",
    "South Africa",
    "Kenya",
    "Tanzania",
    "Ethiopia",
    "United Kingdom",
    "France",
    "Germany",
    "Italy",
    "Spain",
    "Portugal",
    "Netherlands",
    "Poland",
    "Norway",
    "Sweden",
    "Finland",
    "Denmark",
    "中国",
    "中华人民共和国",
    "日本",
    "韩国",
    "朝鲜",
    "蒙古",
    "俄罗斯",
    "印度",
    "尼泊尔",
    "不丹",
    "缅甸",
    "越南",
    "老挝",
    "泰国",
    "柬埔寨",
    "菲律宾",
    "印度尼西亚",
    "马来西亚",
    "新加坡",
    "澳大利亚",
    "新西兰",
    "美国",
    "加拿大",
    "墨西哥",
    "巴西",
    "阿根廷",
    "智利",
    "秘鲁",
    "南非",
    "肯尼亚",
    "坦桑尼亚",
    "埃塞俄比亚",
    "英国",
    "法国",
    "德国",
    "意大利",
    "西班牙",
    "葡萄牙",
    "荷兰",
    "波兰",
    "挪威",
    "瑞典",
    "芬兰",
    "丹麦",
}

DISTRIBUTION_SECTION_RE = re.compile(
    r"distribution|range|habitat|ecology|migration|migrat|population and distribution",
    re.IGNORECASE,
)
CONSERVATION_SECTION_RE = re.compile(
    r"conservation|status|threat|decline|protection",
    re.IGNORECASE,
)
DISTRIBUTION_SENTENCE_RE = re.compile(
    r"\b(found in|occurs in|distributed in|range(?:s|d)? in|native to|breeds in|winter(?:s|ing)? in|migrat(?:es|e|ing) to|inhabit(?:s|ing)|found across)\b",
    re.IGNORECASE,
)
HABITAT_SENTENCE_RE = re.compile(
    r"\b(lives? in|inhabit(?:s|ing)|habitat|found in|nests? in|breeds? in|forages? in|occurs in)\b",
    re.IGNORECASE,
)
THREAT_SENTENCE_RE = re.compile(
    r"\b(threat(?:ened|s)?|decline|endangered by|pressures?|due to|because of|suffers from|face(?:s|d)?)\b",
    re.IGNORECASE,
)


@dataclass
class PageBundle:
    wiki: str
    requested_title: str
    resolved_title: str
    extract: str
    wikitext: str
    zh_title: str
    coordinates: Tuple[Optional[float], Optional[float]]
    page_id: Optional[int]
    canonical_url: str
    image_url: str = ""


class WikiCrawler:
    def __init__(self, delay: float = 0.3, proxy: str = "") -> None:
        self.delay = delay
        self.page_cache: Dict[Tuple[str, str, bool], PageBundle] = {}
        self.opener = None
        if proxy:
            proxy_handler = ProxyHandler({"https": proxy})
            self.opener = build_opener(proxy_handler)
            install_opener(self.opener)

    def fetch_page_bundle(self, title: str, wiki: str = "en", include_wikitext: bool = True) -> PageBundle:
        cache_key = (wiki, title, include_wikitext)
        if cache_key in self.page_cache:
            return self.page_cache[cache_key]

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
            "titles": title,
            "prop": "extracts|coordinates|langlinks|pageimages" + ("|revisions" if include_wikitext else ""),
            "explaintext": "1",
            "exsectionformat": "plain",
            "exlimit": "1",
            "lllang": "zh",
            "lllimit": "1",
            "pithumbsize": "800",
        }
        if include_wikitext:
            params["rvprop"] = "content"
            params["rvslots"] = "main"

        url = f"https://{wiki}.wikipedia.org/w/api.php?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "User-Agent": "bird-kg-crawler/1.0 (research prototype; contact local-user)",
                "Accept": "application/json",
            },
        )

        try:
            opener = self.opener if self.opener else None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if opener:
                        with opener.open(request, timeout=30) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                    else:
                        with urlopen(request, timeout=30) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                    break
                except HTTPError as error:
                    if error.code == 429 and attempt < max_retries - 1:
                        wait = (attempt + 1) * 5
                        print(f"  [retry] 429 限流，{wait}s 后重试 ({attempt + 1}/{max_retries - 1})")
                        time.sleep(wait)
                        continue
                    raise
        except HTTPError as error:
            raise RuntimeError(f"{wiki} Wikipedia 请求失败: {error.code} {error.reason}") from error
        except URLError as error:
            raise RuntimeError(f"{wiki} Wikipedia 网络错误: {error.reason}") from error

        pages = payload.get("query", {}).get("pages", [])
        if not pages:
            raise RuntimeError(f"{wiki} Wikipedia 未返回页面: {title}")

        page = pages[0]
        if page.get("missing"):
            raise RuntimeError(f"{wiki} Wikipedia 页面不存在: {title}")

        revisions = page.get("revisions", [])
        wikitext = ""
        if revisions:
            slots = revisions[0].get("slots", {})
            main_slot = slots.get("main", {})
            wikitext = main_slot.get("content", "") or revisions[0].get("content", "") or ""

        coords = page.get("coordinates", [])
        lat = coords[0].get("lat") if coords else None
        lng = coords[0].get("lon") if coords else None
        langlinks = page.get("langlinks", [])
        zh_title = langlinks[0].get("title", "") if langlinks else ""
        thumbnail = page.get("thumbnail", {})
        image_url = thumbnail.get("source", "") if thumbnail else ""
        resolved_title = page.get("title", title)
        bundle = PageBundle(
            wiki=wiki,
            requested_title=title,
            resolved_title=resolved_title,
            extract=page.get("extract", "") or "",
            wikitext=wikitext,
            zh_title=zh_title,
            coordinates=(lat, lng),
            page_id=page.get("pageid"),
            canonical_url=f"https://{wiki}.wikipedia.org/wiki/{quote(resolved_title.replace(' ', '_'))}",
            image_url=image_url,
        )
        self.page_cache[cache_key] = bundle
        if self.delay:
            time.sleep(self.delay)
        return bundle


def normalize_title_key(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip()).casefold()


def merge_title_aliases(*title_groups: Sequence[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for group in title_groups:
        for title in group:
            cleaned = re.sub(r"\s+", " ", (title or "").strip())
            if not cleaned:
                continue
            key = normalize_title_key(cleaned)
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
    return merged


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or md5(text.encode("utf-8")).hexdigest()[:8]


def stable_id(prefix: str, name: str) -> str:
    normalized = slugify(name)
    digest = md5(name.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{normalized}-{digest}" if normalized else f"{prefix}-{digest}"


def strip_templates(text: str) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        current = re.sub(r"\{\{[^{}]*\}\}", "", current)
    return current


def clean_wikitext_sentence(text: str) -> str:
    text = re.sub(r"<ref[^>/]*>.*?</ref>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = strip_templates(text)
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[https?://[^\s\]]+\s*([^\]]*)\]", r"\1", text)
    text = re.sub(r"''+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .;,\n\t")


def split_wikitext_sections(wikitext: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = {"__lead__": []}
    current = "__lead__"
    for line in wikitext.splitlines():
        heading_match = re.match(r"^(={2,})\s*(.*?)\s*\1\s*$", line.strip())
        if heading_match:
            current = heading_match.group(2).strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def split_sentences(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", text)
    pieces = re.split(r"(?<=[.!?。！？])\s+", normalized)
    return [piece.strip() for piece in pieces if piece.strip()]


def extract_links(raw_sentence: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]", raw_sentence):
        title = match.group(1).strip()
        label = (match.group(2) or title).strip()
        if ":" in title:
            continue
        links.append((title, label))
    return links


def first_sentences(text: str, limit: int = 2, max_length: int = 180) -> str:
    sentences = split_sentences(text)
    selected = " ".join(sentences[:limit]).strip()
    if len(selected) <= max_length:
        return selected
    return selected[: max_length - 1].rstrip() + "…"


def normalize_status(value: str) -> str:
    candidate = clean_wikitext_sentence(value).upper().strip()
    for status, patterns in STATUS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, candidate, re.IGNORECASE):
                return status
    return ""


def parse_infobox_value(wikitext: str, keys: Sequence[str]) -> str:
    pattern = re.compile(
        r"^\|\s*(?:" + "|".join(re.escape(key) for key in keys) + r")\s*=\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(wikitext)
    return clean_wikitext_sentence(match.group(1)) if match else ""


def infer_latin_name(wikitext: str, extract: str) -> str:
    direct = parse_infobox_value(wikitext, ["taxon", "binomial", "binomial_name"])
    if direct:
        latin = re.search(r"([A-Z][a-z]+ [a-z][a-z-]+(?: [a-z][a-z-]+)?)", direct)
        if latin:
            return latin.group(1)

    genus = parse_infobox_value(wikitext, ["genus"])
    species = parse_infobox_value(wikitext, ["species"])
    if genus and species:
        species_clean = species.replace(".", "").strip()
        if species_clean and species_clean.lower() != species_clean:
            return f"{genus} {species_clean}"
        if species_clean:
            return f"{genus} {species_clean}"

    from_extract = re.search(r"\(([A-Z][a-z]+ [a-z][a-z-]+(?: [a-z][a-z-]+)?)\)", extract)
    return from_extract.group(1) if from_extract else ""


def infer_status(wikitext: str, extract: str) -> str:
    status_value = parse_infobox_value(wikitext, ["status", "conservation_status"])
    normalized = normalize_status(status_value)
    if normalized:
        return normalized
    for status, patterns in STATUS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, extract, re.IGNORECASE):
                return status
    return ""


def infer_taxon_name(wikitext: str) -> str:
    for keys in (["family", "familia"], ["order", "ordo"], ["parent"]):
        value = parse_infobox_value(wikitext, keys)
        if not value:
            continue
        cleaned = clean_wikitext_sentence(value)
        if re.search(r"(idae|formes)$", cleaned, re.IGNORECASE):
            return cleaned
    return ""


def infer_habitats(text: str) -> List[Tuple[str, str, str]]:
    triples = []
    lowered = text.lower()
    for name, patterns in HABITAT_PATTERNS:
        if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in patterns):
            object_id, summary = HABITAT_CATALOG[name]
            triples.append((object_id, name, summary))
    return triples


def infer_threats(text: str) -> List[Tuple[str, str, str]]:
    triples = []
    lowered = text.lower()
    for name, patterns in THREAT_PATTERNS:
        if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in patterns):
            object_id, summary = THREAT_CATALOG[name]
            triples.append((object_id, name, summary))
    return triples


def looks_like_location_title(title: str) -> bool:
    lowered = title.lower()
    if lowered.startswith(("bird", "species", "taxonomy")):
        return False
    if re.search(r"\b(order|family|genus|species)\b", lowered):
        return False
    return any(keyword in lowered for keyword in LOCATION_HINT_WORDS) or bool(re.search(r"[A-Z][a-z]+(?: [A-Z][a-z]+)+", title))


def is_country_location_name(name: str) -> bool:
    text = (name or "").strip()
    if not text:
        return False
    if text in COUNTRY_LOCATION_NAMES:
        return True
    lowered = text.lower()
    return lowered in {item.lower() for item in COUNTRY_LOCATION_NAMES}


def resolve_location_bundle(crawler: WikiCrawler, title: str, lang: str = "en") -> Optional[PageBundle]:
    try:
        bundle = crawler.fetch_page_bundle(title, wiki=lang, include_wikitext=False)
    except RuntimeError:
        return None

    lat, lng = bundle.coordinates
    if lat is not None and lng is not None:
        return bundle
    if looks_like_location_title(bundle.resolved_title):
        return bundle
    return None


def build_location_row(bundle: PageBundle, crawler: WikiCrawler) -> Dict[str, str]:
    zh_title = bundle.zh_title
    zh_summary = ""
    if zh_title:
        try:
            zh_bundle = crawler.fetch_page_bundle(zh_title, wiki="zh", include_wikitext=False)
            zh_summary = first_sentences(zh_bundle.extract, limit=2, max_length=120)
        except RuntimeError:
            zh_summary = ""

    lat, lng = bundle.coordinates
    return {
        "id": stable_id("loc", zh_title or bundle.resolved_title),
        "name": zh_title or bundle.resolved_title,
        "summary": zh_summary or first_sentences(bundle.extract, limit=1, max_length=120),
        "lat": "" if lat is None else f"{lat}",
        "lng": "" if lng is None else f"{lng}",
    }


def location_specificity_score(location_row: Dict[str, str]) -> int:
    name = location_row["name"].lower()
    score = 0
    keyword_groups = [
        ("国家级自然保护区", 6),
        ("自然保护区", 6),
        ("湿地", 5),
        ("delta", 5),
        ("三角洲", 5),
        ("lake", 4),
        ("湖", 4),
        ("river", 4),
        ("江", 4),
        ("mountain", 4),
        ("山", 4),
        ("bay", 4),
        ("湾", 4),
        ("park", 4),
        ("reserve", 4),
        ("coast", 3),
        ("peninsula", 2),
        ("province", 1),
        ("中国", 0),
        ("日本", 0),
        ("俄羅斯", 0),
        ("俄罗斯", 0),
    ]
    for keyword, value in keyword_groups:
        if keyword.lower() in name:
            score = max(score, value)
    return score


def load_csv_rows(path: Path, headers: Sequence[str]) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    normalized_rows = []
    for row in rows:
        normalized = {header: (row.get(header, "") or "").strip() for header in headers}
        normalized_rows.append(normalized)
    return normalized_rows


def normalize_structured_row(row: Dict, headers: Sequence[str]) -> Dict[str, str]:
    return {header: str(row.get(header, "") or "").strip() for header in headers}


def write_csv_rows(path: Path, headers: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    # Write UTF-8 BOM so Excel/WPS on Windows opens Chinese text correctly.
    with temp_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    temp_path.replace(path)


def merge_row(existing: Dict[str, str], incoming: Dict[str, str], overwrite: bool = False) -> Dict[str, str]:
    merged = dict(existing)
    for key, value in incoming.items():
        if overwrite:
            if value != "":
                merged[key] = value
        else:
            if not merged.get(key) and value != "":
                merged[key] = value
    return merged


def upsert_rows(
    rows: List[Dict[str, str]],
    new_rows: Iterable[Dict[str, str]],
    key_fields: Sequence[str],
    overwrite: bool = False,
) -> Tuple[List[Dict[str, str]], bool]:
    indexed = {tuple(row[field] for field in key_fields): dict(row) for row in rows}
    order = [tuple(row[field] for field in key_fields) for row in rows]
    changed = False
    for new_row in new_rows:
        key = tuple(new_row[field] for field in key_fields)
        if key in indexed:
            merged_row = merge_row(indexed[key], new_row, overwrite=overwrite)
            if merged_row != indexed[key]:
                changed = True
            indexed[key] = merged_row
        else:
            indexed[key] = dict(new_row)
            order.append(key)
            changed = True
    return [indexed[key] for key in order], changed


def load_titles(args: argparse.Namespace) -> List[str]:
    titles = [title.strip() for title in args.titles if title.strip()]
    if args.input_file:
        path = Path(args.input_file)
        if not path.exists():
            raise FileNotFoundError(f"输入文件不存在: {path}")
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    candidate = row.get("title") or row.get("page_title") or row.get("english_name") or ""
                    candidate = candidate.strip()
                    if candidate:
                        titles.append(candidate)
        else:
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line:
                    titles.append(line)
    return list(dict.fromkeys(titles))


def build_bird_row(en_bundle: PageBundle, zh_bundle: Optional[PageBundle]) -> Dict[str, str]:
    name = zh_bundle.resolved_title if zh_bundle else (en_bundle.zh_title or en_bundle.resolved_title)
    summary_source = zh_bundle.extract if zh_bundle and zh_bundle.extract else en_bundle.extract
    lat, lng = zh_bundle.coordinates if zh_bundle and any(zh_bundle.coordinates) else en_bundle.coordinates
    return {
        "id": stable_id("bird", name or en_bundle.resolved_title),
        "name": name or en_bundle.resolved_title,
        "english_name": en_bundle.resolved_title,
        "latin_name": infer_latin_name(en_bundle.wikitext, en_bundle.extract),
        "summary": first_sentences(summary_source, limit=2, max_length=140),
        "lat": "" if lat is None else f"{lat}",
        "lng": "" if lng is None else f"{lng}",
        "image_url": en_bundle.image_url or "",
    }


def build_raw_payload(en_bundle: PageBundle, zh_bundle: Optional[PageBundle], status: str, taxon_name: str) -> Dict:
    return {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "en": {
            "requested_title": en_bundle.requested_title,
            "resolved_title": en_bundle.resolved_title,
            "url": en_bundle.canonical_url,
            "page_id": en_bundle.page_id,
            "extract": en_bundle.extract,
            "wikitext": en_bundle.wikitext,
            "coordinates": {
                "lat": en_bundle.coordinates[0],
                "lng": en_bundle.coordinates[1],
            },
            "zh_title": en_bundle.zh_title,
            "image_url": en_bundle.image_url,
        },
        "zh": None
        if not zh_bundle
        else {
            "resolved_title": zh_bundle.resolved_title,
            "url": zh_bundle.canonical_url,
            "page_id": zh_bundle.page_id,
            "extract": zh_bundle.extract,
            "coordinates": {
                "lat": zh_bundle.coordinates[0],
                "lng": zh_bundle.coordinates[1],
            },
        },
        "parsed": {
            "status": status,
            "taxon_name": taxon_name,
        },
    }


def build_checkpoint_payload(
    requested_title: str,
    bird_row: Dict[str, str],
    location_rows: List[Dict[str, str]],
    relations: List[Dict[str, str]],
    raw_file: Path,
) -> Dict:
    return {
        "version": CHECKPOINT_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "requested_title": requested_title,
        "resolved_title": bird_row["english_name"],
        "title_aliases": merge_title_aliases([requested_title, bird_row["english_name"]]),
        "bird_id": bird_row["id"],
        "raw_file": raw_file.name,
        "bird": bird_row,
        "locations": location_rows,
        "relations": relations,
    }


def build_relation(subject_row: Dict[str, str], predicate: str, object_id: str, object_name: str, object_type: str, evidence: str, object_summary: str) -> Dict[str, str]:
    return {
        "subject_id": subject_row["id"],
        "subject": subject_row["name"],
        "predicate": predicate,
        "object_id": object_id,
        "object": object_name,
        "subject_type": "Bird",
        "object_type": object_type,
        "evidence": evidence,
        "object_summary": object_summary,
    }


def collect_distribution_relations(
    subject_row: Dict[str, str],
    sections: Dict[str, str],
    crawler: WikiCrawler,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    location_rows: List[Dict[str, str]] = []
    relations: List[Dict[str, str]] = []
    seen_object_ids = set()

    for section_name, raw_text in sections.items():
        if section_name != "__lead__" and not DISTRIBUTION_SECTION_RE.search(section_name):
            continue
        for raw_sentence in split_sentences(raw_text):
            if not DISTRIBUTION_SENTENCE_RE.search(raw_sentence):
                continue
            evidence = clean_wikitext_sentence(raw_sentence)
            for link_title, _label in extract_links(raw_sentence):
                bundle = resolve_location_bundle(crawler, link_title, lang="en")
                if bundle is None:
                    continue
                location_row = build_location_row(bundle, crawler)
                if is_country_location_name(location_row["name"]) or is_country_location_name(bundle.resolved_title):
                    continue
                if location_row["id"] in seen_object_ids:
                    continue
                seen_object_ids.add(location_row["id"])
                location_rows.append(location_row)
                relations.append(
                    build_relation(
                        subject_row,
                        "distributed_in",
                        location_row["id"],
                        location_row["name"],
                        "Location",
                        evidence,
                        "",
                    )
                )
    return location_rows, relations


def collect_habitat_relations(subject_row: Dict[str, str], sections: Dict[str, str]) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    seen = set()
    for section_name, raw_text in sections.items():
        if section_name != "__lead__" and not DISTRIBUTION_SECTION_RE.search(section_name):
            continue
        for raw_sentence in split_sentences(raw_text):
            evidence = clean_wikitext_sentence(raw_sentence)
            if not HABITAT_SENTENCE_RE.search(evidence):
                continue
            for object_id, object_name, object_summary in infer_habitats(evidence):
                key = (object_id, evidence)
                if key in seen:
                    continue
                seen.add(key)
                relations.append(
                    build_relation(
                        subject_row,
                        "lives_in",
                        object_id,
                        object_name,
                        "Habitat",
                        evidence,
                        object_summary,
                    )
                )
    return relations


def collect_status_relations(subject_row: Dict[str, str], status: str, extract: str) -> List[Dict[str, str]]:
    if not status:
        return []
    evidence = f"status = {status}"
    return [
        build_relation(
            subject_row,
            "has_status",
            f"status-{status.lower()}",
            status,
            "Status",
            evidence or f"{subject_row['name']} 的保护等级为 {status}。",
            STATUS_SUMMARIES.get(status, f"依据 Wikipedia 抽取的保护等级：{status}。"),
        )
    ]


def collect_threat_relations(subject_row: Dict[str, str], sections: Dict[str, str]) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    seen = set()
    for section_name, raw_text in sections.items():
        if section_name != "__lead__" and not CONSERVATION_SECTION_RE.search(section_name):
            continue
        for raw_sentence in split_sentences(raw_text):
            evidence = clean_wikitext_sentence(raw_sentence)
            if not THREAT_SENTENCE_RE.search(evidence):
                continue
            for object_id, object_name, object_summary in infer_threats(evidence):
                key = object_id
                if key in seen:
                    continue
                seen.add(key)
                relations.append(
                    build_relation(
                        subject_row,
                        "threatened_by",
                        object_id,
                        object_name,
                        "Threat",
                        evidence,
                        object_summary,
                    )
                )
    return relations


def collect_taxon_relations(subject_row: Dict[str, str], taxon_name: str, extract: str) -> List[Dict[str, str]]:
    if not taxon_name:
        return []
    return [
        build_relation(
            subject_row,
            "belongs_to",
            stable_id("taxonomy", taxon_name),
            taxon_name,
            "Taxon",
            first_sentences(extract, limit=1, max_length=160) or f"{subject_row['name']} 属于 {taxon_name}。",
            f"依据 Wikipedia infobox 抽取的分类单元：{taxon_name}。",
        )
    ]


def crawl_one_title(crawler: WikiCrawler, title: str) -> Tuple[Dict[str, str], List[Dict[str, str]], List[Dict[str, str]], Dict]:
    en_bundle = crawler.fetch_page_bundle(title, wiki="en", include_wikitext=True)
    zh_bundle = None
    if en_bundle.zh_title:
        try:
            zh_bundle = crawler.fetch_page_bundle(en_bundle.zh_title, wiki="zh", include_wikitext=False)
        except RuntimeError:
            zh_bundle = None

    bird_row = build_bird_row(en_bundle, zh_bundle)
    sections = split_wikitext_sections(en_bundle.wikitext)
    status = infer_status(en_bundle.wikitext, en_bundle.extract)
    taxon_name = infer_taxon_name(en_bundle.wikitext)

    location_rows, distribution_relations = collect_distribution_relations(bird_row, sections, crawler)
    habitat_relations = collect_habitat_relations(bird_row, sections)
    status_relations = collect_status_relations(bird_row, status, en_bundle.extract)
    threat_relations = collect_threat_relations(bird_row, sections)
    taxon_relations = collect_taxon_relations(bird_row, taxon_name, en_bundle.extract)

    if (not bird_row["lat"] or not bird_row["lng"]) and location_rows:
        candidates = [row for row in location_rows if row["lat"] and row["lng"]]
        if candidates:
            preferred = sorted(candidates, key=location_specificity_score, reverse=True)[0]
            bird_row["lat"] = preferred["lat"]
            bird_row["lng"] = preferred["lng"]

    raw_payload = build_raw_payload(en_bundle, zh_bundle, status, taxon_name)
    relations = distribution_relations + habitat_relations + status_relations + threat_relations + taxon_relations
    return bird_row, location_rows, relations, raw_payload


def write_json_payload(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def save_raw_payload(raw_dir: Path, bird_id: str, payload: Dict) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{bird_id}.json"
    write_json_payload(path, payload)
    return path


def load_json_payload(path: Path) -> Dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"JSON 解析失败: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON 顶层结构必须为对象: {path}")
    return payload


def save_checkpoint(checkpoint_dir: Path, bird_id: str, payload: Dict) -> Path:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / f"{bird_id}.json"
    if path.exists():
        existing_payload = load_json_payload(path)
        payload["title_aliases"] = merge_title_aliases(
            existing_payload.get("title_aliases", []),
            [existing_payload.get("requested_title", ""), existing_payload.get("resolved_title", "")],
            payload.get("title_aliases", []),
            [payload.get("requested_title", ""), payload.get("resolved_title", "")],
        )
    write_json_payload(path, payload)
    return path


def load_checkpoints(checkpoint_dir: Path) -> List[Dict]:
    if not checkpoint_dir.exists():
        return []

    checkpoints: List[Dict] = []
    for path in sorted(checkpoint_dir.glob("*.json")):
        payload = load_json_payload(path)
        version = payload.get("version")
        if version not in (None, CHECKPOINT_VERSION):
            raise RuntimeError(f"不支持的 checkpoint 版本: {path}")
        payload["_checkpoint_path"] = str(path)
        checkpoints.append(payload)
    return checkpoints


def recover_rows_from_checkpoints(
    checkpoints: Sequence[Dict],
    birds_rows: List[Dict[str, str]],
    locations_rows: List[Dict[str, str]],
    relations_rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], bool]:
    checkpoint_birds: List[Dict[str, str]] = []
    checkpoint_locations: List[Dict[str, str]] = []
    checkpoint_relations: List[Dict[str, str]] = []

    for checkpoint in checkpoints:
        bird = checkpoint.get("bird")
        if isinstance(bird, dict) and bird.get("id"):
            checkpoint_birds.append(normalize_structured_row(bird, BIRDS_HEADERS))

        for location in checkpoint.get("locations", []):
            if isinstance(location, dict) and location.get("id"):
                checkpoint_locations.append(normalize_structured_row(location, LOCATIONS_HEADERS))

        for relation in checkpoint.get("relations", []):
            if isinstance(relation, dict) and relation.get("subject_id") and relation.get("object_id"):
                checkpoint_relations.append(normalize_structured_row(relation, RELATIONS_HEADERS))

    birds_rows, birds_changed = upsert_rows(birds_rows, checkpoint_birds, key_fields=["id"], overwrite=False)
    locations_rows, locations_changed = upsert_rows(locations_rows, checkpoint_locations, key_fields=["id"], overwrite=False)
    relations_rows, relations_changed = upsert_rows(
        relations_rows,
        checkpoint_relations,
        key_fields=["subject_id", "predicate", "object_id"],
        overwrite=False,
    )
    return birds_rows, locations_rows, relations_rows, birds_changed or locations_changed or relations_changed


def build_completed_title_keys(existing_birds: Sequence[Dict[str, str]], checkpoints: Sequence[Dict]) -> set[str]:
    completed = set()
    for row in existing_birds:
        english_name = row.get("english_name", "")
        if english_name:
            completed.add(normalize_title_key(english_name))

    for checkpoint in checkpoints:
        for title in merge_title_aliases(
            checkpoint.get("title_aliases", []),
            [checkpoint.get("requested_title", ""), checkpoint.get("resolved_title", "")],
            [checkpoint.get("bird", {}).get("english_name", "")] if isinstance(checkpoint.get("bird"), dict) else [],
        ):
            completed.add(normalize_title_key(title))
    return completed


def persist_tables(
    birds_path: Path,
    locations_path: Path,
    relations_path: Path,
    birds_rows: List[Dict[str, str]],
    locations_rows: List[Dict[str, str]],
    relations_rows: List[Dict[str, str]],
) -> None:
    write_csv_rows(birds_path, BIRDS_HEADERS, birds_rows)
    write_csv_rows(locations_path, LOCATIONS_HEADERS, locations_rows)
    write_csv_rows(relations_path, RELATIONS_HEADERS, relations_rows)


def maybe_build_json(build_json: bool) -> None:
    if not build_json:
        return
    if not BUILD_SCRIPT.exists():
        print("未找到 build_knowledge_json.py，跳过静态数据构建。", file=sys.stderr)
        return
    exit_code = __import__("subprocess").run([sys.executable, str(BUILD_SCRIPT)], check=False).returncode
    if exit_code != 0:
        raise RuntimeError("执行 build_knowledge_json.py 失败")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 Wikipedia 抓取鸟类页面并写入 data/*.csv")
    parser.add_argument("--titles", nargs="*", default=[], help="英文 Wikipedia 页面标题，可一次传多个")
    parser.add_argument("--input-file", help="可选，提供标题输入文件；支持 txt 每行一个标题，或 csv 的 title/page_title/english_name 列")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="CSV 数据目录，默认 data/")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="原始页面 JSON 输出目录，默认 data/wikipedia_raw/")
    parser.add_argument("--checkpoint-dir", default=str(DEFAULT_CHECKPOINT_DIR), help="断点 checkpoint 目录，默认 data/wikipedia_checkpoint/")
    parser.add_argument("--overwrite", action="store_true", help="强制重抓已完成标题，并用新抓取值覆盖同一 id 的非空字段")
    parser.add_argument("--build-json", action="store_true", help="抓取结束后自动执行 build_knowledge_json.py")
    parser.add_argument("--delay", type=float, default=0.3, help="请求间隔秒数，默认 0.3")
    parser.add_argument("--proxy", type=str, default="", help="HTTPS 代理地址，例如 http://127.0.0.1:7890")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    titles = load_titles(args)
    if not titles:
        raise SystemExit("请通过 --titles 或 --input-file 提供至少一个 Wikipedia 页面标题。")

    data_dir = Path(args.data_dir)
    raw_dir = Path(args.raw_dir)
    checkpoint_dir = Path(args.checkpoint_dir)
    birds_path = data_dir / "birds.csv"
    locations_path = data_dir / "locations.csv"
    relations_path = data_dir / "relations.csv"

    birds_rows = load_csv_rows(birds_path, BIRDS_HEADERS)
    locations_rows = load_csv_rows(locations_path, LOCATIONS_HEADERS)
    relations_rows = load_csv_rows(relations_path, RELATIONS_HEADERS)
    checkpoints = load_checkpoints(checkpoint_dir)
    birds_rows, locations_rows, relations_rows, restored_from_checkpoint = recover_rows_from_checkpoints(
        checkpoints,
        birds_rows,
        locations_rows,
        relations_rows,
    )
    if restored_from_checkpoint:
        persist_tables(birds_path, locations_path, relations_path, birds_rows, locations_rows, relations_rows)
        print("[resume] 已从 checkpoint 补齐本地 CSV 数据")

    completed_title_keys = build_completed_title_keys(birds_rows, checkpoints)

    crawler = WikiCrawler(delay=args.delay, proxy=args.proxy)
    crawled_count = 0
    skipped_count = 0

    for title in titles:
        title_key = normalize_title_key(title)
        if title_key in completed_title_keys and not args.overwrite:
            skipped_count += 1
            print(f"[skip] {title}")
            continue

        print(f"[crawl] {title}")
        try:
            bird_row, location_rows, relations, raw_payload = crawl_one_title(crawler, title)
            raw_path = save_raw_payload(raw_dir, bird_row["id"], raw_payload)
            checkpoint_payload = build_checkpoint_payload(title, bird_row, location_rows, relations, raw_path)
            save_checkpoint(checkpoint_dir, bird_row["id"], checkpoint_payload)

            birds_rows, birds_changed = upsert_rows(birds_rows, [bird_row], key_fields=["id"], overwrite=args.overwrite)
            locations_rows, locations_changed = upsert_rows(
                locations_rows,
                location_rows,
                key_fields=["id"],
                overwrite=args.overwrite,
            )
            relations_rows, relations_changed = upsert_rows(
                relations_rows,
                relations,
                key_fields=["subject_id", "predicate", "object_id"],
                overwrite=args.overwrite,
            )
            if birds_changed or locations_changed or relations_changed:
                persist_tables(birds_path, locations_path, relations_path, birds_rows, locations_rows, relations_rows)

            completed_title_keys.update(normalize_title_key(item) for item in merge_title_aliases([title, bird_row["english_name"]]))
            crawled_count += 1
        except Exception as exc:
            print(f"[error] {title}: {exc}", file=sys.stderr)
            continue

    print(f"本次新增抓取标题数: {crawled_count}")
    print(f"本次自动跳过标题数: {skipped_count}")
    print(f"checkpoint 文件数: {len(list(checkpoint_dir.glob('*.json'))) if checkpoint_dir.exists() else 0}")

    print(f"birds.csv 行数: {len(birds_rows)}")
    print(f"locations.csv 行数: {len(locations_rows)}")
    print(f"relations.csv 行数: {len(relations_rows)}")

    maybe_build_json(args.build_json)


if __name__ == "__main__":
    main()
