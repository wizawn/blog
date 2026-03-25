
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

        # Don't pass client, let TechnicalIndicators create its own
        indicators = TechnicalIndicators()

        klines = indicators.get_klines(symbol, interval, limit)

        # 转换为前端需要的格式
        formatted_klines = []
        for kline in klines:
            # indicators.get_klines() returns dicts, not arrays
            formatted_klines.append({
                'time': kline.get('open_time', 0),
                'open': float(kline.get('open', 0)),
                'high': float(kline.get('high', 0)),
                'low': float(kline.get('low', 0)),
                'close': float(kline.get('close', 0)),
                'volume': float(kline.get('volume', 0))
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


@bp.route('/summary', methods=['GET'])
def get_analysis_summary():
    """获取分析摘要"""
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')

        # Don't pass client, let TechnicalIndicators create its own
        indicators = TechnicalIndicators()

        klines = indicators.get_klines(symbol, interval, 100)

        # 计算各种指标
        rsi = indicators.calculate_rsi(klines)
        macd_line, signal_line, _ = indicators.calculate_macd(klines)
        upper, middle, lower = indicators.calculate_bollinger_bands(klines)
        ma20 = indicators.calculate_ma(klines, 20)
        ma50 = indicators.calculate_ma(klines, 50)

        current_price = float(klines[-1].get('close', 0))

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

# ==================== 新增的技术分析API端点 ====================

@bp.route('/indicators', methods=['GET'])
def get_indicators():
    """获取技术指标"""
    try:
        symbol = request.args.get('symbol')
        interval = request.args.get('interval', '1h')
        limit = request.args.get('limit', 100, type=int)

        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol'
            }), 400

        # 验证symbol格式和长度
        if len(symbol) > 20:
            return jsonify({
                'success': False,
                'error': f'交易对名称过长: {len(symbol)}字符，最大20字符'
            }), 400

        if not symbol.endswith('USDT') or len(symbol) < 5:
            return jsonify({
                'success': False,
                'error': f'无效的交易对: {symbol}，必须以USDT结尾且长度至少5字符'
            }), 400

        from src.analysis.indicators import TechnicalIndicators

        indicators = TechnicalIndicators()

        # 获取K线数据 - use indicators.get_klines instead of client
        klines = indicators.get_klines(symbol, interval, limit)

        # 提取收盘价
        prices = [float(k['close']) for k in klines]

        # 计算各种指标
        result = {
            'symbol': symbol,
            'interval': interval,
            'timestamp': klines[-1]['close_time'] if klines else 0,
            'indicators': {}
        }

        # RSI
        try:
            rsi = indicators.calculate_rsi(prices, period=14)
            if rsi:
                result['indicators']['rsi'] = {
                    'value': round(rsi[-1], 2),
                    'signal': 'OVERBOUGHT' if rsi[-1] > 70 else 'OVERSOLD' if rsi[-1] < 30 else 'NEUTRAL'
                }
        except Exception as e:
            logger.warning(f"计算RSI失败: {e}")

        # MACD
        try:
            macd = indicators.calculate_macd(prices)
            if macd and macd['macd']:
                result['indicators']['macd'] = {
                    'macd': round(macd['macd'][-1], 2),
                    'signal': round(macd['signal'][-1], 2),
                    'histogram': round(macd['histogram'][-1], 2),
                    'trend': 'BULLISH' if macd['histogram'][-1] > 0 else 'BEARISH'
                }
        except Exception as e:
            logger.warning(f"计算MACD失败: {e}")

        # 布林带
        try:
            bb = indicators.calculate_bollinger_bands(prices, period=20)
            if bb and bb['upper']:
                current_price = prices[-1]
                result['indicators']['bollinger_bands'] = {
                    'upper': round(bb['upper'][-1], 2),
                    'middle': round(bb['middle'][-1], 2),
                    'lower': round(bb['lower'][-1], 2),
                    'position': 'ABOVE_UPPER' if current_price > bb['upper'][-1] else
                               'BELOW_LOWER' if current_price < bb['lower'][-1] else
                               'WITHIN_BANDS'
                }
        except Exception as e:
            logger.warning(f"计算布林带失败: {e}")

        # EMA
        try:
            ema_12 = indicators.calculate_ema(prices, period=12)
            ema_26 = indicators.calculate_ema(prices, period=26)
            if ema_12 and ema_26:
                result['indicators']['ema'] = {
                    'ema12': round(ema_12[-1], 2),
                    'ema26': round(ema_26[-1], 2),
                    'trend': 'BULLISH' if ema_12[-1] > ema_26[-1] else 'BEARISH'
                }
        except Exception as e:
            logger.warning(f"计算EMA失败: {e}")

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


