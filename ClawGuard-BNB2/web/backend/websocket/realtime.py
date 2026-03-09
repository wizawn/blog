
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

"""
WebSocket 实时数据推送
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask_socketio import emit
from src.trading.unified_client import UnifiedTradingClient
import logging
import threading
import time

logger = logging.getLogger(__name__)


def register_events(socketio):
    """注册 WebSocket 事件"""

    @socketio.on('connect')
    def handle_connect():
        """客户端连接"""
        logger.info('客户端已连接')
        emit('connected', {'message': '连接成功'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开"""
        logger.info('客户端已断开')

    @socketio.on('subscribe_price')
    def handle_subscribe_price(data):
        """订阅价格推送"""
        symbols = data.get('symbols', ['BTCUSDT'])
        logger.info(f'订阅价格: {symbols}')

        def push_prices():
            """推送价格数据"""
            client = UnifiedTradingClient()
            while True:
                try:
                    prices = []
                    for symbol in symbols:
                        ticker = client.get_ticker_price(symbol)
                        prices.append({
                            'symbol': symbol,
                            'price': float(ticker.get('price', 0)),
                            'change_percent': float(ticker.get('priceChangePercent', 0))
                        })

                    socketio.emit('price_update', {'prices': prices})
                    time.sleep(2)  # 每2秒推送一次

                except Exception as e:
                    logger.error(f'推送价格失败: {e}')
                    time.sleep(5)

        # 启动推送线程
        thread = threading.Thread(target=push_prices, daemon=True)
        thread.start()

        emit('subscribed', {'symbols': symbols})

    @socketio.on('subscribe_account')
    def handle_subscribe_account():
        """订阅账户更新"""
        logger.info('订阅账户更新')

        def push_account():
            """推送账户数据"""
            client = UnifiedTradingClient()
            while True:
                try:
                    account = client.get_account_info()
                    socketio.emit('account_update', {'account': account})
                    time.sleep(5)  # 每5秒推送一次

                except Exception as e:
                    logger.error(f'推送账户失败: {e}')
                    time.sleep(10)

        # 启动推送线程
        thread = threading.Thread(target=push_account, daemon=True)
        thread.start()

        emit('subscribed', {'type': 'account'})

    @socketio.on('subscribe_orders')
    def handle_subscribe_orders():
        """订阅订单更新"""
        logger.info('订阅订单更新')

        def push_orders():
            """推送订单数据"""
            client = UnifiedTradingClient()
            while True:
                try:
                    orders = client.get_open_orders()
                    socketio.emit('orders_update', {'orders': orders})
                    time.sleep(3)  # 每3秒推送一次

                except Exception as e:
                    logger.error(f'推送订单失败: {e}')
                    time.sleep(5)

        # 启动推送线程
        thread = threading.Thread(target=push_orders, daemon=True)
        thread.start()

        emit('subscribed', {'type': 'orders'})
