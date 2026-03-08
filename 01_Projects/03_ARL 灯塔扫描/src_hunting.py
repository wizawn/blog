#!/usr/bin/env python3
# SRC 挖洞 - 信息收集脚本

import requests, time
from datetime import datetime

print("=" * 50)
print("SRC 挖洞 - 信息收集阶段")
print("=" * 50)
print("开始时间:", datetime.now())
print()

# 读取已导入的 IP 列表
try:
    with open('/tmp/all_ips.txt', 'r') as f:
        ips = [line.strip() for line in f if line.strip()]
    print("待扫描 IP 总数:", len(ips))
except:
    print("错误：找不到 /tmp/all_ips.txt")
    ips = []

print()
print("开始指纹识别...")
print()

# 分类统计
categories = {'OpenClaw': 0, 'WordPress': 0, 'ThinkPHP': 0, '其他': 0}
results = []

for i, ip in enumerate(ips[:500]):  # 先扫描前 500 个
    found = False
    
    # HTTP 18789 端口检查 (OpenClaw)
    try:
        resp = requests.get('http://' + ip + ':18789', timeout=2)
        if 'OpenClaw' in resp.text or 'admin' in resp.text.lower():
            categories['OpenClaw'] += 1
            results.append({'ip': ip, 'port': 18789, 'type': 'OpenClaw'})
            print("[+]", ip + ":18789 - OpenClaw 管理界面")
            found = True
    except:
        pass
    
    # HTTP 80 端口
    if not found:
        try:
            resp = requests.get('http://' + ip, timeout=2)
            body = resp.text.lower()
            if 'wordpress' in body:
                categories['WordPress'] += 1
                results.append({'ip': ip, 'port': 80, 'type': 'WordPress'})
            elif 'thinkphp' in body:
                categories['ThinkPHP'] += 1
                results.append({'ip': ip, 'port': 80, 'type': 'ThinkPHP'})
            else:
                categories['其他'] += 1
        except:
            categories['其他'] += 1
    
    if (i + 1) % 100 == 0:
        print("进度:", str(i+1) + "/" + str(min(500, len(ips))))
        time.sleep(1)

print()
print("=" * 50)
print("指纹识别完成")
print("=" * 50)
print("OpenClaw:", categories['OpenClaw'])
print("WordPress:", categories['WordPress'])
print("ThinkPHP:", categories['ThinkPHP'])
print("其他:", categories['其他'])
print()
print("结束时间:", datetime.now())

# 保存结果
import json
with open('/tmp/src_targets.json', 'w') as f:
    json.dump(results, f, indent=2)
print()
print("目标已保存到 /tmp/src_targets.json")
