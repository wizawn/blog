#!/usr/bin/env python3
"""
意图识别器
识别用户自然语言输入的意图
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """意图识别器"""

    def __init__(self):
        """初始化意图识别器"""
        self.intent_patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        加载意图模式

        Returns:
            意图模式字典
        """
        return {
            # 查询类意图
            'query_price': [
                r'(查询|查看|看看|告诉我|显示)(.*?)(价格|多少钱|现价|行情)',
                r'(.*?)(现在|当前|目前)(多少钱|什么价格|价格)',
                r'(BTC|ETH|BNB|币)(.*?)(价格|多少)',
                r'(价格|行情)(.*?)(BTC|ETH|BNB)',
            ],
            'query_account': [
                r'(查询|查看|看看|显示)(.*?)(账户|余额|资产)',
                r'(我的|账户)(.*?)(余额|资产|有多少)',
                r'(账户|余额)(.*?)(信息|情况|状态)',
            ],
            'query_balance': [
                r'(查询|查看)(.*?)(USDT|BTC|ETH)(.*?)(余额|有多少)',
                r'(我有|还有)(多少|几个)(USDT|BTC|ETH)',
                r'(USDT|BTC|ETH)(.*?)(余额|数量)',
            ],
            'query_orders': [
                r'(查询|查看|显示)(.*?)(订单|委托)',
                r'(我的|当前)(.*?)(订单|委托)',
                r'(订单|委托)(.*?)(列表|记录|历史)',
            ],
            'query_position': [
                r'(查询|查看|显示)(.*?)(持仓|仓位)',
                r'(我的|当前)(.*?)(持仓|仓位)',
                r'(持仓|仓位)(.*?)(情况|状态)',
            ],

            # 交易类意图
            'place_buy_order': [
                r'(买入|买|购买)(.*?)(BTC|ETH|BNB)',
                r'(用|花)(.*?)(USDT|美元)(.*?)(买|买入)(.*?)(BTC|ETH|BNB)',
                r'(市价|限价)(.*?)(买入|买)',
            ],
            'place_sell_order': [
                r'(卖出|卖|出售)(.*?)(BTC|ETH|BNB)',
                r'(在|以)(.*?)(价格|美元)(.*?)(卖出|卖)',
                r'(市价|限价)(.*?)(卖出|卖)',
            ],
            'cancel_order': [
                r'(取消|撤销|删除)(.*?)(订单|委托)',
                r'(订单|委托)(.*?)(取消|撤销)',
            ],

            # 分析类意图
            'analyze_market': [
                r'(分析|看看|查看)(.*?)(走势|趋势|行情)',
                r'(技术|指标)(.*?)(分析)',
                r'(帮我|给我)(.*?)(分析)',
            ],
            'get_recommendation': [
                r'(建议|推荐|应该)(.*?)(买|卖|操作)',
                r'(现在|当前)(.*?)(适合|可以)(.*?)(买|卖)',
                r'(给个|给我)(.*?)(建议|意见)',
            ],

            # 策略类意图
            'start_strategy': [
                r'(启动|开始|运行)(.*?)(策略|网格|交易)',
                r'(策略|网格)(.*?)(启动|开始)',
            ],
            'stop_strategy': [
                r'(停止|暂停|关闭)(.*?)(策略|网格|交易)',
                r'(策略|网格)(.*?)(停止|暂停)',
            ],
            'query_strategy': [
                r'(查询|查看|显示)(.*?)(策略|网格)(.*?)(状态|情况)',
                r'(策略|网格)(.*?)(运行|表现|收益)',
            ],

            # 配置类意图
            'set_leverage': [
                r'(设置|调整|修改)(.*?)(杠杆|倍数)',
                r'(杠杆|倍数)(.*?)(设置|调整|改成)',
            ],
            'set_stop_loss': [
                r'(设置|添加|加上)(.*?)(止损|停损)',
                r'(止损|停损)(.*?)(设置|价格)',
            ],
            'configure_proxy': [
                r'(设置|配置|修改)(.*?)(代理|proxy)',
                r'(代理|proxy)(.*?)(设置|配置)',
            ],

            # 帮助类意图
            'help': [
                r'^(帮助|help|怎么用|如何使用)$',
                r'(不知道|不会|教我)(.*?)(怎么|如何)',
            ],
        }

    def recognize(self, text: str) -> Tuple[str, float]:
        """
        识别意图

        Args:
            text: 用户输入文本

        Returns:
            (意图名称, 置信度)
        """
        text = text.strip().lower()

        if not text:
            return 'unknown', 0.0

        # 遍历所有意图模式
        best_intent = 'unknown'
        best_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # 计算置信度（基于匹配长度）
                    match_length = len(match.group(0))
                    text_length = len(text)
                    confidence = match_length / text_length

                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence

        logger.info(f"Intent recognized: {best_intent} (confidence: {best_confidence:.2f})")

        return best_intent, best_confidence

    def get_intent_description(self, intent: str) -> str:
        """
        获取意图描述

        Args:
            intent: 意图名称

        Returns:
            意图描述
        """
        descriptions = {
            'query_price': '查询价格',
            'query_account': '查询账户',
            'query_balance': '查询余额',
            'query_orders': '查询订单',
            'query_position': '查询持仓',
            'place_buy_order': '买入下单',
            'place_sell_order': '卖出下单',
            'cancel_order': '取消订单',
            'analyze_market': '市场分析',
            'get_recommendation': '获取建议',
            'start_strategy': '启动策略',
            'stop_strategy': '停止策略',
            'query_strategy': '查询策略',
            'set_leverage': '设置杠杆',
            'set_stop_loss': '设置止损',
            'configure_proxy': '配置代理',
            'help': '帮助',
            'unknown': '未知意图'
        }
        return descriptions.get(intent, '未知意图')

    def is_query_intent(self, intent: str) -> bool:
        """判断是否为查询类意图"""
        return intent.startswith('query_')

    def is_trading_intent(self, intent: str) -> bool:
        """判断是否为交易类意图"""
        return 'order' in intent or 'buy' in intent or 'sell' in intent

    def is_risky_intent(self, intent: str) -> bool:
        """判断是否为高风险意图（需要确认）"""
        risky_intents = [
            'place_buy_order',
            'place_sell_order',
            'cancel_order',
            'start_strategy',
            'stop_strategy',
            'set_leverage'
        ]
        return intent in risky_intents


# 使用示例
if __name__ == "__main__":
    recognizer = IntentRecognizer()

    # 测试用例
    test_cases = [
        "BTC现在多少钱？",
        "查询我的账户余额",
        "用1000 USDT买入BTC",
        "在70000价格卖出0.1个BTC",
        "帮我分析一下BTC的走势",
        "启动BTC的网格交易",
        "把BTC的杠杆调到5倍",
        "设置止损",
        "查询我的订单",
    ]

    print("=" * 60)
    print("意图识别测试")
    print("=" * 60)

    for text in test_cases:
        intent, confidence = recognizer.recognize(text)
        description = recognizer.get_intent_description(intent)
        print(f"\n输入: {text}")
        print(f"意图: {intent} ({description})")
        print(f"置信度: {confidence:.2f}")
        print(f"高风险: {'是' if recognizer.is_risky_intent(intent) else '否'}")
