#!/usr/bin/env python3
"""
合约网格策略
在合约市场使用网格交易策略
"""

from typing import Dict, List, Optional
import logging

from ..api.binance_futures_client import BinanceFuturesClient
from ..risk.futures_risk_control import FuturesRiskControl

logger = logging.getLogger(__name__)


class FuturesGridStrategy:
    """合约网格策略"""

    def __init__(self, symbol: str, lower_price: float, upper_price: float,
                 grid_count: int, investment: float, leverage: int = 3,
                 client: Optional[BinanceFuturesClient] = None):
        """
        初始化合约网格策略

        Args:
            symbol: 交易对
            lower_price: 网格下限
            upper_price: 网格上限
            grid_count: 网格数量
            investment: 投资金额
            leverage: 杠杆倍数
            client: 合约客户端
        """
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_count = grid_count
        self.investment = investment
        self.leverage = leverage
        self.client = client or BinanceFuturesClient()
        self.risk_control = FuturesRiskControl()

        # 计算网格参数
        self.grid_step = (upper_price - lower_price) / grid_count
        self.grid_levels = [lower_price + i * self.grid_step for i in range(grid_count + 1)]
        self.quantity_per_grid = investment / grid_count / lower_price

        self.active_orders = []
        self.filled_orders = []
        self.running = False

    def setup(self) -> Dict:
        """
        设置策略（设置杠杆等）

        Returns:
            设置结果
        """
        try:
            # 风控检查
            passed, error = self.risk_control.check_leverage(self.symbol, self.leverage)
            if not passed:
                return {'success': False, 'error': error}

            # 设置杠杆
            result = self.client.change_leverage(self.symbol, self.leverage)
            logger.info(f"杠杆已设置: {self.leverage}x")

            return {
                'success': True,
                'leverage': result.get('leverage'),
                'message': f'策略设置完成，杠杆: {self.leverage}x'
            }

        except Exception as e:
            logger.error(f"策略设置失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def place_grid_orders(self) -> Dict:
        """
        放置网格订单

        Returns:
            放置结果
        """
        try:
            # 获取当前价格
            ticker = self.client.get_ticker_price(self.symbol)
            current_price = float(ticker.get('lastPrice', 0))

            placed_orders = []

            # 在当前价格下方放置买单
            for level in self.grid_levels:
                if level < current_price:
                    try:
                        order = self.client.place_limit_order(
                            symbol=self.symbol,
                            side='BUY',
                            quantity=self.quantity_per_grid,
                            price=level
                        )
                        placed_orders.append({
                            'level': level,
                            'side': 'BUY',
                            'order_id': order.get('orderId')
                        })
                        logger.info(f"买单已放置: {level:.2f}")
                    except Exception as e:
                        logger.error(f"放置买单失败 @ {level:.2f}: {e}")

            # 在当前价格上方放置卖单
            for level in self.grid_levels:
                if level > current_price:
                    try:
                        order = self.client.place_limit_order(
                            symbol=self.symbol,
                            side='SELL',
                            quantity=self.quantity_per_grid,
                            price=level
                        )
                        placed_orders.append({
                            'level': level,
                            'side': 'SELL',
                            'order_id': order.get('orderId')
                        })
                        logger.info(f"卖单已放置: {level:.2f}")
                    except Exception as e:
                        logger.error(f"放置卖单失败 @ {level:.2f}: {e}")

            self.active_orders = placed_orders

            return {
                'success': True,
                'placed_orders': len(placed_orders),
                'message': f'已放置 {len(placed_orders)} 个网格订单'
            }

        except Exception as e:
            logger.error(f"放置网格订单失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def start(self) -> Dict:
        """
        启动策略

        Returns:
            启动结果
        """
        # 设置策略
        setup_result = self.setup()
        if not setup_result['success']:
            return setup_result

        # 放置网格订单
        orders_result = self.place_grid_orders()
        if not orders_result['success']:
            return orders_result

        self.running = True

        return {
            'success': True,
            'message': '合约网格策略已启动',
            'details': {
                'leverage': self.leverage,
                'grid_count': self.grid_count,
                'placed_orders': orders_result['placed_orders']
            }
        }

    def stop(self) -> Dict:
        """
        停止策略

        Returns:
            停止结果
        """
        try:
            # 取消所有活跃订单
            result = self.client.cancel_all_orders(self.symbol)

            self.running = False
            self.active_orders = []

            return {
                'success': True,
                'message': '合约网格策略已停止'
            }

        except Exception as e:
            logger.error(f"停止策略失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_performance(self) -> Dict:
        """
        获取策略表现

        Returns:
            表现统计
        """
        try:
            # 获取持仓信息
            positions = self.client.get_position_risk(self.symbol)

            total_pnl = 0
            for pos in positions:
                if float(pos.get('positionAmt', 0)) != 0:
                    total_pnl += float(pos.get('unRealizedProfit', 0))

            return {
                'running': self.running,
                'active_orders': len(self.active_orders),
                'filled_orders': len(self.filled_orders),
                'unrealized_pnl': total_pnl,
                'grid_levels': len(self.grid_levels)
            }

        except Exception as e:
            logger.error(f"获取表现失败: {e}", exc_info=True)
            return {'error': str(e)}

    def print_status(self):
        """打印策略状态"""
        print("\n" + "=" * 60)
        print(f"合约网格策略 - {self.symbol}")
        print("=" * 60)
        print(f"价格区间: ${self.lower_price:.2f} - ${self.upper_price:.2f}")
        print(f"网格数量: {self.grid_count}")
        print(f"网格间距: ${self.grid_step:.2f}")
        print(f"杠杆倍数: {self.leverage}x")
        print(f"投资金额: ${self.investment:.2f}")
        print(f"每格数量: {self.quantity_per_grid:.6f}")
        print(f"运行状态: {'运行中' if self.running else '已停止'}")

        # 表现统计
        perf = self.get_performance()
        if 'error' not in perf:
            print(f"\n策略表现:")
            print(f"活跃订单: {perf['active_orders']}")
            print(f"已成交订单: {perf['filled_orders']}")
            print(f"未实现盈亏: ${perf['unrealized_pnl']:.2f}")

        print("=" * 60 + "\n")


def create_futures_grid_strategy(symbol: str, lower_price: float, upper_price: float,
                                 grid_count: int, investment: float,
                                 leverage: int = 3) -> FuturesGridStrategy:
    """创建合约网格策略"""
    return FuturesGridStrategy(symbol, lower_price, upper_price, grid_count, investment, leverage)


# 使用示例
if __name__ == "__main__":
    strategy = create_futures_grid_strategy(
        symbol='BTCUSDT',
        lower_price=65000,
        upper_price=70000,
        grid_count=10,
        investment=1000,
        leverage=3
    )

    print("=" * 60)
    print("合约网格策略测试")
    print("=" * 60)

    strategy.print_status()
