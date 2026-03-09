#!/usr/bin/env python3
"""
均线交叉策略
基于快速和慢速移动平均线的交叉信号进行交易
"""

from typing import Dict, List, Optional
import logging

from ..api.binance_client import BinanceClient
from ..analysis.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class MACrossoverStrategy:
    """均线交叉策略"""

    def __init__(self, symbol: str, fast_period: int = 10, slow_period: int = 30,
                 interval: str = '1h', client: Optional[BinanceClient] = None):
        """
        初始化策略

        Args:
            symbol: 交易对
            fast_period: 快速均线周期
            slow_period: 慢速均线周期
            interval: 时间间隔
            client: API客户端
        """
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.interval = interval
        self.client = client or BinanceClient()
        self.indicators = TechnicalIndicators(self.client)

        self.position = None  # 当前持仓 ('LONG', 'SHORT', None)
        self.entry_price = 0
        self.trades = []

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
            limit=self.slow_period + 50
        )

        if len(klines) < self.slow_period:
            return {'signal': 'HOLD', 'reason': '数据不足'}

        # 提取收盘价
        closes = [k['close'] for k in klines]

        # 计算快速和慢速均线
        fast_ma = self.indicators.calculate_ema(closes, self.fast_period)
        slow_ma = self.indicators.calculate_ema(closes, self.slow_period)

        if not fast_ma or not slow_ma:
            return {'signal': 'HOLD', 'reason': '指标计算失败'}

        # 当前值
        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        current_price = closes[-1]

        # 前一个值
        prev_fast = fast_ma[-2] if len(fast_ma) > 1 else current_fast
        prev_slow = slow_ma[-2] if len(slow_ma) > 1 else current_slow

        # 检测交叉
        signal = 'HOLD'
        reason = ''

        # 金叉：快线上穿慢线
        if prev_fast <= prev_slow and current_fast > current_slow:
            signal = 'BUY'
            reason = f'金叉：快线({current_fast:.2f})上穿慢线({current_slow:.2f})'

        # 死叉：快线下穿慢线
        elif prev_fast >= prev_slow and current_fast < current_slow:
            signal = 'SELL'
            reason = f'死叉：快线({current_fast:.2f})下穿慢线({current_slow:.2f})'

        else:
            # 判断当前趋势
            if current_fast > current_slow:
                reason = f'多头趋势：快线({current_fast:.2f}) > 慢线({current_slow:.2f})'
            else:
                reason = f'空头趋势：快线({current_fast:.2f}) < 慢线({current_slow:.2f})'

        return {
            'signal': signal,
            'reason': reason,
            'current_price': current_price,
            'fast_ma': current_fast,
            'slow_ma': current_slow,
            'timestamp': klines[-1]['close_time']
        }

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
                # 买入
                order = self.client.place_market_order(self.symbol, 'BUY', quantity)
                self.position = 'LONG'
                self.entry_price = signal['current_price']

                trade = {
                    'type': 'BUY',
                    'price': signal['current_price'],
                    'quantity': quantity,
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
                # 卖出
                order = self.client.place_market_order(self.symbol, 'SELL', quantity)

                # 计算盈亏
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

    def get_performance(self) -> Dict:
        """
        获取策略表现

        Returns:
            表现统计
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0
            }

        winning_trades = 0
        losing_trades = 0
        total_pnl = 0

        for trade in self.trades:
            if 'pnl_percent' in trade:
                pnl = trade['pnl_percent']
                total_pnl += pnl

                if pnl > 0:
                    winning_trades += 1
                elif pnl < 0:
                    losing_trades += 1

        total_trades = len([t for t in self.trades if 'pnl_percent' in t])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / total_trades if total_trades > 0 else 0
        }

    def print_status(self):
        """打印策略状态"""
        print("\n" + "=" * 60)
        print(f"均线交叉策略 - {self.symbol}")
        print("=" * 60)
        print(f"快速均线: {self.fast_period}")
        print(f"慢速均线: {self.slow_period}")
        print(f"时间间隔: {self.interval}")
        print(f"当前持仓: {self.position or '无'}")

        if self.position and self.entry_price > 0:
            print(f"入场价格: ${self.entry_price:.2f}")

        # 获取当前信号
        signal = self.generate_signal()
        print(f"\n当前信号: {signal['signal']}")
        print(f"原因: {signal['reason']}")

        # 表现统计
        perf = self.get_performance()
        if perf['total_trades'] > 0:
            print(f"\n策略表现:")
            print(f"总交易次数: {perf['total_trades']}")
            print(f"胜率: {perf['win_rate']:.2f}%")
            print(f"总盈亏: {perf['total_pnl']:+.2f}%")
            print(f"平均盈亏: {perf['avg_pnl']:+.2f}%")

        print("=" * 60 + "\n")


def create_ma_crossover_strategy(symbol: str, fast_period: int = 10,
                                 slow_period: int = 30, interval: str = '1h') -> MACrossoverStrategy:
    """创建均线交叉策略"""
    return MACrossoverStrategy(symbol, fast_period, slow_period, interval)


# 使用示例
if __name__ == "__main__":
    strategy = create_ma_crossover_strategy('BTCUSDT', fast_period=10, slow_period=30)

    print("=" * 60)
    print("均线交叉策略测试")
    print("=" * 60)

    # 生成信号
    signal = strategy.generate_signal()
    print(f"\n信号: {signal['signal']}")
    print(f"原因: {signal['reason']}")
    print(f"当前价格: ${signal['current_price']:.2f}")

    # 打印状态
    strategy.print_status()
