#!/usr/bin/env python3
"""
统一交易客户端
根据交易模式自动切换到对应的客户端
"""

from typing import Dict, List, Optional
from src.trading.trading_mode_manager import get_current_trading_mode, TradingMode
from src.trading.paper_trading_engine import get_paper_trading_engine


class UnifiedTradingClient:
    """统一交易客户端"""

    def __init__(self):
        """初始化统一客户端"""
        self.mode = get_current_trading_mode()
        self._client = None

    def _get_client(self):
        """获取当前模式对应的客户端"""
        if self._client is None:
            self.mode = get_current_trading_mode()

            if self.mode == TradingMode.PAPER:
                # 模拟盘
                self._client = get_paper_trading_engine()
            else:
                # 测试网或实盘
                from src.api.binance_client import BinanceClient
                self._client = BinanceClient()

        return self._client

    def get_ticker_price(self, symbol: str) -> Dict:
        """获取价格"""
        return self._get_client().get_ticker_price(symbol)

    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return self._get_client().get_account_info()

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """下市价单"""
        return self._get_client().place_market_order(symbol, side, quantity)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """下限价单"""
        return self._get_client().place_limit_order(symbol, side, quantity, price)

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取活跃订单"""
        return self._get_client().get_open_orders(symbol)

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """取消订单"""
        return self._get_client().cancel_order(symbol, order_id)

    def get_current_mode(self) -> TradingMode:
        """获取当前交易模式"""
        return self.mode

    def get_mode_name(self) -> str:
        """获取模式名称"""
        names = {
            TradingMode.PAPER: "模拟盘",
            TradingMode.TESTNET: "测试网",
            TradingMode.LIVE: "实盘"
        }
        return names.get(self.mode, "未知")

    def is_paper_trading(self) -> bool:
        """是否为模拟盘"""
        return self.mode == TradingMode.PAPER

    def is_live_trading(self) -> bool:
        """是否为实盘"""
        return self.mode == TradingMode.LIVE

    # 模拟盘专用方法
    def get_paper_statistics(self) -> Optional[Dict]:
        """获取模拟盘统计（仅模拟盘可用）"""
        if self.mode == TradingMode.PAPER:
            return self._get_client().get_statistics()
        return None

    def reset_paper_trading(self) -> bool:
        """重置模拟盘（仅模拟盘可用）"""
        if self.mode == TradingMode.PAPER:
            self._get_client().reset()
            return True
        return False


# 全局实例
_unified_client = None


def get_unified_client() -> UnifiedTradingClient:
    """获取统一客户端单例"""
    global _unified_client
    if _unified_client is None:
        _unified_client = UnifiedTradingClient()
    return _unified_client


# 使用示例
if __name__ == '__main__':
    client = get_unified_client()

    print("=" * 60)
    print(f"当前模式: {client.get_mode_name()}")
    print("=" * 60)

    # 查询价格
    ticker = client.get_ticker_price('BTCUSDT')
    print(f"\nBTC价格: ${ticker['price']}")

    # 查询账户
    account = client.get_account_info()
    print(f"\n账户余额:")
    for balance in account['balances'][:3]:
        if float(balance['free']) > 0:
            print(f"  {balance['asset']}: {balance['free']}")

    # 如果是模拟盘，显示统计
    if client.is_paper_trading():
        stats = client.get_paper_statistics()
        if stats:
            print(f"\n模拟盘统计:")
            print(f"  总价值: ${stats['total_value']:.2f}")
            print(f"  总盈亏: ${stats['total_pnl']:.2f} ({stats['pnl_percent']:+.2f}%)")
            print(f"  交易次数: {stats['total_trades']}")

    print("\n" + "=" * 60)