@bp.route('/patterns', methods=['GET'])
def get_patterns():
    """识别K线形态"""
    try:
        symbol = request.args.get('symbol')
        interval = request.args.get('interval', '1h')
        limit = request.args.get('limit', 100, type=int)
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol'
            }), 400
        
        from src.analysis.pattern_recognition import PatternRecognition
        from src.api.binance_futures_client import BinanceFuturesClient
        
        recognizer = PatternRecognition()
        client = BinanceFuturesClient()
        
        # 获取K线数据
        klines = client.get_klines(symbol, interval, limit)
        
        # 识别所有形态
        patterns = recognizer.recognize_all_patterns(klines)
        
        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'interval': interval,
                'patterns': patterns,
                'count': len(patterns)
            }
        })
        
    except Exception as e:
        logger.error(f"识别K线形态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/signals', methods=['GET'])
def get_signals():
    """获取综合交易信号"""
    try:
        symbol = request.args.get('symbol')
        interval = request.args.get('interval', '1h')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol'
            }), 400
        
        from src.analysis.indicators import TechnicalIndicators
        from src.analysis.pattern_recognition import PatternRecognition
        from src.api.binance_futures_client import BinanceFuturesClient
        
        indicators = TechnicalIndicators()
        recognizer = PatternRecognition()
        client = BinanceFuturesClient()
        
        # 获取K线数据
        klines = client.get_klines(symbol, interval, 100)
        prices = [float(k['close']) for k in klines]
        
        # 综合信号评分
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        # RSI信号
        try:
            rsi = indicators.calculate_rsi(prices, period=14)
            if rsi:
                if rsi[-1] < 30:
                    bullish_score += 2
                    signals.append({'indicator': 'RSI', 'signal': 'BUY', 'strength': 'STRONG'})
                elif rsi[-1] > 70:
                    bearish_score += 2
                    signals.append({'indicator': 'RSI', 'signal': 'SELL', 'strength': 'STRONG'})
        except Exception as e:
            logger.warning(f"计算RSI信号失败: {e}")

        # MACD信号
        try:
            macd = indicators.calculate_macd(prices)
            if macd and macd['histogram']:
                if macd['histogram'][-1] > 0:
                    bullish_score += 1
                    signals.append({'indicator': 'MACD', 'signal': 'BUY', 'strength': 'MEDIUM'})
                else:
                    bearish_score += 1
                    signals.append({'indicator': 'MACD', 'signal': 'SELL', 'strength': 'MEDIUM'})
        except Exception as e:
            logger.warning(f"计算MACD信号失败: {e}")

        # EMA信号
        try:
            ema_12 = indicators.calculate_ema(prices, period=12)
            ema_26 = indicators.calculate_ema(prices, period=26)
            if ema_12 and ema_26:
                if ema_12[-1] > ema_26[-1]:
                    bullish_score += 1
                    signals.append({'indicator': 'EMA', 'signal': 'BUY', 'strength': 'MEDIUM'})
                else:
                    bearish_score += 1
                    signals.append({'indicator': 'EMA', 'signal': 'SELL', 'strength': 'MEDIUM'})
        except Exception as e:
            logger.warning(f"计算EMA信号失败: {e}")

        # K线形态信号
        try:
            patterns = recognizer.recognize_all_patterns(klines)
            for pattern in patterns:
                if pattern['signal'] == 'BULLISH':
                    bullish_score += 1
                    signals.append({'indicator': 'PATTERN', 'signal': 'BUY', 'pattern': pattern['pattern']})
                elif pattern['signal'] == 'BEARISH':
                    bearish_score += 1
                    signals.append({'indicator': 'PATTERN', 'signal': 'SELL', 'pattern': pattern['pattern']})
        except Exception as e:
            logger.warning(f"识别K线形态失败: {e}")
        
        # 综合判断
        total_score = bullish_score + bearish_score
        if total_score == 0:
            overall_signal = 'NEUTRAL'
            confidence = 0
        else:
            if bullish_score > bearish_score:
                overall_signal = 'BUY'
                confidence = round((bullish_score / total_score) * 100, 2)
            elif bearish_score > bullish_score:
                overall_signal = 'SELL'
                confidence = round((bearish_score / total_score) * 100, 2)
            else:
                overall_signal = 'NEUTRAL'
                confidence = 50
        
        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'interval': interval,
                'overallSignal': overall_signal,
                'confidence': confidence,
                'bullishScore': bullish_score,
                'bearishScore': bearish_score,
                'signals': signals,
                'recommendation': f'建议{overall_signal}' if overall_signal != 'NEUTRAL' else '观望'
            }
        })
        
    except Exception as e:
        logger.error(f"获取交易信号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


