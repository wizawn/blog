#!/usr/bin/env python3
"""
NLP 命令解析器
整合意图识别、实体提取、上下文管理，将自然语言转换为可执行命令
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, Optional, Tuple
import logging

from .intent_recognizer import IntentRecognizer
from .entity_extractor import EntityExtractor
from .context_manager import ContextManager
from .response_generator import ResponseGenerator

logger = logging.getLogger(__name__)


class NLPCommandParser:
    """NLP 命令解析器"""

    def __init__(self):
        """初始化命令解析器"""
        self.intent_recognizer = IntentRecognizer()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()

    def parse(self, text: str, use_context: bool = True) -> Dict[str, Any]:
        """
        解析自然语言输入

        Args:
            text: 用户输入文本
            use_context: 是否使用上下文

        Returns:
            解析结果字典
        """
        try:
            # 1. 意图识别
            intent, confidence = self.intent_recognizer.recognize(text)

            if intent == 'unknown' or confidence < 0.3:
                return {
                    'success': False,
                    'error': '无法理解您的意图，请尝试更清晰的表达',
                    'suggestions': self._get_suggestions()
                }

            # 2. 实体提取
            entities = self.entity_extractor.extract(text, intent)

            # 3. 使用上下文填充缺失实体
            if use_context:
                entities = self.context_manager.fill_missing_entities(entities, intent)

            # 4. 验证实体完整性
            valid, error = self.entity_extractor.validate_entities(entities, intent)
            if not valid:
                return {
                    'success': False,
                    'error': error,
                    'intent': intent,
                    'entities': entities,
                    'missing_info': self._get_missing_info(intent, entities)
                }

            # 5. 生成命令
            command = self._generate_command(intent, entities)

            # 6. 检查是否需要确认
            requires_confirmation = self.intent_recognizer.is_risky_intent(intent)
            confirmation_message = None
            if requires_confirmation:
                confirmation_message = self.response_generator.generate_confirmation_message(
                    intent, entities
                )

            return {
                'success': True,
                'intent': intent,
                'intent_description': self.intent_recognizer.get_intent_description(intent),
                'confidence': confidence,
                'entities': entities,
                'command': command,
                'requires_confirmation': requires_confirmation,
                'confirmation_message': confirmation_message
            }

        except Exception as e:
            logger.error(f"Parse error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'解析失败: {str(e)}'
            }

    def _generate_command(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成可执行命令

        Args:
            intent: 意图
            entities: 实体

        Returns:
            命令字典
        """
        command = {
            'action': self._intent_to_action(intent),
            'params': {}
        }

        # 根据意图映射参数
        if intent == 'query_price':
            command['params'] = {
                'symbol': entities.get('symbol')
            }

        elif intent == 'query_account':
            command['params'] = {}

        elif intent == 'query_balance':
            command['params'] = {
                'asset': entities.get('asset')
            }

        elif intent in ['place_buy_order', 'place_sell_order']:
            command['params'] = {
                'symbol': entities.get('symbol'),
                'side': entities.get('side', 'BUY' if intent == 'place_buy_order' else 'SELL'),
                'type': entities.get('order_type', 'MARKET'),
                'quantity': entities.get('amount')
            }
            if entities.get('price'):
                command['params']['price'] = entities.get('price')

        elif intent == 'cancel_order':
            command['params'] = {
                'symbol': entities.get('symbol'),
                'order_id': entities.get('order_id')
            }

        elif intent == 'analyze_market':
            command['params'] = {
                'symbol': entities.get('symbol'),
                'interval': entities.get('interval', '1h')
            }

        elif intent == 'get_recommendation':
            command['params'] = {
                'symbol': entities.get('symbol')
            }

        elif intent == 'query_orders':
            command['params'] = {
                'symbol': entities.get('symbol'),
                'limit': entities.get('limit', 10)
            }

        elif intent == 'set_leverage':
            command['params'] = {
                'symbol': entities.get('symbol'),
                'leverage': entities.get('leverage')
            }

        return command

    def _intent_to_action(self, intent: str) -> str:
        """
        将意图转换为动作名称

        Args:
            intent: 意图

        Returns:
            动作名称
        """
        action_mapping = {
            'query_price': 'get_price',
            'query_account': 'get_account',
            'query_balance': 'get_balance',
            'query_orders': 'get_orders',
            'query_position': 'get_position',
            'place_buy_order': 'place_order',
            'place_sell_order': 'place_order',
            'cancel_order': 'cancel_order',
            'analyze_market': 'analyze_market',
            'get_recommendation': 'get_recommendation',
            'start_strategy': 'start_strategy',
            'stop_strategy': 'stop_strategy',
            'query_strategy': 'get_strategy_status',
            'set_leverage': 'set_leverage',
            'set_stop_loss': 'set_stop_loss',
        }
        return action_mapping.get(intent, 'unknown')

    def _get_missing_info(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        获取缺失信息提示

        Args:
            intent: 意图
            entities: 实体

        Returns:
            提示信息
        """
        if intent in ['place_buy_order', 'place_sell_order']:
            if 'symbol' not in entities:
                return "请指定要交易的币种，例如：BTC、ETH"
            if 'amount' not in entities:
                return "请指定交易数量，例如：1000 USDT 或 0.1 BTC"
            if entities.get('order_type') == 'LIMIT' and 'price' not in entities:
                return "限价单需要指定价格，例如：在 70000 价格"

        elif intent in ['query_price', 'analyze_market']:
            if 'symbol' not in entities:
                return "请指定要查询的币种，例如：BTC、ETH"

        return "请提供更多信息"

    def _get_suggestions(self) -> list:
        """
        获取使用建议

        Returns:
            建议列表
        """
        return [
            "查询价格：BTC现在多少钱？",
            "查询账户：我的账户余额是多少？",
            "买入：用1000 USDT买入BTC",
            "卖出：在70000价格卖出0.1个BTC",
            "分析：帮我分析一下BTC的走势",
            "建议：现在适合买入BTC吗？"
        ]

    def execute_and_respond(self, text: str, executor_func=None) -> Dict[str, Any]:
        """
        解析并执行命令，生成响应

        Args:
            text: 用户输入
            executor_func: 执行函数（可选）

        Returns:
            包含响应的结果字典
        """
        # 解析命令
        parse_result = self.parse(text)

        if not parse_result['success']:
            return parse_result

        # 如果需要确认且没有执行器，返回确认请求
        if parse_result.get('requires_confirmation') and not executor_func:
            return parse_result

        # 执行命令（如果提供了执行器）
        if executor_func:
            try:
                command = parse_result['command']
                execution_result = executor_func(command['action'], command['params'])

                # 生成响应
                response_text = self.response_generator.generate(
                    parse_result['intent'],
                    execution_result,
                    parse_result['entities']
                )

                # 记录到上下文
                self.context_manager.add_interaction(
                    user_input=text,
                    intent=parse_result['intent'],
                    entities=parse_result['entities'],
                    response=response_text,
                    success=execution_result.get('success', False)
                )

                return {
                    'success': True,
                    'response': response_text,
                    'data': execution_result.get('data'),
                    'intent': parse_result['intent']
                }

            except Exception as e:
                logger.error(f"Execution error: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'执行失败: {str(e)}'
                }

        return parse_result

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        return self.context_manager.get_conversation_summary()

    def clear_context(self):
        """清除上下文"""
        self.context_manager.clear_context()
        self.context_manager.clear_history()


# 使用示例
if __name__ == "__main__":
    parser = NLPCommandParser()

    # 测试用例
    test_cases = [
        "BTC现在多少钱？",
        "用1000 USDT买入BTC",
        "在70000价格卖出0.1个BTC",
        "帮我分析一下ETH的走势",
        "查询我的账户余额",
        "我的USDT还有多少？",
        "现在适合买入BTC吗？",
    ]

    print("=" * 60)
    print("NLP 命令解析器测试")
    print("=" * 60)

    for text in test_cases:
        print(f"\n{'='*60}")
        print(f"输入: {text}")
        print(f"{'='*60}")

        result = parser.parse(text)

        if result['success']:
            print(f"✅ 解析成功")
            print(f"意图: {result['intent']} ({result['intent_description']})")
            print(f"置信度: {result['confidence']:.2f}")
            print(f"实体: {result['entities']}")
            print(f"命令: {result['command']}")

            if result.get('requires_confirmation'):
                print(f"\n⚠️ 需要确认:")
                print(result['confirmation_message'])
        else:
            print(f"❌ 解析失败: {result['error']}")
            if 'suggestions' in result:
                print("\n💡 使用建议:")
                for suggestion in result['suggestions'][:3]:
                    print(f"  - {suggestion}")

    # 显示对话摘要
    print(f"\n{'='*60}")
    print("对话摘要")
    print(f"{'='*60}")
    print(parser.get_context_summary())
