#!/usr/bin/env python3
"""
合约风控系统
提供合约交易的风险控制功能
"""

from typing import Dict, Optional, Tuple
import logging

from ..config.config_manager import ConfigManager
from ..api.binance_futures_client import BinanceFuturesClient

logger = logging.getLogger(__name__)


class FuturesRiskControl:
    """合约风控系统"""

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        初始化风控系统

        Args:
            config: 配置管理器
        """
        self.config = config or ConfigManager()
        self.client = BinanceFuturesClient(config=self.config)

        # 加载风控配置
        self.max_leverage = self.config.get('futures_risk.max_leverage', 5)
        self.max_position_value = self.config.get('futures_risk.max_position_value', 10000)
        self.liquidation_buffer = self.config.get('futures_risk.liquidation_buffer', 0.1)
        self.max_funding_rate = self.config.get('futures_risk.max_funding_rate', 0.01)

    def check_leverage(self, symbol: str, leverage: int) -> Tuple[bool, Optional[str]]:
        """
        检查杠杆倍数

        Args:
            symbol: 交易对
            leverage: 杠杆倍数

        Returns:
            (是否通过, 错误信息)
        """
        if leverage < 1:
            return False, "杠杆倍数不能小于1"

        if leverage > 125:
            return False, "杠杆倍数不能大于125"

        if leverage > self.max_leverage:
            return False, f"杠杆倍数超过风控限制 (最大: {self.max_leverage}倍)"

        logger.info(f"Leverage check passed: {symbol} {leverage}x")
        return True, None

    def check_position_value(self, symbol: str, quantity: float, price: float) -> Tuple[bool, Optional[str]]:
        """
        检查持仓价值

        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格

        Returns:
            (是否通过, 错误信息)
        """
        position_value = abs(quantity * price)

        if position_value > self.max_position_value:
            return False, f"持仓价值超过风控限制 (最大: ${self.max_position_value:,.2f})"

        logger.info(f"Position value check passed: {symbol} ${position_value:,.2f}")
        return True, None

    def check_liquidation_risk(self, symbol: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        检查强平风险

        Args:
            symbol: 交易对

        Returns:
            (是否安全, 警告信息, 风险详情)
        """
        try:
            # 获取持仓信息
            positions = self.client.get_position_risk(symbol)

            if not positions:
                return True, None, None

            for position in positions:
                position_amt = float(position.get('positionAmt', 0))

                if position_amt == 0:
                    continue

                # 计算强平价格距离
                entry_price = float(position.get('entryPrice', 0))
                liquidation_price = float(position.get('liquidationPrice', 0))
                mark_price = float(position.get('markPrice', 0))

                if liquidation_price == 0:
                    continue

                # 计算距离强平的百分比
                if position_amt > 0:  # 多头
                    distance_pct = (mark_price - liquidation_price) / mark_price
                else:  # 空头
                    distance_pct = (liquidation_price - mark_price) / mark_price

                risk_info = {
                    'symbol': symbol,
                    'position_amt': position_amt,
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'liquidation_price': liquidation_price,
                    'distance_pct': distance_pct * 100,
                    'leverage': int(position.get('leverage', 1))
                }

                # 检查是否接近强平
                if distance_pct < self.liquidation_buffer:
                    warning = f"⚠️ 强平风险警告: 距离强平仅 {distance_pct*100:.2f}%"
                    logger.warning(f"Liquidation risk: {symbol} {distance_pct*100:.2f}%")
                    return False, warning, risk_info

                logger.info(f"Liquidation check passed: {symbol} {distance_pct*100:.2f}%")
                return True, None, risk_info

            return True, None, None

        except Exception as e:
            logger.error(f"Liquidation check failed: {e}")
            return False, f"强平检查失败: {str(e)}", None

    def check_funding_rate(self, symbol: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        检查资金费率

        Args:
            symbol: 交易对

        Returns:
            (是否通过, 警告信息, 资金费率)
        """
        try:
            funding_rates = self.client.get_funding_rate(symbol, limit=1)

            if not funding_rates:
                return True, None, None

            latest_rate = float(funding_rates[0].get('fundingRate', 0))

            if abs(latest_rate) > self.max_funding_rate:
                warning = f"⚠️ 资金费率过高: {latest_rate*100:.4f}%"
                logger.warning(f"High funding rate: {symbol} {latest_rate*100:.4f}%")
                return False, warning, latest_rate

            logger.info(f"Funding rate check passed: {symbol} {latest_rate*100:.4f}%")
            return True, None, latest_rate

        except Exception as e:
            logger.error(f"Funding rate check failed: {e}")
            return False, f"资金费率检查失败: {str(e)}", None

    def calculate_position_size(self, symbol: str, risk_amount: float,
                               entry_price: float, stop_loss_price: float,
                               leverage: int = 1) -> Dict:
        """
        计算建议仓位大小

        Args:
            symbol: 交易对
            risk_amount: 风险金额 (USDT)
            entry_price: 入场价格
            stop_loss_price: 止损价格
            leverage: 杠杆倍数

        Returns:
            仓位建议
        """
        # 计算每单位风险
        price_diff = abs(entry_price - stop_loss_price)
        risk_per_unit = price_diff

        # 计算建议数量
        suggested_quantity = risk_amount / risk_per_unit

        # 计算所需保证金
        position_value = suggested_quantity * entry_price
        required_margin = position_value / leverage

        # 计算风险回报比
        risk_reward_ratio = price_diff / entry_price

        return {
            'symbol': symbol,
            'suggested_quantity': suggested_quantity,
            'position_value': position_value,
            'required_margin': required_margin,
            'leverage': leverage,
            'risk_amount': risk_amount,
            'risk_reward_ratio': risk_reward_ratio,
            'entry_price': entry_price,
            'stop_loss_price': stop_loss_price
        }

    def validate_order(self, symbol: str, side: str, quantity: float,
                      price: Optional[float] = None, leverage: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        验证订单

        Args:
            symbol: 交易对
            side: 方向
            quantity: 数量
            price: 价格
            leverage: 杠杆

        Returns:
            (是否通过, 错误信息)
        """
        # 获取当前价格
        if not price:
            try:
                ticker = self.client.get_ticker_price(symbol)
                price = float(ticker.get('lastPrice', 0))
            except Exception as e:
                return False, f"获取价格失败: {str(e)}"

        # 检查杠杆
        if leverage:
            passed, error = self.check_leverage(symbol, leverage)
            if not passed:
                return False, error

        # 检查持仓价值
        passed, error = self.check_position_value(symbol, quantity, price)
        if not passed:
            return False, error

        # 检查强平风险
        passed, warning, risk_info = self.check_liquidation_risk(symbol)
        if not passed:
            return False, warning

        # 检查资金费率
        passed, warning, funding_rate = self.check_funding_rate(symbol)
        if not passed:
            # 资金费率警告不阻止交易，只提示
            logger.warning(warning)

        logger.info(f"Order validation passed: {symbol} {side} {quantity}")
        return True, None

    def get_risk_summary(self, symbol: Optional[str] = None) -> Dict:
        """
        获取风险摘要

        Args:
            symbol: 交易对（可选）

        Returns:
            风险摘要
        """
        try:
            # 获取账户信息
            account = self.client.get_account_info()
            total_balance = float(account.get('totalWalletBalance', 0))
            total_unrealized_pnl = float(account.get('totalUnrealizedProfit', 0))

            # 获取持仓
            positions = self.client.get_position_risk(symbol)

            position_summary = []
            total_position_value = 0

            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))

                if position_amt == 0:
                    continue

                mark_price = float(pos.get('markPrice', 0))
                position_value = abs(position_amt * mark_price)
                total_position_value += position_value

                liquidation_price = float(pos.get('liquidationPrice', 0))

                # 计算距离强平百分比
                if liquidation_price > 0:
                    if position_amt > 0:
                        distance_pct = (mark_price - liquidation_price) / mark_price * 100
                    else:
                        distance_pct = (liquidation_price - mark_price) / mark_price * 100
                else:
                    distance_pct = 100

                position_summary.append({
                    'symbol': pos['symbol'],
                    'position_amt': position_amt,
                    'position_value': position_value,
                    'leverage': int(pos.get('leverage', 1)),
                    'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                    'liquidation_price': liquidation_price,
                    'distance_to_liquidation_pct': distance_pct
                })

            # 计算风险指标
            position_ratio = (total_position_value / total_balance) if total_balance > 0 else 0

            return {
                'total_balance': total_balance,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_position_value': total_position_value,
                'position_ratio': position_ratio,
                'positions': position_summary,
                'risk_level': self._calculate_risk_level(position_ratio, position_summary)
            }

        except Exception as e:
            logger.error(f"Get risk summary failed: {e}")
            return {
                'error': str(e)
            }

    def _calculate_risk_level(self, position_ratio: float, positions: list) -> str:
        """计算风险等级"""
        # 检查持仓比例
        if position_ratio > 0.8:
            return 'HIGH'
        elif position_ratio > 0.5:
            return 'MEDIUM'

        # 检查强平距离
        for pos in positions:
            if pos['distance_to_liquidation_pct'] < 10:
                return 'HIGH'
            elif pos['distance_to_liquidation_pct'] < 20:
                return 'MEDIUM'

        return 'LOW'


