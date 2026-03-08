#!/usr/bin/env python3
"""
突破策略
基于价格突破关键支撑/阻力位进行交易
"""

from typing import Dict, List, Optional
import logging

from ..api.binance_client import BinanceClient
from ..analysis.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class BreakoutStrategy:
    """突破策略"""

    def __init__(self, symbol: str, lookback_period: int = 20,
                 breakout_threshold: float = 0.02, interval: str = '1h',
                 client: Optional[BinanceClient] = None):
        """
        初始化策略

        Args:
            symbol: 交易对
            lookback_period: 回看周期
            breakout_threshold: 突破阈值（百分比）
            interval: 时间间隔
            client: API客户端
        """
        self.symbol = symbol
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.interval = interval
        self.client = client or BinanceClient()
        self.indicators = TechnicalIndicators(self.client)

        self.position = None
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.trades = []

    def calculate_support_resistance(self, klines: List[Dict]) -> Dict:
        """
        计算支撑和阻力位

        Args:
            klines: K线数据

        Returns:
            支撑和阻力位
        """
        if len(klines) < self.lookback_period:
            return {'support': 0, 'resistance': 0}

        # 取最近N根K线
        recent_klines = klines[-self.lookback_period:]

        # 计算支撑位（最低价）
        support = min([k['low'] for k in recent_klines])

        # 计算阻力位（最高价）
        resistance = max([k['high'] for k in recent_klines])

        return {
            'support': support,
            'resistance': resistance,
            'range': resistance - support,
            'range_percent': (resistance - support) / support * 100
        }

    def generate_signal(self) -> Dict:
        """
        生成交易信号

        Returns:
            信号字典
        """
        # 获取K线数据
        klines = self.indicators.get_klines(
            self.symbol,
            self.interval,
            limit=self.lookback_period + 10
        )

        if len(klines) < self.lookback_period:
            return {'signal': 'HOLD', 'reason': '数据不足'}

        # 计算支撑和阻力位
        levels = self.calculate_support_resistance(klines[:-1])  # 不包括当前K线
        current_price = klines[-1]['close']
        current_high = klines[-1]['high']
        current_low = klines[-1]['low']

        support = levels['support']
        resistance = levels['resistance']

        signal = 'HOLD'
        reason = ''

        # 向上突破阻力位
        if current_high > resistance * (1 + self.breakout_threshold):
            signal = 'BUY'
            reason = f'向上突破阻力位: {current_high:.2f} > {resistance:.2f}'
            # 设置止损和止盈
            self.stop_loss = resistance * 0.98  # 阻力位下方2%
            self.take_profit = current_price * 1.05  # 当前价格上方5%

        # 向下突破支撑位
        elif current_low < support * (1 - self.breakout_threshold):
            signal = 'SELL'
            reason = f'向下突破支撑位: {current_low:.2f} < {support:.2f}'
            self.stop_loss = support * 1.02  # 支撑位上方2%
            self.take_profit = current_price * 0.95  # 当前价格下方5%

        # 在区间内
        else:
            distance_to_resistance = (resistance - current_price) / current_price * 100
            distance_to_support = (current_price - support) / current_price * 100
            reason = f'区间震荡: 支撑{support:.2f}(-{distance_to_support:.1f}%) - 阻力{resistance:.2f}(+{distance_to_resistance:.1f}%)'

        return {
            'signal': signal,
            'reason': reason,
            'current_price': current_price,
            'support': support,
            'resistance': resistance,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timestamp': klines[-1]['close_time']
        }

    def check_exit_conditions(self, current_price: float) -> Dict:
        """
        检查退出条件

        Args:
            current_price: 当前价格

        Returns:
            退出信号
        """
        if not self.position:
            return {'should_exit': False}

        # 检查止损
        if self.position == 'LONG' and current_price <= self.stop_loss:
            return {
                'should_exit': True,
                'reason': f'触发止损: {current_price:.2f} <= {self.stop_loss:.2f}',
                'type': 'STOP_LOSS'
            }

        # 检查止盈
        if self.position == 'LONG' and current_price >= self.take_profit:
            return {
                'should_exit': True,
                'reason': f'触发止盈: {current_price:.2f} >= {self.take_profit:.2f}',
                'type': 'TAKE_PROFIT'
            }

        return {'should_exit': False}

    def execute_signal(self, signal: Dict, quantity: float) -> Dict:
        """
        执行交易信号

        Args:
            signal: 交易信号
            quantity: 交易数量

        Returns:
            执行结果
        """
        if signal['signal'] == 'HOLD':
            return {'success': False, 'message': '无交易信号'}

        try:
            if signal['signal'] == 'BUY':
                order = self.client.place_market_order(self.symbol, 'BUY', quantity)
                self.position = 'LONG'
                self.entry_price = signal['current_price']

                trade = {
                    'type': 'BUY',
                    'price': signal['current_price'],
                    'quantity': quantity,
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'timestamp': signal['timestamp'],
                    'order_id': order.get('orderId')
                }
                self.trades.append(trade)

                return {
                    'success': True,
                    'message': f"买入成功: {quantity} @ {signal['current_price']:.2f}",
                    'trade': trade
                }

            elif signal['signal'] == 'SELL':
                order = self.client.place_market_order(self.symbol, 'SELL', quantity)

                pnl = 0
                if self.position == 'LONG' and self.entry_price > 0:
                    pnl = (signal['current_price'] - self.entry_price) / self.entry_price * 100

                self.position = None
                self.entry_price = 0

                trade = {
                    'type': 'SELL',
                    'price': signal['current_price'],
                    'quantity': quantity,
                    'timestamp': signal['timestamp'],
                    'order_id': order.get('orderId'),
                    'pnl_percent': pnl
                }
                self.trades.append(trade)

                return {
                    'success': True,
                    'message': f"卖出成功: {quantity} @ {signal['current_price']:.2f}, 盈亏: {pnl:+.2f}%",
                    'trade': trade
                }

        except Exception as e:
            logger.error(f"执行交易失败: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}

    def print_status(self):
        """打印策略状态"""
        print("\n" + "=" * 60)
        print(f"突破策略 - {self.symbol}")
        print("=" * 60)
        print(f"回看周期: {self.lookback_period}")
        print(f"突破阈值: {self.breakout_threshold * 100:.1f}%")
        print(f"时间间隔: {self.interval}")
        print(f"当前持仓: {self.position or '无'}")

        if self.position and self.entry_price > 0:
            print(f"入场价格: ${self.entry_price:.2f}")
            print(f"止损价格: ${self.stop_loss:.2f}")
            print(f"止盈价格: ${self.take_profit:.2f}")

        # 获取当前信号
        signal = self.generate_signal()
        print(f"\n当前信号: {signal['signal']}")
        print(f"原因: {signal['reason']}")
        print(f"支撑位: ${signal['support']:.2f}")
        print(f"阻力位: ${signal['resistance']:.2f}")

        print("=" * 60 + "\n")


def create_breakout_strategy(symbol: str, lookback_period: int = 20,
                             breakout_threshold: float = 0.02,
                             interval: str = '1h') -> BreakoutStrategy:
    """创建突破策略"""
    return BreakoutStrategy(symbol, lookback_period, breakout_threshold, interval)


# 使用示例
if __name__ == "__main__":
    strategy = create_breakout_strategy('BTCUSDT', lookback_period=20)

    print("=" * 60)
    print("突破策略测试")
    print("=" * 60)

    # 生成信号
    signal = strategy.generate_signal()
    print(f"\n信号: {signal['signal']}")
    print(f"原因: {signal['reason']}")

    # 打印状态
    strategy.print_status()
