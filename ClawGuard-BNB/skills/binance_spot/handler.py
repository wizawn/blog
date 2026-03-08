#!/usr/bin/env python3
"""
币安现货交易 Skill
提供价格查询、账户管理、订单操作等功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill
from src.api.binance_client import BinanceClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BinanceSpotSkill(BaseSkill):
    """币安现货交易 Skill"""

    def __init__(self):
        """初始化 Skill"""
        super().__init__()
        self.name = "binance_spot"
        self.version = "1.0.0"
        self.description = "币安现货交易 Skill，提供价格查询、账户管理、订单操作等功能"
        self.actions = [
            "query_price",
            "query_account",
            "query_balance",
            "place_order",
            "query_orders",
            "cancel_order"
        ]
        self.client = BinanceClient()

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行动作

        Args:
            action: 动作名称
            params: 参数字典

        Returns:
            执行结果
        """
        try:
            if action == "query_price":
                return self._query_price(params)
            elif action == "query_account":
                return self._query_account(params)
            elif action == "query_balance":
                return self._query_balance(params)
            elif action == "place_order":
                return self._place_order(params)
            elif action == "query_orders":
                return self._query_orders(params)
            elif action == "cancel_order":
                return self._cancel_order(params)
            else:
                return self.error_response(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Action execution failed: {e}", exc_info=True)
            return self.error_response(str(e))

    def _query_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询价格"""
        valid, error = self.validate_params(params, ['symbol'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        ticker = self.client.get_ticker_price(symbol)

        return self.success_response({
            'symbol': symbol,
            'price': float(ticker.get('price', 0)),
            'change_percent': float(ticker.get('priceChangePercent', 0)),
            'high_24h': float(ticker.get('highPrice', 0)),
            'low_24h': float(ticker.get('lowPrice', 0)),
            'volume_24h': float(ticker.get('volume', 0))
        })

    def _query_account(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询账户信息"""
        account = self.client.get_account_info()

        balances = []
        for balance in account.get('balances', []):
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance.get('asset'),
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })

        return self.success_response({
            'account_type': account.get('accountType'),
            'can_trade': account.get('canTrade'),
            'can_withdraw': account.get('canWithdraw'),
            'can_deposit': account.get('canDeposit'),
            'balances': balances
        })

    def _query_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询余额"""
        asset = params.get('asset', '').upper()

        account = self.client.get_account_info()

        if asset:
            # 查询指定资产
            for balance in account.get('balances', []):
                if balance.get('asset') == asset:
                    free = float(balance.get('free', 0))
                    locked = float(balance.get('locked', 0))
                    return self.success_response({
                        'asset': asset,
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })

            return self.success_response({
                'asset': asset,
                'free': 0,
                'locked': 0,
                'total': 0
            })
        else:
            # 查询所有余额
            balances = []
            for balance in account.get('balances', []):
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                if free > 0 or locked > 0:
                    balances.append({
                        'asset': balance.get('asset'),
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })

            return self.success_response(balances)

    def _place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """下单"""
        valid, error = self.validate_params(params, ['symbol', 'side', 'type', 'quantity'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        side = params['side'].upper()
        order_type = params['type'].upper()
        quantity = float(params['quantity'])

        if order_type == 'LIMIT':
            if 'price' not in params:
                return self.error_response("LIMIT 订单必须指定 price")
            price = float(params['price'])
            order = self.client.place_limit_order(symbol, side, quantity, price)
        else:
            order = self.client.place_market_order(symbol, side, quantity)

        return self.success_response({
            'order_id': order.get('orderId'),
            'client_order_id': order.get('clientOrderId'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'type': order.get('type'),
            'status': order.get('status'),
            'price': float(order.get('price', 0)),
            'quantity': float(order.get('origQty', 0)),
            'executed_qty': float(order.get('executedQty', 0))
        })

    def _query_orders(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询订单"""
        valid, error = self.validate_params(params, ['symbol'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        limit = params.get('limit', 10)

        orders = self.client.get_all_orders(symbol, limit)

        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order.get('orderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'status': order.get('status'),
                'price': float(order.get('price', 0)),
                'quantity': float(order.get('origQty', 0)),
                'executed_qty': float(order.get('executedQty', 0)),
                'time': order.get('time')
            })

        return self.success_response({
            'symbol': symbol,
            'orders': formatted_orders,
            'count': len(formatted_orders)
        })

    def _cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """取消订单"""
        valid, error = self.validate_params(params, ['symbol', 'order_id'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        order_id = int(params['order_id'])

        result = self.client.cancel_order(symbol, order_id)

        return self.success_response({
            'order_id': result.get('orderId'),
            'symbol': result.get('symbol'),
            'status': result.get('status')
        })


# 创建 Skill 实例
def create_skill():
    """创建 Skill 实例"""
    return BinanceSpotSkill()


if __name__ == "__main__":
    # 测试 Skill
    skill = create_skill()

    print("=" * 60)
    print(f"Skill: {skill.name}")
    print(f"Version: {skill.version}")
    print(f"Description: {skill.description}")
    print(f"Actions: {', '.join(skill.actions)}")
    print("=" * 60)

    # 测试查询价格
    print("\n测试查询价格:")
    result = skill.execute('query_price', {'symbol': 'BTC'})
    print(result)

    # 测试查询账户
    print("\n测试查询账户:")
    result = skill.execute('query_account', {})
    print(result)
