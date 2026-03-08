#!/usr/bin/env python3
"""
输入验证器 - 防止注入攻击和参数错误
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation


class InputValidator:
    """输入验证器"""

    # 币安支持的交易对格式
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}(USDT|BUSD|BTC|ETH|BNB)$')

    # 支持的订单类型
    VALID_ORDER_TYPES = {'MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT'}

    # 支持的订单方向
    VALID_SIDES = {'BUY', 'SELL'}

    # 支持的时间周期
    VALID_INTERVALS = {'1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'}

    @staticmethod
    def validate_symbol(symbol: str) -> Tuple[bool, str]:
        """
        验证交易对格式

        Args:
            symbol: 交易对，如 BTCUSDT

        Returns:
            (是否有效, 错误信息)
        """
        if not symbol:
            return False, "交易对不能为空"

        if not isinstance(symbol, str):
            return False, "交易对必须是字符串"

        # 转换为大写
        symbol = symbol.upper()

        # 长度检查
        if len(symbol) < 6 or len(symbol) > 20:
            return False, f"交易对长度不合法: {len(symbol)}"

        # 格式检查
        if not InputValidator.SYMBOL_PATTERN.match(symbol):
            return False, f"交易对格式不正确: {symbol}"

        return True, ""

    @staticmethod
    def validate_amount(amount: Any, min_amount: float = 0.00001, max_amount: float = 1000000) -> Tuple[bool, str, Optional[Decimal]]:
        """
        验证交易金额

        Args:
            amount: 金额
            min_amount: 最小金额
            max_amount: 最大金额

        Returns:
            (是否有效, 错误信息, 标准化后的金额)
        """
        if amount is None:
            return False, "金额不能为空", None

        # 转换为Decimal（避免浮点数精度问题）
        try:
            if isinstance(amount, str):
                amount_decimal = Decimal(amount)
            elif isinstance(amount, (int, float)):
                amount_decimal = Decimal(str(amount))
            else:
                return False, f"金额类型不支持: {type(amount)}", None
        except (InvalidOperation, ValueError) as e:
            return False, f"金额格式错误: {e}", None

        # 范围检查
        if amount_decimal <= 0:
            return False, "金额必须大于0", None

        if amount_decimal < Decimal(str(min_amount)):
            return False, f"金额过小，最小值: {min_amount}", None

        if amount_decimal > Decimal(str(max_amount)):
            return False, f"金额过大，最大值: {max_amount}", None

        return True, "", amount_decimal

    @staticmethod
    def validate_side(side: str) -> Tuple[bool, str]:
        """
        验证订单方向

        Args:
            side: BUY 或 SELL

        Returns:
            (是否有效, 错误信息)
        """
        if not side:
            return False, "订单方向不能为空"

        side = side.upper()

        if side not in InputValidator.VALID_SIDES:
            return False, f"订单方向不正确: {side}，支持: {InputValidator.VALID_SIDES}"

        return True, ""

    @staticmethod
    def validate_order_type(order_type: str) -> Tuple[bool, str]:
        """
        验证订单类型

        Args:
            order_type: 订单类型

        Returns:
            (是否有效, 错误信息)
        """
        if not order_type:
            return False, "订单类型不能为空"

        order_type = order_type.upper()

        if order_type not in InputValidator.VALID_ORDER_TYPES:
            return False, f"订单类型不正确: {order_type}"

        return True, ""

    @staticmethod
    def validate_interval(interval: str) -> Tuple[bool, str]:
        """
        验证K线周期

        Args:
            interval: 时间周期，如 1m, 1h, 1d

        Returns:
            (是否有效, 错误信息)
        """
        if not interval:
            return False, "时间周期不能为空"

        if interval not in InputValidator.VALID_INTERVALS:
            return False, f"时间周期不正确: {interval}"

        return True, ""

    @staticmethod
    def validate_limit(limit: int, max_limit: int = 1000) -> Tuple[bool, str]:
        """
        验证数据条数限制

        Args:
            limit: 数据条数
            max_limit: 最大条数

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(limit, int):
            return False, f"limit必须是整数，当前类型: {type(limit)}"

        if limit <= 0:
            return False, "limit必须大于0"

        if limit > max_limit:
            return False, f"limit过大，最大值: {max_limit}"

        return True, ""

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        清理字符串，移除危险字符

        Args:
            text: 输入文本
            max_length: 最大长度

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除危险字符
        dangerous_chars = r'[<>\"\';&|`$\n\r\t]'
        text = re.sub(dangerous_chars, '', text)

        # 限制长度
        return text[:max_length]

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """
        验证API Key格式

        Args:
            api_key: API Key

        Returns:
            (是否有效, 错误信息)
        """
        if not api_key:
            return False, "API Key不能为空"

        if not isinstance(api_key, str):
            return False, "API Key必须是字符串"

        # 长度检查（币安API Key通常为64字符）
        if len(api_key) < 32:
            return False, f"API Key长度过短: {len(api_key)}"

        if len(api_key) > 128:
            return False, f"API Key长度过长: {len(api_key)}"

        # 字符检查（只允许字母数字）
        if not re.match(r'^[A-Za-z0-9]+$', api_key):
            return False, "API Key包含非法字符"

        return True, ""

    @staticmethod
    def validate_price(price: Any, min_price: float = 0.00001) -> Tuple[bool, str, Optional[Decimal]]:
        """
        验证价格

        Args:
            price: 价格
            min_price: 最小价格

        Returns:
            (是否有效, 错误信息, 标准化后的价格)
        """
        if price is None:
            return False, "价格不能为空", None

        try:
            if isinstance(price, str):
                price_decimal = Decimal(price)
            elif isinstance(price, (int, float)):
                price_decimal = Decimal(str(price))
            else:
                return False, f"价格类型不支持: {type(price)}", None
        except (InvalidOperation, ValueError) as e:
            return False, f"价格格式错误: {e}", None

        if price_decimal <= 0:
            return False, "价格必须大于0", None

        if price_decimal < Decimal(str(min_price)):
            return False, f"价格过低，最小值: {min_price}", None

        return True, "", price_decimal