# 使用示例
if __name__ == "__main__":
    risk_control = FuturesRiskControl()

    print("=" * 60)
    print("合约风控系统测试")
    print("=" * 60)

    # 测试杠杆检查
    print("\n1. 杠杆检查:")
    passed, error = risk_control.check_leverage('BTCUSDT', 5)
    print(f"5倍杠杆: {'✅ 通过' if passed else f'❌ {error}'}")

    passed, error = risk_control.check_leverage('BTCUSDT', 20)
    print(f"20倍杠杆: {'✅ 通过' if passed else f'❌ {error}'}")

    # 测试仓位计算
    print("\n2. 仓位计算:")
    suggestion = risk_control.calculate_position_size(
        symbol='BTCUSDT',
        risk_amount=100,
        entry_price=68000,
        stop_loss_price=67000,
        leverage=5
    )
    print(f"建议数量: {suggestion['suggested_quantity']:.4f}")
    print(f"所需保证金: ${suggestion['required_margin']:.2f}")

    # 获取风险摘要
    print("\n3. 风险摘要:")
    summary = risk_control.get_risk_summary()
    if 'error' not in summary:
        print(f"总权益: ${summary['total_balance']:.2f}")
        print(f"持仓价值: ${summary['total_position_value']:.2f}")
        print(f"风险等级: {summary['risk_level']}")
