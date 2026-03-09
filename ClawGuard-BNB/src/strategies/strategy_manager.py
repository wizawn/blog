#!/usr/bin/env python3
"""
策略管理器 - 统一管理所有交易策略
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import logging

from .grid_strategy import GridStrategy
from .ma_crossover_strategy import MACrossoverStrategy
from .breakout_strategy import BreakoutStrategy
from .futures_grid_strategy import FuturesGridStrategy
from ..api.binance_client import BinanceClient
from ..risk.risk_control import RiskControlEngine

logger = logging.getLogger(__name__)


class StrategyInstance:
    """策略实例包装器"""

    def __init__(self, strategy_id: str, strategy_type: str, symbol: str,
                 config: Dict, strategy_obj: Any):
        self.id = strategy_id
        self.type = strategy_type
        self.symbol = symbol
        self.config = config
        self.strategy = strategy_obj
        self.status = 'stopped'  # stopped, running, paused, error
        self.created_at = datetime.now()
        self.started_at = None
        self.stopped_at = None
        self.thread = None
        self.error_message = None

        # 统计数据
        self.total_profit = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'symbol': self.symbol,
            'status': self.status,
            'config': self.config,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'error_message': self.error_message,
            'stats': {
                'total_profit': round(self.total_profit, 2),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': round((self.winning_trades / self.total_trades * 100)
                                 if self.total_trades > 0 else 0, 2)
            }
        }


class StrategyManager:
    """策略管理器 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.strategies: Dict[str, StrategyInstance] = {}
        self.client = BinanceClient()
        self.risk_engine = RiskControlEngine()

        # 数据目录
        self.data_dir = Path.home() / ".clawguard" / "data" / "strategies"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("策略管理器初始化完成")

        # 自动加载已保存的策略
        self._load_saved_strategies()

    def _load_saved_strategies(self):
        """加载已保存的策略"""
        try:
            if not self.data_dir.exists():
                return

            for strategy_file in self.data_dir.glob("*.json"):
                try:
                    with open(strategy_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 验证数据完整性
                    required_fields = ['id', 'type', 'symbol', 'config']
                    if not all(field in data for field in required_fields):
                        logger.warning(f"策略文件 {strategy_file} 数据不完整，跳过")
                        continue

                    # 重新创建策略（但不自动启动）
                    logger.info(f"恢复策略: {data['id']}")
                    self.create_strategy(
                        strategy_type=data['type'],
                        symbol=data['symbol'],
                        config=data['config'],
                        auto_start=False
                    )

                except Exception as e:
                    logger.error(f"加载策略文件 {strategy_file} 失败: {e}")
                    continue

            logger.info(f"已恢复 {len(self.strategies)} 个策略")

        except Exception as e:
            logger.error(f"加载策略失败: {e}")

    def create_strategy(self, strategy_type: str, symbol: str,
                       config: Dict, auto_start: bool = False) -> Dict:
        """
        创建策略

        Args:
            strategy_type: 策略类型 (grid, ma_crossover, breakout, futures_grid)
            symbol: 交易对
            config: 策略配置
            auto_start: 是否自动启动

        Returns:
            创建结果
        """
        try:
            # 生成策略ID
            strategy_id = f"{strategy_type}_{symbol}_{uuid.uuid4().hex[:8]}"

            # 根据类型创建策略对象
            strategy_obj = None

            if strategy_type == 'grid':
                strategy_obj = GridStrategy(
                    symbol=symbol,
                    lower_price=config['lower_price'],
                    upper_price=config['upper_price'],
                    grid_count=config['grids'],
                    investment=config['amount'],
                    client=self.client,
                    risk_engine=self.risk_engine
                )

            elif strategy_type == 'ma_crossover':
                strategy_obj = MACrossoverStrategy(
                    symbol=symbol,
                    fast_period=config.get('fast_period', 10),
                    slow_period=config.get('slow_period', 30),
                    interval=config.get('interval', '1h'),
                    client=self.client
                )

            elif strategy_type == 'breakout':
                strategy_obj = BreakoutStrategy(
                    symbol=symbol,
                    period=config.get('period', 20),
                    interval=config.get('interval', '1h'),
                    client=self.client
                )

            elif strategy_type == 'futures_grid':
                strategy_obj = FuturesGridStrategy(
                    symbol=symbol,
                    lower_price=config['lower_price'],
                    upper_price=config['upper_price'],
                    grid_count=config['grids'],
                    investment=config['amount'],
                    leverage=config.get('leverage', 1),
                    client=self.client,
                    risk_engine=self.risk_engine
                )

            else:
                return {
                    'success': False,
                    'error': f'不支持的策略类型: {strategy_type}'
                }

            # 创建策略实例
            instance = StrategyInstance(
                strategy_id=strategy_id,
                strategy_type=strategy_type,
                symbol=symbol,
                config=config,
                strategy_obj=strategy_obj
            )

            # 保存到管理器
            self.strategies[strategy_id] = instance

            # 保存到文件
            self._save_strategy(instance)

            logger.info(f"策略创建成功: {strategy_id}")

            # 自动启动
            if auto_start:
                self.start_strategy(strategy_id)

            return {
                'success': True,
                'data': {
                    'id': strategy_id,
                    'type': strategy_type,
                    'symbol': symbol,
                    'status': instance.status,
                    'message': '策略创建成功'
                }
            }

        except Exception as e:
            logger.error(f"创建策略失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def start_strategy(self, strategy_id: str) -> Dict:
        """启动策略"""
        try:
            if strategy_id not in self.strategies:
                return {
                    'success': False,
                    'error': f'策略不存在: {strategy_id}'
                }

            instance = self.strategies[strategy_id]

            if instance.status == 'running':
                return {
                    'success': False,
                    'error': '策略已在运行中'
                }

            # 在新线程中启动策略
            def run_strategy():
                try:
                    instance.status = 'running'
                    instance.started_at = datetime.now()
                    instance.error_message = None

                    logger.info(f"启动策略: {strategy_id}")

                    # 根据策略类型执行
                    if instance.type in ['grid', 'futures_grid']:
                        instance.strategy.start()
                    else:
                        # 对于信号类策略，循环检查信号
                        while instance.status == 'running':
                            signal = instance.strategy.generate_signal()
                            if signal['signal'] != 'HOLD':
                                # 执行交易
                                quantity = instance.config.get('amount', 100) / signal['current_price']
                                result = instance.strategy.execute_signal(signal, quantity)

                                if result['success']:
                                    instance.total_trades += 1
                                    logger.info(f"策略交易: {result['message']}")

                            time.sleep(60)  # 每分钟检查一次

                except Exception as e:
                    logger.error(f"策略运行异常: {e}", exc_info=True)
                    instance.status = 'error'
                    instance.error_message = str(e)

            instance.thread = threading.Thread(target=run_strategy, daemon=True)
            instance.thread.start()

            return {
                'success': True,
                'data': {
                    'id': strategy_id,
                    'status': 'running',
                    'message': '策略已启动'
                }
            }

        except Exception as e:
            logger.error(f"启动策略失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def stop_strategy(self, strategy_id: str) -> Dict:
        """停止策略"""
        try:
            if strategy_id not in self.strategies:
                return {
                    'success': False,
                    'error': f'策略不存在: {strategy_id}'
                }

            instance = self.strategies[strategy_id]

            if instance.status != 'running':
                return {
                    'success': False,
                    'error': '策略未在运行'
                }

            # 停止策略
            instance.status = 'stopped'
            instance.stopped_at = datetime.now()

            # 如果有stop方法，调用它
            if hasattr(instance.strategy, 'stop'):
                instance.strategy.stop()

            logger.info(f"策略已停止: {strategy_id}")

            # 更新统计数据
            self._update_stats(instance)

            return {
                'success': True,
                'data': {
                    'id': strategy_id,
                    'status': 'stopped',
                    'message': '策略已停止'
                }
            }

        except Exception as e:
            logger.error(f"停止策略失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def delete_strategy(self, strategy_id: str) -> Dict:
        """删除策略"""
        try:
            if strategy_id not in self.strategies:
                return {
                    'success': False,
                    'error': f'策略不存在: {strategy_id}'
                }

            instance = self.strategies[strategy_id]

            # 如果正在运行，先停止
            if instance.status == 'running':
                self.stop_strategy(strategy_id)

            # 删除策略
            del self.strategies[strategy_id]

            # 删除文件
            strategy_file = self.data_dir / f"{strategy_id}.json"
            if strategy_file.exists():
                strategy_file.unlink()

            logger.info(f"策略已删除: {strategy_id}")

            return {
                'success': True,
                'data': {
                    'id': strategy_id,
                    'message': '策略已删除'
                }
            }

        except Exception as e:
            logger.error(f"删除策略失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """获取策略详情"""
        if strategy_id not in self.strategies:
            return None

        instance = self.strategies[strategy_id]

        # 更新统计数据
        self._update_stats(instance)

        # 获取订单历史
        orders = []
        if hasattr(instance.strategy, 'filled_orders'):
            orders = instance.strategy.filled_orders[-20:]  # 最近20个订单
        elif hasattr(instance.strategy, 'trades'):
            orders = instance.strategy.trades[-20:]

        data = instance.to_dict()
        data['orders'] = orders

        return data

    def list_strategies(self, status: Optional[str] = None) -> List[Dict]:
        """列出所有策略"""
        strategies = []

        for strategy_id, instance in self.strategies.items():
            if status is None or instance.status == status:
                # 更新统计数据
                self._update_stats(instance)
                strategies.append(instance.to_dict())

        # 按创建时间倒序排序
        strategies.sort(key=lambda x: x['created_at'], reverse=True)

        return strategies

    def _update_stats(self, instance: StrategyInstance):
        """更新策略统计数据"""
        try:
            if hasattr(instance.strategy, 'total_profit'):
                instance.total_profit = instance.strategy.total_profit

            if hasattr(instance.strategy, 'filled_orders'):
                instance.total_trades = len(instance.strategy.filled_orders)
            elif hasattr(instance.strategy, 'trades'):
                instance.total_trades = len(instance.strategy.trades)

            if hasattr(instance.strategy, 'get_performance'):
                perf = instance.strategy.get_performance()
                instance.winning_trades = perf.get('winning_trades', 0)
                instance.losing_trades = perf.get('losing_trades', 0)

        except Exception as e:
            logger.error(f"更新统计数据失败: {e}")

    def _save_strategy(self, instance: StrategyInstance):
        """保存策略到文件"""
        try:
            strategy_file = self.data_dir / f"{instance.id}.json"

            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(instance.to_dict(), f, indent=2, ensure_ascii=False)

            logger.debug(f"策略已保存: {strategy_file}")

        except Exception as e:
            logger.error(f"保存策略失败: {e}")

    def load_strategies(self):
        """从文件加载策略"""
        try:
            for strategy_file in self.data_dir.glob("*.json"):
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 重新创建策略（但不自动启动）
                self.create_strategy(
                    strategy_type=data['type'],
                    symbol=data['symbol'],
                    config=data['config'],
                    auto_start=False
                )

            logger.info(f"已加载 {len(self.strategies)} 个策略")

        except Exception as e:
            logger.error(f"加载策略失败: {e}")


# 全局单例
_strategy_manager = None


def get_strategy_manager() -> StrategyManager:
    """获取策略管理器单例"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
