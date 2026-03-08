#!/usr/bin/env python3
"""
NVD CVE 数据采集脚本 - 续采模式
继续采集 2015-2026 年 CVE 数据
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/root/.openclaw/workspace/vuln_collector")
OUTPUT_DIR.mkdir(exist_ok=True)

# 加载已有数据
cve_database_file = OUTPUT_DIR / "cve_database_full.json"
if cve_database_file.exists():
    with open(cve_database_file) as f:
        cve_database = json.load(f)
    print(f"✅ 加载已有数据：{len(cve_database)} 条 CVE")
else:
    cve_database = {}
    print("⚠️ 无已有数据，从头开始采集")

# NVD API
api_base = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def fetch_nvd_range(start_date, end_date):
    """获取指定时间范围的 CVE"""
    url = f"{api_base}?pubStartDate={start_date}&pubEndDate={end_date}&resultsPerPage=2000"
    
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get('vulnerabilities', [])
    except Exception as e:
        print(f"❌ 错误：{e}")
        return []

# 采集年份范围
years = list(range(2015, 2027))

print(f"\n🚀 开始 NVD CVE 数据采集")
print(f"年份范围：{years[0]} - {years[-1]}")
print(f"已有数据：{len(cve_database)} 条\n")

total_new = 0

for year in years:
    print(f"\n📅 采集 {year} 年...")
    
    # 按季度采集
    for quarter in range(1, 5):
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        
        if end_month > 12:
            end_month = 12
        
        start_date = f"{year}-{start_month:02d}-01T00:00:00.000"
        
        if year == 2026 and quarter == 1:
            # 今年只采集到当前
            end_date = datetime.now().strftime("%Y-%m-%dT23:59:59.999")
        else:
            end_date = f"{year}-{end_month:02d}-28T23:59:59.999"
        
        vulns = fetch_nvd_range(start_date, end_date)
        
        new_count = 0
        for vuln in vulns:
            cve_item = vuln.get('cve', {})
            cve_id = cve_item.get('id', '')
            
            if cve_id and cve_id not in cve_database:
                cve_database[cve_id] = {
                    'source': 'NVD',
                    'id': cve_id,
                    'description': cve_item.get('descriptions', [{}])[0].get('value', '')[:500],
                    'published': cve_item.get('published', ''),
                    'modified': cve_item.get('lastModified', ''),
                    'year': year,
                    'quarter': quarter
                }
                new_count += 1
        
        if new_count > 0:
            print(f"  Q{quarter}: +{new_count} 条新 CVE")
            total_new += new_count
        
        # NVD 限流：每 6 秒一次请求
        time.sleep(6)
    
    print(f"  {year} 年累计：{len([k for k in cve_database if k.startswith(f'CVE-{year}')])} 条")
    
    # 保存中间结果
    with open(cve_database_file, 'w', encoding='utf-8') as f:
        json.dump(cve_database, f, indent=2, ensure_ascii=False)

print(f"\n✅ 采集完成！")
print(f"新增 CVE: {total_new} 条")
print(f"总计 CVE: {len(cve_database)} 条")
print(f"保存位置：{cve_database_file}")
