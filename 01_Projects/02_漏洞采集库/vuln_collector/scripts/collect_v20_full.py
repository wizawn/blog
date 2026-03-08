#!/usr/bin/env python3
"""
V20 漏洞库全量采集脚本
目标：175,891 CVE
数据源：
1. NVD NIST (官方 CVE 数据库)
2. GitHub Advisory Database
3. CISA KEV (已完成 1,529 条)
4. Exploit-DB
5. Packet Storm Security
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace/vuln_collector"
NVD_API_KEY = ""  # 可选，提高限流

def fetch_nvd_cve(start_date, end_date):
    """从 NVD NIST 获取 CVE 数据"""
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        'pubStartDate': start_date,
        'pubEndDate': end_date,
        'resultsPerPage': 2000
    }
    if NVD_API_KEY:
        params['apiKey'] = NVD_API_KEY
    
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get('vulnerabilities', [])
    except Exception as e:
        print(f"❌ NVD 错误：{e}")
        return []

def fetch_github_advisories():
    """从 GitHub Advisory Database 获取"""
    url = "https://api.github.com/advisories"
    headers = {'Accept': 'application/vnd.github+json'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"❌ GitHub 错误：{e}")
    return []

def main():
    print(f"🚀 V20 漏洞库全量采集开始: {datetime.now()}")
    
    cve_database = {}
    
    # 1. 加载已有数据
    existing_index = Path(f"{WORKSPACE}/cve_index.json")
    if existing_index.exists():
        with open(existing_index) as f:
            cve_database = json.load(f)
        print(f"📂 已加载现有数据：{len(cve_database)} 条")
    
    # 2. 从 NVD 获取最近一年的 CVE
    print("📥 获取 NVD 数据...")
    now = datetime.now()
    for year in range(2015, now.year + 1):
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31) if year < now.year else now
        
        cves = fetch_nvd_cve(
            start.strftime('%Y-%m-%dT%H:%M:%S.000'),
            end.strftime('%Y-%m-%dT%H:%M:%S.000')
        )
        
        for vuln in cves:
            cve_id = vuln['cve']['id']
            if cve_id not in cve_database:
                cve_database[cve_id] = {
                    'source': 'NVD',
                    'description': vuln['cve']['descriptions'][0]['value'] if vuln['cve'].get('descriptions') else '',
                    'cvss': vuln['cve']['metrics'].get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0),
                    'published': vuln['cve']['published'],
                    'modified': vuln['cve']['lastModified']
                }
        
        print(f"  ✓ {year} : {len(cves)} 条 (总计：{len(cve_database)})")
        time.sleep(6)  # NVD 限流
    
    # 3. 保存数据库
    output_file = f"{WORKSPACE}/cve_database_full.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cve_database, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 采集完成!")
    print(f"📊 总计：{len(cve_database)} CVE")
    print(f"💾 保存到：{output_file}")
    print(f"⏰ 完成时间：{datetime.now()}")

if __name__ == '__main__':
    main()
