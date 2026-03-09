#!/usr/bin/env python3
"""BTC 实时监控告警 - 24/7 运行"""
import requests, time
from datetime import datetime

LOG = '/root/.openclaw/workspace/memory/btc-realtime-alerts.log'
PROXY = 'http://127.0.0.1:7890'

# 告警阈值
ALERT_LOW = 68000   # 跌破告警
ALERT_HIGH = 69000  # 突破告警

def log(m):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{t}] {m}")
    with open(LOG, 'a') as f: f.write(f"[{t}] {m}\n")

def get_price():
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            proxies={'http': PROXY, 'https': PROXY}, timeout=5)
        return float(r.json()['price']) if r.status_code == 200 else None
    except: return None

def main():
    log("="*60)
    log(f"🔍 BTC 实时监控启动")
    log(f"告警阈值：${ALERT_LOW:,.2f} - ${ALERT_HIGH:,.2f}")
    log(f"检查间隔：10 秒")
    log("="*60)
    
    alerted_low = False
    alerted_high = False
    
    while True:
        p = get_price()
        if p:
            # 跌破告警
            if p <= ALERT_LOW and not alerted_low:
                log(f"🚨 📉 **BTC 跌破 ${ALERT_LOW:,.2f}**")
                log(f"   当前价格：${p:,.2f}")
                log(f"   建议：关注支撑位，考虑是否平仓")
                alerted_low = True
                alerted_high = False
            # 突破告警
            elif p >= ALERT_HIGH and not alerted_high:
                log(f"🚨 📈 **BTC 突破 ${ALERT_HIGH:,.2f}**")
                log(f"   当前价格：${p:,.2f}")
                log(f"   建议：关注阻力位，空头注意风险")
                alerted_high = True
                alerted_low = False
            # 重置告警状态（价格回到中间）
            elif ALERT_LOW < p < ALERT_HIGH:
                alerted_low = False
                alerted_high = False
            
            # 每分钟汇报
            if int(time.time()) % 60 < 10:
                log(f"💰 ${p:,.2f} | 区间：${ALERT_LOW:,.0f}-${ALERT_HIGH:,.0f}")
        
        time.sleep(10)

if __name__ == '__main__': main()
