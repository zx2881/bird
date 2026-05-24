"""
将 data/ 目录中的展示文本统一为简体中文。

默认处理范围:
  - data/birds.csv: name, summary
  - data/locations.csv: name, summary
  - data/relations.csv: subject, object, object_summary

脚本特点:
  - 只处理展示字段，不修改 id / english_name / latin_name 等源字段
  - 先扫描疑似英文或繁体文本，再调用可配置的 OpenAI 兼容接口翻译
  - 提供缓存、备份、--scan-only 和 --dry-run，降低误改风险
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_CACHE_PATH = DEFAULT_DATA_DIR / ".simplified_translation_cache.json"
DEFAULT_FILES = ("birds.csv", "locations.csv", "relations.csv")
STATUS_CODES = {"EX", "EW", "CR", "EN", "VU", "NT", "LC", "DD", "NE"}
ALLOWED_EMBEDDED_ASCII_TOKENS = STATUS_CODES | {"IUCN", "GBIF", "API", "CSV", "JSON", "KM", "M"}

ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CODE_FENCE_RE = re.compile(r"^```(?:\w+)?\s*|\s*```$", re.DOTALL)

# 这里只做“是否疑似繁体”的粗筛，不追求 100% 语言学完备。
TRADITIONAL_HINT_CHARS = set(
    "臺灣濕棲護與為於區國龍澤關體觀遷瀕錄點魚鳥龜縣鄉層網線綠總臺邊際廣門開閉"
    "濱溝溼號種壩樹園廠蘆蘭灣務場習劃顏類靜聯聲學書會處裡圍後徑從樣機檔"
)
TRADITIONAL_HINT_TERMS = (
    "臺灣",
    "濕地",
    "溼地",
    "棲地",
    "瀕危",
    "遷徙",
    "保護區",
    "國家公園",
    "觀察站",
    "關聯",
    "記錄點",
)

SYSTEM_PROMPT = """你是鸟类知识图谱的数据清洗助手。
你的唯一任务，是把输入文本整理成可直接写回 CSV 的简体中文。

