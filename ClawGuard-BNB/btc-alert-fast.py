#!/usr/bin/env python3
import requests, hmac, hashlib, time
from datetime import datetime

API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
API_SECRET = 'FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q'

# 阶梯止盈
STOP_LOSS = 67180   # 止损预警
TP1 = 65500         # 第一止盈
TP2 = 65000         # 第二止盈
TP3 = 64500         # 延伸
TP4 = 64000         # 延伸
TP5 = 63000         # 极端

ENTRY = 66914.30
SIZE = 0.008
LOG = '/root/.openclaw/workspace/memory/btc-alerts.log'

def log(m):
    t = datetime.now().strftime('%H:%M:%S')
    print(f"[{t}] {m}")
    with open(LOG, 'a') as f: f.write(f"[{t}] {m}\n")

def get_price():
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
        return float(r.json()['price'])
    except: return None

def main():
    log("="*50)
    log(f"🔍 BTC 监控启动 | 空头 {SIZE} BTC | 入场：${ENTRY:,.2f}")
    log(f"止损：${STOP_LOSS:,.2f}")
    log(f"止盈：${TP1} → ${TP5}")
    log("="*50)
    
    last = None
    triggered = set()
    
    while True:
        p = get_price()
        if p:
            pnl = (ENTRY - p) * SIZE
            
            # 告警检查
            if p >= STOP_LOSS and 'SL' not in triggered:
                log(f"⚠️ 突破止损预警 ${STOP_LOSS} | 当前：${p:,.2f}")
                triggered.add('SL')
            if p <= TP1 and 'TP1' not in triggered:
                log(f"✅ 第一止盈 ${TP1} | 建议：止盈 30-50%")
                triggered.add('TP1')
            if p <= TP2 and 'TP2' not in triggered:
                log(f"✅ 第二止盈 ${TP2}")
                triggered.add('TP2')
            if p <= TP3 and 'TP3' not in triggered:
                log(f"🎯 延伸目标 ${TP3}")
                triggered.add('TP3')
            if p <= TP4 and 'TP4' not in triggered:
                log(f"🎯 延伸目标 ${TP4}")
                triggered.add('TP4')
            
            # 每 5 分钟汇报
            if int(time.time()) % 300 < 30:
                log(f"💰 ${p:,.2f} | 盈亏：${pnl:+.2f} USDT ({pnl/ENTRY*100:+.2f}%)")
        
        time.sleep(30)

if __name__ == '__main__': main()
