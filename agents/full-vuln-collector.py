#!/usr/bin/env python3
"""
全量漏洞采集脚本 v3.0
采集源：CISA KEV + NVD + GitHub Advisory + OpenCVE
同步：hostbrr1-storage
清理：本地数据（保留记录）
"""

import requests
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = "/root/.openclaw/workspace/vuln-data"
RCLONE_DEST = "hostbrr1:vuln_collector/processed"

# API 端点（免钥）
CISA_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
GITHUB_ADV_BASE = "https://raw.githubusercontent.com/github/advisory-database/main/ecosystems"
OPENCVE_URL = "https://www.opencve.io/api/cve"

def save_json(data, filename):
    filepath = Path(OUTPUT_DIR) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存：{filepath}")

def run_rclone(src, dest):
    """执行 rclone 同步"""
    cmd = f"rclone sync {src} {dest} --progress"
    print(f"📤 同步：{cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ 同步失败：{result.stderr}")
    return result.returncode == 0

print("=" * 60)
print("🔍 全量漏洞采集 v3.0")
print("=" * 60)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
all_vulns = []

# ================= 1. CISA KEV =================
print("\n🔴 采集 CISA KEV...")
try:
    resp = requests.get(CISA_URL, timeout=30)
    data = resp.json()
    
    for item in data.get('vulnerabilities', []):
        all_vulns.append({
            'source': 'CISA_KEV',
            'cve_id': item.get('cveID', '').upper(),
            'vendor': item.get('vendorProject', ''),
            'product': item.get('product', ''),
            'name': item.get('vulnerabilityName', ''),
            'date_added': item.get('dateAdded', ''),
            'description': item.get('shortDescription', ''),
            'priority': 'CRITICAL'
        })
    
    print(f"   采集 {len(data.get('vulnerabilities', []))} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# ================= 2. NVD（最近 30 天） =================
print("\n🔵 采集 NVD（最近 30 天，限 500 条）...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    nvd_vulns = []
    page = 0
    
    while len(nvd_vulns) < 500:
        url = f"{NVD_URL}?lastModStartDate={start_str}&lastModEndDate={end_str}&resultsPerPage=100&startIndex={page * 100}"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        
        cves = data.get('vulnerabilities', [])
        if not cves:
            break
        
        for item in cves:
            cve = item.get('cve', {})
            nvd_vulns.append({
                'source': 'NVD',
                'cve_id': cve.get('id', '').upper(),
                'description': cve.get('descriptions', [{}])[0].get('value', ''),
                'severity': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN'),
                'score': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0),
                'last_modified': cve.get('lastModified', '')
            })
        
        print(f"   已采集 {len(nvd_vulns)} 条...")
        page += 1
        
        import time
        time.sleep(6)  # NVD 限流
    
    all_vulns.extend(nvd_vulns)
    print(f"   采集 {len(nvd_vulns)} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# ================= 3. GitHub Advisory（NPM） =================
print("\n🟢 采集 GitHub Advisory (NPM)...")
try:
    url = f"{GITHUB_ADV_BASE}/npm/advisories.json"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    
    github_count = 0
    for item in data[:200]:  # 限制 200 条
        all_vulns.append({
            'source': 'GitHub_Advisory',
            'cve_id': item.get('schema_version', str(item.get('id', ''))).upper(),
            'ecosystem': 'npm',
            'package': item.get('package', {}).get('name', ''),
            'severity': item.get('severity', ''),
            'summary': item.get('summary', ''),
            'description': item.get('details', '')
        })
        github_count += 1
    
    print(f"   采集 {github_count} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# ================= 4. OpenCVE =================
print("\n🟡 采集 OpenCVE（前 100 条）...")
try:
    url = f"{OPENCVE_URL}?per_page=100"
    resp = requests.get(url, timeout=30)
    
    if resp.status_code == 200:
        data = resp.json()
        for item in data:
            all_vulns.append({
                'source': 'OpenCVE',
                'cve_id': item.get('id', '').upper(),
                'summary': item.get('summary', ''),
                'severity': item.get('cvss', {}).get('severity', ''),
                'score': item.get('cvss', {}).get('score', 0)
            })
        
        print(f"   采集 {len(data)} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# ================= 5. 合并去重 =================
print("\n🔄 合并去重...")
dedup_dict = {}
priority = {'CISA_KEV': 1, 'NVD': 2, 'GitHub_Advisory': 3, 'OpenCVE': 4}

for vuln in all_vulns:
    cve_id = vuln.get('cve_id', '')
    if not cve_id:
        continue
    src_priority = priority.get(vuln.get('source', ''), 99)
    if cve_id not in dedup_dict or src_priority < priority.get(dedup_dict[cve_id].get('source', ''), 99):
        dedup_dict[cve_id] = vuln

merged = list(dedup_dict.values())
save_json(merged, 'merged_vulns_full.json')

# ================= 6. 生成报告 =================
report = {
    '采集时间': datetime.now().isoformat(),
    '数据源': {
        'CISA_KEV': len([v for v in all_vulns if v.get('source') == 'CISA_KEV']),
        'NVD': len([v for v in all_vulns if v.get('source') == 'NVD']),
        'GitHub_Advisory': len([v for v in all_vulns if v.get('source') == 'GitHub_Advisory']),
        'OpenCVE': len([v for v in all_vulns if v.get('source') == 'OpenCVE'])
    },
    '总计（去重前）': len(all_vulns),
    '总计（去重后）': len(merged),
    '去重率': f"{(1 - len(merged)/len(all_vulns))*100:.1f}%" if all_vulns else 0
}
save_json(report, 'full_collection_report.json')

print("\n" + "=" * 60)
print(f"✅ 采集完成！总计 {len(merged)} 条")
print("=" * 60)

# ================= 7. 同步到 hostbrr1 =================
print("\n📤 同步到 hostbrr1-storage...")
if run_rclone(f"{OUTPUT_DIR}/", f"{RCLONE_DEST}/"):
    print("✅ 同步成功！")
else:
    print("❌ 同步失败")

# ================= 8. 清理本地数据（保留记录） =================
print("\n🧹 清理本地数据...")
import os

# 保留的文件
keep_files = ['full_collection_report.json', 'expanded-collection-report-20260302.md']

# 删除其他 JSON 数据文件
for filepath in Path(OUTPUT_DIR).glob('*.json'):
    if filepath.name not in keep_files:
        try:
            os.remove(filepath)
            print(f"   删除：{filepath.name}")
        except:
            pass

print("\n" + "=" * 60)
print("✅ 全部完成！")
print(f"📊 总计：{len(merged)} 条漏洞数据")
print(f"📁 已同步到：{RCLONE_DEST}")
print("=" * 60)
