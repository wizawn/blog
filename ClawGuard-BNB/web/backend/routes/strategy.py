"""
策略路由 - 提供策略管理功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.strategies.grid_strategy import GridStrategy
import logging

bp = Blueprint('strategy', __name__)
logger = logging.getLogger(__name__)


@bp.route('/list', methods=['GET'])
def list_strategies():
    """获取策略列表"""
    try:
        # TODO: 从策略管理器获取运行中的策略
        # 这里返回示例数据

        strategies = [
            {
                'id': 'grid_btc_1',
                'type': 'grid',
                'name': 'BTC 网格策略',
                'symbol': 'BTCUSDT',
                'status': 'running',
                'profit': 125.50,
                'profit_percent': 2.5,
                'orders_filled': 15,
                'orders_total': 20,
                'start_time': '2024-03-08 10:00:00',
                'config': {
                    'lower_price': 65000,
                    'upper_price': 70000,
                    'grids': 20,
                    'amount': 1000
                }
            }
        ]

        return jsonify({
            'success': True,
            'data': strategies
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

        if not all([strategy_type, symbol]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        # 根据策略类型创建策略
        if strategy_type == 'grid':
            lower_price = config.get('lower_price')
            upper_price = config.get('upper_price')
            grids = config.get('grids')
            amount = config.get('amount')

            if not all([lower_price, upper_price, grids, amount]):
                return jsonify({
                    'success': False,
                    'error': '网格策略缺少必需参数'
                }), 400

            # TODO: 实际创建并启动策略
            # strategy = GridStrategy(...)
            # strategy.start()

            return jsonify({
                'success': True,
                'data': {
                    'id': f'grid_{symbol}_1',
                    'message': '策略创建成功'
                }
            })

        else:
            return jsonify({
                'success': False,
                'error': f'不支持的策略类型: {strategy_type}'
            }), 400

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
        # TODO: 从策略管理器获取策略详情

        strategy = {
            'id': strategy_id,
            'type': 'grid',
            'name': 'BTC 网格策略',
            'symbol': 'BTCUSDT',
            'status': 'running',
            'profit': 125.50,
            'profit_percent': 2.5,
            'orders_filled': 15,
            'orders_total': 20,
            'start_time': '2024-03-08 10:00:00',
            'config': {
                'lower_price': 65000,
                'upper_price': 70000,
                'grids': 20,
                'amount': 1000
            },
            'orders': [
                {
                    'id': 'order_1',
                    'side': 'BUY',
                    'price': 65500,
                    'quantity': 0.015,
                    'status': 'FILLED',
                    'time': '2024-03-08 10:15:00'
                }
            ]
        }

        return jsonify({
            'success': True,
            'data': strategy
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
        # TODO: 停止策略

        return jsonify({
            'success': True,
            'data': {
                'id': strategy_id,
                'status': 'stopped',
                'message': '策略已停止'
            }
        })

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
        # TODO: 启动策略

        return jsonify({
            'success': True,
            'data': {
                'id': strategy_id,
                'status': 'running',
                'message': '策略已启动'
            }
        })

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
        # TODO: 删除策略

        return jsonify({
            'success': True,
            'data': {
                'id': strategy_id,
                'message': '策略已删除'
            }
        })

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
