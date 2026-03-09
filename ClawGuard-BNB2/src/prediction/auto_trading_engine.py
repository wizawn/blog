
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

#!/usr/bin/env python3
"""
智能自动交易引擎
结合趋势预测和事件分析，实现智能自动交易
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import threading
import time

from .trend_predictor import TrendPredictor
from .event_analyzer import EventAnalyzer
from ..api.binance_client import BinanceClient
from ..risk.risk_control import RiskControlEngine
from ..trading.trading_mode_manager import get_current_trading_mode, TradingMode

logger = logging.getLogger(__name__)


class AutoTradingEngine:
    """智能自动交易引擎"""

    def __init__(self, config: Dict = None):
        """
        初始化自动交易引擎

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.client = BinanceClient()
        self.risk_engine = RiskControlEngine()
        self.trend_predictor = TrendPredictor(self.client)
        self.event_analyzer = EventAnalyzer(self.client)

        # 交易参数
        self.symbols = self.config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        self.check_interval = self.config.get('check_interval', 300)  # 5分钟
        self.min_confidence = self.config.get('min_confidence', 70)  # 最小置信度
        self.position_size = self.config.get('position_size', 0.1)  # 仓位比例
        self.stop_loss_percent = self.config.get('stop_loss', 0.03)  # 止损3%
        self.take_profit_percent = self.config.get('take_profit', 0.05)  # 止盈5%

        # 运行状态
        self.running = False
        self.positions = {}  # {symbol: position_info}
        self.trade_history = []
        self.thread = None

    def start(self):
        """启动自动交易"""
        if self.running:
            logger.warning("自动交易已在运行中")
            return

        # 检查交易模式
        mode = get_current_trading_mode()
        if mode == TradingMode.LIVE:
            logger.warning("⚠️ 当前为实盘模式，请确认后再启动自动交易")

        self.running = True
        self.thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.thread.start()

        logger.info("✅ 智能自动交易引擎已启动")
        logger.info(f"监控币种: {', '.join(self.symbols)}")
        logger.info(f"检查间隔: {self.check_interval}秒")
        logger.info(f"最小置信度: {self.min_confidence}%")

    def stop(self):
        """停止自动交易"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)

        logger.info("🛑 智能自动交易引擎已停止")

    def _trading_loop(self):
        """交易主循环"""
        while self.running:
            try:
                for symbol in self.symbols:
                    self._process_symbol(symbol)

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("收到停止信号")
                break
            except Exception as e:
                logger.error(f"交易循环异常: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟

    def _process_symbol(self, symbol: str):
        """处理单个交易对"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"分析 {symbol}")
            logger.info(f"{'='*60}")

            # 1. 获取当前价格
            ticker = self.client.get_ticker_price(symbol)
            current_price = float(ticker['price'])

            # 2. 趋势预测
            trend_result = self.trend_predictor.predict_trend(symbol, '1h', 24)
            if not trend_result['success']:
                logger.error(f"趋势预测失败: {trend_result.get('error')}")
                return

            # 3. 事件分析
            event_result = self.event_analyzer.analyze_market_events(symbol)
            if not event_result['success']:
                logger.error(f"事件分析失败: {event_result.get('error')}")
                return

            # 4. 综合决策
            decision = self._make_trading_decision(
                symbol, current_price, trend_result, event_result
            )

            logger.info(f"\n决策结果: {decision['action']}")
            logger.info(f"置信度: {decision['confidence']:.0f}%")
            logger.info(f"理由: {decision['reason']}")

            # 5. 执行交易
            if decision['action'] != 'HOLD':
                self._execute_trade(symbol, decision, current_price)

            # 6. 管理现有持仓
            self._manage_positions(symbol, current_price)

        except Exception as e:
            logger.error(f"处理 {symbol} 时出错: {e}", exc_info=True)

    def _make_trading_decision(self, symbol: str, current_price: float,
                               trend_result: Dict, event_result: Dict) -> Dict:
        """
        综合决策

        Args:
            symbol: 交易对
            current_price: 当前价格
            trend_result: 趋势预测结果
            event_result: 事件分析结果

        Returns:
            交易决策
        """
        # 提取关键信息
        trend_recommendation = trend_result['recommendation']
        trend_confidence = trend_result['trend']['confidence']
        event_signals = event_result['signals']
        sentiment = event_result['sentiment']

        # 计算综合置信度
        # 趋势预测权重60%，事件分析权重40%
        trend_weight = 0.6
        event_weight = 0.4

        event_confidence = event_signals[0]['confidence'] if event_signals else 50

        combined_confidence = (
            trend_confidence * trend_weight +
            event_confidence * event_weight
        )

        # 判断操作方向
        trend_action = trend_recommendation['action']
        event_action = event_signals[0]['action'] if event_signals else 'HOLD'

        # 如果两个信号一致，增强置信度
        if trend_action == event_action and trend_action != 'HOLD':
            action = trend_action
            combined_confidence = min(combined_confidence * 1.2, 95)
            reason = f"趋势预测和事件分析均建议{action}，信号强烈"
        # 如果信号冲突，降低置信度
        elif trend_action != event_action and 'HOLD' not in [trend_action, event_action]:
            action = 'HOLD'
            combined_confidence = 50
            reason = "趋势预测和事件分析信号冲突，建议观望"
        # 如果只有一个信号
        elif trend_action != 'HOLD':
            action = trend_action
            reason = f"趋势预测建议{action}"
        elif event_action != 'HOLD':
            action = event_action
            reason = f"事件分析建议{action}"
        else:
            action = 'HOLD'
            reason = "市场信号不明确"

        # 检查是否已有持仓
        if symbol in self.positions:
            position = self.positions[symbol]
            if position['side'] == 'LONG' and action == 'BUY':
                action = 'HOLD'
                reason = "已有多头持仓，避免重复买入"
            elif position['side'] == 'SHORT' and action == 'SELL':
                action = 'HOLD'
                reason = "已有空头持仓，避免重复卖出"

        return {
            'action': action,
            'confidence': round(combined_confidence, 2),
            'reason': reason,
            'trend_data': trend_result,
            'event_data': event_result
        }

    def _execute_trade(self, symbol: str, decision: Dict, current_price: float):
        """
        执行交易

        Args:
            symbol: 交易对
            decision: 交易决策
            current_price: 当前价格
        """
        # 检查置信度
        if decision['confidence'] < self.min_confidence:
            logger.info(f"置信度({decision['confidence']:.0f}%)低于阈值({self.min_confidence}%)，不执行交易")
            return

        # 检查是否已有持仓
        if symbol in self.positions:
            logger.info(f"已有 {symbol} 持仓，不执行新交易")
            return

        try:
            # 获取账户余额
            account = self.client.get_account()
            usdt_balance = 0
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                    break

            if usdt_balance < 10:
                logger.warning(f"USDT余额不足({usdt_balance:.2f})，无法交易")
                return

            # 计算交易金额
            trade_amount = usdt_balance * self.position_size
            trade_amount = min(trade_amount, 1000)  # 限制单笔最大1000 USDT

            # 风控检查
            passed, msg = self.risk_engine.pre_trade_check(
                symbol=symbol,
                side=decision['action'],
                amount=trade_amount,
                account_balance=usdt_balance,
                current_price=current_price,
                has_real_trade_permission=True
            )

            if not passed:
                logger.warning(f"风控拒绝: {msg}")
                return

            # 执行交易
            if decision['action'] == 'BUY':
                logger.info(f"🔵 执行买入: {symbol}")
                logger.info(f"   金额: ${trade_amount:.2f}")
                logger.info(f"   价格: ${current_price:.2f}")

                order = self.client.place_market_order(
                    symbol=symbol,
                    side='BUY',
                    quote_order_qty=trade_amount
                )

                # 记录持仓
                quantity = float(order.get('executedQty', 0))
                self.positions[symbol] = {
                    'side': 'LONG',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'entry_time': datetime.now(),
                    'stop_loss': current_price * (1 - self.stop_loss_percent),
                    'take_profit': current_price * (1 + self.take_profit_percent),
                    'order_id': order.get('orderId')
                }

                logger.info(f"✅ 买入成功")
                logger.info(f"   数量: {quantity:.6f}")
                logger.info(f"   止损: ${self.positions[symbol]['stop_loss']:.2f}")
                logger.info(f"   止盈: ${self.positions[symbol]['take_profit']:.2f}")

            elif decision['action'] == 'SELL':
                # 现货交易不支持做空，这里只是平多头仓位
                logger.info(f"🔴 执行卖出: {symbol}")
                logger.info(f"   金额: ${trade_amount:.2f}")
                logger.info(f"   价格: ${current_price:.2f}")

                # 获取持仓数量
                quantity = 0
                for balance in account['balances']:
                    if balance['asset'] == symbol.replace('USDT', ''):
                        quantity = float(balance['free'])
                        break

                if quantity > 0:
                    order = self.client.place_market_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=quantity
                    )

                    logger.info(f"✅ 卖出成功")
                    logger.info(f"   数量: {quantity:.6f}")
                else:
                    logger.warning("无可卖出的持仓")

            # 记录交易历史
            self.trade_history.append({
                'symbol': symbol,
                'action': decision['action'],
                'price': current_price,
                'amount': trade_amount,
                'confidence': decision['confidence'],
                'reason': decision['reason'],
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"执行交易失败: {e}", exc_info=True)

    def _manage_positions(self, symbol: str, current_price: float):
        """
        管理现有持仓（止损止盈）

        Args:
            symbol: 交易对
            current_price: 当前价格
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # 计算盈亏
        if position['side'] == 'LONG':
            pnl_percent = (current_price - position['entry_price']) / position['entry_price']

            # 检查止损
            if current_price <= position['stop_loss']:
                logger.warning(f"⚠️ {symbol} 触发止损")
                logger.warning(f"   入场价: ${position['entry_price']:.2f}")
                logger.warning(f"   当前价: ${current_price:.2f}")
                logger.warning(f"   亏损: {pnl_percent*100:.2f}%")
                self._close_position(symbol, current_price, 'STOP_LOSS')

            # 检查止盈
            elif current_price >= position['take_profit']:
                logger.info(f"🎉 {symbol} 触发止盈")
                logger.info(f"   入场价: ${position['entry_price']:.2f}")
                logger.info(f"   当前价: ${current_price:.2f}")
                logger.info(f"   盈利: {pnl_percent*100:.2f}%")
                self._close_position(symbol, current_price, 'TAKE_PROFIT')

            # 移动止损（盈利超过3%时，将止损移至成本价）
            elif pnl_percent > 0.03 and position['stop_loss'] < position['entry_price']:
                position['stop_loss'] = position['entry_price']
                logger.info(f"📈 {symbol} 移动止损至成本价 ${position['entry_price']:.2f}")

    def _close_position(self, symbol: str, current_price: float, reason: str):
        """
        平仓

        Args:
            symbol: 交易对
            current_price: 当前价格
            reason: 平仓原因
        """
        if symbol not in self.positions:
            return

        try:
            position = self.positions[symbol]

            # 执行卖出
            order = self.client.place_market_order(
                symbol=symbol,
                side='SELL',
                quantity=position['quantity']
            )

            # 计算盈亏
            pnl = (current_price - position['entry_price']) * position['quantity']
            pnl_percent = (current_price - position['entry_price']) / position['entry_price']

            logger.info(f"✅ 平仓成功: {symbol}")
            logger.info(f"   原因: {reason}")
            logger.info(f"   盈亏: ${pnl:.2f} ({pnl_percent*100:+.2f}%)")

            # 移除持仓
            del self.positions[symbol]

            # 记录交易历史
            self.trade_history.append({
                'symbol': symbol,
                'action': 'CLOSE',
                'price': current_price,
                'pnl': pnl,
                'pnl_percent': pnl_percent * 100,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"平仓失败: {e}", exc_info=True)

    def get_status(self) -> Dict:
        """获取引擎状态"""
        return {
            'running': self.running,
            'symbols': self.symbols,
            'positions': len(self.positions),
            'total_trades': len(self.trade_history),
            'position_details': self.positions,
            'recent_trades': self.trade_history[-10:]
        }


if __name__ == '__main__':
    # 测试自动交易引擎
    config = {
        'symbols': ['BTCUSDT'],
        'check_interval': 60,  # 1分钟检查一次（测试用）
        'min_confidence': 70,
        'position_size': 0.05,  # 5%仓位
        'stop_loss': 0.02,  # 2%止损
        'take_profit': 0.03  # 3%止盈
    }

    engine = AutoTradingEngine(config)

    print("\n" + "=" * 60)
    print("智能自动交易引擎")
    print("=" * 60)
    print("\n⚠️  警告: 这是自动交易系统，请确保:")
    print("1. 已充分测试")
    print("2. 使用模拟盘或测试网")
    print("3. 设置合理的止损")
    print("4. 监控运行状态")
    print("\n按 Ctrl+C 停止\n")

    try:
        engine.start()

        # 保持运行
        while True:
            time.sleep(10)
            status = engine.get_status()
            print(f"\r运行中... 持仓: {status['positions']} | 总交易: {status['total_trades']}", end='')

    except KeyboardInterrupt:
        print("\n\n停止中...")
        engine.stop()
        print("已停止")
