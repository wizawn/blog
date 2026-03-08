#!/usr/bin/env python3
"""
WebSocket 实时行情模块
提供实时价格推送、深度数据、交易流等
"""

import asyncio
import json
import websockets
from typing import Callable, Dict, List, Optional
from datetime import datetime
import threading

from ..utils.logger import get_logger

logger = get_logger("websocket")


class BinanceWebSocket:
    """币安WebSocket客户端"""

    def __init__(self, testnet: bool = False):
        """
        初始化WebSocket客户端

        Args:
            testnet: 是否使用测试网
        """
        self.testnet = testnet
        self.base_url = "wss://testnet.binance.vision/ws" if testnet else "wss://stream.binance.com:9443/ws"
        self.connections = {}
        self.callbacks = {}
        self.running = False

    async def _connect(self, stream: str, callback: Callable):
        """
        连接到WebSocket流

        Args:
            stream: 流名称
            callback: 回调函数
        """
        url = f"{self.base_url}/{stream}"
        logger.info(f"连接到WebSocket: {url}")

        try:
            async with websockets.connect(url) as websocket:
                self.connections[stream] = websocket
                logger.info(f"WebSocket连接成功: {stream}")

                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)

                        # 调用回调函数
                        if callback:
                            try:
                                callback(data)
                            except Exception as e:
                                logger.error(f"回调函数执行失败: {e}", exc_info=True)

                    except asyncio.TimeoutError:
                        # 发送ping保持连接
                        await websocket.ping()
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning(f"WebSocket连接关闭: {stream}")
                        break
                    except Exception as e:
                        logger.error(f"接收消息失败: {e}", exc_info=True)
                        break

        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}", exc_info=True)
        finally:
            if stream in self.connections:
                del self.connections[stream]

    def subscribe_ticker(self, symbol: str, callback: Callable):
        """
        订阅实时价格

        Args:
            symbol: 交易对（如 BTCUSDT）
            callback: 回调函数，接收价格数据

        Example:
            def on_price(data):
                print(f"价格: {data['c']}")

            ws.subscribe_ticker("BTCUSDT", on_price)
        """
        stream = f"{symbol.lower()}@ticker"
        self.callbacks[stream] = callback

        def wrapped_callback(data):
            """包装回调，提取关键信息"""
            price_data = {
                'symbol': data.get('s'),
                'price': float(data.get('c', 0)),  # 最新价格
                'change': float(data.get('p', 0)),  # 价格变化
                'change_percent': float(data.get('P', 0)),  # 变化百分比
                'high': float(data.get('h', 0)),  # 24h最高
                'low': float(data.get('l', 0)),  # 24h最低
                'volume': float(data.get('v', 0)),  # 24h成交量
                'timestamp': data.get('E', 0)  # 事件时间
            }
            callback(price_data)

        asyncio.create_task(self._connect(stream, wrapped_callback))
        logger.info(f"订阅实时价格: {symbol}")

    def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """
        订阅K线数据

        Args:
            symbol: 交易对
            interval: 时间间隔（1m, 5m, 15m, 1h, 4h, 1d等）
            callback: 回调函数

        Example:
            def on_kline(data):
                print(f"K线: {data}")

            ws.subscribe_kline("BTCUSDT", "1m", on_kline)
        """
        stream = f"{symbol.lower()}@kline_{interval}"
        self.callbacks[stream] = callback

        def wrapped_callback(data):
            """包装回调，提取K线信息"""
            kline = data.get('k', {})
            kline_data = {
                'symbol': kline.get('s'),
                'interval': kline.get('i'),
                'open_time': kline.get('t'),
                'close_time': kline.get('T'),
                'open': float(kline.get('o', 0)),
                'high': float(kline.get('h', 0)),
                'low': float(kline.get('l', 0)),
                'close': float(kline.get('c', 0)),
                'volume': float(kline.get('v', 0)),
                'is_closed': kline.get('x', False)  # K线是否完成
            }
            callback(kline_data)

        asyncio.create_task(self._connect(stream, wrapped_callback))
        logger.info(f"订阅K线数据: {symbol} {interval}")

    def subscribe_depth(self, symbol: str, levels: int, callback: Callable):
        """
        订阅深度数据（订单簿）

        Args:
            symbol: 交易对
            levels: 深度级别（5, 10, 20）
            callback: 回调函数

        Example:
            def on_depth(data):
                print(f"买一: {data['bids'][0]}")
                print(f"卖一: {data['asks'][0]}")

            ws.subscribe_depth("BTCUSDT", 5, on_depth)
        """
        stream = f"{symbol.lower()}@depth{levels}"
        self.callbacks[stream] = callback

        def wrapped_callback(data):
            """包装回调，提取深度信息"""
            depth_data = {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in data.get('bids', [])],
                'asks': [[float(price), float(qty)] for price, qty in data.get('asks', [])],
                'timestamp': data.get('E', 0)
            }
            callback(depth_data)

        asyncio.create_task(self._connect(stream, wrapped_callback))
        logger.info(f"订阅深度数据: {symbol} (级别: {levels})")

    def subscribe_trades(self, symbol: str, callback: Callable):
        """
        订阅实时成交

        Args:
            symbol: 交易对
            callback: 回调函数

        Example:
            def on_trade(data):
                print(f"成交: {data['price']} x {data['quantity']}")

            ws.subscribe_trades("BTCUSDT", on_trade)
        """
        stream = f"{symbol.lower()}@trade"
        self.callbacks[stream] = callback

        def wrapped_callback(data):
            """包装回调，提取成交信息"""
            trade_data = {
                'symbol': data.get('s'),
                'price': float(data.get('p', 0)),
                'quantity': float(data.get('q', 0)),
                'time': data.get('T', 0),
                'is_buyer_maker': data.get('m', False)  # 买方是否为挂单方
            }
            callback(trade_data)

        asyncio.create_task(self._connect(stream, wrapped_callback))
        logger.info(f"订阅实时成交: {symbol}")

    def start(self):
        """启动WebSocket连接"""
        self.running = True
        logger.info("WebSocket服务启动")

    def stop(self):
        """停止WebSocket连接"""
        self.running = False
        logger.info("WebSocket服务停止")

        # 关闭所有连接
        for stream, ws in self.connections.items():
            asyncio.create_task(ws.close())

    def run_forever(self):
        """在新线程中运行WebSocket"""
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.start()
            loop.run_forever()

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        logger.info("WebSocket在后台线程运行")


