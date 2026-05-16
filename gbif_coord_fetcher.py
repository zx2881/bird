#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBIF Coordinate Fetcher - 优化版
从 GBIF 获取鸟类观测坐标并更新 knowledge.json

优化点:
1. 多层名称解析回退机制 (name_backbone -> name_suggest -> name_lookup)
2. 默认全球搜索，不限制国家
3. 数据质量过滤可配置
4. 细化日志：区分"名称解析失败"、"无坐标记录"、"成功获取"
5. 指数退避重试机制

依赖: pip install requests

使用说明:
    # 全球搜索，只填补空坐标
    python gbif_coord_fetcher.py --null-only
    
    # 限定国家搜索
    python gbif_coord_fetcher.py --null-only --country CN
    
    # 关闭不确定性过滤
    python gbif_coord_fetcher.py --null-only --min-uncertainty None
    
    # 详细日志
    python gbif_coord_fetcher.py --verbose
"""

import sys
import io
for stream in [sys.stdout, sys.stderr]:
    if hasattr(stream, 'buffer'):
        stream.flush()
        dup = io.TextIOWrapper(stream.buffer, encoding='utf-8', line_buffering=True)
        if stream is sys.stdout:
            sys.stdout = dup
        else:
            sys.stderr = dup

import argparse
import json
import logging
import os
import shutil
import time
from typing import Optional

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


GBIF_SPECIES_API = "https://api.gbif.org/v1/species"
GBIF_MATCH_API = "https://api.gbif.org/v1/species/match"
GBIF_SUGGEST_API = "https://api.gbif.org/v1/species/suggest"
GBIF_LOOKUP_API = "https://api.gbif.org/v1/species"
GBIF_OCCURRENCE_API = "https://api.gbif.org/v1/occurrence/search"


class GBIFCoordFetcher:
    """GBIF 坐标获取器 - 优化版"""
    
    def __init__(self, args):
        self.args = args
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GBIFCoordFetcher/1.0 (bird-project)'
        })
        self.stats = {
            'total': 0,
            'success': 0,
            'no_coords': 0,
            'name_failed': 0,
        }
    
    def _retry_request(self, func, *args, **kwargs):
        """带指数退避重试的请求"""
        max_retries = getattr(self.args, 'max_retries', 3)
        timeout = kwargs.pop('timeout', 20)
        
        for attempt in range(max_retries):
            try:
                return func(*args, timeout=timeout, **kwargs)
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}), {wait_time}s后退重试: {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise
    
    def _get_usage_key_via_match(self, name: str) -> Optional[int]:
        """通过 match API 获取 usageKey"""
        params = {'name': name}
        try:
            result = self._retry_request(
                self.session.get,
                GBIF_MATCH_API,
                params=params
            )
            data = result.json()
            
            if data.get('usageKey'):
                key = data.get('acceptedUsageKey') or data.get('usageKey')
                if key:
                    logger.debug(f"Match成功: {data.get('canonicalName')}, key={key}")
                    return key
        except Exception as e:
            logger.debug(f"Match API失败: {e}")
        return None
    
    def _get_usage_key_via_suggest(self, name: str) -> Optional[int]:
        """通过 suggest API 获取 usageKey"""
        params = {'q': name, 'limit': 5}
        try:
            result = self._retry_request(
                self.session.get,
                GBIF_SUGGEST_API,
                params=params
            )
            data = result.json()
            
            for item in data:
                if item.get('key'):
                    logger.debug(f"Suggest成功: {item.get('scientificName')}, key={item.get('key')}")
                    return item.get('key')
        except Exception as e:
            logger.debug(f"Suggest API失败: {e}")
        return None
    
    def _get_usage_key_via_lookup(self, name: str) -> Optional[int]:
        """通过 lookup API 获取 usageKey"""
        params = {'q': name, 'limit': 3}
        try:
            result = self._retry_request(
                self.session.get,
                GBIF_LOOKUP_API,
                params=params
            )
            data = result.json()
            
            for item in data.get('results', []):
                if item.get('usageKey'):
                    logger.debug(f"Lookup成功: {item.get('scientificName')}, key={item.get('usageKey')}")
                    return item.get('usageKey')
        except Exception as e:
            logger.debug(f"Lookup API失败: {e}")
        return None
    
    def get_usage_key(self, name: str) -> Optional[int]:
        """多层名称解析回退获取 usageKey"""
        # 优先级1: match API (精确/模糊匹配)
        key = self._get_usage_key_via_match(name)
        if key:
            return key
        
        # 优先级2: suggest API
        key = self._get_usage_key_via_suggest(name)
        if key:
            return key
        
        # 优先级3: lookup API
        key = self._get_usage_key_via_lookup(name)
        if key:
            return key
        
        return None
    
    def get_coordinates(self, usage_key: int, limit: int = 5) -> Optional[tuple]:
        """获取物种的观测坐标"""
        params = {
            'taxonKey': usage_key,
            'hasCoordinate': True,
            'limit': limit,
        }
        
        # 可选：添加国家限制
        if self.args.country:
            params['country'] = self.args.country
        
        try:
            result = self._retry_request(
                self.session.get,
                GBIF_OCCURRENCE_API,
                params=params
            )
            data = result.json()
            
            records = data.get('results', [])
            if not records:
                return None
            
            # 获取不确定性阈值
            min_uncertainty = getattr(self.args, 'min_uncertainty', None)
            
            for record in records:
                lat = record.get('decimalLatitude')
                lng = record.get('decimalLongitude')
                
                if lat is None or lng is None:
                    continue
                
                try:
                    lat = float(lat)
                    lng = float(lng)
                except (TypeError, ValueError):
                    continue
                
                # 坐标范围检查
                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    logger.debug(f"坐标超出范围: lat={lat}, lng={lng}")
                    continue
                
                # 不确定性过滤
                if min_uncertainty is not None:
                    uncertainty = record.get('coordinateUncertaintyInMeters')
                    if uncertainty is not None:
                        try:
                            if float(uncertainty) > min_uncertainty:
                                logger.debug(f"不确定性过高: {uncertainty}m > {min_uncertainty}m")
                                continue
                        except (TypeError, ValueError):
                            pass
                
                logger.debug(f"获取坐标: lat={lat}, lng={lng}")
                return (lat, lng)
                
        except Exception as e:
            logger.debug(f"获取坐标失败: {e}")
        
        return None
    
    def process_bird(self, bird: dict) -> tuple:
        """
        处理单个鸟类
        返回: (状态, lat, lng)
        状态: 'success' | 'no_coords' | 'name_failed'
        """
        name = bird.get('name', '')
        latin_name = bird.get('latinName', '')
        
        # 优先使用拉丁名
        if not latin_name:
            if name:
                query_name = name
            else:
                return ('name_failed', None, None)
        else:
            query_name = latin_name
        
        logger.info(f"查询: {query_name}")
        
        # 获取 usageKey
        usage_key = self.get_usage_key(query_name)
        
        # 如果拉丁名失败，尝试中文名
        if not usage_key and name and name != query_name:
            logger.debug(f"尝试中文名: {name}")
            usage_key = self.get_usage_key(name)
        
        if not usage_key:
            logger.warning(f"名称解析失败: {query_name}")
            return ('name_failed', None, None)
        
        # 获取坐标
        limit = getattr(self.args, 'limit', 5)
        coords = self.get_coordinates(usage_key, limit=limit)
        
        if coords:
            return ('success', coords[0], coords[1])
        
        logger.warning(f"无坐标记录: {query_name}")
        return ('no_coords', None, None)
    
    def load_birds(self, filepath: str) -> list:
        """加载鸟类数据（从 CSV 而非 knowledge.json）"""
        import csv as csv_module
        birds = []
        if not os.path.exists(filepath):
            logger.error(f"文件不存在: {filepath}")
            return birds

        is_csv = filepath.lower().endswith('.csv')
        if is_csv:
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv_module.DictReader(f)
                for row in reader:
                    lat_val = row.get('lat', '').strip()
                    lng_val = row.get('lng', '').strip()
                    birds.append({
                        'id': row.get('id', '').strip(),
                        'name': row.get('name', '').strip(),
                        'latin_name': row.get('latin_name', '').strip() or row.get('latinName', '').strip(),
                        'english_name': row.get('english_name', '').strip() or row.get('englishName', '').strip(),
                        'lat': float(lat_val) if lat_val else None,
                        'lng': float(lng_val) if lng_val else None,
                    })
        else:
            # 兼容旧的 knowledge.json 模式
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nodes = data.get('nodes', [])
            for n in nodes:
                if n.get('type') == 'bird':
                    birds.append({
                        'id': n.get('id', ''),
                        'name': n.get('name', ''),
                        'latin_name': n.get('latinName', ''),
                        'english_name': n.get('englishName', ''),
                        'lat': n.get('lat'),
                        'lng': n.get('lng'),
                    })

        logger.info(f"加载 {len(birds)} 个鸟类节点")

        if self.args.null_only:
            birds_to_process = [b for b in birds if b.get('lat') is None or b.get('lng') is None]
            logger.info(f"需要更新坐标: {len(birds_to_process)} 个")
        else:
            birds_to_process = birds

        return birds_to_process
    
    def save_birds(self, filepath: str, all_birds: list, updated_birds: list):
        """保存鸟类坐标到 CSV（或在 knowledge.json 模式下更新 JSON）"""
        if not updated_birds:
            return

        is_csv = filepath.lower().endswith('.csv')
        if is_csv:
            self._save_to_csv(filepath, updated_birds)
        else:
            self._save_to_json(filepath, all_birds, updated_birds)

    def _save_to_csv(self, filepath: str, updated_birds: list):
        import csv as csv_module
        if not self.args.no_backup:
            backup_path = filepath + '.bak'
            shutil.copy(filepath, backup_path)
            logger.info(f"备份到: {backup_path}")

        updated_map = {b['id']: (b['lat'], b['lng']) for b in updated_birds if b['lat'] is not None}

        with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv_module.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        for row in rows:
            bid = row.get('id', '').strip()
            if bid in updated_map:
                lat, lng = updated_map[bid]
                row['lat'] = str(lat)
                row['lng'] = str(lng)

        temp_path = filepath + '.tmp'
        with open(temp_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv_module.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        shutil.move(temp_path, filepath)
        logger.info(f"已保存到: {filepath}")

    def _save_to_json(self, filepath: str, all_birds: list, updated_birds: list):
        updated_map = {b['id']: (b['lat'], b['lng']) for b in updated_birds if b['lat'] is not None}
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for node in data.get('nodes', []):
            if node.get('id') in updated_map:
                lat, lng = updated_map[node['id']]
                node['lat'] = lat
                node['lng'] = lng

        if not self.args.no_backup:
            backup_path = filepath + '.bak'
            shutil.copy(filepath, backup_path)
            logger.info(f"备份到: {backup_path}")

        temp_path = filepath + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(temp_path, filepath)
        logger.info(f"已保存到: {filepath}")
    
    def run(self):
        """运行主流程"""
        input_file = self.args.input

        if not os.path.exists(input_file):
            logger.error(f"文件不存在: {input_file}")
            return 1

        birds = self.load_birds(input_file)
        self.stats['total'] = len(birds)
        updated_birds = []
        all_birds = birds  # 保留引用用于 JSON 模式

        for i, bird in enumerate(birds, 1):
            name = bird.get('name', bird.get('id', ''))

            logger.info(f"[{i}/{len(birds)}] 处理: {name}")

            status, lat, lng = self.process_bird(bird)

            if status == 'success':
                bird['lat'] = lat
                bird['lng'] = lng
                updated_birds.append(bird)
                self.stats['success'] += 1
                logger.info(f"  -> 坐标: {lat}, {lng}")
            elif status == 'no_coords':
                self.stats['no_coords'] += 1
                logger.info(f"  -> 无坐标记录")
            else:
                self.stats['name_failed'] += 1
                logger.info(f"  -> 名称解析失败")

            time.sleep(1)

        self.save_birds(input_file, all_birds, updated_birds)

        logger.info(f"完成: 成功 {self.stats['success']}/{self.stats['total']}, "
                   f"无坐标 {self.stats['no_coords']}, "
                   f"名称失败 {self.stats['name_failed']}")

        return 0


def main():
    parser = argparse.ArgumentParser(
        description='从 GBIF 获取鸟类坐标',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python gbif_coord_fetcher.py --null-only
  python gbif_coord_fetcher.py --null-only --country CN
  python gbif_coord_fetcher.py --null-only --min-uncertainty None --verbose
        """
    )
    parser.add_argument(
        '-i', '--input',
        default='data/birds.csv',
        help='输入文件路径 (默认: data/birds.csv，也支持 public/knowledge.json)'
    )
    parser.add_argument(
        '--null-only',
        action='store_true',
        help='只处理 lat/lng 为空的鸟类'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=5,
        help='每个物种最多获取的观测记录数 (默认: 5)'
    )
    parser.add_argument(
        '--country',
        type=str,
        default=None,
        help='限制查询国家代码 (如 CN, US)，不指定则为全球'
    )
    parser.add_argument(
        '--min-uncertainty',
        type=int,
        default=10000,
        help='最大坐标不确定性(米)，None表示不过滤 (默认: 10000)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='单次请求最大重试次数 (默认: 3)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不创建备份文件'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='打印详细日志'
    )
    
    args = parser.parse_args()
    
    # 处理 min-uncertainty 的 None 值
    if args.min_uncertainty is not None:
        try:
            args.min_uncertainty = int(args.min_uncertainty)
        except ValueError:
            args.min_uncertainty = None
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    fetcher = GBIFCoordFetcher(args)
    return fetcher.run()


if __name__ == '__main__':
    sys.exit(main())