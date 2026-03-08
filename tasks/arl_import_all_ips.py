#!/usr/bin/env python3
"""
ARL 灯塔 - 全量 IP 导入工具 (MongoDB 直连版)
- 通过 Docker 网络直接连接 MongoDB
- 低速率导入 (0.1 秒/条)
- 支持断点续传
"""

import sys
import os
from datetime import datetime

# 检查 IP 文件
IP_FILE = "/tmp/openclaw_all_ips.txt"
STATUS_FILE = "/tmp/arl_import_status.json"

print("="*60)
print("ARL 灯塔 - 全量 IP 导入工具")
print("="*60)

# 检查 IP 文件是否存在
if not os.path.exists(IP_FILE):
    print(f"\n[!] IP 文件不存在：{IP_FILE}")
    print("[*] 先运行 extract_ips.py 提取 IP...")
    
    # 自动运行提取脚本
    import subprocess
    result = subprocess.run(['python3', '/root/.openclaw/workspace/extract_ips.py'], 
                          capture_output=False, timeout=3600)
    if result.returncode != 0:
        print("[!] IP 提取失败")
        sys.exit(1)

# 读取 IP 列表
print(f"\n[*] 读取 IP 列表：{IP_FILE}")
with open(IP_FILE, 'r') as f:
    ips = [line.strip() for line in f if line.strip()]

print(f"[+] 读取到 {len(ips)} 个 IP")

# 读取导入状态 (断点续传)
imported_count = 0
if os.path.exists(STATUS_FILE):
    import json
    try:
        with open(STATUS_FILE, 'r') as f:
            status = json.load(f)
            imported_count = status.get('imported', 0)
            print(f"[!] 发现历史状态，已导入 {imported_count} 个 IP")
    except:
        pass

# 通过 Docker 执行 MongoDB 导入
print(f"\n[*] 开始导入到 ARL MongoDB...")
print(f"[*] 导入速率：10 IP/秒 (低速率模式)")
print(f"[*] 起始位置：{imported_count + 1}")
print()

batch_size = 100
start_time = datetime.now()

for batch_start in range(imported_count, len(ips), batch_size):
    batch_end = min(batch_start + batch_size, len(ips))
    batch_ips = ips[batch_start:batch_end]
    
    # 构建 IP 数据
    ip_docs = []
    for ip in batch_ips:
        # 解析 IP:端口
        if ':' in ip:
            ip_addr, port = ip.rsplit(':', 1)
        else:
            ip_addr = ip
            port = '80'
        
        ip_docs.append(f'{{"ip": "{ip_addr}", "port": {port}, "group_id": 1}}')
    
    # 通过 Docker 执行 MongoDB 插入
    docker_cmd = f'''docker run --rm --network arl-docker_default -v /tmp:/tmp python:3.11-slim bash -c '
pip install pymongo==3.13.0 -q
python3 << PYEOF
from pymongo import MongoClient
import json

client = MongoClient("mongodb://arl_mongodb:27017/", username="admin", password="admin")
db = client["arl"]
collection = db["ip"]

ips = [{",".join(ip_docs)}]

# 批量插入 (忽略重复)
for ip_doc in ips:
    try:
        collection.update_one(
            {{"ip": ip_doc["ip"], "port": ip_doc["port"]}},
            {{"$set": ip_doc}},
            upsert=True
        )
    except Exception as e:
        print(f"Error: {{e}}")

print(f"Inserted {{len(ips)}} IPs")
client.close()
PYEOF
' '''
    
    import subprocess
    result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        imported_count = batch_end
        # 保存状态
        with open(STATUS_FILE, 'w') as f:
            json.dump({'imported': imported_count, 'total': len(ips)}, f)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = imported_count / elapsed if elapsed > 0 else 0
        eta = (len(ips) - imported_count) / rate if rate > 0 else 0
        
        print(f"  批次 {batch_start+1}-{batch_end}: ✅ 成功 (总计 {imported_count}/{len(ips)}, 速率 {rate:.1f} IP/s, 剩余 {eta:.0f}s)")
    else:
        print(f"  批次 {batch_start+1}-{batch_end}: ❌ 失败 - {result.stderr[:100]}")
    
    # 限流
    time.sleep(0.5)

print()
print("="*60)
print(f"✅ 导入完成!")
print(f"   总 IP 数：{len(ips)}")
print(f"   已导入：{imported_count}")
print(f"   耗时：{(datetime.now() - start_time).total_seconds():.1f} 秒")
print("="*60)
