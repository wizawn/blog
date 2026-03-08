#!/usr/bin/env python3
"""
回测引擎
用于测试交易策略的历史表现
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.initial_capital = initial_capital
        self.commission = commission

        # 回测状态
        self.capital = initial_capital
        self.position = 0  # 持仓数量
        self.position_value = 0  # 持仓价值
        self.trades = []
        self.equity_curve = []

    def run_backtest(self, klines: List[Dict], strategy_func: Callable) -> Dict:
        """
        运行回测

        Args:
            klines: K线数据
            strategy_func: 策略函数，接收K线数据，返回信号

        Returns:
            回测结果
        """
        logger.info(f"开始回测，初始资金: ${self.initial_capital:.2f}")

        for i in range(len(klines)):
            # 获取当前K线和历史数据
            current_kline = klines[i]
            historical_klines = klines[:i+1]

            # 生成交易信号
            signal = strategy_func(historical_klines)

            # 执行交易
            if signal['signal'] == 'BUY' and self.position == 0:
                self._execute_buy(current_kline['close'])

            elif signal['signal'] == 'SELL' and self.position > 0:
                self._execute_sell(current_kline['close'])

            # 记录权益曲线
            current_equity = self.capital + (self.position * current_kline['close'])
            self.equity_curve.append({
                'timestamp': current_kline['close_time'],
                'equity': current_equity,
                'capital': self.capital,
                'position_value': self.position * current_kline['close']
            })

        # 如果还有持仓，按最后价格平仓
        if self.position > 0:
            self._execute_sell(klines[-1]['close'])

        # 计算绩效指标
        performance = self._calculate_performance()

        logger.info(f"回测完成，最终资金: ${self.capital:.2f}")

        return performance

    def _execute_buy(self, price: float):
        """执行买入"""
        # 计算可买数量（扣除手续费）
        available_capital = self.capital * (1 - self.commission)
        quantity = available_capital / price

        self.position = quantity
        self.capital = 0

        trade = {
            'type': 'BUY',
            'price': price,
            'quantity': quantity,
            'commission': self.capital * self.commission,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)

        logger.debug(f"买入: {quantity:.6f} @ ${price:.2f}")

    def _execute_sell(self, price: float):
        """执行卖出"""
        # 卖出所有持仓
        sell_value = self.position * price
        commission = sell_value * self.commission
        self.capital = sell_value - commission

        # 计算盈亏
        if self.trades:
            last_buy = [t for t in self.trades if t['type'] == 'BUY'][-1]
            pnl = (price - last_buy['price']) / last_buy['price'] * 100
        else:
            pnl = 0

        trade = {
            'type': 'SELL',
            'price': price,
            'quantity': self.position,
            'commission': commission,
            'pnl_percent': pnl,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)

        logger.debug(f"卖出: {self.position:.6f} @ ${price:.2f}, 盈亏: {pnl:+.2f}%")

        self.position = 0

    def _calculate_performance(self) -> Dict:
        """计算绩效指标"""
        # 总收益
        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100

        # 交易统计
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']

        total_trades = len(sell_trades)
        winning_trades = len([t for t in sell_trades if t.get('pnl_percent', 0) > 0])
        losing_trades = len([t for t in sell_trades if t.get('pnl_percent', 0) < 0])

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()

        # 夏普比率（简化版）
        sharpe_ratio = self._calculate_sharpe_ratio()

        # 平均盈亏
        avg_win = 0
        avg_loss = 0

        if winning_trades > 0:
            wins = [t['pnl_percent'] for t in sell_trades if t.get('pnl_percent', 0) > 0]
            avg_win = sum(wins) / len(wins)

        if losing_trades > 0:
            losses = [t['pnl_percent'] for t in sell_trades if t.get('pnl_percent', 0) < 0]
            avg_loss = sum(losses) / len(losses)

        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_commission': sum([t.get('commission', 0) for t in self.trades])
        }

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0

        peak = self.equity_curve[0]['equity']
        max_dd = 0

        for point in self.equity_curve:
            equity = point['equity']

            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak * 100
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def _calculate_sharpe_ratio(self) -> float:
        """计算夏普比率（简化版）"""
        if len(self.equity_curve) < 2:
            return 0

        # 计算收益率序列
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1]['equity']
            curr_equity = self.equity_curve[i]['equity']
            ret = (curr_equity - prev_equity) / prev_equity
            returns.append(ret)

        if not returns:
            return 0

        # 平均收益率
        avg_return = sum(returns) / len(returns)

        # 收益率标准差
        variance = sum([(r - avg_return) ** 2 for r in returns]) / len(returns)
        std_dev = variance ** 0.5

        # 夏普比率（假设无风险利率为0）
        if std_dev == 0:
            return 0

        sharpe = avg_return / std_dev * (252 ** 0.5)  # 年化

        return sharpe

    def print_report(self, performance: Dict):
        """打印回测报告"""
        print("\n" + "=" * 60)
        print("回测报告")
        print("=" * 60)

        print(f"\n资金情况:")
        print(f"初始资金: ${performance['initial_capital']:,.2f}")
        print(f"最终资金: ${performance['final_capital']:,.2f}")
        print(f"总收益率: {performance['total_return']:+.2f}%")

        print(f"\n交易统计:")
        print(f"总交易次数: {performance['total_trades']}")
        print(f"盈利次数: {performance['winning_trades']}")
        print(f"亏损次数: {performance['losing_trades']}")
        print(f"胜率: {performance['win_rate']:.2f}%")

        print(f"\n盈亏分析:")
        print(f"平均盈利: {performance['avg_win']:+.2f}%")
        print(f"平均亏损: {performance['avg_loss']:+.2f}%")

        print(f"\n风险指标:")
        print(f"最大回撤: {performance['max_drawdown']:.2f}%")
        print(f"夏普比率: {performance['sharpe_ratio']:.2f}")

        print(f"\n手续费:")
        print(f"总手续费: ${performance['total_commission']:.2f}")

        print("=" * 60 + "\n")


def create_backtest_engine(initial_capital: float = 10000,
                           commission: float = 0.001) -> BacktestEngine:
    """创建回测引擎"""
    return BacktestEngine(initial_capital, commission)


# 使用示例
if __name__ == "__main__":
    from ..api.binance_client import BinanceClient
    from ..analysis.indicators import TechnicalIndicators

    # 创建回测引擎
    engine = create_backtest_engine(initial_capital=10000)

    # 获取历史数据
    client = BinanceClient()
    indicators = TechnicalIndicators(client)
    klines = indicators.get_klines('BTCUSDT', '1h', limit=500)

    # 定义简单的均线交叉策略
    def ma_crossover_strategy(historical_klines):
        if len(historical_klines) < 30:
            return {'signal': 'HOLD'}

        closes = [k['close'] for k in historical_klines]
        fast_ma = sum(closes[-10:]) / 10
        slow_ma = sum(closes[-30:]) / 30

        if fast_ma > slow_ma:
            return {'signal': 'BUY'}
        elif fast_ma < slow_ma:
            return {'signal': 'SELL'}
        else:
            return {'signal': 'HOLD'}

    # 运行回测
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)

    performance = engine.run_backtest(klines, ma_crossover_strategy)
    engine.print_report(performance)
