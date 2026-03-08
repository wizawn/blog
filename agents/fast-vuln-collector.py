#!/usr/bin/env python3
"""
快速漏洞采集脚本 - 直连 API
采集：CISA KEV + NVD（最近 30 天，限 500 条）
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = "/root/.openclaw/workspace/vuln-data"

# API 端点
CISA_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def save_json(data, filename):
    filepath = Path(OUTPUT_DIR) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存：{filepath} ({len(data) if isinstance(data, list) else 'object'} 条)")

print("=" * 60)
print("🔍 快速漏洞采集")
print("=" * 60)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# 1. CISA KEV
print("\n🔴 采集 CISA KEV...")
try:
    resp = requests.get(CISA_URL, timeout=30)
    data = resp.json()
    
    vulns = []
    for item in data.get('vulnerabilities', []):
        vulns.append({
            'source': 'CISA_KEV',
            'cve_id': item.get('cveID', '').upper(),
            'vendor': item.get('vendorProject', ''),
            'product': item.get('product', ''),
            'name': item.get('vulnerabilityName', ''),
            'date_added': item.get('dateAdded', ''),
            'description': item.get('shortDescription', ''),
            'priority': 'CRITICAL'
        })
    
    save_json(vulns, 'cisa_kev.json')
    print(f"   采集 {len(vulns)} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# 2. NVD（最近 30 天）
print("\n🔵 采集 NVD（最近 30 天）...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    vulns = []
    page = 0
    
    while len(vulns) < 500:  # 免钥上限
        url = f"{NVD_URL}?lastModStartDate={start_str}&lastModEndDate={end_str}&resultsPerPage=100&startIndex={page * 100}"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        
        cves = data.get('vulnerabilities', [])
        if not cves:
            break
        
        for item in cves:
            cve = item.get('cve', {})
            vulns.append({
                'source': 'NVD',
                'cve_id': cve.get('id', '').upper(),
                'description': cve.get('descriptions', [{}])[0].get('value', ''),
                'severity': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN'),
                'score': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0),
                'last_modified': cve.get('lastModified', '')
            })
        
        print(f"   已采集 {len(vulns)} 条...")
        page += 1
        
        import time
        time.sleep(6)  # NVD 限流
    
    save_json(vulns, 'nvd_recent.json')
    print(f"   采集 {len(vulns)} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# 3. 合并去重
print("\n🔄 合并去重...")
import glob

all_vulns = []
for filepath in Path(OUTPUT_DIR).glob('*.json'):
    if 'merged' in str(filepath) or 'report' in str(filepath):
        continue
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_vulns.extend(data)
    except:
        pass

# 去重
dedup_dict = {}
priority = {'CISA_KEV': 1, 'NVD': 2}
for vuln in all_vulns:
    cve_id = vuln.get('cve_id', '')
    if not cve_id:
        continue
    src_priority = priority.get(vuln.get('source', ''), 99)
    if cve_id not in dedup_dict or src_priority < priority.get(dedup_dict[cve_id].get('source', ''), 99):
        dedup_dict[cve_id] = vuln

merged = list(dedup_dict.values())
save_json(merged, 'merged_vulns.json')

# 4. 生成报告
report = {
    '采集时间': datetime.now().isoformat(),
    'CISA_KEV': len([v for v in all_vulns if v.get('source') == 'CISA_KEV']),
    'NVD': len([v for v in all_vulns if v.get('source') == 'NVD']),
    '总计（去重前）': len(all_vulns),
    '总计（去重后）': len(merged),
    '去重率': f"{(1 - len(merged)/len(all_vulns))*100:.1f}%" if all_vulns else 0
}
save_json(report, 'collection_report.json')

print("\n" + "=" * 60)
print(f"✅ 采集完成！总计 {len(merged)} 条")
print("=" * 60)
