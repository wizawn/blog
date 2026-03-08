#!/usr/bin/env python3
"""
NVD 全量采集脚本
下载 NVD 所有年份的 CVE 数据（JSON 格式）
"""

import requests
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "/root/.openclaw/workspace/vuln-data"

# NVD CVE 数据文件（2002-2026）
NVD_YEARS = list(range(2002, 2027))
NVD_BASE = "https://nvd.nist.gov/feeds/json/cve/1.1"

def download_and_parse(year):
    """下载并解析 NVD JSON 文件"""
    url = f"{NVD_BASE}/nvdcve-1.1-{year}.json.gz"
    output_file = Path(OUTPUT_DIR) / f"nvdcve-{year}.json"
    
    print(f"   下载 {year}...")
    
    try:
        import gzip
        import shutil
        
        # 下载 gzip
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        
        gz_path = str(output_file) + '.gz'
        with open(gz_path, 'wb') as f:
            shutil.copyfileobj(resp.raw, f)
        
        # 解压
        with gzip.open(gz_path, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 清理
        import os
        os.remove(gz_path)
        
        # 解析统计
        with open(output_file, 'r') as f:
            data = json.load(f)
            count = len(data.get('CVE_Items', []))
        
        print(f"   ✅ {year}: {count:,} 条")
        return count
    except Exception as e:
        print(f"   ❌ {year} 失败：{e}")
        return 0

print("=" * 60)
print("🔵 NVD 全量采集（2002-2026）")
print("=" * 60)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

total = 0
for year in NVD_YEARS:
    count = download_and_parse(year)
    total += count

print("\n" + "=" * 60)
print(f"✅ NVD 全量采集完成！总计 {total:,} 条 CVE")
print("=" * 60)

# 保存报告
report = {
    '采集时间': datetime.now().isoformat(),
    'NVD_全量': total,
    '年份范围': f"2002-2026",
    '年均': total // len(NVD_YEARS)
}

with open(Path(OUTPUT_DIR) / 'nvd_full_report.json', 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"📊 报告已保存")
