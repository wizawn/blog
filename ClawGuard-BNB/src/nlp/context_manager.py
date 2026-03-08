#!/usr/bin/env python3
"""
上下文管理器
管理对话上下文，支持多轮对话
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""

    def __init__(self, max_history: int = 10):
        """
        初始化上下文管理器

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.current_context: Dict[str, Any] = {}

    def add_interaction(self, user_input: str, intent: str, entities: Dict[str, Any],
                       response: str, success: bool = True):
        """
        添加交互记录

        Args:
            user_input: 用户输入
            intent: 识别的意图
            entities: 提取的实体
            response: 系统响应
            success: 是否成功
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent': intent,
            'entities': entities,
            'response': response,
            'success': success
        }

        self.history.append(interaction)

        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # 更新当前上下文
        self._update_context(intent, entities)

        logger.info(f"Added interaction: {intent}")

    def _update_context(self, intent: str, entities: Dict[str, Any]):
        """
        更新当前上下文

        Args:
            intent: 意图
            entities: 实体
        """
        # 保存最近的交易对
        if 'symbol' in entities:
            self.current_context['last_symbol'] = entities['symbol']

        # 保存最近的数量
        if 'amount' in entities:
            self.current_context['last_amount'] = entities['amount']

        # 保存最近的价格
        if 'price' in entities:
            self.current_context['last_price'] = entities['price']

        # 保存最近的意图
        self.current_context['last_intent'] = intent

    def get_context_value(self, key: str) -> Optional[Any]:
        """
        获取上下文值

        Args:
            key: 键名

        Returns:
            值或 None
        """
        return self.current_context.get(key)

    def fill_missing_entities(self, entities: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        使用上下文填充缺失的实体

        Args:
            entities: 当前实体
            intent: 当前意图

        Returns:
            填充后的实体
        """
        filled_entities = entities.copy()

        # 如果缺少交易对，尝试从上下文获取
        if 'symbol' not in filled_entities:
            last_symbol = self.get_context_value('last_symbol')
            if last_symbol:
                filled_entities['symbol'] = last_symbol
                logger.info(f"Filled symbol from context: {last_symbol}")

        # 如果是卖出操作且缺少数量，可以从上下文获取
        if intent == 'place_sell_order' and 'amount' not in filled_entities:
            last_amount = self.get_context_value('last_amount')
            if last_amount:
                filled_entities['amount'] = last_amount
                logger.info(f"Filled amount from context: {last_amount}")

        return filled_entities

    def get_last_interaction(self) -> Optional[Dict[str, Any]]:
        """
        获取最后一次交互

        Returns:
            交互记录或 None
        """
        return self.history[-1] if self.history else None

    def get_history(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Args:
            count: 记录数量

        Returns:
            历史记录列表
        """
        return self.history[-count:] if self.history else []

    def clear_context(self):
        """清除上下文"""
        self.current_context = {}
        logger.info("Context cleared")

    def clear_history(self):
        """清除历史记录"""
        self.history = []
        logger.info("History cleared")

    def get_conversation_summary(self) -> str:
        """
        获取对话摘要

        Returns:
            对话摘要文本
        """
        if not self.history:
            return "暂无对话记录"

        summary_lines = ["对话摘要:"]
        for i, interaction in enumerate(self.history[-5:], 1):
            summary_lines.append(
                f"{i}. [{interaction['timestamp']}] "
                f"意图: {interaction['intent']}, "
                f"成功: {'是' if interaction['success'] else '否'}"
            )

        return "\n".join(summary_lines)

    def is_follow_up_question(self, current_intent: str) -> bool:
        """
        判断是否为跟进问题

        Args:
            current_intent: 当前意图

        Returns:
            是否为跟进问题
        """
        last_interaction = self.get_last_interaction()
        if not last_interaction:
            return False

        last_intent = last_interaction['intent']

        # 定义跟进关系
        follow_up_patterns = {
            'query_price': ['place_buy_order', 'place_sell_order', 'analyze_market'],
            'analyze_market': ['place_buy_order', 'place_sell_order', 'get_recommendation'],
            'query_account': ['query_balance', 'query_orders'],
        }

        return current_intent in follow_up_patterns.get(last_intent, [])


# 使用示例
if __name__ == "__main__":
    context_manager = ContextManager()

    # 模拟对话
    print("=" * 60)
    print("上下文管理测试")
    print("=" * 60)

    # 第一轮：查询价格
    context_manager.add_interaction(
        user_input="BTC现在多少钱？",
        intent="query_price",
        entities={'symbol': 'BTCUSDT'},
        response="BTC 当前价格: $68500.50",
        success=True
    )

    # 第二轮：买入（使用上下文中的交易对）
    entities = {}
    filled_entities = context_manager.fill_missing_entities(entities, 'place_buy_order')
    print(f"\n填充后的实体: {filled_entities}")

    context_manager.add_interaction(
        user_input="买入1000 USDT",
        intent="place_buy_order",
        entities=filled_entities,
        response="订单已提交",
        success=True
    )

    # 显示对话摘要
    print("\n" + context_manager.get_conversation_summary())

    # 检查是否为跟进问题
    is_follow_up = context_manager.is_follow_up_question('place_buy_order')
    print(f"\n是否为跟进问题: {is_follow_up}")
