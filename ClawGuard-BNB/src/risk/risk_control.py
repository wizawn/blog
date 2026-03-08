#!/usr/bin/env python3
"""
风控引擎 - 事前/事中/事后三层防护
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from ..config.config_manager import ConfigManager


class RiskControlEngine:
    """风控引擎"""

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        初始化风控引擎

        Args:
            config: 配置管理器
        """
        self.config = config or ConfigManager()

        # 风控参数
        self.max_position_pct = self.config.get('risk_control.max_position_pct', 0.1)
        self.max_total_position_pct = self.config.get('risk_control.max_total_position_pct', 0.8)
        self.max_daily_loss_pct = self.config.get('risk_control.max_daily_loss_pct', 0.05)
        self.max_slippage_pct = self.config.get('risk_control.max_slippage_pct', 0.02)
        self.order_timeout_seconds = self.config.get('risk_control.order_timeout_seconds', 30)

        # 状态跟踪
        self.is_locked = False
        self.lock_reason = ""
        self.daily_pnl = 0.0
        self.total_trades_today = 0
        self.failed_trades_today = 0
        self.last_reset_date = datetime.now().date()

        # 审计日志
        self.audit_log_dir = Path.home() / ".clawguard" / "audit_logs"
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)

        # 加载今日状态
        self._load_daily_state()

    def _load_daily_state(self):
        """加载今日状态"""
        today = datetime.now().date()
        state_file = self.audit_log_dir / f"state_{today}.json"

        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.daily_pnl = state.get('daily_pnl', 0.0)
                    self.total_trades_today = state.get('total_trades', 0)
                    self.failed_trades_today = state.get('failed_trades', 0)
                    self.is_locked = state.get('is_locked', False)
                    self.lock_reason = state.get('lock_reason', '')
            except Exception as e:
                print(f"⚠️  加载状态失败: {e}")

    def _save_daily_state(self):
        """保存今日状态"""
        today = datetime.now().date()
        state_file = self.audit_log_dir / f"state_{today}.json"

        state = {
            'date': str(today),
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades_today,
            'failed_trades': self.failed_trades_today,
            'is_locked': self.is_locked,
            'lock_reason': self.lock_reason,
            'timestamp': datetime.now().isoformat()
        }

        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️  保存状态失败: {e}")

    def _check_daily_reset(self):
        """检查是否需要重置每日统计"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.total_trades_today = 0
            self.failed_trades_today = 0
            self.last_reset_date = today
            print(f"✅ 每日统计已重置: {today}")

    def _write_audit_log(self, event_type: str, data: Dict):
        """写入审计日志"""
        today = datetime.now().date()
        log_file = self.audit_log_dir / f"audit_{today}.jsonl"

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }

        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️  写入审计日志失败: {e}")

    # ============= 事前风控 =============

    def pre_trade_check(self, symbol: str, side: str, amount: float,
                       account_balance: float, current_price: float,
                       has_real_trade_permission: bool = True) -> Tuple[bool, str]:
        """
        事前风控检查

        Args:
            symbol: 交易对
            side: 方向
            amount: 金额（USDT）
            account_balance: 账户余额
            current_price: 当前价格
            has_real_trade_permission: 是否有实盘权限

        Returns:
            (是否通过, 原因)
        """
        self._check_daily_reset()

        checks = []

        # 检查1: 是否锁定
        if self.is_locked:
            return False, f"❌ 账户已锁定: {self.lock_reason}"

        # 检查2: 权限校验
        if not has_real_trade_permission:
            return False, "❌ 未开启实盘交易权限，请先在配置中启用"

        # 检查3: 参数校验
        if amount <= 0:
            return False, f"❌ 交易金额必须大于0: {amount}"

        if account_balance <= 0:
            return False, "❌ 账户余额不足"

        # 检查4: 单笔仓位限制
        position_pct = amount / account_balance
        if position_pct > self.max_position_pct:
            return False, f"❌ 单笔仓位超限: {position_pct*100:.2f}% > {self.max_position_pct*100:.2f}%"

        checks.append(f"✓ 单笔仓位: {position_pct*100:.2f}% (限额{self.max_position_pct*100:.2f}%)")

        # 检查5: 余额校验
        if amount > account_balance:
            return False, f"❌ 余额不足: 需要{amount} USDT，可用{account_balance} USDT"

        checks.append(f"✓ 余额充足: {account_balance:.2f} USDT")

        # 检查6: 每日亏损限制
        max_daily_loss = self.max_daily_loss_pct * account_balance
        if self.daily_pnl < -max_daily_loss:
            self.is_locked = True
            self.lock_reason = f"触发单日亏损限额: {self.daily_pnl:.2f} USDT"
            self._save_daily_state()
            return False, f"❌ {self.lock_reason}"

        checks.append(f"✓ 今日盈亏: {self.daily_pnl:.2f} USDT (限额-{max_daily_loss:.2f})")

        # 检查7: 价格合理性
        if current_price <= 0:
            return False, f"❌ 价格异常: {current_price}"

        checks.append(f"✓ 价格正常: {current_price}")

        # 记录审计日志
        self._write_audit_log('pre_trade_check', {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'account_balance': account_balance,
            'current_price': current_price,
            'result': 'PASS',
            'checks': checks
        })

        return True, "\n".join(checks)

    # ============= 事中风控 =============

    def during_trade_monitor(self, order_id: str, expected_price: float,
                            actual_price: float, order_time: float) -> Tuple[bool, str]:
        """
        事中风控监控

        Args:
            order_id: 订单ID
            expected_price: 预期价格
            actual_price: 实际成交价
            order_time: 订单时间（秒）

        Returns:
            (是否继续, 原因)
        """
        # 检查1: 滑点监控
        if expected_price > 0:
            slippage = abs(actual_price - expected_price) / expected_price
            if slippage > self.max_slippage_pct:
                self._write_audit_log('slippage_alert', {
                    'order_id': order_id,
                    'expected_price': expected_price,
                    'actual_price': actual_price,
                    'slippage': slippage
                })
                return False, f"❌ 滑点过大: {slippage*100:.2f}% > {self.max_slippage_pct*100:.2f}%"

        # 检查2: 订单超时
        if order_time > self.order_timeout_seconds:
            self._write_audit_log('order_timeout', {
                'order_id': order_id,
                'order_time': order_time
            })
            return False, f"❌ 订单超时: {order_time}秒 > {self.order_timeout_seconds}秒"

        return True, "✓ 事中监控通过"

    # ============= 事后风控 =============

    def post_trade_audit(self, order_id: str, symbol: str, side: str,
                        amount: float, price: float, status: str,
                        pnl: float = 0.0) -> Dict:
        """
        事后风控审计

        Args:
            order_id: 订单ID
            symbol: 交易对
            side: 方向
            amount: 数量
            price: 成交价
            status: 订单状态
            pnl: 盈亏

        Returns:
            审计结果
        """
        self._check_daily_reset()

        # 更新统计
        self.total_trades_today += 1
        if status != 'FILLED':
            self.failed_trades_today += 1

        self.daily_pnl += pnl

        # 检查是否触发锁定
        account_equity = 10000  # 这里应该从实际账户获取
        max_daily_loss = self.max_daily_loss_pct * account_equity

        if self.daily_pnl < -max_daily_loss:
            self.is_locked = True
            self.lock_reason = f"触发单日亏损限额: {self.daily_pnl:.2f} USDT (限额-{max_daily_loss:.2f})"

        # 保存状态
        self._save_daily_state()

        # 写入审计日志
        audit_data = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': status,
            'pnl': pnl,
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades_today,
            'failed_trades': self.failed_trades_today,
            'is_locked': self.is_locked
        }

        self._write_audit_log('post_trade_audit', audit_data)

        return audit_data

    # ============= 风控管理 =============

    def unlock_trading(self, reason: str = "手动解锁"):
        """解锁交易"""
        self.is_locked = False
        self.lock_reason = ""
        self._save_daily_state()

        self._write_audit_log('unlock_trading', {'reason': reason})
        print(f"✅ 交易已解锁: {reason}")

    def force_lock(self, reason: str):
        """强制锁定"""
        self.is_locked = True
        self.lock_reason = reason
        self._save_daily_state()

        self._write_audit_log('force_lock', {'reason': reason})
        print(f"🔒 交易已锁定: {reason}")

    def get_risk_status(self) -> Dict:
        """获取风控状态"""
        self._check_daily_reset()

        account_equity = 10000  # 应从实际账户获取
        max_daily_loss = self.max_daily_loss_pct * account_equity

        return {
            'is_locked': self.is_locked,
            'lock_reason': self.lock_reason,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / account_equity * 100) if account_equity > 0 else 0,
            'max_daily_loss': max_daily_loss,
            'total_trades_today': self.total_trades_today,
            'failed_trades_today': self.failed_trades_today,
            'success_rate': ((self.total_trades_today - self.failed_trades_today) / self.total_trades_today * 100)
                           if self.total_trades_today > 0 else 0,
            'date': str(datetime.now().date())
        }

    def print_risk_status(self):
        """打印风控状态"""
        status = self.get_risk_status()

        print("=" * 60)
        print("风控引擎状态")
        print("=" * 60)
        print()
        print(f"日期: {status['date']}")
        print(f"状态: {'🔒 已锁定' if status['is_locked'] else '✅ 正常'}")
        if status['is_locked']:
            print(f"锁定原因: {status['lock_reason']}")
        print()
        print(f"今日盈亏: {status['daily_pnl']:.2f} USDT ({status['daily_pnl_pct']:+.2f}%)")
        print(f"亏损限额: {status['max_daily_loss']:.2f} USDT")
        print(f"今日交易: {status['total_trades_today']}笔")
        print(f"失败交易: {status['failed_trades_today']}笔")
        print(f"成功率: {status['success_rate']:.1f}%")
        print()
        print("=" * 60)


# ============= 使用示例 =============

if __name__ == "__main__":
    # 初始化风控引擎
    engine = RiskControlEngine()

    print("=" * 60)
    print("风控引擎测试")
    print("=" * 60)
    print()

    # 查看当前状态
    engine.print_risk_status()

    # 测试事前检查
    print("\n📋 测试事前风控检查:")
    passed, msg = engine.pre_trade_check(
        symbol="BTCUSDT",
        side="BUY",
        amount=100,
        account_balance=10000,
        current_price=68000,
        has_real_trade_permission=True
    )
    print(f"结果: {'✅ 通过' if passed else '❌ 拒绝'}")
    print(msg)

    # 测试事后审计
    print("\n📋 测试事后审计:")
    audit = engine.post_trade_audit(
        order_id="12345",
        symbol="BTCUSDT",
        side="BUY",
        amount=0.001,
        price=68000,
        status="FILLED",
        pnl=-50
    )
    print(f"审计结果: {json.dumps(audit, indent=2, ensure_ascii=False)}")

    # 查看更新后的状态
    print()
    engine.print_risk_status()
