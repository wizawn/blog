#!/usr/bin/env python3
"""
OpenClaw 暴露 IP 提取工具 - 正确格式
网站分页：/page/1/, /page/2/, ...
"""

import requests
import re
import time

BASE_URL = "https://openclaw.allegro.earth"
OUTPUT = "/tmp/openclaw_all_ips.txt"
HEADERS = {"User-Agent": "Mozilla/5.0"}

all_ips = set()
page = 1

print(f"🚀 开始提取 OpenClaw 暴露 IP")
print(f"📄 分页格式：/page/N/")
print("-" * 60)

while True:
    # 正确格式：/page/1/, /page/2/, ...
    url = f"{BASE_URL}/page/{page}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"❌ 页 {page} 返回 {resp.status_code}，停止")
            break
        
        # 提取 IP:端口
        ips = re.findall(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)', resp.text)
        new_count = len(all_ips)
        all_ips.update(ips)
        
        print(f"页 {page}: +{len(all_ips) - new_count} IP | 累计 {len(all_ips)} 个")
        
        # 如果没有新 IP，说明到最后一页
        if len(ips) == 0:
            print(f"✅ 到达最后一页 (页 {page})")
            break
        
        page += 1
        time.sleep(2)
        
        # 每 100 页保存一次
        if page % 100 == 0:
            with open(OUTPUT, 'w') as f:
                f.write('\n'.join(sorted(all_ips)))
            print(f"💾 已保存到 {OUTPUT}")
        
    except Exception as e:
        print(f"❌ 页 {page} 错误：{e}")
        break

# 最终保存
with open(OUTPUT, 'w') as f:
    f.write('\n'.join(sorted(all_ips)))

print("\n" + "=" * 60)
print(f"✅ 提取完成！")
print(f"📊 总 IP 数：{len(all_ips)}")
print(f"📁 文件：{OUTPUT}")
print("=" * 60)
