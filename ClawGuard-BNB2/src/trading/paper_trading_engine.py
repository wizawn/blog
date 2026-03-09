#!/usr/bin/env python3
"""
模拟交易引擎
提供完整的模拟盘交易功能，无需连接真实API
"""

import time
import random
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


class PaperTradingEngine:
    """模拟交易引擎"""

    def __init__(self, initial_balance: float = 10000):
        """
        初始化模拟交易引擎

        Args:
            initial_balance: 初始余额（USDT）
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}  # {symbol: {quantity, avg_price, side}}
        self.orders = []
        self.trades = []
        self.order_id_counter = 1000000

        # 模拟价格数据
        self.mock_prices = {
            'BTCUSDT': 68000.0,
            'ETHUSDT': 3400.0,
            'BNBUSDT': 580.0,
            'SOLUSDT': 140.0,
            'ADAUSDT': 0.58,
            'DOGEUSDT': 0.15,
            'XRPUSDT': 0.52,
            'DOTUSDT': 7.2,
            'MATICUSDT': 0.85,
            'LINKUSDT': 15.5
        }

        # 加载持久化数据
        self.data_file = Path.home() / ".clawguard" / "paper_trading.json"
        self._load_state()

    def _load_state(self):
        """加载持久化状态"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get('balance', self.initial_balance)
                    self.positions = data.get('positions', {})
                    self.orders = data.get('orders', [])
                    self.trades = data.get('trades', [])
                    self.order_id_counter = data.get('order_id_counter', 1000000)
            except Exception as e:
                print(f"加载模拟盘状态失败: {e}")

    def _save_state(self):
        """保存持久化状态"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'balance': self.balance,
                    'positions': self.positions,
                    'orders': self.orders,
                    'trades': self.trades,
                    'order_id_counter': self.order_id_counter
                }, f, indent=2)
        except Exception as e:
            print(f"保存模拟盘状态失败: {e}")

    def get_price(self, symbol: str) -> float:
        """
        获取模拟价格（带随机波动）

        Args:
            symbol: 交易对

        Returns:
            当前价格
        """
        base_price = self.mock_prices.get(symbol, 100.0)
        # 添加 ±0.5% 的随机波动
        volatility = random.uniform(-0.005, 0.005)
        return base_price * (1 + volatility)

    def get_ticker_price(self, symbol: str) -> Dict:
        """获取价格信息"""
        price = self.get_price(symbol)
        change = random.uniform(-5, 5)

        return {
            'symbol': symbol,
            'price': str(price),
            'priceChange': str(price * change / 100),
            'priceChangePercent': str(change),
            'highPrice': str(price * 1.02),
            'lowPrice': str(price * 0.98),
            'volume': str(random.uniform(10000, 100000)),
            'quoteVolume': str(random.uniform(1000000, 10000000))
        }

    def get_account_info(self) -> Dict:
        """获取账户信息"""
        balances = [
            {
                'asset': 'USDT',
                'free': str(self.balance),
                'locked': '0.0'
            }
        ]

        # 添加持仓资产
        for symbol, position in self.positions.items():
            asset = symbol.replace('USDT', '')
            balances.append({
                'asset': asset,
                'free': str(position['quantity']),
                'locked': '0.0'
            })

        return {
            'canTrade': True,
            'canWithdraw': True,
            'canDeposit': True,
            'balances': balances,
            'updateTime': int(time.time() * 1000)
        }

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        下市价单

        Args:
            symbol: 交易对
            side: BUY 或 SELL
            quantity: 数量

        Returns:
            订单信息
        """
        price = self.get_price(symbol)
        order_id = self.order_id_counter
        self.order_id_counter += 1

        # 计算成本
        cost = quantity * price
        commission = cost * 0.001  # 0.1% 手续费

        if side == 'BUY':
            # 买入检查
            total_cost = cost + commission
            if total_cost > self.balance:
                raise Exception(f"余额不足: 需要 {total_cost:.2f} USDT，当前 {self.balance:.2f} USDT")

            # 扣除余额
            self.balance -= total_cost

            # 更新持仓
            if symbol in self.positions:
                old_pos = self.positions[symbol]
                total_quantity = old_pos['quantity'] + quantity
                avg_price = (old_pos['avg_price'] * old_pos['quantity'] + price * quantity) / total_quantity
                self.positions[symbol] = {
                    'quantity': total_quantity,
                    'avg_price': avg_price,
                    'side': 'LONG'
                }
            else:
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'side': 'LONG'
                }

        else:  # SELL
            # 卖出检查
            if symbol not in self.positions:
                raise Exception(f"没有 {symbol} 持仓")

            position = self.positions[symbol]
            if position['quantity'] < quantity:
                raise Exception(f"持仓不足: 需要 {quantity}，当前 {position['quantity']}")

            # 增加余额
            self.balance += cost - commission

            # 更新持仓
            position['quantity'] -= quantity
            if position['quantity'] < 0.0001:  # 清仓
                del self.positions[symbol]

        # 记录订单
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'status': 'FILLED',
            'side': side,
            'type': 'MARKET',
            'price': str(price),
            'origQty': str(quantity),
            'executedQty': str(quantity),
            'cummulativeQuoteQty': str(cost),
            'timeInForce': 'GTC',
            'transactTime': int(time.time() * 1000)
        }
        self.orders.append(order)

        # 记录交易
        trade = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'price': price,
            'quantity': quantity,
            'commission': commission,
            'time': datetime.now().isoformat()
        }
        self.trades.append(trade)

        # 保存状态
        self._save_state()

        return order

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """
        下限价单

        Args:
            symbol: 交易对
            side: BUY 或 SELL
            quantity: 数量
            price: 价格

        Returns:
            订单信息
        """
        order_id = self.order_id_counter
        self.order_id_counter += 1

        order = {
            'orderId': order_id,
            'symbol': symbol,
            'status': 'NEW',
            'side': side,
            'type': 'LIMIT',
            'price': str(price),
            'origQty': str(quantity),
            'executedQty': '0.0',
            'cummulativeQuoteQty': '0.0',
            'timeInForce': 'GTC',
            'time': int(time.time() * 1000)
        }
        self.orders.append(order)
        self._save_state()

        return order

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取活跃订单"""
        orders = [o for o in self.orders if o['status'] in ['NEW', 'PARTIALLY_FILLED']]
        if symbol:
            orders = [o for o in orders if o['symbol'] == symbol]
        return orders

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """取消订单"""
        for order in self.orders:
            if order['orderId'] == order_id and order['symbol'] == symbol:
                order['status'] = 'CANCELED'
                self._save_state()
                return order

        raise Exception(f"订单不存在: {order_id}")

    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取持仓信息"""
        positions = []

        if symbol:
            if symbol in self.positions:
                pos = self.positions[symbol]
                current_price = self.get_price(symbol)
                unrealized_pnl = (current_price - pos['avg_price']) * pos['quantity']

                positions.append({
                    'symbol': symbol,
                    'positionAmt': str(pos['quantity']),
                    'entryPrice': str(pos['avg_price']),
                    'markPrice': str(current_price),
                    'unRealizedProfit': str(unrealized_pnl),
                    'liquidationPrice': '0',
                    'leverage': '1',
                    'positionSide': pos['side']
                })
        else:
            for symbol, pos in self.positions.items():
                current_price = self.get_price(symbol)
                unrealized_pnl = (current_price - pos['avg_price']) * pos['quantity']

                positions.append({
                    'symbol': symbol,
                    'positionAmt': str(pos['quantity']),
                    'entryPrice': str(pos['avg_price']),
                    'markPrice': str(current_price),
                    'unRealizedProfit': str(unrealized_pnl),
                    'liquidationPrice': '0',
                    'leverage': '1',
                    'positionSide': pos['side']
                })

        return positions

    def get_trades(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取交易历史"""
        trades = self.trades[-limit:]
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
        return trades

    def reset(self):
        """重置模拟盘"""
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = []
        self.trades = []
        self.order_id_counter = 1000000
        self._save_state()

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_value = self.balance

        # 计算持仓价值
        for symbol, pos in self.positions.items():
            current_price = self.get_price(symbol)
            total_value += pos['quantity'] * current_price

        # 计算盈亏
        total_pnl = total_value - self.initial_balance
        pnl_percent = (total_pnl / self.initial_balance) * 100

        # 计算交易统计
        total_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t['side'] == 'BUY'])
        sell_trades = len([t for t in self.trades if t['side'] == 'SELL'])

        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'pnl_percent': pnl_percent,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'positions_count': len(self.positions)
        }


# 全局模拟交易引擎实例
_paper_trading_engine = None


def get_paper_trading_engine(initial_balance: float = 10000) -> PaperTradingEngine:
    """获取模拟交易引擎单例"""
    global _paper_trading_engine
    if _paper_trading_engine is None:
        _paper_trading_engine = PaperTradingEngine(initial_balance)
    return _paper_trading_engine


# 使用示例
if __name__ == '__main__':
    engine = get_paper_trading_engine()

    print("=" * 60)
    print("模拟交易引擎测试")
    print("=" * 60)

    # 查询价格
    ticker = engine.get_ticker_price('BTCUSDT')
    print(f"\nBTC价格: ${ticker['price']}")

    # 查询账户
    account = engine.get_account_info()
    print(f"\n账户余额: {account['balances'][0]['free']} USDT")

    # 下单
    try:
        order = engine.place_market_order('BTCUSDT', 'BUY', 0.01)
        print(f"\n买入成功: {order['executedQty']} BTC @ ${order['price']}")
    except Exception as e:
        print(f"\n买入失败: {e}")

    # 查询持仓
    positions = engine.get_position_risk()
    if positions:
        print(f"\n持仓:")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['positionAmt']} @ ${pos['entryPrice']}")
            print(f"  未实现盈亏: ${pos['unRealizedProfit']}")

    # 统计信息
    stats = engine.get_statistics()
    print(f"\n统计信息:")
    print(f"  初始余额: ${stats['initial_balance']:.2f}")
    print(f"  当前余额: ${stats['current_balance']:.2f}")
    print(f"  总价值: ${stats['total_value']:.2f}")
    print(f"  总盈亏: ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)")
    print(f"  交易次数: {stats['total_trades']}")

    print("\n" + "=" * 60)
