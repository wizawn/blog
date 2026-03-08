#!/usr/bin/env python3
"""
ClawGuard-BNB 币安组合保证金交易模块
支持 UM/CM 合约、杠杆账户交易
文档：https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/trade
"""

import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, Any

class BinancePortfolioMargin:
    """币安组合保证金交易客户端"""
    
    def __init__(self, api_key: str, api_secret: str, proxy: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = {'http': proxy, 'https': proxy} if proxy else None
        # 组合保证金 API 使用 papi.binance.com
        self.base_url = 'https://papi.binance.com'
        
    def _sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, signed: bool = False):
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            params['signature'] = self._sign(params)
        
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            proxies=self.proxy,
            timeout=10
        )
        
        # 错误处理
        if response.status_code != 200:
            print(f"❌ 请求失败：{response.status_code}")
            print(f"响应：{response.text}")
            return {'error': response.status_code, 'msg': response.text}
        
        try:
            return response.json()
        except:
            print(f"❌ JSON 解析失败：{response.text[:200]}")
            return {'error': 'JSON decode error', 'msg': response.text[:200]}
    
    # ==================== UM 合约交易 ====================
    
    def um_order(self, symbol: str, side: str, type_: str, 
                 quantity: Optional[float] = None,
                 price: Optional[float] = None,
                 positionSide: str = 'BOTH',
                 timeInForce: str = 'GTC',
                 reduceOnly: bool = False,
                 newClientOrderId: str = None) -> Dict:
        """
        UM 合约下单
        
        Args:
            symbol: 交易对，如 BTCUSDT
            side: 方向，BUY/SELL
            type_: 类型，LIMIT/MARKET
            quantity: 数量
            price: 价格（LIMIT 单必填）
            positionSide: 持仓方向，BOTH/LONG/SHORT
            timeInForce: 有效方式，GTC/IOC/FOK/GTD
            reduceOnly: 是否只减仓
            newClientOrderId: 自定义订单 ID
            
        Returns:
            订单响应
        """
        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': positionSide,
            'type': type_,
            'timeInForce': timeInForce,
            'reduceOnly': str(reduceOnly).lower(),
        }
        
        if quantity:
            params['quantity'] = quantity
        if price:
            params['price'] = price
        if newClientOrderId:
            params['newClientOrderId'] = newClientOrderId
            
        return self._request('POST', '/papi/v1/um/order', params, signed=True)
    
    def um_market_buy(self, symbol: str, quantity: float, **kwargs) -> Dict:
        """UM 市价买入"""
        return self.um_order(symbol, 'BUY', 'MARKET', quantity=quantity, **kwargs)
    
    def um_market_sell(self, symbol: str, quantity: float, **kwargs) -> Dict:
        """UM 市价卖出"""
        return self.um_order(symbol, 'SELL', 'MARKET', quantity=quantity, **kwargs)
    
    def um_limit_buy(self, symbol: str, quantity: float, price: float, **kwargs) -> Dict:
        """UM 限价买入"""
        return self.um_order(symbol, 'BUY', 'LIMIT', quantity=quantity, price=price, **kwargs)
    
    def um_limit_sell(self, symbol: str, quantity: float, price: float, **kwargs) -> Dict:
        """UM 限价卖出"""
        return self.um_order(symbol, 'SELL', 'LIMIT', quantity=quantity, price=price, **kwargs)
    
    def um_cancel_order(self, symbol: str, orderId: int = None, origClientOrderId: str = None) -> Dict:
        """撤销 UM 订单"""
        params = {'symbol': symbol}
        if orderId:
            params['orderId'] = orderId
        if origClientOrderId:
            params['origClientOrderId'] = origClientOrderId
        return self._request('DELETE', '/papi/v1/um/order', params, signed=True)
    
    def um_query_order(self, symbol: str, orderId: int = None, origClientOrderId: str = None) -> Dict:
        """查询 UM 订单"""
        params = {'symbol': symbol}
        if orderId:
            params['orderId'] = orderId
        if origClientOrderId:
            params['origClientOrderId'] = origClientOrderId
        return self._request('GET', '/papi/v1/um/order', params, signed=True)
    
    def um_open_orders(self, symbol: str = None) -> Dict:
        """查询当前 UM 挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/papi/v1/um/openOrders', params, signed=True)
    
    def um_cancel_all_orders(self, symbol: str) -> Dict:
        """撤销全部 UM 订单"""
        return self._request('DELETE', '/papi/v1/um/allOpenOrders', {'symbol': symbol}, signed=True)
    
    # ==================== CM 合约交易 ====================
    
    def cm_order(self, symbol: str, side: str, type_: str,
                 quantity: Optional[float] = None,
                 price: Optional[float] = None,
                 positionSide: str = 'BOTH',
                 timeInForce: str = 'GTC',
                 reduceOnly: bool = False) -> Dict:
        """
        CM 合约下单
        
        Args:
            symbol: 交易对，如 BTCUSD_PERP
            side: 方向，BUY/SELL
            type_: 类型，LIMIT/MARKET
            quantity: 数量（张）
            price: 价格
            positionSide: 持仓方向
            timeInForce: 有效方式
            reduceOnly: 只减仓
            
        Returns:
            订单响应
        """
        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': positionSide,
            'type': type_,
            'timeInForce': timeInForce,
            'reduceOnly': str(reduceOnly).lower(),
        }
        
        if quantity:
            params['quantity'] = quantity
        if price:
            params['price'] = price
            
        return self._request('POST', '/papi/v1/cm/order', params, signed=True)
    
    def cm_market_buy(self, symbol: str, quantity: float, **kwargs) -> Dict:
        """CM 市价买入"""
        return self.cm_order(symbol, 'BUY', 'MARKET', quantity=quantity, **kwargs)
    
    def cm_market_sell(self, symbol: str, quantity: float, **kwargs) -> Dict:
        """CM 市价卖出"""
        return self.cm_order(symbol, 'SELL', 'MARKET', quantity=quantity, **kwargs)
    
    # ==================== 杠杆账户交易 ====================
    
    def margin_order(self, symbol: str, side: str, type_: str,
                     quantity: Optional[float] = None,
                     price: Optional[float] = None,
                     timeInForce: str = 'GTC',
                     isIsolated: bool = False) -> Dict:
        """
        杠杆账户下单
        
        Args:
            symbol: 交易对
            side: 方向，BUY/SELL
            type_: 类型，LIMIT/MARKET
            quantity: 数量
            price: 价格
            timeInForce: 有效方式
            isIsolated: 是否逐仓杠杆
            
        Returns:
            订单响应
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': type_,
            'timeInForce': timeInForce,
            'isIsolated': str(isIsolated).lower(),
        }
        
        if quantity:
            params['quantity'] = quantity
        if price:
            params['price'] = price
            
        return self._request('POST', '/papi/v1/margin/order', params, signed=True)
    
    def margin_borrow(self, asset: str, amount: float, isIsolated: bool = False, symbol: str = None) -> Dict:
        """
        杠杆账户借贷
        
        Args:
            asset: 币种，如 USDT
            amount: 借入数量
            isIsolated: 是否逐仓
            symbol: 逐仓交易对（逐仓模式必填）
            
        Returns:
            借入响应
        """
        params = {
            'asset': asset,
            'amount': amount,
            'isIsolated': str(isIsolated).lower(),
        }
        
        if isIsolated and symbol:
            params['symbol'] = symbol
            
        return self._request('POST', '/papi/v1/margin/loan', params, signed=True)
    
    def margin_repay(self, asset: str, amount: float, isIsolated: bool = False, symbol: str = None) -> Dict:
        """
        杠杆账户归还借贷
        
        Args:
            asset: 币种
            amount: 归还数量
            isIsolated: 是否逐仓
            symbol: 逐仓交易对
            
        Returns:
            归还响应
        """
        params = {
            'asset': asset,
            'amount': amount,
            'isIsolated': str(isIsolated).lower(),
        }
        
        if isIsolated and symbol:
            params['symbol'] = symbol
            
        return self._request('POST', '/papi/v1/margin/repay', params, signed=True)
    
    # ==================== 账户信息 ====================
    
    def um_account(self) -> Dict:
        """查询 UM 合约账户信息"""
        return self._request('GET', '/papi/v1/um/account', signed=True)
    
    def cm_account(self) -> Dict:
        """查询 CM 合约账户信息"""
        return self._request('GET', '/papi/v1/cm/account', signed=True)
    
    def um_position(self, symbol: str = None) -> Dict:
        """查询 UM 持仓"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/papi/v1/um/positionRisk', params, signed=True)
    
    def cm_position(self, symbol: str = None) -> Dict:
        """查询 CM 持仓"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/papi/v1/cm/positionRisk', params, signed=True)
    
    def um_balance(self) -> Dict:
        """查询 UM 账户余额"""
        return self._request('GET', '/papi/v1/um/balance', signed=True)
    
    def cm_balance(self) -> Dict:
        """查询 CM 账户余额"""
        return self._request('GET', '/papi/v1/cm/balance', signed=True)
    
    def margin_account(self) -> Dict:
        """查询杠杆账户信息"""
        return self._request('GET', '/papi/v1/margin/account', signed=True)


