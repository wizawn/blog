#!/usr/bin/env python3
"""
OpenClaw 暴露 IP 全量提取工具
目标：224,015 个暴露实例
策略：分页爬取 + 批量导入 ARL
"""

import requests
import re
import time
from datetime import datetime

BASE_URL = "https://openclaw.allegro.earth/"
OUTPUT_FILE = "/tmp/openclaw_all_ips.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 估算总页数
TOTAL_PAGES = 2241  # 224,015 / 100
BATCH_SIZE = 50  # 每次爬取 50 页
SLEEP_SECONDS = 3  # 每页间隔

all_ips = set()
start_time = datetime.now()

print(f"🚀 开始全量提取 OpenClaw 暴露 IP")
print(f"📊 目标：{TOTAL_PAGES} 页 (~224,015 个 IP)")
print(f"⏰ 开始时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 60)

try:
    for batch_start in range(1, TOTAL_PAGES + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE - 1, TOTAL_PAGES)
        print(f"\n📦 爬取第 {batch_start}-{batch_end} 页...")
        
        for page in range(batch_start, batch_end + 1):
            try:
                url = f"{BASE_URL}?page={page}"
                resp = requests.get(url, headers=HEADERS, timeout=30)
                
                if resp.status_code == 200:
                    # 提取 IP:端口
                    ips = re.findall(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)', resp.text)
                    all_ips.update(ips)
                    
                    if page % 10 == 0:
                        print(f"  页 {page}: 累计 {len(all_ips)} 个唯一 IP")
                
                time.sleep(SLEEP_SECONDS)
                
            except Exception as e:
                print(f"  ❌ 页 {page} 失败：{e}")
                break
        
        # 每批保存
        with open(OUTPUT_FILE, 'w') as f:
            f.write('\n'.join(sorted(all_ips)))
        
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = len(all_ips) / elapsed if elapsed > 0 else 0
        eta = (TOTAL_PAGES * SLEEP_SECONDS - elapsed) / 60
        
        print(f"✅ 已保存 {len(all_ips)} 个 IP | 速率：{rate:.1f} IP/s | 剩余：{eta:.0f}分钟")
        
        # 如果连续失败，停止
        if len(all_ips) == 0 and batch_start > 100:
            print("⚠️ 连续失败，停止爬取")
            break

except KeyboardInterrupt:
    print("\n⚠️ 用户中断")

finally:
    # 最终保存
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(sorted(all_ips)))
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("✅ 提取完成！")
    print(f"📊 总 IP 数：{len(all_ips)}")
    print(f"⏰ 耗时：{elapsed/60:.1f} 分钟")
    print(f"📁 文件：{OUTPUT_FILE}")
    print("=" * 60)
