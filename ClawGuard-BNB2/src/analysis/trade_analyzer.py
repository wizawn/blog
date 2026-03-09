#!/usr/bin/env python3
"""
交易历史分析模块
提供交易记录查询、盈亏统计、胜率分析等功能
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

from ..api.binance_client import BinanceClient
from ..utils.logger import get_logger, log_trade

logger = get_logger("trade_analyzer")


class TradeAnalyzer:
    """交易分析器"""

    def __init__(self, client: Optional[BinanceClient] = None):
        """
        初始化交易分析器

        Args:
            client: 币安API客户端
        """
        self.client = client or BinanceClient()
        self.cache_dir = Path.home() / ".clawguard" / "data" / "trades"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_trade_history(self, symbol: str, limit: int = 500) -> List[Dict]:
        """
        获取交易历史

        Args:
            symbol: 交易对
            limit: 返回数量（最大1000）

        Returns:
            交易历史列表
        """
        try:
            # 调用币安API获取交易历史
            endpoint = "/api/v3/myTrades"
            params = {
                "symbol": symbol,
                "limit": min(limit, 1000)
            }

            trades = self.client._signed_request("GET", endpoint, params)

            # 格式化交易数据
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    'id': trade['id'],
                    'order_id': trade['orderId'],
                    'symbol': trade['symbol'],
                    'price': float(trade['price']),
                    'quantity': float(trade['qty']),
                    'quote_quantity': float(trade['quoteQty']),
                    'commission': float(trade['commission']),
                    'commission_asset': trade['commissionAsset'],
                    'time': trade['time'],
                    'is_buyer': trade['isBuyer'],
                    'is_maker': trade['isMaker'],
                })

            logger.info(f"获取交易历史: {symbol}, 数量: {len(formatted_trades)}")
            return formatted_trades

        except Exception as e:
            logger.error(f"获取交易历史失败: {e}", exc_info=True)
            return []

    def get_order_history(self, symbol: str, limit: int = 500) -> List[Dict]:
        """
        获取订单历史

        Args:
            symbol: 交易对
            limit: 返回数量（最大1000）

        Returns:
            订单历史列表
        """
        try:
            endpoint = "/api/v3/allOrders"
            params = {
                "symbol": symbol,
                "limit": min(limit, 1000)
            }

            orders = self.client._signed_request("GET", endpoint, params)

            # 格式化订单数据
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'status': order['status'],
                    'type': order['type'],
                    'side': order['side'],
                    'price': float(order.get('price', 0)),
                    'quantity': float(order['origQty']),
                    'executed_quantity': float(order['executedQty']),
                    'cumulative_quote_qty': float(order.get('cummulativeQuoteQty', 0)),
                    'time': order['time'],
                    'update_time': order['updateTime'],
                })

            logger.info(f"获取订单历史: {symbol}, 数量: {len(formatted_orders)}")
            return formatted_orders

        except Exception as e:
            logger.error(f"获取订单历史失败: {e}", exc_info=True)
            return []

    def calculate_pnl(self, trades: List[Dict]) -> Dict:
        """
        计算盈亏

        Args:
            trades: 交易列表

        Returns:
            盈亏统计
        """
        if not trades:
            return {
                'total_pnl': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_commission': 0
            }

        # 按交易对分组
        positions = {}
        total_commission = 0

        for trade in trades:
            symbol = trade['symbol']
            if symbol not in positions:
                positions[symbol] = {
                    'quantity': 0,
                    'cost': 0,
                    'trades': []
                }

            quantity = trade['quantity']
            price = trade['price']
            is_buyer = trade['is_buyer']
            commission = trade['commission']

            total_commission += commission

            if is_buyer:
                # 买入
                positions[symbol]['quantity'] += quantity
                positions[symbol]['cost'] += quantity * price
            else:
                # 卖出
                if positions[symbol]['quantity'] > 0:
                    # 计算这笔卖出的盈亏
                    avg_cost = positions[symbol]['cost'] / positions[symbol]['quantity']
                    pnl = (price - avg_cost) * quantity

                    positions[symbol]['trades'].append({
                        'pnl': pnl,
                        'quantity': quantity,
                        'price': price,
                        'time': trade['time']
                    })

                    # 更新持仓
                    positions[symbol]['quantity'] -= quantity
                    if positions[symbol]['quantity'] > 0:
                        positions[symbol]['cost'] -= avg_cost * quantity
                    else:
                        positions[symbol]['cost'] = 0

        # 统计盈亏
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0

        for symbol, position in positions.items():
            for trade in position['trades']:
                pnl = trade['pnl']
                total_pnl += pnl

                if pnl > 0:
                    winning_trades += 1
                elif pnl < 0:
                    losing_trades += 1

        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_pnl': round(total_pnl, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_commission': round(total_commission, 2),
            'positions': positions
        }

    def generate_report(self, symbol: str, days: int = 30) -> str:
        """
        生成交易报告

        Args:
            symbol: 交易对
            days: 统计天数

        Returns:
            报告文本
        """
        logger.info(f"生成交易报告: {symbol}, 天数: {days}")

        # 获取交易历史
        trades = self.get_trade_history(symbol, limit=1000)

        if not trades:
            return "暂无交易记录"

        # 过滤指定天数内的交易
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        recent_trades = [t for t in trades if t['time'] >= cutoff_time]

        # 计算盈亏
        pnl_stats = self.calculate_pnl(recent_trades)

        # 生成报告
        report = []
        report.append("=" * 60)
        report.append(f"📊 {symbol} 交易报告 ({days}天)")
        report.append("=" * 60)
        report.append("")

        report.append("📈 盈亏统计")
        report.append("─" * 60)
        report.append(f"总盈亏: {pnl_stats['total_pnl']:+.2f} USDT")
        report.append(f"总交易次数: {pnl_stats['total_trades']}")
        report.append(f"盈利次数: {pnl_stats['winning_trades']}")
        report.append(f"亏损次数: {pnl_stats['losing_trades']}")
        report.append(f"胜率: {pnl_stats['win_rate']:.2f}%")
        report.append(f"总手续费: {pnl_stats['total_commission']:.2f} USDT")
        report.append("")

        # 平均盈亏
        if pnl_stats['total_trades'] > 0:
            avg_pnl = pnl_stats['total_pnl'] / pnl_stats['total_trades']
            report.append(f"平均每笔盈亏: {avg_pnl:+.2f} USDT")

        if pnl_stats['winning_trades'] > 0:
            avg_win = sum(t['pnl'] for p in pnl_stats['positions'].values()
                         for t in p['trades'] if t['pnl'] > 0) / pnl_stats['winning_trades']
            report.append(f"平均盈利: +{avg_win:.2f} USDT")

        if pnl_stats['losing_trades'] > 0:
            avg_loss = sum(t['pnl'] for p in pnl_stats['positions'].values()
                          for t in p['trades'] if t['pnl'] < 0) / pnl_stats['losing_trades']
            report.append(f"平均亏损: {avg_loss:.2f} USDT")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def get_performance_metrics(self, symbol: str, days: int = 30) -> Dict:
        """
        获取绩效指标

        Args:
            symbol: 交易对
            days: 统计天数

        Returns:
            绩效指标字典
        """
        trades = self.get_trade_history(symbol, limit=1000)

        if not trades:
            return {}

        # 过滤指定天数内的交易
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        recent_trades = [t for t in trades if t['time'] >= cutoff_time]

        pnl_stats = self.calculate_pnl(recent_trades)

        # 计算更多指标
        metrics = {
            'symbol': symbol,
            'period_days': days,
            'total_pnl': pnl_stats['total_pnl'],
            'total_trades': pnl_stats['total_trades'],
            'winning_trades': pnl_stats['winning_trades'],
            'losing_trades': pnl_stats['losing_trades'],
            'win_rate': pnl_stats['win_rate'],
            'total_commission': pnl_stats['total_commission'],
        }

        # 计算盈亏比
        if pnl_stats['winning_trades'] > 0 and pnl_stats['losing_trades'] > 0:
            avg_win = sum(t['pnl'] for p in pnl_stats['positions'].values()
                         for t in p['trades'] if t['pnl'] > 0) / pnl_stats['winning_trades']
            avg_loss = abs(sum(t['pnl'] for p in pnl_stats['positions'].values()
                              for t in p['trades'] if t['pnl'] < 0) / pnl_stats['losing_trades'])

            metrics['profit_loss_ratio'] = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0
            metrics['avg_win'] = round(avg_win, 2)
            metrics['avg_loss'] = round(-avg_loss, 2)

        # 计算交易频率
        if recent_trades:
            first_trade_time = min(t['time'] for t in recent_trades)
            last_trade_time = max(t['time'] for t in recent_trades)
            time_span_days = (last_trade_time - first_trade_time) / (1000 * 86400)

            if time_span_days > 0:
                metrics['trades_per_day'] = round(len(recent_trades) / time_span_days, 2)

        return metrics

    def save_report(self, symbol: str, days: int = 30):
        """
        保存交易报告到文件

        Args:
            symbol: 交易对
            days: 统计天数
        """
        report = self.generate_report(symbol, days)
        metrics = self.get_performance_metrics(symbol, days)

        # 保存文本报告
        report_file = self.cache_dir / f"{symbol}_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        # 保存JSON数据
        metrics_file = self.cache_dir / f"{symbol}_metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        logger.info(f"交易报告已保存: {report_file}")
        logger.info(f"绩效指标已保存: {metrics_file}")

        return report_file, metrics_file


# 便捷函数
def create_analyzer(client: Optional[BinanceClient] = None) -> TradeAnalyzer:
    """创建交易分析器"""
    return TradeAnalyzer(client)


def analyze_trades(symbol: str, days: int = 30) -> str:
    """分析交易（便捷函数）"""
    analyzer = create_analyzer()
    return analyzer.generate_report(symbol, days)


if __name__ == "__main__":
    # 测试交易分析
    analyzer = create_analyzer()

    # 生成报告
    report = analyzer.generate_report("BTCUSDT", days=30)
    print(report)

    # 获取绩效指标
    metrics = analyzer.get_performance_metrics("BTCUSDT", days=30)
    print("\n绩效指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
