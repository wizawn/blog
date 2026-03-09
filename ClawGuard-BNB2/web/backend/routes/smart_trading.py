#!/usr/bin/env python3
"""
智能交易 API 路由
提供趋势预测、事件分析和自动交易接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.prediction.trend_predictor import predict_price_trend
from src.prediction.event_analyzer import analyze_market_events
from src.prediction.auto_trading_engine import AutoTradingEngine
import logging

bp = Blueprint('smart_trading', __name__)
logger = logging.getLogger(__name__)

# 全局自动交易引擎实例
_auto_trading_engine = None


@bp.route('/predict/trend', methods=['GET'])
def get_trend_prediction():
    """获取价格趋势预测"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')
        periods = int(request.args.get('periods', 24))

        result = predict_price_trend(symbol, interval, periods)

        return jsonify(result)

    except Exception as e:
        logger.error(f"趋势预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/analyze/events', methods=['GET'])
def get_event_analysis():
    """获取市场事件分析"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')

        result = analyze_market_events(symbol)

        return jsonify(result)

    except Exception as e:
        logger.error(f"事件分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/auto-trading/start', methods=['POST'])
def start_auto_trading():
    """启动自动交易"""
    try:
        global _auto_trading_engine

        if _auto_trading_engine and _auto_trading_engine.running:
            return jsonify({
                'success': False,
                'error': '自动交易已在运行中'
            }), 400

        data = request.get_json() or {}

        config = {
            'symbols': data.get('symbols', ['BTCUSDT', 'ETHUSDT']),
            'check_interval': data.get('check_interval', 300),
            'min_confidence': data.get('min_confidence', 70),
            'position_size': data.get('position_size', 0.1),
            'stop_loss': data.get('stop_loss', 0.03),
            'take_profit': data.get('take_profit', 0.05)
        }

        _auto_trading_engine = AutoTradingEngine(config)
        _auto_trading_engine.start()

        return jsonify({
            'success': True,
            'message': '自动交易已启动',
            'config': config
        })

    except Exception as e:
        logger.error(f"启动自动交易失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/auto-trading/stop', methods=['POST'])
def stop_auto_trading():
    """停止自动交易"""
    try:
        global _auto_trading_engine

        if not _auto_trading_engine or not _auto_trading_engine.running:
            return jsonify({
                'success': False,
                'error': '自动交易未运行'
            }), 400

        _auto_trading_engine.stop()

        return jsonify({
            'success': True,
            'message': '自动交易已停止'
        })

    except Exception as e:
        logger.error(f"停止自动交易失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/auto-trading/status', methods=['GET'])
def get_auto_trading_status():
    """获取自动交易状态"""
    try:
        global _auto_trading_engine

        if not _auto_trading_engine:
            return jsonify({
                'success': True,
                'data': {
                    'running': False,
                    'message': '自动交易未初始化'
                }
            })

        status = _auto_trading_engine.get_status()

        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/smart-signal', methods=['GET'])
def get_smart_signal():
    """获取智能交易信号（综合预测和事件分析）"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')

        # 获取趋势预测
        trend_result = predict_price_trend(symbol, '1h', 24)

        # 获取事件分析
        event_result = analyze_market_events(symbol)

        if not trend_result['success'] or not event_result['success']:
            return jsonify({
                'success': False,
                'error': '分析失败'
            }), 500

        # 综合信号
        trend_action = trend_result['recommendation']['action']
        trend_confidence = trend_result['trend']['confidence']

        event_action = event_result['signals'][0]['action'] if event_result['signals'] else 'HOLD'
        event_confidence = event_result['signals'][0]['confidence'] if event_result['signals'] else 50

        # 计算综合置信度
        combined_confidence = (trend_confidence * 0.6 + event_confidence * 0.4)

        # 判断最终信号
        if trend_action == event_action and trend_action != 'HOLD':
            final_action = trend_action
            combined_confidence = min(combined_confidence * 1.2, 95)
            reason = f"趋势预测和事件分析均建议{final_action}"
        elif trend_action != event_action and 'HOLD' not in [trend_action, event_action]:
            final_action = 'HOLD'
            combined_confidence = 50
            reason = "信号冲突，建议观望"
        elif trend_action != 'HOLD':
            final_action = trend_action
            reason = f"趋势预测建议{final_action}"
        elif event_action != 'HOLD':
            final_action = event_action
            reason = f"事件分析建议{final_action}"
        else:
            final_action = 'HOLD'
            reason = "市场信号不明确"

        return jsonify({
            'success': True,
            'symbol': symbol,
            'signal': {
                'action': final_action,
                'confidence': round(combined_confidence, 2),
                'reason': reason
            },
            'trend_analysis': trend_result,
            'event_analysis': event_result,
            'timestamp': trend_result['timestamp']
        })

    except Exception as e:
        logger.error(f"获取智能信号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
