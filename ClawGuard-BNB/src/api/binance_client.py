#!/usr/bin/env python3
"""
增强版币安API客户端
特性：
- 安全的签名生成
- 请求限速保护
- 缓存机制
- 连接池
- 完善的错误处理
- SSL证书验证
"""

import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
from urllib.parse import urlencode
from functools import lru_cache
import logging

from ..config.config_manager import ConfigManager
from ..security.input_validator import InputValidator, validate_trade_params, ValidationError
from ..network.proxy_manager import ProxyManager


class BinanceAPIError(Exception):
    """币安API错误"""

    def __init__(self, code: int, message: str, response: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.response = response
        super().__init__(f"[{code}] {message}")


class RateLimiter:
    """请求限速器"""

    def __init__(self, max_requests: int = 1200, time_window: int = 60):
        """
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        """如果超过限速，等待"""
        now = time.time()

        # 清理过期记录
        self.requests = [t for t in self.requests if now - t < self.time_window]

        # 检查是否超限
        if len(self.requests) >= self.max_requests:
            oldest = self.requests[0]
            wait_time = self.time_window - (now - oldest)
            if wait_time > 0:
                logging.warning(f"触发限速，等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
                self.requests = []

        # 记录本次请求
        self.requests.append(now)


class BinanceClient:
    """增强版币安API客户端"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: Optional[bool] = None, config: Optional[ConfigManager] = None):
        """
        初始化客户端

        Args:
            api_key: API Key（可选，从配置读取）
            api_secret: API Secret（可选，从配置读取）
            testnet: 是否使用测试网（可选，从配置读取）
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
            self.base_url = self.config.get('binance.testnet_url', 'https://testnet.binance.vision')
        else:
            self.base_url = self.config.get('binance.base_url', 'https://api.binance.com')

        # 初始化代理管理器
        proxy_config = self.config.get_proxy_config()
        self.proxy_manager = ProxyManager(proxy_config)

        # 初始化Session（连接池）
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
                self.logger.info(f"已启用代理: {self.proxy_manager.current_proxy}")

        # 初始化限速器
        self.rate_limiter = RateLimiter(
            max_requests=1200,  # 币安限制：1200请求/分钟
            time_window=60
        )

        # 初始化验证器
        self.validator = InputValidator()

        # 缓存配置
        self.cache_enabled = self.config.get('cache.enabled', True)
        self.cache_ttl = self.config.get('cache.ttl_seconds', 3)
        self._price_cache = {}

        # 日志
        self.logger = logging.getLogger(__name__)

    def _generate_signature(self, params: Dict) -> str:
        """
        生成API签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        # 按键排序（确保签名一致性）
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 signed: bool = False) -> Dict:
        """
        发送API请求

        Args:
            method: HTTP方法
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名

        Returns:
            响应数据

        Raises:
            BinanceAPIError: API错误
        """
        if params is None:
            params = {}

        # 限速检查
        self.rate_limiter.wait_if_needed()

        # 签名
        if signed:
            if not self.api_key or not self.api_secret:
                raise BinanceAPIError(-1, "需要API密钥才能执行此操作")

            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        url = f"{self.base_url}{endpoint}"

        try:
            # 发送请求
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10, verify=True)
            elif method == 'POST':
                response = self.session.post(url, data=params, timeout=10, verify=True)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=10, verify=True)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            # 检查HTTP状态码
            if response.status_code == 429:
                raise BinanceAPIError(-1003, "请求过于频繁，已触发限速")

            response.raise_for_status()

            # 解析响应
            data = response.json()

            # 检查API错误
            if isinstance(data, dict) and 'code' in data:
                raise BinanceAPIError(
                    data.get('code', -1),
                    data.get('msg', '未知错误'),
                    data
                )

            return data

        except requests.exceptions.Timeout:
            raise BinanceAPIError(-1001, "请求超时，请检查网络连接")
        except requests.exceptions.SSLError as e:
            raise BinanceAPIError(-1, f"SSL证书验证失败: {e}")
        except requests.exceptions.ConnectionError as e:
            raise BinanceAPIError(-1, f"网络连接失败: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    raise BinanceAPIError(
                        error_data.get('code', -1),
                        error_data.get('msg', str(e)),
                        error_data
                    )
                except:
                    pass
            raise BinanceAPIError(-1, f"HTTP错误: {e}")
        except BinanceAPIError:
            raise
        except Exception as e:
            self.logger.error(f"未知错误: {e}", exc_info=True)
            raise BinanceAPIError(-1, f"未知错误: {e}")

    # ============= 行情查询 =============

    def get_ticker_price(self, symbol: str) -> Dict:
        """
        获取单个交易对价格（带缓存）

        Args:
            symbol: 交易对

        Returns:
            {"symbol": "BTCUSDT", "price": "68234.50"}
        """
        # 验证输入
        valid, msg = self.validator.validate_symbol(symbol)
        if not valid:
            raise ValidationError(msg)

        symbol = symbol.upper()

        # 检查缓存
        if self.cache_enabled:
            cache_key = f"price:{symbol}"
            if cache_key in self._price_cache:
                cached_data, cached_time = self._price_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return cached_data

        # 请求数据
        data = self._request('GET', '/api/v3/ticker/price', {'symbol': symbol})

        # 更新缓存
        if self.cache_enabled:
            self._price_cache[cache_key] = (data, time.time())

        return data

    def get_24h_ticker(self, symbol: str) -> Dict:
        """
        获取24小时价格变化

        Args:
            symbol: 交易对

        Returns:
            24小时统计数据
        """
        valid, msg = self.validator.validate_symbol(symbol)
        if not valid:
            raise ValidationError(msg)

        return self._request('GET', '/api/v3/ticker/24hr', {'symbol': symbol.upper()})

    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List:
        """
        获取K线数据

        Args:
            symbol: 交易对
            interval: 时间周期
            limit: 数据条数

        Returns:
            K线数据列表
        """
        # 验证输入
        valid, msg = self.validator.validate_symbol(symbol)
        if not valid:
            raise ValidationError(msg)

        valid, msg = self.validator.validate_interval(interval)
        if not valid:
            raise ValidationError(msg)

        valid, msg = self.validator.validate_limit(limit)
        if not valid:
            raise ValidationError(msg)

        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        return self._request('GET', '/api/v3/klines', params)

    # ============= 账户信息 =============

    def get_account(self) -> Dict:
        """获取账户信息"""
        return self._request('GET', '/api/v3/account', signed=True)

    def get_balance(self, asset: str = "USDT") -> Dict:
        """
        获取指定资产余额

        Args:
            asset: 资产名称

        Returns:
            {"asset": "USDT", "free": 1000.0, "locked": 0.0, "total": 1000.0}
        """
        account = self.get_account()

        for balance in account.get('balances', []):
            if balance['asset'] == asset.upper():
                return {
                    'asset': asset.upper(),
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': float(balance['free']) + float(balance['locked'])
                }

        raise BinanceAPIError(-1, f'未找到资产 {asset}')

    # ============= 交易执行 =============

    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: Optional[float] = None,
                    quote_order_qty: Optional[float] = None,
                    price: Optional[float] = None) -> Dict:
        """
        下单交易

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            order_type: 类型 (MARKET/LIMIT)
            quantity: 数量
            quote_order_qty: 金额（市价单）
            price: 价格（限价单）

        Returns:
            订单信息
        """
        # 验证参数
        amount = quantity or quote_order_qty
        validated = validate_trade_params(symbol, side, amount, order_type, price)

        params = {
            'symbol': validated['symbol'],
            'side': validated['side'],
            'type': validated['order_type'],
        }

        if quantity:
            params['quantity'] = quantity
        if quote_order_qty:
            params['quoteOrderQty'] = quote_order_qty
        if price:
            params['price'] = price
        if order_type == 'LIMIT':
            params['timeInForce'] = 'GTC'

        return self._request('POST', '/api/v3/order', params, signed=True)

    def market_buy(self, symbol: str, quote_order_qty: float) -> Dict:
        """市价买入"""
        return self.place_order(symbol, 'BUY', 'MARKET', quote_order_qty=quote_order_qty)

    def market_sell(self, symbol: str, quantity: float) -> Dict:
        """市价卖出"""
        return self.place_order(symbol, 'SELL', 'MARKET', quantity=quantity)

    # ============= 工具方法 =============

    def test_connectivity(self) -> Dict:
        """测试连接"""
        return self._request('GET', '/api/v3/ping')

    def get_server_time(self) -> Dict:
        """获取服务器时间"""
        return self._request('GET', '/api/v3/time')


# ============= 使用示例 =============

if __name__ == "__main__":
    import sys
    sys.path.append('..')

    # 初始化客户端
    client = BinanceClient()

    print("=" * 50)
    print("增强版币安API客户端")
    print("=" * 50)
    print()

    # 测试连接
    print("🔗 测试连接...")
    try:
        ping = client.test_connectivity()
        print("✅ 连接成功")
    except BinanceAPIError as e:
        print(f"❌ 连接失败: {e}")

    # 获取价格
    print("\n💰 获取价格...")
    try:
        btc = client.get_ticker_price("BTCUSDT")
        print(f"BTC: ${btc['price']}")
    except (BinanceAPIError, ValidationError) as e:
        print(f"❌ 获取失败: {e}")

    print("\n" + "=" * 50)
