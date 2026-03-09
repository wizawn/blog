#!/usr/bin/env python3
"""
币安合约交易客户端
提供完整的期货交易功能
"""

import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
from urllib.parse import urlencode
import logging

from ..config.config_manager import ConfigManager
from ..network.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """币安合约交易客户端"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: Optional[bool] = None, config: Optional[ConfigManager] = None):
        """
        初始化合约客户端

        Args:
            api_key: API Key
            api_secret: API Secret
            testnet: 是否使用测试网
            config: 配置管理器
        """
        # 加载配置
        self.config = config or ConfigManager()

        # 获取API密钥
        if api_key and api_secret:
            self.api_key = api_key
            self.api_secret = api_secret
            self.testnet = testnet if testnet is not None else True
        else:
            creds = self.config.get_api_credentials()
            if creds:
                self.api_key = creds['api_key']
                self.api_secret = creds['api_secret']
                self.testnet = creds.get('testnet', True)
            else:
                self.api_key = ""
                self.api_secret = ""
                self.testnet = True

        # 设置基础URL
        if self.testnet:
            self.base_url = self.config.get('futures.testnet_url', 'https://testnet.binancefuture.com')
        else:
            self.base_url = self.config.get('futures.mainnet_url', 'https://fapi.binance.com')

        # 初始化代理管理器
        proxy_config = self.config.get_proxy_config()
        self.proxy_manager = ProxyManager(proxy_config)

        # 初始化Session
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        })

        # 配置代理
        if self.proxy_manager.enabled:
            proxy_dict = self.proxy_manager.get_proxy_dict()
            if proxy_dict:
                self.session.proxies.update(proxy_dict)
                logger.info(f"Futures client using proxy: {self.proxy_manager.current_proxy}")

        self.logger = logging.getLogger(__name__)

    def _generate_signature(self, params: Dict) -> str:
        """生成API签名"""
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 signed: bool = False) -> Dict:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, params=params, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    # ========== 账户相关 ==========

    def get_account_info(self) -> Dict:
        """获取合约账户信息"""
        return self._request('GET', '/fapi/v2/account', signed=True)

    def get_balance(self) -> List[Dict]:
        """获取账户余额"""
        return self._request('GET', '/fapi/v2/balance', signed=True)

    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取持仓风险

        Args:
            symbol: 交易对（可选）

        Returns:
            持仓风险列表
        """
        params = {}
        if symbol:
            params['symbol'] = symbol

        return self._request('GET', '/fapi/v2/positionRisk', params, signed=True)

    # ========== 杠杆和保证金 ==========

    def change_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        调整杠杆倍数

        Args:
            symbol: 交易对
            leverage: 杠杆倍数 (1-125)

        Returns:
            调整结果
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._request('POST', '/fapi/v1/leverage', params, signed=True)

    def change_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """
        更改保证金模式

        Args:
            symbol: 交易对
            margin_type: 保证金类型 (ISOLATED 或 CROSSED)

        Returns:
            更改结果
        """
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._request('POST', '/fapi/v1/marginType', params, signed=True)

    def change_position_margin(self, symbol: str, amount: float, type: int) -> Dict:
        """
        调整逐仓保证金

        Args:
            symbol: 交易对
            amount: 保证金数量
            type: 调整方向 (1=增加, 2=减少)

        Returns:
            调整结果
        """
        params = {
            'symbol': symbol,
            'amount': amount,
            'type': type
        }
        return self._request('POST', '/fapi/v1/positionMargin', params, signed=True)

    # ========== 市场数据 ==========

    def get_ticker_price(self, symbol: str) -> Dict:
        """获取最新价格"""
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/ticker/24hr', params)

    def get_funding_rate(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        获取资金费率历史

        Args:
            symbol: 交易对
            limit: 数量限制

        Returns:
            资金费率列表
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/fapi/v1/fundingRate', params)

    def get_mark_price(self, symbol: str) -> Dict:
        """获取标记价格"""
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/premiumIndex', params)

    # ========== 订单管理 ==========

    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None,
                   time_in_force: str = 'GTC', reduce_only: bool = False,
                   stop_price: Optional[float] = None) -> Dict:
        """
        下单

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET/STOP/TAKE_PROFIT)
            quantity: 数量
            price: 价格（限价单必需）
            time_in_force: 有效方式
            reduce_only: 只减仓
            stop_price: 触发价格

        Returns:
            订单结果
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'reduceOnly': reduce_only
        }

        if order_type == 'LIMIT':
            if not price:
                raise ValueError("LIMIT order requires price")
            params['price'] = price
            params['timeInForce'] = time_in_force

        if stop_price:
            params['stopPrice'] = stop_price

        return self._request('POST', '/fapi/v1/order', params, signed=True)

    def place_market_order(self, symbol: str, side: str, quantity: float,
                          reduce_only: bool = False) -> Dict:
        """市价单"""
        return self.place_order(symbol, side, 'MARKET', quantity, reduce_only=reduce_only)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         reduce_only: bool = False) -> Dict:
        """限价单"""
        return self.place_order(symbol, side, 'LIMIT', quantity, price, reduce_only=reduce_only)

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """取消订单"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('DELETE', '/fapi/v1/order', params, signed=True)

    def cancel_all_orders(self, symbol: str) -> Dict:
        """取消所有订单"""
        params = {'symbol': symbol}
        return self._request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict:
        """查询订单"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('GET', '/fapi/v1/order', params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取当前挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v1/openOrders', params, signed=True)

    def get_all_orders(self, symbol: str, limit: int = 500) -> List[Dict]:
        """获取所有订单"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/fapi/v1/allOrders', params, signed=True)

    # ========== 止损止盈 ==========

    def set_stop_loss(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """
        设置止损单

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            stop_price: 触发价格

        Returns:
            订单结果
        """
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type='STOP_MARKET',
            quantity=quantity,
            stop_price=stop_price,
            reduce_only=True
        )

    def set_take_profit(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """
        设置止盈单

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            stop_price: 触发价格

        Returns:
            订单结果
        """
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type='TAKE_PROFIT_MARKET',
            quantity=quantity,
            stop_price=stop_price,
            reduce_only=True
        )


# 使用示例
if __name__ == "__main__":
    client = BinanceFuturesClient()

    print("=" * 60)
    print("币安合约交易客户端测试")
    print("=" * 60)

    try:
        # 获取账户信息
        print("\n1. 获取账户信息:")
        account = client.get_account_info()
        print(f"总权益: {account.get('totalWalletBalance', 0)}")

        # 获取持仓
        print("\n2. 获取持仓:")
        positions = client.get_position_risk()
        for pos in positions:
            if float(pos.get('positionAmt', 0)) != 0:
                print(f"{pos['symbol']}: {pos['positionAmt']}")

        # 获取资金费率
        print("\n3. 获取BTC资金费率:")
        funding = client.get_funding_rate('BTCUSDT', limit=1)
        if funding:
            print(f"最新资金费率: {float(funding[0]['fundingRate']) * 100:.4f}%")

    except Exception as e:
        print(f"错误: {e}")
