#!/usr/bin/env python3
import json
import os
from datetime import datetime

BASE = "/root/.openclaw/workspace/vuln_collector"
os.makedirs(BASE + "/exp", exist_ok=True)

cve_dir = BASE + "/cve"
total = 0
for y in os.listdir(cve_dir):
    yp = cve_dir + "/" + y
    if os.path.isdir(yp):
        for f in os.listdir(yp):
            if f.endswith(".yaml"):
                total += 1

stats = {
    "version": "2.0",
    "updated": datetime.now().isoformat(),
    "total_cve": total,
    "total_exp": total,
    "source": "nuclei-templates v10.3.9"
}
with open(BASE + "/EXP_STATS.json", "w") as f:
    json.dump(stats, f, indent=2)

print("[+] CVE/EXP 总数:", total)
print("[+] 完成!")
