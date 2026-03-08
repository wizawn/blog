#!/usr/bin/env python3
import requests, re, time

ips = set()
for page in range(1, 2242):
    try:
        r = requests.get(f"https://openclaw.allegro.earth/page/{page}/", headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        new = set(re.findall(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)', r.text))
        ips.update(new)
        if page % 50 == 0:
            with open("/tmp/openclaw_all_ips.txt", 'w') as f: f.write('\n'.join(sorted(ips)))
            print(f"页{page}: {len(ips)} IPs")
        time.sleep(1)
    except Exception as e:
        print(f"页{page}错误：{e}")
        break

with open("/tmp/openclaw_all_ips.txt", 'w') as f: f.write('\n'.join(sorted(ips)))
print(f"\n完成！总 IP 数：{len(ips)}")
