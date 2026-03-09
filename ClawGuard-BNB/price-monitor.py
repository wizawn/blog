#!/usr/bin/env python3
"""
ClawGuard-BNB 价格监控告警
监控 BTC, ETH, XAG, XAU 价格，涨跌幅超过 0.3% 自动告警
"""

import requests
import time
from datetime import datetime

# 配置
SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'XAG': 'XAGUSD',  # 白银（使用备用 API）
    'XAU': 'XAUUSD'   # 黄金（使用备用 API）
}

# 贵金属使用备用 API（https://api.metals.live）
METALS_API = 'https://api.metals.live/v1/spot'

# 告警阈值（涨跌幅百分比）
ALERT_THRESHOLD = 0.3  # 0.3%

# 币安 API
BASE_URL = 'https://api.binance.com'
PROXY = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

# 存储上次价格
last_prices = {}

def get_price(name, symbol):
    """获取当前价格"""
    try:
        # 加密货币使用币安 API
        if name in ['BTC', 'ETH']:
            response = requests.get(
                f'{BASE_URL}/api/v3/ticker/price?symbol={symbol}',
                proxies=PROXY,
                timeout=10
            )
            if response.status_code == 200:
                return float(response.json()['price'])
        # 贵金属使用备用 API
        elif name in ['XAG', 'XAU']:
            response = requests.get(
                f'{METALS_API}',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for metal in data['data']:
                        if metal.get('symbol') == symbol:
                            return float(metal.get('price', 0))
    except Exception as e:
        print(f"❌ 获取 {name} 价格失败：{e}")
    return None

def check_alert(symbol, current_price):
    """检查是否需要告警"""
    if symbol not in last_prices:
        last_prices[symbol] = current_price
        return False
    
    last_price = last_prices[symbol]
    change_percent = ((current_price - last_price) / last_price) * 100
    
    if abs(change_percent) >= ALERT_THRESHOLD:
        direction = "📈" if change_percent > 0 else "📉"
        print(f"\n{'='*60}")
        print(f"{direction} **价格告警** {symbol}")
        print(f"{'='*60}")
        print(f"当前价格：${current_price:,.2f}")
        print(f"上次价格：${last_price:,.2f}")
        print(f"涨跌幅度：{change_percent:+.3f}%")
        print(f"告警阈值：±{ALERT_THRESHOLD}%")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 更新价格
        last_prices[symbol] = current_price
        return True
    
    # 更新价格
    last_prices[symbol] = current_price
    return False

def main():
    """主循环"""
    print("=" * 60)
    print("🔍 ClawGuard-BNB 价格监控")
    print("=" * 60)
    print(f"监控目标：{', '.join(SYMBOLS.keys())}")
    print(f"告警阈值：±{ALERT_THRESHOLD}%")
    print(f"检查间隔：60 秒")
    print("=" * 60)
    print("\n开始监控...\n")
    
    # 初始化价格
    print("初始化价格...")
    for name, symbol in SYMBOLS.items():
        price = get_price(name, symbol)
        if price:
            last_prices[name] = price
            print(f"  {name}: ${price:,.2f}")
        time.sleep(0.5)
    
    print("\n✅ 初始化完成，开始监控...\n")
    
    # 主循环
    try:
        while True:
            for name, symbol in SYMBOLS.items():
                price = get_price(name, symbol)
                if price:
                    check_alert(name, price)
            
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        print("\n\n⚠️ 监控已停止")

if __name__ == '__main__':
    main()
