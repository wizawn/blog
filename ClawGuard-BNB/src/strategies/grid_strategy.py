#!/usr/bin/env python3
"""
网格交易策略引擎
实现自动化网格交易策略
"""

from typing import Dict, List, Optional, Callable
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path

from ..api.binance_client import BinanceClient
from ..risk.risk_control import RiskControlEngine
from ..utils.logger import get_logger, log_trade

logger = get_logger("grid_strategy")


class GridStrategy:
    """网格交易策略"""

    def __init__(self,
                 symbol: str,
                 lower_price: float,
                 upper_price: float,
                 grid_count: int,
                 investment: float,
                 client: Optional[BinanceClient] = None,
                 risk_engine: Optional[RiskControlEngine] = None):
        """
        初始化网格交易策略

        Args:
            symbol: 交易对
            lower_price: 网格下限价格
            upper_price: 网格上限价格
            grid_count: 网格数量
            investment: 投资金额（USDT）
            client: 币安API客户端
            risk_engine: 风控引擎
        """
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_count = grid_count
        self.investment = investment
        self.client = client or BinanceClient()
        self.risk_engine = risk_engine or RiskControlEngine()

        # 计算网格参数
        self.grid_step = (upper_price - lower_price) / grid_count
        self.grid_levels = [lower_price + i * self.grid_step for i in range(grid_count + 1)]
        self.amount_per_grid = investment / grid_count

        # 网格状态
        self.active_orders = {}  # {price: order_id}
        self.filled_orders = []
        self.total_profit = 0
        self.running = False

        # 配置目录
        self.config_dir = Path.home() / ".clawguard" / "data" / "grid_strategies"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"网格策略初始化: {symbol}")
        logger.info(f"  价格区间: ${lower_price:.2f} - ${upper_price:.2f}")
        logger.info(f"  网格数量: {grid_count}")
        logger.info(f"  每格金额: ${self.amount_per_grid:.2f}")

    def calculate_quantity(self, price: float) -> float:
        """
        计算交易数量

        Args:
            price: 价格

        Returns:
            数量
        """
        return self.amount_per_grid / price

    def place_buy_order(self, price: float) -> Optional[Dict]:
        """
        下买单

        Args:
            price: 价格

        Returns:
            订单信息
        """
        try:
            quantity = self.calculate_quantity(price)

            # 风控检查
            passed, msg = self.risk_engine.pre_trade_check(
                symbol=self.symbol,
                side="BUY",
                amount=self.amount_per_grid,
                account_balance=self.investment,
                current_price=price,
                has_real_trade_permission=True
            )

            if not passed:
                logger.warning(f"风控拒绝买单: {msg}")
                return None

            # 下限价买单
            order = self.client.place_order(
                symbol=self.symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force="GTC"
            )

            logger.info(f"买单已下: 价格=${price:.2f}, 数量={quantity:.6f}")
            log_trade(order['orderId'], self.symbol, "BUY", quantity, price, "NEW")

            return order

        except Exception as e:
            logger.error(f"下买单失败: {e}", exc_info=True)
            return None

    def place_sell_order(self, price: float, quantity: float) -> Optional[Dict]:
        """
        下卖单

        Args:
            price: 价格
            quantity: 数量

        Returns:
            订单信息
        """
        try:
            # 风控检查
            passed, msg = self.risk_engine.pre_trade_check(
                symbol=self.symbol,
                side="SELL",
                amount=price * quantity,
                account_balance=self.investment,
                current_price=price,
                has_real_trade_permission=True
            )

            if not passed:
                logger.warning(f"风控拒绝卖单: {msg}")
                return None

            # 下限价卖单
            order = self.client.place_order(
                symbol=self.symbol,
                side="SELL",
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                time_in_force="GTC"
            )

            logger.info(f"卖单已下: 价格=${price:.2f}, 数量={quantity:.6f}")
            log_trade(order['orderId'], self.symbol, "SELL", quantity, price, "NEW")

            return order

        except Exception as e:
            logger.error(f"下卖单失败: {e}", exc_info=True)
            return None

    def initialize_grid(self):
        """初始化网格（下所有买单）"""
        logger.info("初始化网格...")

        current_price = float(self.client.get_ticker_price(self.symbol)['price'])
        logger.info(f"当前价格: ${current_price:.2f}")

        # 在当前价格以下的网格下买单
        for price in self.grid_levels:
            if price < current_price:
                order = self.place_buy_order(price)
                if order:
                    self.active_orders[price] = order['orderId']

        logger.info(f"网格初始化完成，已下 {len(self.active_orders)} 个买单")

    def check_orders(self):
        """检查订单状态"""
        for price, order_id in list(self.active_orders.items()):
            try:
                # 查询订单状态
                order = self.client.get_order(self.symbol, order_id)
                status = order['status']

                if status == 'FILLED':
                    # 订单成交
                    logger.info(f"订单成交: {order_id}, 价格=${price:.2f}")

                    side = order['side']
                    quantity = float(order['executedQty'])

                    # 记录成交
                    self.filled_orders.append({
                        'order_id': order_id,
                        'side': side,
                        'price': price,
                        'quantity': quantity,
                        'time': datetime.now().isoformat()
                    })

                    # 移除活跃订单
                    del self.active_orders[price]

                    # 如果是买单成交，下对应的卖单
                    if side == 'BUY':
                        sell_price = price + self.grid_step
                        if sell_price <= self.upper_price:
                            sell_order = self.place_sell_order(sell_price, quantity)
                            if sell_order:
                                self.active_orders[sell_price] = sell_order['orderId']

                    # 如果是卖单成交，下对应的买单
                    elif side == 'SELL':
                        buy_price = price - self.grid_step
                        if buy_price >= self.lower_price:
                            buy_order = self.place_buy_order(buy_price)
                            if buy_order:
                                self.active_orders[buy_price] = buy_order['orderId']

                        # 计算利润
                        profit = self.grid_step * quantity
                        self.total_profit += profit
                        logger.info(f"网格利润: +${profit:.2f}, 累计: ${self.total_profit:.2f}")

            except Exception as e:
                logger.error(f"检查订单失败: {e}", exc_info=True)

    def start(self, check_interval: int = 10):
        """
        启动网格策略

        Args:
            check_interval: 检查间隔（秒）
        """
        logger.info("启动网格策略...")

        self.running = True
        self.initialize_grid()

        import time

        while self.running:
            try:
                self.check_orders()
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("收到停止信号")
                break
            except Exception as e:
                logger.error(f"策略运行异常: {e}", exc_info=True)

        self.stop()

    def stop(self):
        """停止网格策略"""
        logger.info("停止网格策略...")

        self.running = False

        # 取消所有活跃订单
        for price, order_id in self.active_orders.items():
            try:
                self.client.cancel_order(self.symbol, order_id)
                logger.info(f"订单已取消: {order_id}")
            except Exception as e:
                logger.error(f"取消订单失败: {e}", exc_info=True)

        # 保存策略状态
        self.save_state()

        logger.info("网格策略已停止")

    def get_status(self) -> Dict:
        """获取策略状态"""
        return {
            'symbol': self.symbol,
            'running': self.running,
            'grid_count': self.grid_count,
            'price_range': f"${self.lower_price:.2f} - ${self.upper_price:.2f}",
            'investment': self.investment,
            'active_orders': len(self.active_orders),
            'filled_orders': len(self.filled_orders),
            'total_profit': round(self.total_profit, 2),
            'roi': round((self.total_profit / self.investment * 100), 2) if self.investment > 0 else 0
        }

    def print_status(self):
        """打印策略状态"""
        status = self.get_status()

        print("\n" + "=" * 60)
        print(f"📊 网格策略状态 - {status['symbol']}")
        print("=" * 60)
        print(f"\n状态: {'🟢 运行中' if status['running'] else '🔴 已停止'}")
        print(f"网格数量: {status['grid_count']}")
        print(f"价格区间: {status['price_range']}")
        print(f"投资金额: ${status['investment']:.2f}")
        print(f"\n活跃订单: {status['active_orders']}")
        print(f"成交订单: {status['filled_orders']}")
        print(f"累计利润: ${status['total_profit']:.2f}")
        print(f"投资回报率: {status['roi']:.2f}%")
        print("=" * 60 + "\n")

    def save_state(self):
        """保存策略状态"""
        state = {
            'symbol': self.symbol,
            'lower_price': self.lower_price,
            'upper_price': self.upper_price,
            'grid_count': self.grid_count,
            'investment': self.investment,
            'active_orders': self.active_orders,
            'filled_orders': self.filled_orders,
            'total_profit': self.total_profit,
            'timestamp': datetime.now().isoformat()
        }

        state_file = self.config_dir / f"{self.symbol}_grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        logger.info(f"策略状态已保存: {state_file}")


