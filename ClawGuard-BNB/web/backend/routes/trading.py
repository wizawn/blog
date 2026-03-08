"""
交易路由 - 提供现货和合约交易功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.trading.unified_client import UnifiedTradingClient
from src.api.binance_futures_client import BinanceFuturesClient
from src.risk.risk_control import RiskControl
from src.config.config_manager import ConfigManager
import logging

bp = Blueprint('trading', __name__)
logger = logging.getLogger(__name__)


@bp.route('/spot/order', methods=['POST'])
def place_spot_order():
    """下现货订单"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        side = data.get('side')  # BUY or SELL
        order_type = data.get('type', 'MARKET')  # MARKET or LIMIT
        quantity = data.get('quantity')
        price = data.get('price')

        if not all([symbol, side, quantity]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        # 风控检查
        risk_control = RiskControl()
        if not risk_control.check_order_allowed(symbol, side, float(quantity)):
            return jsonify({
                'success': False,
                'error': '订单被风控拒绝'
            }), 403

        # 下单
        client = UnifiedTradingClient()

        order_params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
        }

        if order_type == 'MARKET':
            if side == 'BUY':
                order_params['quoteOrderQty'] = quantity  # 用 USDT 数量买入
            else:
                order_params['quantity'] = quantity  # 卖出币的数量
        else:  # LIMIT
            order_params['quantity'] = quantity
            order_params['price'] = price
            order_params['timeInForce'] = 'GTC'

        result = client.create_order(**order_params)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"下单失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/spot/orders', methods=['GET'])
def get_spot_orders():
    """获取现货订单"""
    try:
        symbol = request.args.get('symbol')
        status = request.args.get('status', 'all')  # all, open, closed

        client = UnifiedTradingClient()

        if status == 'open':
            orders = client.get_open_orders(symbol)
        else:
            # 获取所有订单（需要 symbol）
            if not symbol:
                return jsonify({
                    'success': False,
                    'error': '查询历史订单需要指定 symbol'
                }), 400
            orders = client.get_all_orders(symbol)

        return jsonify({
            'success': True,
            'data': orders
        })

    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/spot/order/<order_id>', methods=['DELETE'])
def cancel_spot_order(order_id):
    """取消现货订单"""
    try:
        symbol = request.args.get('symbol')

        if not symbol:
            return jsonify({
                'success': False,
                'error': '需要指定 symbol'
            }), 400

        client = UnifiedTradingClient()
        result = client.cancel_order(symbol, order_id)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/futures/order', methods=['POST'])
def place_futures_order():
    """下合约订单"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        side = data.get('side')  # BUY or SELL
        position_side = data.get('positionSide', 'BOTH')  # BOTH, LONG, SHORT
        order_type = data.get('type', 'MARKET')
        quantity = data.get('quantity')
        price = data.get('price')

        if not all([symbol, side, quantity]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        # 检查合约是否启用
        config_manager = ConfigManager()
        if not config_manager.get('futures', {}).get('enabled', False):
            return jsonify({
                'success': False,
                'error': '合约交易未启用'
            }), 403

        # 下单
        client = BinanceFuturesClient()

        order_params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': order_type,
            'quantity': quantity
        }

        if order_type == 'LIMIT':
            order_params['price'] = price
            order_params['timeInForce'] = 'GTC'

        result = client.create_order(**order_params)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"合约下单失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/futures/positions', methods=['GET'])
def get_futures_positions():
    """获取合约持仓"""
    try:
        config_manager = ConfigManager()
        if not config_manager.get('futures', {}).get('enabled', False):
            return jsonify({
                'success': False,
                'error': '合约交易未启用'
            }), 403

        client = BinanceFuturesClient()
        positions = client.get_position_risk()

        # 过滤出有持仓的
        active_positions = [
            pos for pos in positions
            if float(pos.get('positionAmt', 0)) != 0
        ]

        return jsonify({
            'success': True,
            'data': active_positions
        })

    except Exception as e:
        logger.error(f"获取合约持仓失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/futures/leverage', methods=['POST'])
def set_futures_leverage():
    """设置合约杠杆"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        leverage = data.get('leverage')

        if not all([symbol, leverage]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400

        config_manager = ConfigManager()
        if not config_manager.get('futures', {}).get('enabled', False):
            return jsonify({
                'success': False,
                'error': '合约交易未启用'
            }), 403

        client = BinanceFuturesClient()
        result = client.change_leverage(symbol, leverage)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"设置杠杆失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/account', methods=['GET'])
def get_account():
    """获取账户信息"""
    try:
        account_type = request.args.get('type', 'spot')  # spot or futures

        if account_type == 'futures':
            config_manager = ConfigManager()
            if not config_manager.get('futures', {}).get('enabled', False):
                return jsonify({
                    'success': False,
                    'error': '合约交易未启用'
                }), 403

            client = BinanceFuturesClient()
            account = client.get_account_info()
        else:
            client = UnifiedTradingClient()
            account = client.get_account_info()

        return jsonify({
            'success': True,
            'data': account
        })

    except Exception as e:
        logger.error(f"获取账户信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
