"""
策略路由 - 提供策略管理功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.strategies.strategy_manager import get_strategy_manager
import logging

bp = Blueprint('strategy', __name__)
logger = logging.getLogger(__name__)

# 获取策略管理器单例
strategy_manager = get_strategy_manager()


@bp.route('/list', methods=['GET'])
def list_strategies():
    """获取策略列表"""
    try:
        # 从策略管理器获取所有策略
        strategies = strategy_manager.list_strategies()

        # 格式化数据以匹配前端期望
        formatted_strategies = []
        for s in strategies:
            # 安全地访问嵌套字典
            stats = s.get('stats', {})
            config = s.get('config', {})

            total_profit = stats.get('total_profit', 0)
            amount = config.get('amount', 1)

            # 计算盈利百分比，避免除零
            profit_percent = 0
            if amount and amount > 0:
                profit_percent = (total_profit / amount) * 100

            formatted_strategies.append({
                'id': s.get('id', ''),
                'type': s.get('type', ''),
                'name': f"{s.get('symbol', 'Unknown')} {s.get('type', '')} 策略",
                'symbol': s.get('symbol', ''),
                'status': s.get('status', 'unknown'),
                'profit': total_profit,
                'profit_percent': profit_percent,
                'orders_filled': stats.get('total_trades', 0),
                'orders_total': stats.get('total_trades', 0),
                'start_time': s.get('started_at') or s.get('created_at', ''),
                'config': config
            })

        return jsonify({
            'success': True,
            'data': formatted_strategies
        })

    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/create', methods=['POST'])
def create_strategy():
    """创建新策略"""
    try:
        data = request.get_json()

        strategy_type = data.get('type')
        symbol = data.get('symbol')
        config = data.get('config', {})
        auto_start = data.get('auto_start', False)

        if not all([strategy_type, symbol]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        # 验证配置参数
        if strategy_type == 'grid':
            required = ['lower_price', 'upper_price', 'grids', 'amount']
            if not all(config.get(k) for k in required):
                return jsonify({
                    'success': False,
                    'error': '网格策略缺少必需参数'
                }), 400

        elif strategy_type == 'ma_crossover':
            required = ['fast_period', 'slow_period', 'amount']
            if not all(config.get(k) for k in required):
                return jsonify({
                    'success': False,
                    'error': '均线策略缺少必需参数'
                }), 400

        elif strategy_type == 'breakout':
            required = ['period', 'amount']
            if not all(config.get(k) for k in required):
                return jsonify({
                    'success': False,
                    'error': '突破策略缺少必需参数'
                }), 400

        # 使用策略管理器创建策略
        result = strategy_manager.create_strategy(
            strategy_type=strategy_type,
            symbol=symbol,
            config=config,
            auto_start=auto_start
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """获取策略详情"""
    try:
        # 从策略管理器获取策略详情
        strategy = strategy_manager.get_strategy(strategy_id)

        if not strategy:
            return jsonify({
                'success': False,
                'error': f'策略不存在: {strategy_id}'
            }), 404

        # 格式化数据
        stats = strategy.get('stats', {})
        config = strategy.get('config', {})

        total_profit = stats.get('total_profit', 0)
        amount = config.get('amount', 1)

        # 计算盈利百分比，避免除零
        profit_percent = 0
        if amount and amount > 0:
            profit_percent = (total_profit / amount) * 100

        formatted_strategy = {
            'id': strategy.get('id', ''),
            'type': strategy.get('type', ''),
            'name': f"{strategy.get('symbol', 'Unknown')} {strategy.get('type', '')} 策略",
            'symbol': strategy.get('symbol', ''),
            'status': strategy.get('status', 'unknown'),
            'profit': total_profit,
            'profit_percent': profit_percent,
            'orders_filled': stats.get('total_trades', 0),
            'orders_total': stats.get('total_trades', 0),
            'start_time': strategy.get('started_at') or strategy.get('created_at', ''),
            'config': config,
            'orders': strategy.get('orders', []),
            'error_message': strategy.get('error_message')
        }

        return jsonify({
            'success': True,
            'data': formatted_strategy
        })

    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<strategy_id>/stop', methods=['POST'])
def stop_strategy(strategy_id):
    """停止策略"""
    try:
        # 使用策略管理器停止策略
        result = strategy_manager.stop_strategy(strategy_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<strategy_id>/start', methods=['POST'])
def start_strategy(strategy_id):
    """启动策略"""
    try:
        # 使用策略管理器启动策略
        result = strategy_manager.start_strategy(strategy_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    """删除策略"""
    try:
        # 使用策略管理器删除策略
        result = strategy_manager.delete_strategy(strategy_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/types', methods=['GET'])
def get_strategy_types():
    """获取支持的策略类型"""
    try:
        types = [
            {
                'id': 'grid',
                'name': '网格策略',
                'description': '在价格区间内自动低买高卖',
                'params': [
                    {'name': 'lower_price', 'label': '下限价格', 'type': 'number', 'required': True},
                    {'name': 'upper_price', 'label': '上限价格', 'type': 'number', 'required': True},
                    {'name': 'grids', 'label': '网格数量', 'type': 'number', 'required': True},
                    {'name': 'amount', 'label': '投入金额', 'type': 'number', 'required': True}
                ]
            },
            {
                'id': 'ma_crossover',
                'name': '均线交叉策略',
                'description': '基于移动平均线交叉信号交易',
                'params': [
                    {'name': 'fast_period', 'label': '快线周期', 'type': 'number', 'required': True},
                    {'name': 'slow_period', 'label': '慢线周期', 'type': 'number', 'required': True},
                    {'name': 'amount', 'label': '每次交易金额', 'type': 'number', 'required': True}
                ]
            }
        ]

        return jsonify({
            'success': True,
            'data': types
        })

    except Exception as e:
        logger.error(f"获取策略类型失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
