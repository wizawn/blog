#!/usr/bin/env python3
"""
交易管理 API 路由
提供下单、查询订单、取消订单等接口
"""

from flask import Blueprint, jsonify, request
from ..binance_client import BinanceClient
import logging

logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__, url_prefix='/api/v1/trading')


@trading_bp.route('/order', methods=['POST'])
def place_order():
    """
    下单

    Request body:
        {
            "symbol": "BTCUSDT",
            "side": "BUY" | "SELL",
            "type": "MARKET" | "LIMIT",
            "quantity": 0.001,
            "price": 68000.0 (LIMIT订单必需)
        }

    Returns:
        JSON 格式的订单结果
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400

        symbol = data.get('symbol', '').upper()
        side = data.get('side', '').upper()
        order_type = data.get('type', '').upper()
        quantity = data.get('quantity')
        price = data.get('price')

        # 验证必需参数
        if not all([symbol, side, order_type, quantity]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol, side, type, quantity'
            }), 400

        if side not in ['BUY', 'SELL']:
            return jsonify({
                'success': False,
                'error': 'side 必须是 BUY 或 SELL'
            }), 400

        if order_type not in ['MARKET', 'LIMIT']:
            return jsonify({
                'success': False,
                'error': 'type 必须是 MARKET 或 LIMIT'
            }), 400

        if order_type == 'LIMIT' and not price:
            return jsonify({
                'success': False,
                'error': 'LIMIT 订单必须指定 price'
            }), 400

        client = BinanceClient()

        # 下单
        if order_type == 'MARKET':
            order = client.place_market_order(symbol, side, quantity)
        else:
            order = client.place_limit_order(symbol, side, quantity, price)

        return jsonify({
            'success': True,
            'data': {
                'order_id': order.get('orderId'),
                'client_order_id': order.get('clientOrderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'status': order.get('status'),
                'price': float(order.get('price', 0)),
                'quantity': float(order.get('origQty', 0)),
                'executed_qty': float(order.get('executedQty', 0)),
                'time': order.get('transactTime')
            }
        })

    except Exception as e:
        logger.error(f"下单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trading_bp.route('/order/<symbol>', methods=['GET'])
def get_orders(symbol):
    """
    查询订单

    Args:
        symbol: 交易对符号

    Query params:
        status: 订单状态 (可选: NEW, FILLED, CANCELED, ALL)
        limit: 数量限制 (默认: 10)

    Returns:
        JSON 格式的订单列表
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        status = request.args.get('status', 'ALL').upper()
        limit = int(request.args.get('limit', 10))

        client = BinanceClient()

        if status == 'ALL':
            orders = client.get_all_orders(symbol, limit)
        else:
            orders = client.get_open_orders(symbol)

        # 格式化订单数据
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order.get('orderId'),
                'client_order_id': order.get('clientOrderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'status': order.get('status'),
                'price': float(order.get('price', 0)),
                'quantity': float(order.get('origQty', 0)),
                'executed_qty': float(order.get('executedQty', 0)),
                'time': order.get('time'),
                'update_time': order.get('updateTime')
            })

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'orders': formatted_orders,
                'count': len(formatted_orders)
            }
        })

    except Exception as e:
        logger.error(f"查询订单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trading_bp.route('/order/<symbol>/<int:order_id>', methods=['DELETE'])
def cancel_order(symbol, order_id):
    """
    取消订单

    Args:
        symbol: 交易对符号
        order_id: 订单ID

    Returns:
        JSON 格式的取消结果
    """
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        client = BinanceClient()
        result = client.cancel_order(symbol, order_id)

        return jsonify({
            'success': True,
            'data': {
                'order_id': result.get('orderId'),
                'symbol': result.get('symbol'),
                'status': result.get('status'),
                'client_order_id': result.get('clientOrderId')
            }
        })

    except Exception as e:
        logger.error(f"取消订单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@trading_bp.route('/orders/open', methods=['GET'])
def get_open_orders():
    """
    获取所有活跃订单

    Query params:
        symbol: 交易对符号 (可选)

    Returns:
        JSON 格式的活跃订单列表
    """
    try:
        symbol = request.args.get('symbol', '').upper()
        if symbol and not symbol.endswith('USDT'):
            symbol += 'USDT'

        client = BinanceClient()
        orders = client.get_open_orders(symbol if symbol else None)

        # 格式化订单数据
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_id': order.get('orderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'price': float(order.get('price', 0)),
                'quantity': float(order.get('origQty', 0)),
                'executed_qty': float(order.get('executedQty', 0)),
                'status': order.get('status'),
                'time': order.get('time')
            })

        return jsonify({
            'success': True,
            'data': {
                'orders': formatted_orders,
                'count': len(formatted_orders)
            }
        })

    except Exception as e:
        logger.error(f"获取活跃订单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
