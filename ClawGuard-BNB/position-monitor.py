
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
"""专业持仓实时监控 - 24/7 运行"""
import requests, time
from datetime import datetime

# 用户真实持仓数据
POSITION = {
    'symbol': 'BTCUSDT',
    'side': 'SHORT',  # 空头
    'size': 0.013,  # BTC
    'entry_price': 68716.10,  # 开仓价
    'margin': 89.6,  # 保证金 USDT
    'liquidation_price': 75298.17,  # 强平价
}

# 告警阈值
ALERT_PRICE_HIGH = 69500  # 高位告警
ALERT_PRICE_LOW = 68000   # 低位告警
STOP_LOSS = 70000         # 止损位

API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
PROXY = 'http://127.0.0.1:7890'
LOG = '/root/.openclaw/workspace/memory/position-monitor.log'

def log(m):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{t}] {m}")
    with open(LOG, 'a') as f: f.write(f"[{t}] {m}\n")

def get_price():
    try:
        r = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            proxies={'http': PROXY, 'https': PROXY},
            headers={'X-MBX-APIKEY': API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            return float(r.json()['price'])
    except: pass
    return None

def analyze(p):
    entry = POSITION['entry_price']
    size = POSITION['size']
    margin = POSITION['margin']
    
    # 空头盈亏
    pnl = (entry - p) * size
    pnl_pct = (pnl / margin) * 100
    
    # 距离强平
    liq = POSITION['liquidation_price']
    dist_liq = ((liq - p) / p) * 100
    
    # 回本价
    break_even = entry
    
    return pnl, pnl_pct, dist_liq, break_even

def main():
    log("="*70)
    log("🔍 专业持仓实时监控启动")
    log(f"持仓：{POSITION['size']} BTC {POSITION['side']}")
    log(f"开仓价：${POSITION['entry_price']:,.2f}")
    log(f"保证金：${POSITION['margin']:,.2f}")
    log(f"强平价：${POSITION['liquidation_price']:,.2f}")
    log(f"止损位：${STOP_LOSS:,.2f}")
    log("="*70)
    
    last_alert = 0
    
    while True:
        p = get_price()
        if p:
            pnl, pnl_pct, dist_liq, break_even = analyze(p)
            
            # 每分钟汇报
            if int(time.time()) % 60 < 10:
                status = "🔴 亏损" if pnl < 0 else "✅ 盈利"
                log(f"💰 ${p:,.2f} | 盈亏：${pnl:,.2f} ({pnl_pct:.2f}%) {status} | 距强平：+{dist_liq:.1f}%")
            
            # 告警
            now = time.time()
            if p >= STOP_LOSS and now - last_alert > 300:
                log(f"🚨 触及止损位 ${STOP_LOSS:,.2f}！建议立即平仓！")
                last_alert = now
            elif p >= ALERT_PRICE_HIGH and now - last_alert > 300:
                log(f"⚠️ 高位告警 ${p:,.2f}！考虑减仓或止损！")
                last_alert = now
            elif p <= ALERT_PRICE_LOW and now - last_alert > 300:
                log(f"✅ 低位告警 ${p:,.2f}！考虑加仓或止盈！")
                last_alert = now
            
            # 专业建议
            if int(time.time()) % 300 < 10:
                if pnl_pct < -5:
                    log(f"💡 建议：亏损超过 5%，建议止损")
                elif pnl_pct > 3:
                    log(f"💡 建议：盈利超过 3%，建议部分止盈")
                elif p > POSITION['entry_price'] * 1.02:
                    log(f"💡 建议：价格上涨 2%，考虑止损")
                elif p < POSITION['entry_price'] * 0.98:
                    log(f"💡 建议：价格下跌 2%，考虑加仓")
        
        time.sleep(10)

if __name__ == '__main__': main()
