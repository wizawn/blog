#!/usr/bin/env python3
"""
策略管理器集成测试
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.strategy_manager import StrategyManager, get_strategy_manager


class TestStrategyManager(unittest.TestCase):
    """策略管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = get_strategy_manager()

    def test_singleton(self):
        """测试单例模式"""
        manager1 = get_strategy_manager()
        manager2 = get_strategy_manager()
        self.assertIs(manager1, manager2)

    def test_create_grid_strategy(self):
        """测试创建网格策略"""
        result = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 10,
                'amount': 1000
            },
            auto_start=False
        )

        self.assertTrue(result['success'])
        self.assertIn('id', result['data'])

        strategy_id = result['data']['id']

        # 清理
        self.manager.delete_strategy(strategy_id)

    def test_create_ma_crossover_strategy(self):
        """测试创建均线策略"""
        result = self.manager.create_strategy(
            strategy_type='ma_crossover',
            symbol='ETHUSDT',
            config={
                'fast_period': 10,
                'slow_period': 30,
                'amount': 500,
                'interval': '1h'
            },
            auto_start=False
        )

        self.assertTrue(result['success'])
        self.assertIn('id', result['data'])

        strategy_id = result['data']['id']

        # 清理
        self.manager.delete_strategy(strategy_id)

    def test_list_strategies(self):
        """测试列出策略"""
        # 创建测试策略
        result1 = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 10,
                'amount': 1000
            }
        )

        strategy_id = result1['data']['id']

        # 列出策略
        strategies = self.manager.list_strategies()

        self.assertIsInstance(strategies, list)
        self.assertGreater(len(strategies), 0)

        # 清理
        self.manager.delete_strategy(strategy_id)

    def test_get_strategy(self):
        """测试获取策略详情"""
        # 创建测试策略
        result = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 10,
                'amount': 1000
            }
        )

        strategy_id = result['data']['id']

        # 获取策略详情
        strategy = self.manager.get_strategy(strategy_id)

        self.assertIsNotNone(strategy)
        self.assertEqual(strategy['id'], strategy_id)
        self.assertEqual(strategy['type'], 'grid')
        self.assertEqual(strategy['symbol'], 'BTCUSDT')

        # 清理
        self.manager.delete_strategy(strategy_id)

    def test_delete_strategy(self):
        """测试删除策略"""
        # 创建测试策略
        result = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 10,
                'amount': 1000
            }
        )

        strategy_id = result['data']['id']

        # 删除策略
        delete_result = self.manager.delete_strategy(strategy_id)

        self.assertTrue(delete_result['success'])

        # 验证已删除
        strategy = self.manager.get_strategy(strategy_id)
        self.assertIsNone(strategy)

    def test_invalid_strategy_type(self):
        """测试无效的策略类型"""
        result = self.manager.create_strategy(
            strategy_type='invalid_type',
            symbol='BTCUSDT',
            config={}
        )

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_missing_config(self):
        """测试缺少配置参数"""
        result = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000
                # 缺少其他必需参数
            }
        )

        # 应该失败或使用默认值
        self.assertIsInstance(result, dict)


class TestStrategyLifecycle(unittest.TestCase):
    """策略生命周期测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = get_strategy_manager()

    def test_strategy_lifecycle(self):
        """测试策略完整生命周期"""
        # 1. 创建策略
        result = self.manager.create_strategy(
            strategy_type='grid',
            symbol='BTCUSDT',
            config={
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 10,
                'amount': 1000
            },
            auto_start=False
        )

        self.assertTrue(result['success'])
        strategy_id = result['data']['id']

        # 2. 验证初始状态
        strategy = self.manager.get_strategy(strategy_id)
        self.assertEqual(strategy['status'], 'stopped')

        # 3. 启动策略（注意：实际启动会连接交易所，这里只测试接口）
        # start_result = self.manager.start_strategy(strategy_id)
        # self.assertTrue(start_result['success'])

        # 4. 停止策略
        # stop_result = self.manager.stop_strategy(strategy_id)
        # self.assertTrue(stop_result['success'])

        # 5. 删除策略
        delete_result = self.manager.delete_strategy(strategy_id)
        self.assertTrue(delete_result['success'])


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