# ==================== 使用示例 ====================
if __name__ == '__main__':
    # 配置
    API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
    API_SECRET = 'hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt'
    PROXY = 'http://127.0.0.1:7890'
    
    # 初始化客户端
    client = BinancePortfolioMargin(API_KEY, API_SECRET, PROXY)
    
    print("=" * 70)
    print("📊 币安组合保证金账户查询")
    print("=" * 70)
    
    # 查询 UM 账户
    print("\n💰 UM 合约账户:")
    um_account = client.um_account()
    if 'totalWalletBalance' in um_account:
        print(f"  总权益：{um_account['totalWalletBalance']} USDT")
        print(f"  可用余额：{um_account['availableBalance']} USDT")
    
    # 查询持仓
    print("\n📈 UM 持仓:")
    positions = client.um_position()
    for pos in positions:
        if float(pos.get('positionAmt', 0)) != 0:
            print(f"  {pos['symbol']}: {pos['positionAmt']} {pos['symbol'].replace('USDT', '')}")
    
    # 查询杠杆账户
    print("\n🏦 杠杆账户:")
    margin_account = client.margin_account()
    if 'totalAssetOfBtc' in margin_account:
        print(f"  总资产：{margin_account['totalAssetOfBtc']} BTC")
        print(f"  总负债：{margin_account['totalLiabilityOfBtc']} BTC")
    
    print("=" * 70)
