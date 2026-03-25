
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

        from src.risk.risk_control import RiskControlEngine
        risk_control = RiskControlEngine()
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
        # 从数据库获取风控告警
        from src.database.repository import RiskAlertRepository

        alert_repo = RiskAlertRepository()

        # 获取未解决的告警
        db_alerts = alert_repo.get_unresolved()

        # 转换为前端格式
        alerts = []
        for alert in db_alerts:
            alerts.append({
                'id': f"alert_{alert.id}",
                'type': alert.type,
                'level': alert.level,
                'message': alert.message,
                'symbol': alert.symbol,
                'time': alert.created_at.isoformat() if alert.created_at else None,
                'resolved': alert.resolved
            })

        # 限制返回数量
        alerts = alerts[:50]  # 最近50条

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

        # 计算拒绝订单数量（从数据库查询风控告警）
        rejected_orders = 0
        try:
            from src.database.repository import RiskAlertRepository
            alert_repo = RiskAlertRepository()
            # 获取所有拒绝类型的告警
            all_alerts = alert_repo.get_unresolved()
            rejected_orders = sum(1 for alert in all_alerts if '拒绝' in alert.message or 'reject' in alert.message.lower())
        except Exception as e:
            logger.warning(f"获取拒绝订单统计失败: {e}")
            rejected_orders = 0

        # 计算拒绝率
        rejection_rate = (rejected_orders / (total_orders + rejected_orders) * 100) if (total_orders + rejected_orders) > 0 else 0

        stats = {
            'total_orders': total_orders,
            'rejected_orders': rejected_orders,
            'rejection_rate': round(rejection_rate, 2),
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
            'success': False,
            'error': str(e)
        }), 500

# ==================== 新增的风险管理API端点 ====================

@bp.route('/positions', methods=['GET'])
def get_risk_positions():
    """获取风险持仓列表（带风险评分）"""
    try:
        from src.api.binance_futures_client import BinanceFuturesClient
        from src.risk.liquidation_risk_monitor import LiquidationRiskMonitor
        
        futures_client = BinanceFuturesClient()
        monitor = LiquidationRiskMonitor(futures_client)
        
        # 获取所有持仓
        position_risk = futures_client.get_position_risk()
        
        risk_positions = []
        for pos in position_risk:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt == 0:
                continue
                
            symbol = pos['symbol']
            entry_price = float(pos.get('entryPrice', 0))
            mark_price = float(pos.get('markPrice', 0))
            leverage = int(pos.get('leverage', 1))
            liquidation_price = float(pos.get('liquidationPrice', 0))
            
            # 计算风险评分
            side = 'LONG' if position_amt > 0 else 'SHORT'
            risk_score = monitor.calculate_risk_score(
                current_price=mark_price,
                liquidation_price=liquidation_price,
                position_side=side
            )
            
            risk_positions.append({
                'symbol': symbol,
                'positionAmt': position_amt,
                'entryPrice': entry_price,
                'markPrice': mark_price,
                'liquidationPrice': liquidation_price,
                'leverage': leverage,
                'side': side,
                'unRealizedProfit': float(pos.get('unRealizedProfit', 0)),
                'riskScore': risk_score.get('score', 0),
                'riskLevel': risk_score.get('level', 'UNKNOWN'),
                'safetyDistance': risk_score.get('distance_percent', 0),
                'recommendation': risk_score.get('recommendation', '')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'positions': risk_positions,
                'count': len(risk_positions)
            }
        })
        
    except Exception as e:
        logger.error(f"获取风险持仓失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/liquidation-price', methods=['POST'])
def calculate_liquidation_price():
    """计算爆仓价格"""
    try:
        data = request.get_json()
        
        side = data.get('side')  # LONG or SHORT
        entry_price = data.get('entry_price')
        leverage = data.get('leverage')
        maintenance_margin_rate = data.get('maintenance_margin_rate', 0.004)
        
        if not all([side, entry_price, leverage]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: side, entry_price, leverage'
            }), 400
        
        from src.risk.liquidation_risk_monitor import LiquidationRiskMonitor
        monitor = LiquidationRiskMonitor()
        
        liquidation_price = monitor.calculate_liquidation_price(
            side=side,
            entry_price=float(entry_price),
            leverage=int(leverage),
            maintenance_margin_rate=float(maintenance_margin_rate)
        )
        
        # 计算安全距离
        distance_percent = abs(float(entry_price) - liquidation_price) / float(entry_price) * 100
        
        return jsonify({
            'success': True,
            'data': {
                'liquidationPrice': liquidation_price,
                'entryPrice': float(entry_price),
                'leverage': int(leverage),
                'side': side,
                'safetyDistance': round(distance_percent, 2),
                'maintenanceMarginRate': float(maintenance_margin_rate)
            }
        })
        
    except Exception as e:
        logger.error(f"计算爆仓价格失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/risk-score', methods=['GET'])
def get_risk_score():
    """获取账户总体风险评分"""
    try:
        from src.api.binance_futures_client import BinanceFuturesClient
        from src.risk.liquidation_risk_monitor import LiquidationRiskMonitor
        
        futures_client = BinanceFuturesClient()
        monitor = LiquidationRiskMonitor(futures_client)
        
        # 获取所有持仓
        position_risk = futures_client.get_position_risk()
        
        total_risk_score = 0
        high_risk_count = 0
        critical_risk_count = 0
        position_count = 0
        
        for pos in position_risk:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt == 0:
                continue
            
            position_count += 1
            mark_price = float(pos.get('markPrice', 0))
            liquidation_price = float(pos.get('liquidationPrice', 0))
            side = 'LONG' if position_amt > 0 else 'SHORT'
            
            risk_score = monitor.calculate_risk_score(
                current_price=mark_price,
                liquidation_price=liquidation_price,
                position_side=side
            )
            
            score = risk_score.get('score', 0)
            level = risk_score.get('level', 'LOW')
            
            total_risk_score += score
            
            if level == 'HIGH':
                high_risk_count += 1
            elif level == 'CRITICAL':
                critical_risk_count += 1
        
        # 计算平均风险评分
        avg_risk_score = total_risk_score / position_count if position_count > 0 else 0
        
        # 确定总体风险等级
        if critical_risk_count > 0:
            overall_level = 'CRITICAL'
        elif high_risk_count > 0:
            overall_level = 'HIGH'
        elif avg_risk_score > 40:
            overall_level = 'MEDIUM'
        else:
            overall_level = 'LOW'
        
        return jsonify({
            'success': True,
            'data': {
                'overallRiskScore': round(avg_risk_score, 2),
                'overallRiskLevel': overall_level,
                'positionCount': position_count,
                'highRiskCount': high_risk_count,
                'criticalRiskCount': critical_risk_count,
                'recommendation': '建议立即减仓' if overall_level == 'CRITICAL' else 
                                 '建议降低杠杆' if overall_level == 'HIGH' else 
                                 '风险可控' if overall_level == 'MEDIUM' else 
                                 '风险较低'
            }
        })
        
    except Exception as e:
        logger.error(f"获取风险评分失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
