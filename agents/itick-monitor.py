#!/usr/bin/env python3
"""
iTick 金融数据监控服务
监控股票/期货行情，推送异常波动提醒
"""

import requests
import time
import json
from datetime import datetime

API_BASE = "https://api.itick.org"
TOKEN = "f8301b1e35b044baab61731d238ba5aa7339a64bdb6342d1b3c2b8e190599283"

# 监控列表
WATCHLIST = [
    {"region": "US", "code": "AAPL", "name": "苹果"},
    {"region": "US", "code": "NVDA", "name": "英伟达"},
    {"region": "US", "code": "TSLA", "name": "特斯拉"},
    {"region": "CN", "code": "600519.SH", "name": "贵州茅台"},
]

# 异常波动阈值
VOLATILITY_THRESHOLD = 5.0  # 涨跌幅超过 5% 告警

def get_quote(region, code):
    """获取股票行情"""
    url = f"{API_BASE}/stock/quote?region={region}&code={code}"
    headers = {"accept": "application/json", "token": TOKEN}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
    except Exception as e:
        print(f"[ERROR] {e}")
    return None

def check_alert(quote):
    """检查是否触发告警"""
    if not quote:
        return False
    
    chp = float(quote.get("chp", 0))  # 涨跌幅%
    return abs(chp) >= VOLATILITY_THRESHOLD

def format_alert(quote, stock_info):
    """格式化告警消息"""
    return f"""
🚨 **股价异常波动提醒**

📈 {stock_info['name']} ({stock_info['code']})
当前价：${quote['p']}
涨跌幅：{quote['chp']:+.2f}% ({quote['ch']:+.2f})
成交量：{quote['v']:,}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

def monitor_loop():
    """主监控循环"""
    print(f"[INFO] iTick 监控服务启动 - {datetime.now()}")
    print(f"[INFO] 监控标的：{len(WATCHLIST)} 个")
    
    while True:
        for stock in WATCHLIST:
            quote = get_quote(stock["region"], stock["code"])
            if quote:
                print(f"[{stock['name']}] ${quote['p']} ({quote['chp']:+.2f}%)")
                
                if check_alert(quote):
                    alert_msg = format_alert(quote, stock)
                    print(alert_msg)
                    # TODO: 发送告警到 Telegram/微信
        
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n[INFO] 监控服务已停止")
