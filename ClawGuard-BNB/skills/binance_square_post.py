#!/usr/bin/env python3
"""
Binance Square 自动发帖技能
联动 ClawGuard-BNB 生成专业交易分析
"""
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta

import os

# Binance Square API Key
SQUARE_API_KEY = os.getenv('SQUARE_API_KEY', '')

# ClawGuard-BNB API 配置
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
PROXY = os.getenv('PROXY_URL', 'http://127.0.0.1:7890')

def sign(params):
    """生成币安签名"""
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(BINANCE_API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_market_data():
    """获取市场数据"""
    try:
        # BTC 价格
        r = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            proxies={'http': PROXY, 'https': PROXY},
            headers={'X-MBX-APIKEY': BINANCE_API_KEY},
            timeout=5
        )
        btc_price = float(r.json()['price']) if r.status_code == 200 else 0
        
        # 24 小时行情
        r = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            proxies={'http': PROXY, 'https': PROXY},
            headers={'X-MBX-APIKEY': BINANCE_API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            return {
                'price': btc_price,
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
    except Exception as e:
        print(f"获取市场数据失败：{e}")
    return None

def generate_analysis_post(market_data):
    """生成交易分析帖子"""
    if not market_data:
        return None
    
    now = datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M')
    
    # 分析内容
    if market_data['change_24h'] > 2:
        sentiment = "🐂 多头强势"
    elif market_data['change_24h'] < -2:
        sentiment = "🐻 空头主导"
    else:
        sentiment = "⚖️ 震荡整理"
    
    post = f"""📊 BTC/USDT 市场分析报告
⏰ {time_str}

💰 当前价格：${market_data['price']:,.2f}
📈 24h 涨跌：{market_data['change_24h']:+.2f}%
📊 24h 最高：${market_data['high_24h']:,.2f}
📉 24h 最低：${market_data['low_24h']:,.2f}
📊 24h 成交量：{market_data['volume']:,.2f} BTC

🎯 市场情绪：{sentiment}

💡 技术面分析：
- 价格运行在 24h 区间 {'上半部分' if market_data['price'] > (market_data['high_24h'] + market_data['low_24h']) / 2 else '下半部分'}
- 波动率：{((market_data['high_24h'] - market_data['low_24h']) / market_data['low_24h'] * 100):.2f}%
- 成交量：{'放大' if market_data['volume'] > 30000 else '正常'}

📋 交易策略：
1. 短线：关注 {'突破' if market_data['change_24h'] > 0 else '回调'} 机会
2. 中线：等待明确信号
3. 止损：设置合理止损位

⚠️ 风险提示：
- 加密货币波动较大
- 请做好风险控制
- 本分析仅供参考，不构成投资建议

#BTC #比特币 #交易分析 #加密货币 #Binance"""
    
    return post

def post_to_square(content):
    """发布到币安广场"""
    url = 'https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add'
    
    headers = {
        'X-Square-OpenAPI-Key': SQUARE_API_KEY,
        'Content-Type': 'application/json',
        'clienttype': 'binanceSkill'
    }
    
    data = {
        'bodyTextOnly': content
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 200:
            result = r.json()
            if result.get('code') == '000000':
                post_id = result.get('data', {}).get('id', 'unknown')
                print(f"✅ 发布成功！帖子 ID: {post_id}")
                print(f"🔗 链接：https://www.binance.com/square/post/{post_id}")
                return True, post_id
            else:
                print(f"❌ 发布失败：{result.get('message', 'Unknown error')}")
                return False, None
        else:
            print(f"❌ HTTP 错误：{r.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ 异常：{e}")
        return False, None

def main():
    """主函数"""
    print("="*60)
    print("📝 Binance Square 自动发帖")
    print("="*60)
    
    # 获取市场数据
    print("\n📊 获取市场数据...")
    market_data = get_market_data()
    
    if market_data:
        print(f"✅ BTC 价格：${market_data['price']:,.2f}")
        print(f"✅ 24h 涨跌：{market_data['change_24h']:+.2f}%")
        
        # 生成分析
        print("\n📝 生成交易分析...")
        post_content = generate_analysis_post(market_data)
        
        if post_content:
            print(f"\n📋 帖子内容预览：")
            print("-"*60)
            print(post_content[:200] + "...")
            print("-"*60)
            
            # 发布
            print("\n🚀 发布到币安广场...")
            success, post_id = post_to_square(post_content)
            
            if success:
                print(f"\n✅ 发布完成！")
                return True
            else:
                print(f"\n❌ 发布失败")
                return False
        else:
            print("❌ 生成分析失败")
            return False
    else:
        print("❌ 获取市场数据失败")
        return False

if __name__ == '__main__':
    main()
