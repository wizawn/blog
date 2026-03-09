#!/usr/bin/env python3
"""
市场数据 API 路由
提供价格、K线、深度等市场数据接口
"""

from flask import Blueprint, jsonify, request
from ..binance_client import BinanceClient
import logging

logger = logging.getLogger(__name__)

market_bp = Blueprint('market', __name__, url_prefix='/api/v1/market')


@market_bp.route('/ping', methods=['GET'])
def ping():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'pong',
        'timestamp': int(request.environ.get('REQUEST_TIME', 0) * 1000)
    })


@market_bp.route('/price/<symbol>', methods=['GET'])
def get_price(symbol):
    """
    获取交易对价格

    Args:
        symbol: 交易对符号 (如: BTCUSDT)

    Returns:
        JSON 格式的价格数据
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        client = BinanceClient()
        ticker = client.get_ticker_price(symbol)

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'price': float(ticker.get('price', 0)),
                'change_percent': float(ticker.get('priceChangePercent', 0)),
                'high_24h': float(ticker.get('highPrice', 0)),
                'low_24h': float(ticker.get('lowPrice', 0)),
                'volume_24h': float(ticker.get('volume', 0)),
                'quote_volume_24h': float(ticker.get('quoteVolume', 0)),
                'open_price': float(ticker.get('openPrice', 0)),
                'close_price': float(ticker.get('lastPrice', 0))
            }
        })

    except Exception as e:
        logger.error(f"获取价格失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/prices', methods=['GET'])
def get_prices():
    """
    获取多个交易对价格

    Query params:
        symbols: 逗号分隔的交易对列表 (如: BTC,ETH,BNB)

    Returns:
        JSON 格式的价格列表
    """
    try:
        symbols_param = request.args.get('symbols', '')
        if not symbols_param:
            return jsonify({
                'success': False,
                'error': '缺少 symbols 参数'
            }), 400

        symbols = [s.strip().upper() for s in symbols_param.split(',')]
        symbols = [s if s.endswith('USDT') else s + 'USDT' for s in symbols]

        client = BinanceClient()
        results = []

        for symbol in symbols:
            try:
                ticker = client.get_ticker_price(symbol)
                results.append({
                    'symbol': symbol,
                    'price': float(ticker.get('price', 0)),
                    'change_percent': float(ticker.get('priceChangePercent', 0))
                })
            except Exception as e:
                logger.warning(f"获取 {symbol} 价格失败: {e}")
                results.append({
                    'symbol': symbol,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"获取价格列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/klines/<symbol>', methods=['GET'])
def get_klines(symbol):
    """
    获取K线数据

    Args:
        symbol: 交易对符号

    Query params:
        interval: 时间间隔 (1m, 5m, 15m, 1h, 4h, 1d)
        limit: 数量限制 (默认: 100)

    Returns:
        JSON 格式的K线数据
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))

        client = BinanceClient()
        klines = client.get_klines(symbol, interval, limit)

        # 格式化K线数据
        formatted_klines = []
        for kline in klines:
            formatted_klines.append({
                'open_time': kline[0],
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'close_time': kline[6],
                'quote_volume': float(kline[7]),
                'trades': kline[8]
            })

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'interval': interval,
                'klines': formatted_klines
            }
        })

    except Exception as e:
        logger.error(f"获取K线失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/depth/<symbol>', methods=['GET'])
def get_depth(symbol):
    """
    获取订单簿深度

    Args:
        symbol: 交易对符号

    Query params:
        limit: 深度限制 (5, 10, 20, 50, 100, 500, 1000)

    Returns:
        JSON 格式的深度数据
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        limit = int(request.args.get('limit', 20))

        client = BinanceClient()
        depth = client.get_order_book(symbol, limit)

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'bids': [[float(price), float(qty)] for price, qty in depth.get('bids', [])],
                'asks': [[float(price), float(qty)] for price, qty in depth.get('asks', [])],
                'last_update_id': depth.get('lastUpdateId')
            }
        })

    except Exception as e:
        logger.error(f"获取深度失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/ticker/<symbol>', methods=['GET'])
def get_ticker(symbol):
    """
    获取24小时价格变动统计

    Args:
        symbol: 交易对符号

    Returns:
        JSON 格式的统计数据
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        client = BinanceClient()
        ticker = client.get_ticker_price(symbol)

        return jsonify({
            'success': True,
            'data': {
                'symbol': ticker.get('symbol'),
                'price_change': float(ticker.get('priceChange', 0)),
                'price_change_percent': float(ticker.get('priceChangePercent', 0)),
                'weighted_avg_price': float(ticker.get('weightedAvgPrice', 0)),
                'prev_close_price': float(ticker.get('prevClosePrice', 0)),
                'last_price': float(ticker.get('lastPrice', 0)),
                'bid_price': float(ticker.get('bidPrice', 0)),
                'ask_price': float(ticker.get('askPrice', 0)),
                'open_price': float(ticker.get('openPrice', 0)),
                'high_price': float(ticker.get('highPrice', 0)),
                'low_price': float(ticker.get('lowPrice', 0)),
                'volume': float(ticker.get('volume', 0)),
                'quote_volume': float(ticker.get('quoteVolume', 0)),
                'open_time': ticker.get('openTime'),
                'close_time': ticker.get('closeTime'),
                'count': ticker.get('count')
            }
        })

    except Exception as e:
        logger.error(f"获取ticker失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
