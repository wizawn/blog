#!/usr/bin/env python3
"""
输出格式化器 - 支持人类可读和 JSON 格式输出
用于 OpenClaw AI 集成
"""

import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime


class OutputFormatter:
    """输出格式化器"""

    def __init__(self, json_mode: bool = False):
        """
        初始化格式化器

        Args:
            json_mode: 是否使用 JSON 模式
        """
        self.json_mode = json_mode

    def output(self, data: Any, error: Optional[str] = None):
        """
        输出数据

        Args:
            data: 要输出的数据
            error: 错误信息（如果有）
        """
        if self.json_mode:
            self._output_json(data, error)
        else:
            # 非 JSON 模式下，数据应该已经被格式化为字符串
            if isinstance(data, str):
                print(data)
            else:
                print(str(data))

    def _output_json(self, data: Any, error: Optional[str] = None):
        """输出 JSON 格式"""
        output = {
            'success': error is None,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }

        if error:
            output['error'] = error
        else:
            output['data'] = data

        print(json.dumps(output, ensure_ascii=False, indent=2))

    def format_price(self, symbol: str, ticker: Dict) -> Any:
        """
        格式化价格数据

        Args:
            symbol: 交易对
            ticker: 价格数据

        Returns:
            格式化后的数据
        """
        if self.json_mode:
            return {
                'symbol': symbol,
                'price': float(ticker.get('price', 0)),
                'change_percent': float(ticker.get('priceChangePercent', 0)),
                'high_24h': float(ticker.get('highPrice', 0)),
                'low_24h': float(ticker.get('lowPrice', 0)),
                'volume_24h': float(ticker.get('volume', 0)),
                'quote_volume_24h': float(ticker.get('quoteVolume', 0))
            }
        else:
            # 返回 None，让调用者使用 UI.print_price_card
            return None

    def format_account(self, account: Dict) -> Any:
        """
        格式化账户信息

        Args:
            account: 账户数据

        Returns:
            格式化后的数据
        """
        if self.json_mode:
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

            return {
                'account_type': account.get('accountType'),
                'can_trade': account.get('canTrade'),
                'can_withdraw': account.get('canWithdraw'),
                'can_deposit': account.get('canDeposit'),
                'update_time': account.get('updateTime'),
                'balances': balances
            }
        else:
            return None

    def format_order(self, order: Dict) -> Any:
        """
        格式化订单信息

        Args:
            order: 订单数据

        Returns:
            格式化后的数据
        """
        if self.json_mode:
            return {
                'order_id': order.get('orderId'),
                'client_order_id': order.get('clientOrderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'price': float(order.get('price', 0)),
                'quantity': float(order.get('origQty', 0)),
                'executed_qty': float(order.get('executedQty', 0)),
                'status': order.get('status'),
                'time': order.get('time'),
                'update_time': order.get('updateTime')
            }
        else:
            return None

    def format_orders(self, orders: List[Dict]) -> Any:
        """
        格式化订单列表

        Args:
            orders: 订单列表

        Returns:
            格式化后的数据
        """
        if self.json_mode:
            return [self.format_order(order) for order in orders]
        else:
            return None

    def format_analysis(self, symbol: str, analysis: Dict) -> Any:
        """
        格式化技术分析结果

        Args:
            symbol: 交易对
            analysis: 分析结果

        Returns:
            格式化后的数据
        """
        if self.json_mode:
            return {
                'symbol': symbol,
                'trend': analysis.get('trend'),
                'signal': analysis.get('signal'),
                'indicators': analysis.get('indicators', {}),
                'recommendation': analysis.get('recommendation'),
                'confidence': analysis.get('confidence')
            }
        else:
            return None

    def format_strategy_status(self, strategy: Dict) -> Any:
        """
        格式化策略状态

        Args:
            strategy: 策略数据

        Returns:
            格式化后的数据
        """
        if self.json_mode:
            return {
                'name': strategy.get('name'),
                'symbol': strategy.get('symbol'),
                'status': strategy.get('status'),
                'running': strategy.get('running'),
                'profit': strategy.get('profit'),
                'trades': strategy.get('trades'),
                'start_time': strategy.get('start_time'),
                'parameters': strategy.get('parameters', {})
            }
        else:
            return None

    def format_error(self, error: str) -> str:
        """
        格式化错误信息

        Args:
            error: 错误信息

        Returns:
            格式化后的错误
        """
        if self.json_mode:
            return error
        else:
            return f"❌ {error}"

    def format_success(self, message: str) -> str:
        """
        格式化成功信息

        Args:
            message: 成功信息

        Returns:
            格式化后的消息
        """
        if self.json_mode:
            return message
        else:
            return f"✅ {message}"


def create_formatter(json_mode: bool = False) -> OutputFormatter:
    """
    创建输出格式化器

    Args:
        json_mode: 是否使用 JSON 模式

    Returns:
        OutputFormatter 实例
    """
    return OutputFormatter(json_mode)


# 使用示例
if __name__ == "__main__":
    # JSON 模式
    formatter = OutputFormatter(json_mode=True)

    # 示例数据
    ticker = {
        'price': '68500.50',
        'priceChangePercent': '2.5',
        'highPrice': '69000',
        'lowPrice': '67000',
        'volume': '12345.67'
    }

    price_data = formatter.format_price('BTCUSDT', ticker)
    formatter.output(price_data)

    print("\n---\n")

    # 错误示例
    formatter.output(None, "连接失败")
