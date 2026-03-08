"""
风控路由 - 提供风险管理功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.risk.risk_control import RiskControl
from src.config.config_manager import ConfigManager
import logging

bp = Blueprint('risk', __name__)
logger = logging.getLogger(__name__)


@bp.route('/config', methods=['GET'])
def get_risk_config():
    """获取风控配置"""
    try:
        config_manager = ConfigManager()
        risk_config = config_manager.get('risk', {})

        return jsonify({
            'success': True,
            'data': risk_config
        })

    except Exception as e:
        logger.error(f"获取风控配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/config', methods=['POST'])
def update_risk_config():
    """更新风控配置"""
    try:
        data = request.get_json()

        config_manager = ConfigManager()

        # 更新配置
        if 'max_order_value' in data:
            config_manager.set('risk.max_order_value', data['max_order_value'])
        if 'max_daily_loss' in data:
            config_manager.set('risk.max_daily_loss', data['max_daily_loss'])
        if 'max_position_size' in data:
            config_manager.set('risk.max_position_size', data['max_position_size'])
        if 'enable_stop_loss' in data:
            config_manager.set('risk.enable_stop_loss', data['enable_stop_loss'])
        if 'default_stop_loss_percent' in data:
            config_manager.set('risk.default_stop_loss_percent', data['default_stop_loss_percent'])

        config_manager.save()

        return jsonify({
            'success': True,
            'message': '风控配置已更新'
        })

    except Exception as e:
        logger.error(f"更新风控配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/check', methods=['POST'])
def check_risk():
    """检查订单风险"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        side = data.get('side')
        quantity = data.get('quantity')

        if not all([symbol, side, quantity]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        risk_control = RiskControl()
        allowed = risk_control.check_order_allowed(symbol, side, float(quantity))

        if allowed:
            return jsonify({
                'success': True,
                'data': {
                    'allowed': True,
                    'message': '订单通过风控检查'
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'allowed': False,
                    'message': '订单被风控拒绝',
                    'reason': '超出风控限制'
                }
            })

    except Exception as e:
        logger.error(f"风控检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/alerts', methods=['GET'])
def get_risk_alerts():
    """获取风控告警"""
    try:
        # TODO: 从数据库或缓存获取风控告警历史

        alerts = [
            {
                'id': 'alert_1',
                'type': 'order_rejected',
                'level': 'warning',
                'message': '订单超出单笔限额',
                'symbol': 'BTCUSDT',
                'time': '2024-03-08 14:30:00'
            }
        ]

        return jsonify({
            'success': True,
            'data': alerts
        })

    except Exception as e:
        logger.error(f"获取风控告警失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/stats', methods=['GET'])
def get_risk_stats():
    """获取风控统计"""
    try:
        # TODO: 计算风控统计数据

        stats = {
            'total_orders': 150,
            'rejected_orders': 5,
            'rejection_rate': 3.3,
            'total_value': 50000,
            'max_single_order': 5000,
            'daily_loss': -250,
            'max_daily_loss': 1000,
            'risk_level': 'low'
        }

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取风控统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