class PriceMonitor:
    """价格监控器"""

    def __init__(self, testnet: bool = False):
        """
        初始化价格监控器

        Args:
            testnet: 是否使用测试网
        """
        self.ws = BinanceWebSocket(testnet)
        self.alerts = {}  # {symbol: [(condition, threshold, callback)]}
        self.current_prices = {}

    def add_alert(self, symbol: str, condition: str, threshold: float, callback: Callable):
        """
        添加价格告警

        Args:
            symbol: 交易对
            condition: 条件（'above', 'below', 'change_percent'）
            threshold: 阈值
            callback: 触发时的回调函数

        Example:
            def on_alert(symbol, price, threshold):
                print(f"{symbol} 价格 {price} 触发告警（阈值: {threshold}）")

            monitor.add_alert("BTCUSDT", "above", 70000, on_alert)
        """
        if symbol not in self.alerts:
            self.alerts[symbol] = []

        self.alerts[symbol].append({
            'condition': condition,
            'threshold': threshold,
            'callback': callback,
            'triggered': False
        })

        # 订阅价格
        if symbol not in self.current_prices:
            self.ws.subscribe_ticker(symbol, lambda data: self._check_alerts(data))

        logger.info(f"添加价格告警: {symbol} {condition} {threshold}")

    def _check_alerts(self, price_data: Dict):
        """检查价格告警"""
        symbol = price_data['symbol']
        price = price_data['price']
        change_percent = price_data['change_percent']

        self.current_prices[symbol] = price

        if symbol not in self.alerts:
            return

        for alert in self.alerts[symbol]:
            if alert['triggered']:
                continue

            condition = alert['condition']
            threshold = alert['threshold']
            callback = alert['callback']

            triggered = False

            if condition == 'above' and price >= threshold:
                triggered = True
            elif condition == 'below' and price <= threshold:
                triggered = True
            elif condition == 'change_percent':
                if abs(change_percent) >= threshold:
                    triggered = True

            if triggered:
                alert['triggered'] = True
                logger.info(f"价格告警触发: {symbol} {condition} {threshold}")

                try:
                    callback(symbol, price, threshold)
                except Exception as e:
                    logger.error(f"告警回调执行失败: {e}", exc_info=True)

    def start(self):
        """启动监控"""
        self.ws.run_forever()
        logger.info("价格监控器启动")

    def stop(self):
        """停止监控"""
        self.ws.stop()
        logger.info("价格监控器停止")


# 便捷函数
def create_websocket(testnet: bool = False) -> BinanceWebSocket:
    """创建WebSocket客户端"""
    return BinanceWebSocket(testnet)


def create_price_monitor(testnet: bool = False) -> PriceMonitor:
    """创建价格监控器"""
    return PriceMonitor(testnet)


if __name__ == "__main__":
    # 测试WebSocket
    import time

    def on_price(data):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"{data['symbol']}: ${data['price']:.2f} "
              f"({data['change_percent']:+.2f}%)")

    def on_alert(symbol, price, threshold):
        print(f"\n🚨 告警触发！")
        print(f"   {symbol} 价格: ${price:.2f}")
        print(f"   阈值: ${threshold:.2f}\n")

    # 创建价格监控器
    monitor = create_price_monitor(testnet=True)

    # 添加告警
    monitor.add_alert("BTCUSDT", "above", 70000, on_alert)
    monitor.add_alert("BTCUSDT", "below", 65000, on_alert)

    # 启动监控
    monitor.start()

    print("价格监控器已启动，按 Ctrl+C 退出...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监控...")
        monitor.stop()
