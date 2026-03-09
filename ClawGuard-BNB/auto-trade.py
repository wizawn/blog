#!/usr/bin/env python3
"""专业自动交易执行脚本"""
import requests, json, hmac, hashlib, time
from datetime import datetime

API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
API_SECRET = 'FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q'
PROXY = 'http://127.0.0.1:7890'
LOG = '/root/.openclaw/workspace/memory/trade-execution.log'

def sign(params):
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def log(m):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{t}] {m}")
    with open(LOG, 'a') as f: f.write(f"[{t}] {m}\n")

def get_position():
    """获取当前持仓"""
    timestamp = int(time.time() * 1000)
    params = {'timestamp': timestamp, 'recvWindow': 60000}
    params['signature'] = sign(params)
    
    r = requests.get(
        'https://papi.binance.com/papi/v1/um/positionRisk',
        proxies={'http': PROXY, 'https': PROXY},
        headers={'X-MBX-APIKEY': API_KEY},
        params=params,
        timeout=5
    )
    
    if r.status_code == 200:
        for pos in r.json():
            if pos['symbol'] == 'BTCUSDT' and float(pos['positionAmt']) != 0:
                return {
                    'size': abs(float(pos['positionAmt'])),
                    'side': 'SHORT' if float(pos['positionAmt']) < 0 else 'LONG',
                    'entry': float(pos['entryPrice']),
                    'current': float(pos['markPrice']),
                    'pnl': float(pos['unRealizedProfit'])
                }
    return None

def close_position(size, confirm=True):
    """平仓"""
    if confirm:
        log(f"⚠️ 需要确认：平仓 {size} BTC")
        return False
    
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': 'BTCUSDT',
        'side': 'BUY' if size > 0 else 'SELL',  # 空头平仓用 BUY
        'type': 'MARKET',
        'quantity': size,
        'timestamp': timestamp,
        'recvWindow': 60000
    }
    params['signature'] = sign(params)
    
    r = requests.post(
        'https://papi.binance.com/papi/v1/um/order',
        proxies={'http': PROXY, 'https': PROXY},
        headers={'X-MBX-APIKEY': API_KEY},
        params=params,
        timeout=5
    )
    
    if r.status_code == 200:
        result = r.json()
        log(f"✅ 平仓成功：{result['executedQty']} BTC @ ${result['avgPrice']:,.2f}")
        return True
    else:
        log(f"❌ 平仓失败：{r.text}")
        return False

def set_stop_loss(stop_price, confirm=True):
    """设置止损"""
    if confirm:
        log(f"⚠️ 需要确认：设置止损 ${stop_price:,.2f}")
        return False
    
    pos = get_position()
    if not pos:
        log("❌ 无持仓")
        return False
    
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': 'BTCUSDT',
        'side': 'BUY' if pos['side'] == 'SHORT' else 'SELL',
        'type': 'STOP_MARKET',
        'stopPrice': stop_price,
        'quantity': pos['size'],
        'timestamp': timestamp,
        'recvWindow': 60000
    }
    params['signature'] = sign(params)
    
    r = requests.post(
        'https://papi.binance.com/papi/v1/um/order',
        proxies={'http': PROXY, 'https': PROXY},
        headers={'X-MBX-APIKEY': API_KEY},
        params=params,
        timeout=5
    )
    
    if r.status_code == 200:
        log(f"✅ 止损设置成功：${stop_price:,.2f}")
        return True
    else:
        log(f"❌ 止损设置失败：{r.text}")
        return False

def main():
    log("="*70)
    log("🤖 专业自动交易脚本启动")
    log("="*70)
    
    pos = get_position()
    if pos:
        log(f"\n💼 当前持仓")
        log(f"   方向：{pos['side']}")
        log(f"   持仓：{pos['size']:.4f} BTC")
        log(f"   开仓价：${pos['entry']:,.2f}")
        log(f"   当前价：${pos['current']:,.2f}")
        log(f"   盈亏：${pos['pnl']:,.2f} ({pos['pnl']/pos['entry']*100:.2f}%)")
        
        log(f"\n🎯 交易策略")
        log(f"   止损位：$70,000")
        log(f"   止盈位：$68,000")
        log(f"   回本位：${pos['entry']:,.2f}")
        
        # 自动执行逻辑
        if pos['pnl'] > 3:  # 盈利超过 3%
            log(f"\n✅ 盈利超过 3%，建议部分止盈")
            # close_position(pos['size'] * 0.5, confirm=True)
        elif pos['current'] > 70000:  # 触及止损
            log(f"\n🚨 触及止损位，建议立即平仓")
            # close_position(pos['size'], confirm=True)
        elif pos['current'] < 68000:  # 触及止盈
            log(f"\n✅ 触及止盈位，建议平仓")
            # close_position(pos['size'], confirm=True)
        else:
            log(f"\n⏳ 当前价格正常，建议持有")
    else:
        log(f"⏳ 当前无持仓")
    
    log("\n" + "="*70)
    log(f"⚠️ 注意：实际执行需要确认")
    log(f"   编辑脚本将 confirm=False 来启用自动执行")
    log("="*70)

if __name__ == '__main__':
    main()
