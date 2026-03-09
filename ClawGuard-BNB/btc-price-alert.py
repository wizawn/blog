
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

#!/usr/bin/env python3
import requests, hmac, hashlib, time, json
from datetime import datetime
from urllib.parse import urlencode

API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
API_SECRET = 'FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q'
PROXY = 'http://127.0.0.1:7890'

# 阶梯止盈
ALERT_HIGH = 67180  # 止损预警
ALERT_LOW_1 = 65500  # 第一止盈
ALERT_LOW_2 = 65000  # 第二止盈
ALERT_LOW_3 = 64500  # 延伸
ALERT_LOW_4 = 64000  # 延伸
ALERT_LOW_FINAL = 63000  # 极端

POSITION = {'symbol': 'BTCUSDT', 'size': 0.008, 'type': 'SHORT', 'entry': 66914.30}
ALERT_LOG = '/root/.openclaw/workspace/memory/btc-alerts.log'
proxies = {'http': PROXY, 'https': PROXY}
headers = {'X-MBX-APIKEY': API_KEY}

def sign(p):
    return hmac.new(API_SECRET.encode(), urlencode(p).encode(), hashlib.sha256).hexdigest()

def log(m):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{t}] {m}")
    open(ALERT_LOG, 'a').write(f"[{t}] {m}\n")

def get_price():
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', proxies=proxies, timeout=10)
        return float(r.json()['price']) if r.status_code == 200 else None
    except: return None

def check(p, last):
    alerts = []
    if p >= ALERT_HIGH and (last is None or last < ALERT_HIGH):
        alerts.append(f"⚠️ 突破止损预警 ${ALERT_HIGH} | 当前：${p:,.2f}")
    if p <= ALERT_LOW_1 and (last is None or last > ALERT_LOW_1):
        alerts.append(f"✅ 第一止盈 ${ALERT_LOW_1} | 建议：止盈 30-50%")
    if p <= ALERT_LOW_2 and (last is None or last > ALERT_LOW_2):
        alerts.append(f"✅ 第二止盈 ${ALERT_LOW_2}")
    if p <= ALERT_LOW_3 and (last is None or last > ALERT_LOW_3):
        alerts.append(f"🎯 延伸目标 ${ALERT_LOW_3}")
    if p <= ALERT_LOW_4 and (last is None or last > ALERT_LOW_4):
        alerts.append(f"🎯 延伸目标 ${ALERT_LOW_4}")
    return alerts

def main():
    print("="*60)
    print(f"🔍 BTC 监控 | 空头 {POSITION['size']} BTC | 入场：${POSITION['entry']:,.2f}")
    print(f"止损：${ALERT_HIGH:,.2f} | 止盈：${ALERT_LOW_1} → ${ALERT_LOW_FINAL}")
    print("="*60)
    last = None
    while True:
        p = get_price()
        if p:
            for a in check(p, last): log(a)
            pnl = (POSITION['entry'] - p) * POSITION['size']
            if int(time.time()) % 300 < 30:
                log(f"💰 ${p:,.2f} | 盈亏：${pnl:+.2f} USDT")
            last = p
        time.sleep(30)

if __name__ == '__main__': main()
