#!/usr/bin/env python3
"""
响应生成器
生成友好的自然语言响应
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """响应生成器"""

    def __init__(self):
        """初始化响应生成器"""
        pass

    def generate(self, intent: str, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """
        生成响应

        Args:
            intent: 意图
            result: 执行结果
            entities: 实体

        Returns:
            响应文本
        """
        if not result.get('success'):
            return self._generate_error_response(intent, result.get('error', '未知错误'))

        # 根据意图生成不同的响应
        if intent == 'query_price':
            return self._generate_price_response(result, entities)
        elif intent == 'query_account':
            return self._generate_account_response(result)
        elif intent == 'query_balance':
            return self._generate_balance_response(result, entities)
        elif intent == 'place_buy_order':
            return self._generate_buy_order_response(result, entities)
        elif intent == 'place_sell_order':
            return self._generate_sell_order_response(result, entities)
        elif intent == 'cancel_order':
            return self._generate_cancel_order_response(result)
        elif intent == 'analyze_market':
            return self._generate_analysis_response(result, entities)
        elif intent == 'get_recommendation':
            return self._generate_recommendation_response(result, entities)
        elif intent == 'query_orders':
            return self._generate_orders_response(result, entities)
        else:
            return self._generate_generic_response(result)

    def _generate_error_response(self, intent: str, error: str) -> str:
        """生成错误响应"""
        return f"❌ 操作失败: {error}"

    def _generate_price_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成价格查询响应"""
        data = result.get('data', {})
        symbol = data.get('symbol', entities.get('symbol', 'N/A'))
        price = data.get('price', 0)
        change_percent = data.get('change_percent', 0)

        change_emoji = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"

        response = f"💰 {symbol} 当前价格\n"
        response += f"价格: ${price:,.2f}\n"
        response += f"24h涨跌: {change_emoji} {change_percent:+.2f}%"

        if 'high_24h' in data:
            response += f"\n24h最高: ${data['high_24h']:,.2f}"
        if 'low_24h' in data:
            response += f"\n24h最低: ${data['low_24h']:,.2f}"

        return response

    def _generate_account_response(self, result: Dict[str, Any]) -> str:
        """生成账户查询响应"""
        data = result.get('data', {})
        balances = data.get('balances', [])

        if not balances:
            return "💼 账户余额为空"

        response = "💼 账户信息\n"
        response += "=" * 40 + "\n"

        total_usdt = 0
        for balance in balances[:5]:  # 只显示前5个
            asset = balance.get('asset', 'N/A')
            total = balance.get('total', 0)
            response += f"{asset}: {total:.8f}\n"

            if asset == 'USDT':
                total_usdt = total

        if total_usdt > 0:
            response += f"\n💰 USDT 权益: ${total_usdt:,.2f}"

        return response

    def _generate_balance_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成余额查询响应"""
        data = result.get('data', {})

        if isinstance(data, list):
            # 多个资产
            response = "💰 账户余额\n"
            for balance in data[:5]:
                asset = balance.get('asset', 'N/A')
                total = balance.get('total', 0)
                response += f"{asset}: {total:.8f}\n"
            return response
        else:
            # 单个资产
            asset = data.get('asset', entities.get('asset', 'N/A'))
            total = data.get('total', 0)
            free = data.get('free', 0)
            locked = data.get('locked', 0)

            response = f"💰 {asset} 余额\n"
            response += f"总计: {total:.8f}\n"
            response += f"可用: {free:.8f}\n"
            response += f"冻结: {locked:.8f}"

            return response

    def _generate_buy_order_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成买入订单响应"""
        data = result.get('data', {})
        symbol = data.get('symbol', entities.get('symbol', 'N/A'))
        order_id = data.get('order_id', 'N/A')
        status = data.get('status', 'N/A')
        quantity = data.get('quantity', 0)

        response = f"✅ 买入订单已提交\n"
        response += f"交易对: {symbol}\n"
        response += f"订单ID: {order_id}\n"
        response += f"数量: {quantity}\n"
        response += f"状态: {status}"

        return response

    def _generate_sell_order_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成卖出订单响应"""
        data = result.get('data', {})
        symbol = data.get('symbol', entities.get('symbol', 'N/A'))
        order_id = data.get('order_id', 'N/A')
        status = data.get('status', 'N/A')
        quantity = data.get('quantity', 0)

        response = f"✅ 卖出订单已提交\n"
        response += f"交易对: {symbol}\n"
        response += f"订单ID: {order_id}\n"
        response += f"数量: {quantity}\n"
        response += f"状态: {status}"

        return response

    def _generate_cancel_order_response(self, result: Dict[str, Any]) -> str:
        """生成取消订单响应"""
        data = result.get('data', {})
        order_id = data.get('order_id', 'N/A')

        return f"✅ 订单已取消\n订单ID: {order_id}"

    def _generate_analysis_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成分析响应"""
        data = result.get('data', {})
        symbol = data.get('symbol', entities.get('symbol', 'N/A'))
        trend = data.get('trend', 'UNKNOWN')
        signal = data.get('signal', 'NEUTRAL')

        trend_emoji = {
            'UPTREND': '📈',
            'DOWNTREND': '📉',
            'SIDEWAYS': '➡️',
            'UNKNOWN': '❓'
        }.get(trend, '❓')

        signal_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'NEUTRAL': '🟡'
        }.get(signal, '🟡')

        response = f"📊 {symbol} 技术分析\n"
        response += f"趋势: {trend_emoji} {trend}\n"
        response += f"信号: {signal_emoji} {signal}"

        if 'indicators' in data:
            indicators = data['indicators']
            if 'rsi' in indicators:
                rsi = indicators['rsi'].get('value', 0)
                response += f"\nRSI: {rsi:.2f}"

        return response

    def _generate_recommendation_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成建议响应"""
        data = result.get('data', {})
        recommendation = data.get('recommendation', 'HOLD')
        reason = data.get('reason', '暂无建议')

        emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }.get(recommendation, '🟡')

        response = f"💡 交易建议\n"
        response += f"建议: {emoji} {recommendation}\n"
        response += f"理由: {reason}"

        return response

    def _generate_orders_response(self, result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """生成订单查询响应"""
        data = result.get('data', {})
        orders = data.get('orders', [])
        count = data.get('count', 0)

        if count == 0:
            return "📋 暂无订单记录"

        response = f"📋 订单列表 (共 {count} 条)\n"
        response += "=" * 40 + "\n"

        for i, order in enumerate(orders[:5], 1):
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            status = order.get('status', 'N/A')
            response += f"{i}. {symbol} {side} - {status}\n"

        return response

    def _generate_generic_response(self, result: Dict[str, Any]) -> str:
        """生成通用响应"""
        return "✅ 操作成功"

    def generate_confirmation_message(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        生成确认消息（用于高风险操作）

        Args:
            intent: 意图
            entities: 实体

        Returns:
            确认消息
        """
        if intent == 'place_buy_order':
            symbol = entities.get('symbol', 'N/A')
            amount = entities.get('amount', 0)
            order_type = entities.get('order_type', 'MARKET')

            if order_type == 'MARKET':
                return f"⚠️ 确认市价买入 {symbol}？\n数量: {amount}"
            else:
                price = entities.get('price', 0)
                return f"⚠️ 确认限价买入 {symbol}？\n数量: {amount}\n价格: ${price:,.2f}"

        elif intent == 'place_sell_order':
            symbol = entities.get('symbol', 'N/A')
            amount = entities.get('amount', 0)
            order_type = entities.get('order_type', 'MARKET')

            if order_type == 'MARKET':
                return f"⚠️ 确认市价卖出 {symbol}？\n数量: {amount}"
            else:
                price = entities.get('price', 0)
                return f"⚠️ 确认限价卖出 {symbol}？\n数量: {amount}\n价格: ${price:,.2f}"

        elif intent == 'cancel_order':
            return "⚠️ 确认取消订单？"

        elif intent == 'start_strategy':
            return "⚠️ 确认启动策略？"

        elif intent == 'stop_strategy':
            return "⚠️ 确认停止策略？"

        return "⚠️ 确认执行此操作？"


# 使用示例
if __name__ == "__main__":
    generator = ResponseGenerator()

    # 测试用例
    print("=" * 60)
    print("响应生成测试")
    print("=" * 60)

    # 价格查询响应
    result = {
        'success': True,
        'data': {
            'symbol': 'BTCUSDT',
            'price': 68500.50,
            'change_percent': 2.5,
            'high_24h': 69000.0,
            'low_24h': 67000.0
        }
    }
    response = generator.generate('query_price', result, {'symbol': 'BTCUSDT'})
    print(f"\n价格查询响应:\n{response}")

    # 买入订单响应
    result = {
        'success': True,
        'data': {
            'symbol': 'BTCUSDT',
            'order_id': 12345678,
            'status': 'FILLED',
            'quantity': 0.001
        }
    }
    response = generator.generate('place_buy_order', result, {'symbol': 'BTCUSDT'})
    print(f"\n买入订单响应:\n{response}")

    # 确认消息
    confirmation = generator.generate_confirmation_message(
        'place_buy_order',
        {'symbol': 'BTCUSDT', 'amount': 1000, 'order_type': 'MARKET'}
    )
    print(f"\n确认消息:\n{confirmation}")