规则:
1. 只输出最终文本，不要解释，不要加引号，不要加项目符号。
2. name 字段只输出稳定、自然、常用的简体中文名称。
3. summary 字段只输出忠实原意的简体中文摘要，不要扩写，不要编造新事实。
4. 保留学名、IUCN、数字、年份、单位、专有缩写和必要的英文代码。
5. 如果输入已经是简体中文，只做繁体转简体和轻微顺句，不要随意改写。
6. 如果输入是状态代码，如 VU、EN、CR、LC、NT、DD、NE、EW、EX，保持原样。
"""


@dataclass
class ColumnRule:
    column: str
    field_kind: str
    scope_resolver: Callable[[Dict[str, str]], str]
    skip_predicate: Optional[Callable[[Dict[str, str], str], bool]] = None


@dataclass
class Dataset:
    path: Path
    fieldnames: List[str]
    rows: List[Dict[str, str]]
    rules: List[ColumnRule]


@dataclass
class CellTask:
    dataset_index: int
    row_index: int
    csv_line: int
    column: str
    field_kind: str
    scope: str
    original_text: str
    normalized_text: str
    record_label: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将 data 目录中的 name / summary 展示文本统一为简体中文。"
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="CSV 数据目录，默认 data/")
    parser.add_argument(
        "--files",
        nargs="+",
        default=list(DEFAULT_FILES),
        help="要处理的 CSV 文件名，默认 birds.csv locations.csv relations.csv",
    )
    parser.add_argument("--cache-path", type=Path, default=DEFAULT_CACHE_PATH, help="翻译缓存 JSON 路径")
    parser.add_argument("--scan-only", action="store_true", help="只扫描疑似需要转换的内容，不调用翻译接口")
    parser.add_argument("--dry-run", action="store_true", help="执行翻译但不写回文件")
    parser.add_argument("--translate-cjk-all", action="store_true", help="将所有目标中文字段都送入翻译后端统一成简体")
    parser.add_argument("--refresh-cache", action="store_true", help="忽略已有缓存，强制重新翻译")
    parser.add_argument("--no-backup", action="store_true", help="写回前不创建备份目录")
    parser.add_argument("--encoding", default="utf-8-sig", help="CSV 编码，默认 utf-8-sig")
    parser.add_argument("--timeout", type=int, default=90, help="单次接口请求超时秒数，默认 90")
    parser.add_argument("--max-retries", type=int, default=3, help="接口失败重试次数，默认 3")
    parser.add_argument("--sleep", type=float, default=0.2, help="两次请求之间的间隔秒数，默认 0.2")
    parser.add_argument("--api-base", default=os.getenv("TEXT_NORMALIZER_API_BASE") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1")
    parser.add_argument("--api-key", default=os.getenv("TEXT_NORMALIZER_API_KEY") or os.getenv("OPENAI_API_KEY") or "")
    parser.add_argument("--model", default=os.getenv("TEXT_NORMALIZER_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini")
    return parser


def relation_object_scope(row: Dict[str, str]) -> str:
    object_type = (row.get("object_type") or "").strip()
    mapping = {
        "Bird": "bird_name",
        "Location": "location_name",
        "Habitat": "habitat_name",
        "Threat": "threat_name",
        "Taxon": "taxonomy_name",
        "Status": "status_name",
    }
    return mapping.get(object_type, "generic_name")


def relation_object_summary_scope(row: Dict[str, str]) -> str:
    object_type = (row.get("object_type") or "").strip().lower() or "generic"
    return f"{object_type}_summary"


def skip_relation_object(row: Dict[str, str], value: str) -> bool:
    if (row.get("object_type") or "").strip() != "Status":
        return False
    return value.strip().upper() in STATUS_CODES


def build_rules() -> Dict[str, List[ColumnRule]]:
    return {
        "birds.csv": [
            ColumnRule("name", "name", lambda _: "bird_name"),
            ColumnRule("summary", "summary", lambda _: "bird_summary"),
        ],
        "locations.csv": [
            ColumnRule("name", "name", lambda _: "location_name"),
            ColumnRule("summary", "summary", lambda _: "location_summary"),
        ],
        "relations.csv": [
            ColumnRule("subject", "name", lambda _: "bird_name"),
            ColumnRule("object", "name", relation_object_scope, skip_predicate=skip_relation_object),
            ColumnRule("object_summary", "summary", relation_object_summary_scope),
        ],
    }


def read_csv(path: Path, encoding: str) -> Dataset:
    rules = build_rules().get(path.name)
    if rules is None:
        raise ValueError(f"未配置 {path.name} 的处理规则。")

    with path.open("r", encoding=encoding, newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or [])
        rows = [{key: value or "" for key, value in row.items()} for row in reader]

    return Dataset(path=path, fieldnames=fieldnames, rows=rows, rules=rules)


def write_csv(dataset: Dataset, encoding: str) -> None:
    with dataset.path.open("w", encoding=encoding, newline="") as file:
        writer = csv.DictWriter(file, fieldnames=dataset.fieldnames)
        writer.writeheader()
        writer.writerows(dataset.rows)


def load_cache(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"缓存文件格式错误: {path}")
    return {str(scope): {str(k): str(v) for k, v in values.items()} for scope, values in data.items() if isinstance(values, dict)}


def save_cache(path: Path, cache: Dict[str, Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2, sort_keys=True)


def normalize_source_text(text: str) -> str:
    normalized = (text or "").replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def strip_code_fence(text: str) -> str:
    return CODE_FENCE_RE.sub("", text.strip()).strip()


def cleanup_model_output(text: str, field_kind: str) -> str:
    cleaned = strip_code_fence(text)
    cleaned = re.sub(r"^(译文|翻译结果|结果)\s*[:：]\s*", "", cleaned)
    cleaned = cleaned.strip().strip("\"'“”‘’")
    cleaned = normalize_source_text(cleaned)
    if field_kind == "name":
        cleaned = cleaned.replace("\n", " ").strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned


def contains_traditional_hints(text: str) -> bool:
    if any(term in text for term in TRADITIONAL_HINT_TERMS):
        return True
    return any(char in TRADITIONAL_HINT_CHARS for char in text)


def meaningful_ascii_tokens(text: str) -> List[str]:
    tokens = ASCII_TOKEN_RE.findall(text)
    return [token for token in tokens if token.upper() not in ALLOWED_EMBEDDED_ASCII_TOKENS]


def needs_translation(text: str, *, translate_cjk_all: bool) -> bool:
    normalized = normalize_source_text(text)
    if not normalized:
        return False

    if translate_cjk_all and CJK_RE.search(normalized):
        return True

    if contains_traditional_hints(normalized):
        return True

    if meaningful_ascii_tokens(normalized):
        return True

    return False


def build_record_label(dataset_name: str, row: Dict[str, str], csv_line: int) -> str:
    for key in ("id", "subject_id", "object_id", "name", "subject", "object"):
        value = (row.get(key) or "").strip()
        if value:
            return f"{dataset_name}:{key}={value}"
    return f"{dataset_name}:line={csv_line}"


def collect_tasks(datasets: List[Dataset], translate_cjk_all: bool) -> List[CellTask]:
    tasks: List[CellTask] = []

    for dataset_index, dataset in enumerate(datasets):
        available_columns = set(dataset.fieldnames)
        for rule in dataset.rules:
            if rule.column not in available_columns:
                print(f"[warn] {dataset.path.name} 缺少列 {rule.column}，已跳过该列。", file=sys.stderr)

        for row_index, row in enumerate(dataset.rows):
            csv_line = row_index + 2
            record_label = build_record_label(dataset.path.name, row, csv_line)
            for rule in dataset.rules:
                if rule.column not in row:
                    continue
                normalized = normalize_source_text(row[rule.column])
                if not normalized:
                    continue
                if rule.skip_predicate and rule.skip_predicate(row, normalized):
                    continue
                if not needs_translation(normalized, translate_cjk_all=translate_cjk_all):
                    continue

                tasks.append(
                    CellTask(
                        dataset_index=dataset_index,
                        row_index=row_index,
                        csv_line=csv_line,
                        column=rule.column,
                        field_kind=rule.field_kind,
                        scope=rule.scope_resolver(row),
                        original_text=row[rule.column],
                        normalized_text=normalized,
                        record_label=record_label,
                    )
                )

    return tasks


def print_scan_summary(tasks: List[CellTask], datasets: List[Dataset]) -> None:
    print(f"扫描完成：共发现 {len(tasks)} 个疑似需要转换的单元格。")
    if not tasks:
        return

    counts: Dict[str, int] = {}
    samples: Dict[str, List[str]] = {}
    for task in tasks:
        dataset_name = datasets[task.dataset_index].path.name
        key = f"{dataset_name}:{task.column}"
        counts[key] = counts.get(key, 0) + 1
        if len(samples.setdefault(key, [])) < 3:
            samples[key].append(task.normalized_text)

    print()
    for key in sorted(counts):
        print(f"- {key}: {counts[key]}")
        for sample in samples.get(key, []):
            preview = sample if len(sample) <= 80 else f"{sample[:77]}..."
            print(f"  示例: {preview}")


def make_backup_dir(data_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / "_backup_before_simplify" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_datasets(datasets: List[Dataset], backup_dir: Path) -> None:
    for dataset in datasets:
        shutil.copy2(dataset.path, backup_dir / dataset.path.name)


def ensure_api_ready(tasks: List[CellTask], args: argparse.Namespace) -> None:
    if not tasks:
        return
    if args.scan_only:
        return
    if not args.api_base:
        raise ValueError("未提供 --api-base，也没有 TEXT_NORMALIZER_API_BASE / OPENAI_BASE_URL 环境变量。")
    if not args.model:
        raise ValueError("未提供 --model，也没有 TEXT_NORMALIZER_MODEL / OPENAI_MODEL 环境变量。")


def resolve_endpoint(api_base: str) -> str:
    normalized = api_base.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def extract_message_content(payload: Dict) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("接口响应缺少 choices。")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


def translate_text(
    session: requests.Session,
    endpoint: str,
    api_key: str,
    model: str,
    task: CellTask,
    timeout: int,
    max_retries: int,
) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    user_prompt = (
        f"字段类型: {task.field_kind}\n"
        f"语义范围: {task.scope}\n"
        f"记录: {task.record_label}\n"
        f"CSV 行号: {task.csv_line}\n"
        "请将下面文本统一为简体中文，并严格只输出最终文本：\n"
        f"{task.normalized_text}"
    )

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 300 if task.field_kind == "name" else 700,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = session.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            content = extract_message_content(data)
            translated = cleanup_model_output(content, task.field_kind)
            if not translated:
                raise ValueError("模型返回了空字符串。")
            return translated
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt == max_retries:
                break
            time.sleep(min(2 * attempt, 8))

    raise RuntimeError(
        f"翻译失败: {task.record_label} / {task.column} / 原文={task.normalized_text!r} / 错误={last_error}"
    )


def apply_translations(
    datasets: List[Dataset],
    tasks: List[CellTask],
    cache: Dict[str, Dict[str, str]],
    args: argparse.Namespace,
) -> Dict[str, int]:
    endpoint = resolve_endpoint(args.api_base)
    session = requests.Session()

    changed_cells = 0
    translated_via_api = 0
    used_cache = 0
    per_file_changes: Dict[str, int] = {}

    for index, task in enumerate(tasks, start=1):
        scope_cache = cache.setdefault(task.scope, {})
        if args.refresh_cache:
            cached_translation = None
        else:
            cached_translation = scope_cache.get(task.normalized_text)

        if cached_translation is not None:
            translated = cached_translation
            used_cache += 1
        else:
            translated = translate_text(
                session=session,
                endpoint=endpoint,
                api_key=args.api_key,
                model=args.model,
                task=task,
                timeout=args.timeout,
                max_retries=args.max_retries,
            )
            scope_cache[task.normalized_text] = translated
            translated_via_api += 1
            time.sleep(max(args.sleep, 0))

        dataset = datasets[task.dataset_index]
        old_value = dataset.rows[task.row_index][task.column]
        if translated != old_value:
            dataset.rows[task.row_index][task.column] = translated
            changed_cells += 1
            per_file_changes[dataset.path.name] = per_file_changes.get(dataset.path.name, 0) + 1

        if index % 25 == 0 or index == len(tasks):
            print(
                f"[progress] {index}/{len(tasks)} 已处理，"
                f"API 新翻译 {translated_via_api}，缓存命中 {used_cache}，已变更 {changed_cells}。"
            )

    return {
        "changed_cells": changed_cells,
        "translated_via_api": translated_via_api,
        "used_cache": used_cache,
        **{f"file::{name}": count for name, count in per_file_changes.items()},
    }


def gather_existing_files(data_dir: Path, file_names: Iterable[str]) -> List[Dataset]:
    datasets = []
    for file_name in file_names:
        path = data_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"找不到文件: {path}")
        datasets.append(read_csv(path, encoding=args.encoding))
    return datasets


def print_result_summary(result: Dict[str, int], dry_run: bool) -> None:
    print()
    print("处理完成。")
    print(f"- 变更单元格: {result.get('changed_cells', 0)}")
    print(f"- API 新翻译: {result.get('translated_via_api', 0)}")
    print(f"- 缓存命中: {result.get('used_cache', 0)}")
    for key in sorted(result):
        if key.startswith("file::"):
            print(f"- {key.removeprefix('file::')}: {result[key]} 处变更")
    if dry_run:
        print("- 当前为 dry-run，文件未写回。")


def main(args: argparse.Namespace) -> int:
    datasets = gather_existing_files(args.data_dir, args.files)
    tasks = collect_tasks(datasets, translate_cjk_all=args.translate_cjk_all)

    print_scan_summary(tasks, datasets)
    if args.scan_only:
        return 0

    ensure_api_ready(tasks, args)
    cache = load_cache(args.cache_path)
    result = apply_translations(datasets, tasks, cache, args)

    if not args.dry_run and result.get("changed_cells", 0) > 0:
        if not args.no_backup:
            backup_dir = make_backup_dir(args.data_dir)
            backup_datasets(datasets, backup_dir)
            print(f"已创建备份目录: {backup_dir}")
        for dataset in datasets:
            write_csv(dataset, args.encoding)
    save_cache(args.cache_path, cache)
    print_result_summary(result, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    args = build_parser().parse_args()
    try:
        raise SystemExit(main(args))
    except Exception as error:  # noqa: BLE001
        print(f"[error] {error}", file=sys.stderr)
        raise SystemExit(1)
