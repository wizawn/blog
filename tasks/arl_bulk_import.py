#!/usr/bin/env python3
"""
ARL 批量导入脚本 - 通过 MongoDB 直连
支持：10 万+ IP 快速导入
"""

import sys

if len(sys.argv) < 2:
    print("用法：python3 arl_bulk_import.py <ip_file>")
    print("示例：python3 arl_bulk_import.py /tmp/openclaw_all_ips.txt")
    sys.exit(1)

ip_file = sys.argv[1]

# 通过 Docker 执行
docker_cmd = f'''
docker run --rm --network arl-docker_default -v {ip_file}:/tmp/ips.txt python:3.11-slim bash -c '
pip install pymongo==3.13.0 -q
python3 << PYEOF
from pymongo import MongoClient
import time

client = MongoClient("mongodb://arl_mongodb:27017/", username="admin", password="admin")
db = client["arl"]
collection = db["ip"]

ips = []
with open("/tmp/ips.txt") as f:
    for line in f:
        ip = line.strip()
        if ip and ":" in ip:
            ip_addr, port = ip.rsplit(":", 1)
            ips.append({{"ip": ip_addr, "port": int(port), "group_id": 1}})

print(f"准备导入 {len(ips)} 个 IP...")

# 批量插入
batch_size = 1000
for i in range(0, len(ips), batch_size):
    batch = ips[i:i+batch_size]
    collection.insert_many(batch, ordered=False)
    print(f"  已导入 {min(i+batch_size, len(ips))}/{len(ips)}")

total = collection.count_documents({{}})
print(f"✅ 导入完成！ARL 总 IP 数：{total}")
client.close()
PYEOF
'
'''

import subprocess
subprocess.run(docker_cmd, shell=True)
