"""
市场分析路由 - 提供技术分析和市场数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.trading.unified_client import UnifiedTradingClient
from src.analysis.indicators import TechnicalIndicators
import logging

bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)


@bp.route('/klines', methods=['GET'])
def get_klines():
    """获取K线数据"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))

        client = UnifiedTradingClient()
        indicators = TechnicalIndicators(client)

        klines = indicators.get_klines(symbol, interval, limit)

        # 转换为前端需要的格式
        formatted_klines = []
        for kline in klines:
            formatted_klines.append({
                'time': kline[0],  # 开盘时间
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5])
            })

        return jsonify({
            'success': True,
            'data': formatted_klines
        })

    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/indicators', methods=['GET'])
def get_indicators():
    """获取技术指标"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')
        indicator_type = request.args.get('type', 'all')

        client = UnifiedTradingClient()
        indicators = TechnicalIndicators(client)

        klines = indicators.get_klines(symbol, interval, 100)

        result = {}

        if indicator_type in ['all', 'rsi']:
            rsi = indicators.calculate_rsi(klines)
            result['rsi'] = {
                'value': rsi,
                'signal': 'overbought' if rsi > 70 else 'oversold' if rsi < 30 else 'neutral'
            }

        if indicator_type in ['all', 'macd']:
            macd_line, signal_line, histogram = indicators.calculate_macd(klines)
            result['macd'] = {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram,
                'trend': 'bullish' if macd_line > signal_line else 'bearish'
            }

        if indicator_type in ['all', 'bollinger']:
            upper, middle, lower = indicators.calculate_bollinger_bands(klines)
            current_price = float(klines[-1][4])
            result['bollinger'] = {
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'current_price': current_price,
                'position': 'upper' if current_price > middle else 'lower'
            }

        if indicator_type in ['all', 'ma']:
            ma20 = indicators.calculate_ma(klines, 20)
            ma50 = indicators.calculate_ma(klines, 50)
            result['ma'] = {
                'ma20': ma20,
                'ma50': ma50,
                'trend': 'bullish' if ma20 > ma50 else 'bearish'
            }

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"获取技术指标失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/summary', methods=['GET'])
def get_analysis_summary():
    """获取分析摘要"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')

        client = UnifiedTradingClient()
        indicators = TechnicalIndicators(client)

        klines = indicators.get_klines(symbol, interval, 100)

        # 计算各种指标
        rsi = indicators.calculate_rsi(klines)
        macd_line, signal_line, _ = indicators.calculate_macd(klines)
        upper, middle, lower = indicators.calculate_bollinger_bands(klines)
        ma20 = indicators.calculate_ma(klines, 20)
        ma50 = indicators.calculate_ma(klines, 50)

        current_price = float(klines[-1][4])

        # 综合分析
        signals = []

        # RSI 信号
        if rsi > 70:
            signals.append({'indicator': 'RSI', 'signal': 'SELL', 'strength': 'strong', 'reason': 'RSI超买'})
        elif rsi < 30:
            signals.append({'indicator': 'RSI', 'signal': 'BUY', 'strength': 'strong', 'reason': 'RSI超卖'})

        # MACD 信号
        if macd_line > signal_line:
            signals.append({'indicator': 'MACD', 'signal': 'BUY', 'strength': 'medium', 'reason': 'MACD金叉'})
        else:
            signals.append({'indicator': 'MACD', 'signal': 'SELL', 'strength': 'medium', 'reason': 'MACD死叉'})

        # 布林带信号
        if current_price > upper:
            signals.append({'indicator': 'Bollinger', 'signal': 'SELL', 'strength': 'medium', 'reason': '价格突破上轨'})
        elif current_price < lower:
            signals.append({'indicator': 'Bollinger', 'signal': 'BUY', 'strength': 'medium', 'reason': '价格突破下轨'})

        # 均线信号
        if ma20 > ma50:
            signals.append({'indicator': 'MA', 'signal': 'BUY', 'strength': 'weak', 'reason': '短期均线在长期均线上方'})
        else:
            signals.append({'indicator': 'MA', 'signal': 'SELL', 'strength': 'weak', 'reason': '短期均线在长期均线下方'})

        # 计算综合评分
        buy_score = sum(1 for s in signals if s['signal'] == 'BUY')
        sell_score = sum(1 for s in signals if s['signal'] == 'SELL')

        if buy_score > sell_score:
            overall_signal = 'BUY'
            confidence = buy_score / len(signals) * 100
        elif sell_score > buy_score:
            overall_signal = 'SELL'
            confidence = sell_score / len(signals) * 100
        else:
            overall_signal = 'NEUTRAL'
            confidence = 50

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'interval': interval,
                'current_price': current_price,
                'overall_signal': overall_signal,
                'confidence': round(confidence, 2),
                'signals': signals,
                'indicators': {
                    'rsi': rsi,
                    'macd': macd_line,
                    'ma20': ma20,
                    'ma50': ma50
                }
            }
        })

    except Exception as e:
        logger.error(f"获取分析摘要失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/depth', methods=['GET'])
def get_depth():
    """获取市场深度"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        limit = int(request.args.get('limit', 20))

        client = UnifiedTradingClient()
        depth = client.get_order_book(symbol, limit)

        return jsonify({
            'success': True,
            'data': {
                'bids': depth.get('bids', []),
                'asks': depth.get('asks', [])
            }
        })

    except Exception as e:
        logger.error(f"获取市场深度失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
