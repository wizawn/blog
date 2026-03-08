#!/usr/bin/env python3
"""
实体提取器
从用户输入中提取关键实体（交易对、数量、价格等）
"""

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class EntityExtractor:
    """实体提取器"""

    def __init__(self):
        """初始化实体提取器"""
        self.symbol_aliases = self._load_symbol_aliases()

    def _load_symbol_aliases(self) -> Dict[str, str]:
        """
        加载交易对别名映射

        Returns:
            别名映射字典
        """
        return {
            'btc': 'BTCUSDT',
            '比特币': 'BTCUSDT',
            'bitcoin': 'BTCUSDT',
            'eth': 'ETHUSDT',
            '以太坊': 'ETHUSDT',
            'ethereum': 'ETHUSDT',
            'bnb': 'BNBUSDT',
            '币安币': 'BNBUSDT',
            'binance coin': 'BNBUSDT',
            'sol': 'SOLUSDT',
            'solana': 'SOLUSDT',
            'doge': 'DOGEUSDT',
            '狗狗币': 'DOGEUSDT',
            'dogecoin': 'DOGEUSDT',
            'ada': 'ADAUSDT',
            'cardano': 'ADAUSDT',
            'xrp': 'XRPUSDT',
            'ripple': 'XRPUSDT',
        }

    def extract(self, text: str, intent: str) -> Dict[str, Any]:
        """
        提取实体

        Args:
            text: 用户输入文本
            intent: 识别的意图

        Returns:
            实体字典
        """
        entities = {}

        # 提取交易对
        symbol = self._extract_symbol(text)
        if symbol:
            entities['symbol'] = symbol

        # 提取数量
        amount = self._extract_amount(text)
        if amount:
            entities['amount'] = amount

        # 提取价格
        price = self._extract_price(text)
        if price:
            entities['price'] = price

        # 提取订单类型
        order_type = self._extract_order_type(text)
        if order_type:
            entities['order_type'] = order_type

        # 提取方向（买/卖）
        side = self._extract_side(text, intent)
        if side:
            entities['side'] = side

        # 提取杠杆倍数
        leverage = self._extract_leverage(text)
        if leverage:
            entities['leverage'] = leverage

        # 提取时间间隔
        interval = self._extract_interval(text)
        if interval:
            entities['interval'] = interval

        # 提取资产
        asset = self._extract_asset(text)
        if asset:
            entities['asset'] = asset

        logger.info(f"Extracted entities: {entities}")

        return entities

    def _extract_symbol(self, text: str) -> Optional[str]:
        """提取交易对"""
        text_lower = text.lower()

        # 检查别名
        for alias, symbol in self.symbol_aliases.items():
            if alias in text_lower:
                return symbol

        # 直接匹配交易对格式
        match = re.search(r'(BTC|ETH|BNB|SOL|DOGE|ADA|XRP)USDT', text, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """提取数量"""
        # 匹配数量模式
        patterns = [
            r'(\d+\.?\d*)\s*(个|枚|USDT|美元|刀)',
            r'(用|花|投入)\s*(\d+\.?\d*)',
            r'数量\s*[:：]?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(BTC|ETH|BNB)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 提取数字部分
                number_str = match.group(1) if match.lastindex >= 1 else match.group(2)
                try:
                    return float(number_str)
                except ValueError:
                    continue

        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """提取价格"""
        # 匹配价格模式
        patterns = [
            r'(在|以|价格)\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(价格|美元|刀)',
            r'价格\s*[:：]?\s*(\d+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 提取数字部分
                for group in match.groups():
                    try:
                        price = float(group)
                        # 价格通常较大，过滤掉小数量
                        if price > 10:
                            return price
                    except (ValueError, TypeError):
                        continue

        return None

    def _extract_order_type(self, text: str) -> Optional[str]:
        """提取订单类型"""
        if re.search(r'市价', text, re.IGNORECASE):
            return 'MARKET'
        elif re.search(r'限价', text, re.IGNORECASE):
            return 'LIMIT'
        return None

    def _extract_side(self, text: str, intent: str) -> Optional[str]:
        """提取交易方向"""
        if 'buy' in intent or re.search(r'买入|买|购买', text, re.IGNORECASE):
            return 'BUY'
        elif 'sell' in intent or re.search(r'卖出|卖|出售', text, re.IGNORECASE):
            return 'SELL'
        return None

    def _extract_leverage(self, text: str) -> Optional[int]:
        """提取杠杆倍数"""
        patterns = [
            r'(\d+)\s*倍',
            r'杠杆\s*[:：]?\s*(\d+)',
            r'(\d+)x',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    leverage = int(match.group(1))
                    if 1 <= leverage <= 125:  # 币安最大125倍
                        return leverage
                except ValueError:
                    continue

        return None

    def _extract_interval(self, text: str) -> Optional[str]:
        """提取时间间隔"""
        intervals = {
            '1分钟': '1m',
            '5分钟': '5m',
            '15分钟': '15m',
            '1小时': '1h',
            '4小时': '4h',
            '1天': '1d',
            '1周': '1w',
        }

        text_lower = text.lower()
        for key, value in intervals.items():
            if key in text_lower:
                return value

        # 直接匹配格式
        match = re.search(r'(1m|5m|15m|1h|4h|1d|1w)', text, re.IGNORECASE)
        if match:
            return match.group(1).lower()

        return None

    def _extract_asset(self, text: str) -> Optional[str]:
        """提取资产符号"""
        assets = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD']

        for asset in assets:
            if asset.lower() in text.lower():
                return asset

        return None

    def validate_entities(self, entities: Dict[str, Any], intent: str) -> tuple[bool, Optional[str]]:
        """
        验证实体完整性

        Args:
            entities: 提取的实体
            intent: 意图

        Returns:
            (是否有效, 错误信息)
        """
        # 交易类意图需要交易对
        if intent in ['place_buy_order', 'place_sell_order']:
            if 'symbol' not in entities:
                return False, "缺少交易对信息"
            if 'amount' not in entities:
                return False, "缺少数量信息"
            if intent == 'place_sell_order' and 'order_type' not in entities:
                # 卖出默认市价
                entities['order_type'] = 'MARKET'

        # 限价单需要价格
        if entities.get('order_type') == 'LIMIT' and 'price' not in entities:
            return False, "限价单需要指定价格"

        # 查询类意图需要交易对
        if intent in ['query_price', 'analyze_market']:
            if 'symbol' not in entities:
                return False, "缺少交易对信息"

        return True, None


# 使用示例
if __name__ == "__main__":
    extractor = EntityExtractor()

    # 测试用例
    test_cases = [
        ("用1000 USDT买入BTC", "place_buy_order"),
        ("在70000价格卖出0.1个BTC", "place_sell_order"),
        ("查询BTC价格", "query_price"),
        ("把BTC的杠杆调到5倍", "set_leverage"),
        ("分析ETH的1小时走势", "analyze_market"),
        ("查询我的USDT余额", "query_balance"),
    ]

    print("=" * 60)
    print("实体提取测试")
    print("=" * 60)

    for text, intent in test_cases:
        entities = extractor.extract(text, intent)
        valid, error = extractor.validate_entities(entities, intent)

        print(f"\n输入: {text}")
        print(f"意图: {intent}")
        print(f"实体: {entities}")
        print(f"有效: {'是' if valid else f'否 ({error})'}")
