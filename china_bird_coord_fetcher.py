#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China Bird Coordinate Fetcher
从"中国观鸟记录中心"获取鸟类坐标

功能:
- 读取 public/knowledge.json 中的鸟类信息  
- 从 birdreport.cn API 获取观测坐标 (需要有效Token)
- 自动更新 knowledge.json 中的 lat/lng 字段

依赖:
    pip install requests pycryptodomex

使用说明:
    # 1. 先从浏览器获取Token:
    #    - 登录 https://www.birdreport.cn
    #    - F12 打开开发者工具
    #    - Network -> 点击任意请求 -> 复制 X-Auth-Token

    # 2. 运行脚本:
    python china_bird_coord_fetcher.py --token YOUR_TOKEN
    
    # 模拟运行 (不写入文件)
    python china_bird_coord_fetcher.py --token YOUR_TOKEN --dry-run
    
    # 查询单个物种
    python china_bird_coord_fetcher.py --token YOUR_TOKEN --single "朱鹮"
    
    # 限制处理数量用于测试
    python china_bird_coord_fetcher.py --token YOUR_TOKEN --limit 5 --debug

API说明:
- birdreport.cn API 需要签名验证 (RSA/AES加密 + MD5签名)
- 必须提供有效的X-Auth-Token才能正常访问
- 批量请求请设置 --delay 避免被限流 (建议1-2秒)

注意:
- 该网站API有严格签名验证，简单爬取无法获取数据
- 如果无法获取Token，可以考虑手动添加坐标或使用其他数据源
"""

import sys
import io
import os

for stream in [sys.stdout, sys.stderr]:
    if hasattr(stream, 'buffer'):
        stream.flush()
        old = getattr(stream, 'reconfigure', None)
        if old:
            old(encoding='utf-8')
        else:
            import io
            dup = io.TextIOWrapper(stream.buffer, encoding='utf-8', line_buffering=True)
            if stream is sys.stdout:
                sys.stdout = dup
            else:
                sys.stderr = dup

import argparse
import base64
import json
import time
import uuid
import hashlib
import re
from typing import Optional, List, Dict, Any

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

try:
    from Cryptodome.Cipher import AES, PKCS1_v1_5
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Util import Padding
    CRYPTO_AVAILABLE = True
except ImportError:
    print("提示: pip install pycryptodomex 以支持更多功能")
    CRYPTO_AVAILABLE = False


API_BASE = "https://api.birdreport.cn"
WEB_BASE = "https://www.birdreport.cn"

AES_KEY = b"3583ec0257e2f4c8195eec7410ff1619"
AES_IV = b"d93c0d5ec6352f20"

RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCvxXa98E1uWXnBzXkS2yHUfnBM
6n3PCwLdfIox03T91joBvjtoDqiQ5x3tTOfpHs3LtiqMMEafls6b0YWtgB1dse1W5
m+FpeusVkCOkQxB4SZDH6tuerIknnmB/Hsq5wgEkIvO5Pff9biig6AyoAkdWpS
ek/1/B7zYIepYY0lxKQIDAQAB
-----END PUBLIC KEY-----"""


class BirdInfo:
    """鸟类信息"""
    def __init__(self, id: str, name: str, english_name: str = "", 
                 latin_name: str = "", lat: float = None, lng: float = None):
        self.id = id
        self.name = name
        self.english_name = english_name
        self.latin_name = latin_name
        self.lat = lat
        self.lng = lng