class GridStrategyManager:
    """网格策略管理器"""

    def __init__(self):
        """初始化策略管理器"""
        self.strategies = {}

    def create_strategy(self,
                       symbol: str,
                       lower_price: float,
                       upper_price: float,
                       grid_count: int,
                       investment: float) -> GridStrategy:
        """
        创建网格策略

        Args:
            symbol: 交易对
            lower_price: 下限价格
            upper_price: 上限价格
            grid_count: 网格数量
            investment: 投资金额

        Returns:
            网格策略实例
        """
        strategy = GridStrategy(
            symbol=symbol,
            lower_price=lower_price,
            upper_price=upper_price,
            grid_count=grid_count,
            investment=investment
        )

        self.strategies[symbol] = strategy
        logger.info(f"创建网格策略: {symbol}")

        return strategy

    def start_strategy(self, symbol: str):
        """启动策略"""
        if symbol in self.strategies:
            self.strategies[symbol].start()
        else:
            logger.error(f"策略不存在: {symbol}")

    def stop_strategy(self, symbol: str):
        """停止策略"""
        if symbol in self.strategies:
            self.strategies[symbol].stop()
        else:
            logger.error(f"策略不存在: {symbol}")

    def get_strategy(self, symbol: str) -> Optional[GridStrategy]:
        """获取策略"""
        return self.strategies.get(symbol)

    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self.strategies.keys())


# 便捷函数
def create_grid_strategy(symbol: str,
                        lower_price: float,
                        upper_price: float,
                        grid_count: int,
                        investment: float) -> GridStrategy:
    """创建网格策略（便捷函数）"""
    return GridStrategy(symbol, lower_price, upper_price, grid_count, investment)


if __name__ == "__main__":
    # 测试网格策略
    strategy = create_grid_strategy(
        symbol="BTCUSDT",
        lower_price=65000,
        upper_price=70000,
        grid_count=10,
        investment=1000
    )

    # 打印状态
    strategy.print_status()

    # 启动策略（测试模式）
    # strategy.start()
