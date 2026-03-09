"""
风控路由 - 提供风险管理功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.risk.risk_control import RiskControlEngine
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
        # 从风控引擎获取告警历史
        risk_engine = RiskControlEngine()

        # 读取日志文件获取风控告警
        from pathlib import Path
        import json
        from datetime import datetime, timedelta

        alerts = []
        log_file = Path.home() / ".clawguard" / "clawguard.log"

        if log_file.exists():
            try:
                # 读取最近的日志
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-200:]  # 最近200行

                # 解析风控相关日志
                for line in lines:
                    if '风控' in line or 'risk' in line.lower() or '拒绝' in line:
                        try:
                            # 简单解析日志格式
                            parts = line.split(' - ')
                            if len(parts) >= 3:
                                timestamp = parts[0].strip()
                                level = parts[1].strip()
                                message = parts[2].strip()

                                alert_level = 'warning'
                                if 'ERROR' in level or '错误' in message:
                                    alert_level = 'error'
                                elif 'INFO' in level:
                                    alert_level = 'info'

                                alerts.append({
                                    'id': f"alert_{len(alerts)}",
                                    'type': 'risk_control',
                                    'level': alert_level,
                                    'message': message,
                                    'time': timestamp
                                })
                        except:
                            continue
            except Exception as e:
                logger.error(f"读取日志文件失败: {e}")

        # 如果没有告警，返回空列表
        if not alerts:
            alerts = []

        # 限制返回数量
        alerts = alerts[-50:]  # 最近50条

        return jsonify({
            'success': True,
            'data': alerts
        })

    except Exception as e:
        logger.error(f"获取风控告警失败: {e}")
        return jsonify({
            'success': True,
            'data': []
        })


@bp.route('/stats', methods=['GET'])
def get_risk_stats():
    """获取风控统计"""
    try:
        # 从策略管理器计算风控统计数据
        from src.strategies.strategy_manager import get_strategy_manager
        strategy_manager = get_strategy_manager()

        all_strategies = strategy_manager.list_strategies()

        # 计算统计数据
        total_orders = 0
        total_profit = 0
        total_investment = 0
        winning_trades = 0
        losing_trades = 0

        for strategy in all_strategies:
            total_orders += strategy['stats']['total_trades']
            total_profit += strategy['stats']['total_profit']
            total_investment += strategy['config'].get('amount', 0)
            winning_trades += strategy['stats']['winning_trades']
            losing_trades += strategy['stats']['losing_trades']

        # 计算风险等级
        risk_level = 'low'
        if total_investment > 10000:
            risk_level = 'medium'
        if total_investment > 50000:
            risk_level = 'high'

        # 计算盈亏比
        profit_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0

        stats = {
            'total_orders': total_orders,
            'rejected_orders': 0,  # 需要从日志统计
            'rejection_rate': 0,
            'total_value': round(total_investment, 2),
            'total_profit': round(total_profit, 2),
            'profit_rate': round(profit_rate, 2),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round((winning_trades / total_orders * 100) if total_orders > 0 else 0, 2),
            'risk_level': risk_level
        }

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取风控统计失败: {e}")
        return jsonify({
            'success': True,
            'data': {
                'total_orders': 0,
                'rejected_orders': 0,
                'rejection_rate': 0,
                'total_value': 0,
                'total_profit': 0,
                'profit_rate': 0,
                'risk_level': 'low'
            }
        })