class BirdReportAPI:
    """中国观鸟记录中心 API 客户端"""
    
    def __init__(self, token: str = None, debug: bool = False):
        self.session = requests.Session()
        self.token = token
        self.debug = debug
        
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": WEB_BASE,
            "Referer": WEB_BASE + "/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        })
        
        if token:
            self.session.headers["X-Auth-Token"] = token
    
    def _rsa_encrypt(self, data: str) -> str:
        """RSA公钥加密"""
        if not CRYPTO_AVAILABLE:
            return ""
        try:
            key = RSA.import_key(RSA_PUBLIC_KEY)
            cipher = PKCS1_v1_5.new(key)
            return base64.b64encode(cipher.encrypt(data.encode())).decode()
        except Exception:
            return ""
    
    def _aes_encrypt(self, data: str) -> str:
        """AES加密"""
        if not CRYPTO_AVAILABLE:
            return data
        try:
            padded = Padding.pad(data.encode(), AES.block_size)
            cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
            return base64.b64encode(cipher.encrypt(padded)).decode()
        except Exception:
            return data
    
    def _aes_decrypt(self, data: str) -> str:
        """AES解密"""
        if not CRYPTO_AVAILABLE:
            return data
        try:
            encrypted = base64.b64decode(data)
            cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
            decrypted = cipher.decrypt(encrypted)
            return Padding.unpad(decrypted, AES.block_size).decode()
        except Exception as e:
            if self.debug:
                print("[DEBUG] AES解密失败:", e)
            return ""
    
    def _make_signature(self, params: dict) -> tuple:
        """生成签名参数"""
        ts = str(int(time.time() * 1000))
        req_id = str(uuid.uuid4())
        
        param_str = json.dumps(params, separators=(",", ":"), ensure_ascii=False)
        sign = hashlib.md5((param_str + req_id + ts).encode()).hexdigest()
        
        return param_str, req_id, ts, sign
    
    def search_species(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索物种"""
        results = []
        
        params = {"keyword": keyword, "page": 1, "limit": 20, "type": 1}
        
        param_str, req_id, ts, sign = self._make_signature(params)
        
        # 加密参数
        encrypted = self._rsa_encrypt(param_str)
        if not encrypted:
            encrypted = self._aes_encrypt(param_str)
        
        data = {"data": encrypted, "uuid": req_id, "ts": ts, "sign": sign}
        
        headers = dict(self.session.headers)
        headers.update({"timestamp": ts, "requestId": req_id, "sign": sign})
        
        try:
            resp = self.session.post(
                f"{API_BASE}/front/taxon/search",
                headers=headers,
                data=data,
                timeout=20
            )
            
            if self.debug:
                print("[DEBUG] Search status:", resp.status_code)
            
            result = resp.json()
            
            if result.get("success") and result.get("data"):
                decrypted = self._aes_decrypt(result["data"])
                if decrypted:
                    data_list = json.loads(decrypted)
                    for item in data_list:
                        results.append({
                            "taxonid": item.get("taxonid", 0),
                            "name": item.get("name", ""),
                            "latinName": item.get("latinName", ""),
                            "lat": item.get("lat", 0.0),
                            "lng": item.get("lng", 0.0),
                        })
            else:
                if self.debug:
                    print("[DEBUG] Error:", result.get("msg"), result.get("errorCode"))
                    
        except requests.RequestException as e:
            print("[ERROR] 请求失败:", e)
        
        return results
    
    def get_observations(self, taxon_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """获取物种观测记录"""
        results = []
        
        params = {
            "taxonid": taxon_id,
            "page": 1,
            "limit": limit,
            "state": 2,
            "mode": 0,
            "outside_type": 0,
        }
        
        param_str, req_id, ts, sign = self._make_signature(params)
        
        encrypted = self._rsa_encrypt(param_str)
        if not encrypted:
            encrypted = self._aes_encrypt(param_str)
        
        data = {"data": encrypted, "uuid": req_id, "ts": ts, "sign": sign}
        
        headers = dict(self.session.headers)
        headers.update({"timestamp": ts, "requestId": req_id, "sign": sign})
        
        try:
            resp = self.session.post(
                f"{API_BASE}/front/record/taxon/search",
                headers=headers,
                data=data,
                timeout=20
            )
            
            result = resp.json()
            
            if result.get("success") and result.get("data"):
                decrypted = self._aes_decrypt(result["data"])
                if decrypted:
                    data_list = json.loads(decrypted)
                    for item in data_list:
                        results.append({
                            "lat": item.get("lat", 0.0),
                            "lng": item.get("lng", 0.0),
                            "province": item.get("province", ""),
                            "city": item.get("city", ""),
                            "pointname": item.get("pointname", ""),
                        })
                        
        except requests.RequestException:
            pass
        
        return results


def load_knowledge_json(filepath: str) -> tuple:
    """加载knowledge.json"""
    birds = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    nodes = data.get("nodes", [])
    for node in nodes:
        if node.get("type") == "bird":
            bird = BirdInfo(
                id=node.get("id", ""),
                name=node.get("name", ""),
                english_name=node.get("englishName", ""),
                latin_name=node.get("latinName", ""),
                lat=node.get("lat"),
                lng=node.get("lng"),
            )
            birds.append(bird)
    
    return birds, data


def fetch_coords(api: BirdReportAPI, bird: BirdInfo, debug: bool = False) -> tuple:
    """获取鸟类坐标"""
    
    # 首先用中文名搜索
    sp_results = api.search_species(bird.name)
    
    # 如果没找到，尝试用拉丁名
    if not sp_results and bird.latin_name:
        sp_results = api.search_species(bird.latin_name)
    
    if not sp_results:
        return None, None
    
    # 提取坐标
    for sp in sp_results:
        lat = sp.get("lat", 0.0)
        lng = sp.get("lng", 0.0)
        
        if lat and lng:
            return lat, lng
        
        # 从观测记录获取
        taxon_id = sp.get("taxonid", 0)
        if taxon_id:
            obs_list = api.get_observations(taxon_id)
            for obs in obs_list:
                lat = obs.get("lat", 0.0)
                lng = obs.get("lng", 0.0)
                if lat and lng:
                    return lat, lng
    
    return None, None


def main():
    parser = argparse.ArgumentParser(
        description="从中国观鸟记录中心获取鸟类坐标",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", default="public/knowledge.json",
                      help="输入文件路径")
    parser.add_argument("-o", "--output", 
                      help="输出文件路径 (默认覆盖原文件)")
    parser.add_argument("-t", "--token", required=True,
                      help="API认证Token (必需)")
    parser.add_argument("-s", "--single", 
                      help="只查询单个物种")
    parser.add_argument("-l", "--limit", type=int, default=0,
                      help="限制处理数量")
    parser.add_argument("--dry-run", action="store_true",
                      help="模拟运行，不写入文件")
    parser.add_argument("--debug", action="store_true",
                      help="显示调试信息")
    parser.add_argument("-d", "--delay", type=float, default=1.5,
                      help="请求间隔秒数")
    
    args = parser.parse_args()
    
    # 文件路径
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"[ERROR] 文件不存在: {input_path}")
        sys.exit(1)
    
    output_path = args.output or input_path
    debug = args.debug
    
    # 加载数据
    print(f"[INFO] 加载文件: {input_path}")
    birds, original_data = load_knowledge_json(input_path)
    print(f"[INFO] 找到 {len(birds)} 个鸟类节点")
    
    # 需要更新的
    need_update = [b for b in birds if b.lat is None or b.lng is None]
    print(f"[INFO] 需要更新坐标: {len(need_update)} 个")
    
    # 处理列表
    if args.single:
        matching = [b for b in birds if b.name == args.single]
        if not matching:
            print(f"[ERROR] 未找到物种: {args.single}")
            sys.exit(1)
        birds_to_process = matching
    else:
        birds_to_process = need_update
    
    if args.limit > 0:
        birds_to_process = birds_to_process[:args.limit]
        print(f"[INFO] 限制处理: {args.limit}")
    
    # API
    api = BirdReportAPI(token=args.token, debug=debug)
    
    # 处理
    updated = 0
    for i, bird in enumerate(birds_to_process, 1):
        print(f"[{i}/{len(birds_to_process)}] 处理: {bird.name}")
        
        lat, lng = fetch_coords(api, bird, debug=debug)
        
        if lat and lng:
            bird.lat = lat
            bird.lng = lng
            updated += 1
            print(f"  -> 坐标: {lat}, {lng}")
        else:
            print(f"  -> 未找到坐标")
        
        time.sleep(args.delay)
    
    print(f"\n[INFO] 成功更新 {updated}/{len(birds_to_process)}")
    
    # 保存
    if not args.dry_run and updated > 0:
        for bird in birds:
            for node in original_data.get("nodes", []):
                if node.get("id") == bird.id:
                    node["lat"] = bird.lat
                    node["lng"] = bird.lng
                    break
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 已保存到: {output_path}")
    else:
        print("[INFO] 模拟运行，未写入文件")


if __name__ == "__main__":
    main()