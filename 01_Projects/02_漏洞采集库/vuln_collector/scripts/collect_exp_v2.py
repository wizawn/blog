#!/usr/bin/env python3
import json
import os
from datetime import datetime

BASE_DIR = "/root/.openclaw/workspace/vuln_collector"
EXP_DIR = BASE_DIR + "/exp"

ts = datetime.now().isoformat()
print("[+] EXP 采集脚本 v2 - " + ts)

os.makedirs(EXP_DIR, exist_ok=True)
cve_dir = BASE_DIR + "/cve"
total_exp = 0

print("[+] 扫描 CVE 目录...")
for year in os.listdir(cve_dir):
    year_path = os.path.join(cve_dir, year)
    if not os.path.isdir(year_path):
        continue
    for cve_file in os.listdir(year_path):
        if cve_file.endswith('.yaml'):
            total_exp += 1

stats = {"version": "2.0", "updated": ts, "total_exp": total_exp}
with open(BASE_DIR + "/EXP_STATS.json", 'w') as f:
    json.dump(stats, f, indent=2)

print("[+] CVE/EXP 总数：" + str(total_exp))
print("[+] 完成!")