class ValidationError(Exception):
    """验证错误异常"""
    pass


def validate_trade_params(symbol: str, side: str, amount: Any, order_type: str = "MARKET",
                         price: Optional[Any] = None) -> Dict[str, Any]:
    """
    验证交易参数（一站式验证）

    Args:
        symbol: 交易对
        side: 方向
        amount: 金额
        order_type: 订单类型
        price: 价格（限价单必需）

    Returns:
        验证后的参数字典

    Raises:
        ValidationError: 验证失败
    """
    validator = InputValidator()
    errors = []

    # 验证交易对
    valid, msg = validator.validate_symbol(symbol)
    if not valid:
        errors.append(f"交易对错误: {msg}")

    # 验证方向
    valid, msg = validator.validate_side(side)
    if not valid:
        errors.append(f"方向错误: {msg}")

    # 验证金额
    valid, msg, amount_decimal = validator.validate_amount(amount)
    if not valid:
        errors.append(f"金额错误: {msg}")

    # 验证订单类型
    valid, msg = validator.validate_order_type(order_type)
    if not valid:
        errors.append(f"订单类型错误: {msg}")

    # 限价单必须有价格
    if order_type == "LIMIT":
        if price is None:
            errors.append("限价单必须指定价格")
        else:
            valid, msg, price_decimal = validator.validate_price(price)
            if not valid:
                errors.append(f"价格错误: {msg}")

    if errors:
        raise ValidationError("; ".join(errors))

    result = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "amount": float(amount_decimal),
        "order_type": order_type.upper()
    }

    if price is not None and order_type == "LIMIT":
        result["price"] = float(price_decimal)

    return result


# ============= 使用示例 =============

if __name__ == "__main__":
    validator = InputValidator()

    print("=" * 50)
    print("输入验证器测试")
    print("=" * 50)
    print()

    # 测试1: 交易对验证
    print("📋 测试交易对验证:")
    test_symbols = ["BTCUSDT", "btcusdt", "ETHBUSD", "INVALID", "BTC", ""]
    for symbol in test_symbols:
        valid, msg = validator.validate_symbol(symbol)
        status = "✅" if valid else "❌"
        print(f"  {status} {symbol:15s} - {msg if msg else 'OK'}")
    print()

    # 测试2: 金额验证
    print("📋 测试金额验证:")
    test_amounts = [100, "50.5", 0, -10, "abc", 0.00001, 1000000]
    for amount in test_amounts:
        valid, msg, normalized = validator.validate_amount(amount)
        status = "✅" if valid else "❌"
        print(f"  {status} {str(amount):15s} - {msg if msg else f'OK ({normalized})'}")
    print()

    # 测试3: 订单方向验证
    print("📋 测试订单方向验证:")
    test_sides = ["BUY", "buy", "SELL", "INVALID", ""]
    for side in test_sides:
        valid, msg = validator.validate_side(side)
        status = "✅" if valid else "❌"
        print(f"  {status} {side:15s} - {msg if msg else 'OK'}")
    print()

    # 测试4: 完整交易参数验证
    print("📋 测试完整交易参数:")
    try:
        params = validate_trade_params("BTCUSDT", "BUY", 100, "MARKET")
        print(f"  ✅ 验证通过: {params}")
    except ValidationError as e:
        print(f"  ❌ 验证失败: {e}")

    try:
        params = validate_trade_params("INVALID", "BUY", -100, "MARKET")
        print(f"  ✅ 验证通过: {params}")
    except ValidationError as e:
        print(f"  ❌ 验证失败: {e}")

    print()
    print("=" * 50)
