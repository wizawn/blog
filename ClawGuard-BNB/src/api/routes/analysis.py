#!/usr/bin/env python3
"""
技术分析 API 路由
提供技术指标、趋势分析等接口
"""

from flask import Blueprint, jsonify, request
from ...analysis.indicators import create_indicators
import logging

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/v1/analysis')


@analysis_bp.route('/indicators/<symbol>', methods=['GET'])
def get_indicators(symbol):
    """
    获取技术指标

    Args:
        symbol: 交易对符号

    Query params:
        interval: 时间间隔 (默认: 1h)
        indicators: 指标列表，逗号分隔 (可选: rsi,macd,bb,ma,volume)

    Returns:
        JSON 格式的技术指标数据
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = request.args.get('interval', '1h')
        indicators_param = request.args.get('indicators', 'rsi,macd,bb,ma')
        requested_indicators = [i.strip().lower() for i in indicators_param.split(',')]

        indicators = create_indicators()
        analysis = indicators.analyze(symbol, interval)

        # 根据请求的指标过滤结果
        result = {
            'symbol': symbol,
            'interval': interval,
            'indicators': {}
        }

        if 'rsi' in requested_indicators and 'rsi' in analysis:
            result['indicators']['rsi'] = analysis['rsi']

        if 'macd' in requested_indicators and 'macd' in analysis:
            result['indicators']['macd'] = analysis['macd']

        if 'bb' in requested_indicators and 'bollinger_bands' in analysis:
            result['indicators']['bollinger_bands'] = analysis['bollinger_bands']

        if 'ma' in requested_indicators and 'moving_averages' in analysis:
            result['indicators']['moving_averages'] = analysis['moving_averages']

        if 'volume' in requested_indicators and 'volume' in analysis:
            result['indicators']['volume'] = analysis['volume']

        # 添加趋势和信号
        if 'trend' in analysis:
            result['trend'] = analysis['trend']

        if 'signal' in analysis:
            result['signal'] = analysis['signal']

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"获取技术指标失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/trend/<symbol>', methods=['GET'])
def get_trend(symbol):
    """
    获取趋势分析

    Args:
        symbol: 交易对符号

    Query params:
        interval: 时间间隔 (默认: 1h)

    Returns:
        JSON 格式的趋势分析
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = request.args.get('interval', '1h')

        indicators = create_indicators()
        analysis = indicators.analyze(symbol, interval)

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'interval': interval,
                'trend': analysis.get('trend', 'UNKNOWN'),
                'signal': analysis.get('signal', 'NEUTRAL'),
                'confidence': analysis.get('confidence', 0),
                'recommendation': analysis.get('recommendation', 'HOLD')
            }
        })

    except Exception as e:
        logger.error(f"获取趋势分析失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/summary/<symbol>', methods=['GET'])
def get_summary(symbol):
    """
    获取综合分析摘要

    Args:
        symbol: 交易对符号

    Query params:
        interval: 时间间隔 (默认: 1h)

    Returns:
        JSON 格式的综合分析
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = request.args.get('interval', '1h')

        indicators = create_indicators()
        analysis = indicators.analyze(symbol, interval)

        # 构建摘要
        summary = {
            'symbol': symbol,
            'interval': interval,
            'trend': analysis.get('trend', 'UNKNOWN'),
            'signal': analysis.get('signal', 'NEUTRAL'),
            'recommendation': analysis.get('recommendation', 'HOLD'),
            'key_levels': {},
            'indicators_summary': {}
        }

        # RSI 摘要
        if 'rsi' in analysis:
            rsi_value = analysis['rsi'].get('value', 50)
            if rsi_value > 70:
                rsi_status = 'OVERBOUGHT'
            elif rsi_value < 30:
                rsi_status = 'OVERSOLD'
            else:
                rsi_status = 'NEUTRAL'

            summary['indicators_summary']['rsi'] = {
                'value': rsi_value,
                'status': rsi_status
            }

        # MACD 摘要
        if 'macd' in analysis:
            macd_data = analysis['macd']
            summary['indicators_summary']['macd'] = {
                'signal': macd_data.get('signal', 'NEUTRAL'),
                'histogram': macd_data.get('histogram', 0)
            }

        # 布林带摘要
        if 'bollinger_bands' in analysis:
            bb_data = analysis['bollinger_bands']
            summary['key_levels']['upper_band'] = bb_data.get('upper', 0)
            summary['key_levels']['middle_band'] = bb_data.get('middle', 0)
            summary['key_levels']['lower_band'] = bb_data.get('lower', 0)

        # 移动平均线摘要
        if 'moving_averages' in analysis:
            ma_data = analysis['moving_averages']
            summary['key_levels']['ma20'] = ma_data.get('ma20', 0)
            summary['key_levels']['ma50'] = ma_data.get('ma50', 0)

        return jsonify({
            'success': True,
            'data': summary
        })

    except Exception as e:
        logger.error(f"获取综合分析失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
