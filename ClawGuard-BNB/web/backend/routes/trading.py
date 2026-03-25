
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
交易路由 - 提供现货和合约交易功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.trading.unified_client import UnifiedTradingClient
from src.api.binance_futures_client import BinanceFuturesClient
from src.risk.risk_control import RiskControlEngine
from src.config.config_manager import ConfigManager
from src.database.repository import OrderRepository, TradeRepository
import logging

bp = Blueprint('trading', __name__)
logger = logging.getLogger(__name__)

# Initialize repositories
order_repo = OrderRepository()
trade_repo = TradeRepository()


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

        # 验证参数类型和范围
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'error': 'quantity 必须大于 0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'quantity 必须是有效的数字'
            }), 400

        # 验证 side 参数
        if side not in ['BUY', 'SELL']:
            return jsonify({
                'success': False,
                'error': 'side 必须是 BUY 或 SELL'
            }), 400

        # 如果是限价单，验证 price
        if order_type == 'LIMIT':
            if not price:
                return jsonify({
                    'success': False,
                    'error': '限价单必须提供 price'
                }), 400
            try:
                price = float(price)
                if price <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'price 必须大于 0'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'price 必须是有效的数字'
                }), 400

        # 风控检查
        risk_control = RiskControlEngine()
        client = UnifiedTradingClient()

        # 获取账户余额和当前价格
        try:
            account = client.get_account()
            account_balance = float(account.get('totalWalletBalance', 0))

            # 获取当前价格
            ticker = client.get_ticker(symbol)
            current_price = float(ticker.get('price', 0))
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return jsonify({
                'success': False,
                'error': '获取账户信息失败'
            }), 500

        # 计算交易金额
        if order_type == 'MARKET' and side == 'BUY':
            amount = quantity  # quantity 是 USDT 金额
        else:
            amount = quantity * (price if order_type == 'LIMIT' else current_price)

        # 执行风控检查
        allowed, reason = risk_control.pre_trade_check(
            symbol=symbol,
            side=side,
            amount=amount,
            account_balance=account_balance,
            current_price=current_price,
            has_real_trade_permission=True
        )

        if not allowed:
            return jsonify({
                'success': False,
                'error': f'订单被风控拒绝: {reason}'
            }), 403

        # 下单

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

        # Save order to database
        try:
            order_repo.create(
                strategy_id=None,  # Manual order, no strategy
                order_id=str(result.get('orderId', '')),
                symbol=symbol,
                side=side,
                type=order_type,
                price=float(result.get('price', price or current_price)),
                quantity=float(result.get('executedQty', quantity)),
                status=result.get('status', 'NEW')
            )
            logger.info(f"Spot order saved to database: {result.get('orderId')}")
        except Exception as e:
            logger.error(f"Failed to save order to database: {e}")

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

        # 验证参数类型和范围
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'error': 'quantity 必须大于 0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'quantity 必须是有效的数字'
            }), 400

        # 验证 side 参数
        if side not in ['BUY', 'SELL']:
            return jsonify({
                'success': False,
                'error': 'side 必须是 BUY 或 SELL'
            }), 400

        # 验证 position_side 参数
        if position_side not in ['BOTH', 'LONG', 'SHORT']:
            return jsonify({
                'success': False,
                'error': 'positionSide 必须是 BOTH, LONG 或 SHORT'
            }), 400

        # 如果是限价单，验证 price
        if order_type == 'LIMIT':
            if not price:
                return jsonify({
                    'success': False,
                    'error': '限价单必须提供 price'
                }), 400
            try:
                price = float(price)
                if price <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'price 必须大于 0'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'price 必须是有效的数字'
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

        # Save order to database
        try:
            order_repo.create(
                strategy_id=None,  # Manual order, no strategy
                order_id=str(result.get('orderId', '')),
                symbol=symbol,
                side=side,
                type=order_type,
                price=float(result.get('avgPrice', price or 0)),
                quantity=float(result.get('executedQty', quantity)),
                status=result.get('status', 'NEW')
            )
            logger.info(f"Futures order saved to database: {result.get('orderId')}")
        except Exception as e:
            logger.error(f"Failed to save futures order to database: {e}")

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


@bp.route('/futures/close', methods=['POST'])
def close_futures_position():
    """平仓合约持仓"""
    try:
        data = request.get_json()

        symbol = data.get('symbol')
        position_side = data.get('positionSide', 'BOTH')

        if not symbol:
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

        # 获取当前持仓
        positions = client.get_position_risk()
        target_position = None

        for pos in positions:
            if pos['symbol'] == symbol:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    target_position = pos
                    break

        if not target_position:
            return jsonify({
                'success': False,
                'error': '没有找到持仓'
            }), 404

        # 计算平仓方向和数量
        position_amt = float(target_position['positionAmt'])
        close_side = 'SELL' if position_amt > 0 else 'BUY'
        close_quantity = abs(position_amt)

        # 下市价平仓单
        result = client.create_order(
            symbol=symbol,
            side=close_side,
            positionSide=position_side,
            type='MARKET',
            quantity=close_quantity
        )

        return jsonify({
            'success': True,
            'data': result,
            'message': f'平仓成功: {close_side} {close_quantity}'
        })

    except Exception as e:
        logger.error(f"平仓失败: {e}")
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

# ==================== 新增的统一API端点 ====================

@bp.route('/balance', methods=['GET'])
def get_balance():
    """获取账户余额（现货+合约）"""
    try:
        from src.api.binance_client import BinanceClient
        from src.api.binance_futures_client import BinanceFuturesClient

        spot_client = BinanceClient()
        futures_client = BinanceFuturesClient()

        # 获取现货余额
        spot_balance = []
        try:
            spot_account = spot_client.get_account()
            for balance in spot_account.get('balances', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    spot_balance.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })
        except Exception as e:
            logger.warning(f"获取现货余额失败: {e}")

        # 获取合约余额
        futures_balance = []
        try:
            futures_account = futures_client.get_balance()
            for balance in futures_account:
                available = float(balance.get('availableBalance', 0))
                if available > 0:
                    futures_balance.append({
                        'asset': balance['asset'],
                        'available': available,
                        'balance': float(balance.get('balance', 0)),
                        'crossUnPnl': float(balance.get('crossUnPnl', 0))
                    })
        except Exception as e:
            logger.warning(f"获取合约余额失败: {e}")

        return jsonify({
            'success': True,
            'data': {
                'spot': spot_balance,
                'futures': futures_balance
            }
        })

    except Exception as e:
        logger.error(f"获取余额失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/positions', methods=['GET'])
def get_positions():
    """获取当前持仓（现货+合约）"""
    try:
        from src.api.binance_futures_client import BinanceFuturesClient

        futures_client = BinanceFuturesClient()

        # 获取合约持仓
        positions = []
        try:
            position_risk = futures_client.get_position_risk()
            for pos in position_risk:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:  # 只返回有持仓的
                    positions.append({
                        'symbol': pos['symbol'],
                        'positionAmt': position_amt,
                        'entryPrice': float(pos.get('entryPrice', 0)),
                        'markPrice': float(pos.get('markPrice', 0)),
                        'unRealizedProfit': float(pos.get('unRealizedProfit', 0)),
                        'leverage': int(pos.get('leverage', 1)),
                        'positionSide': pos.get('positionSide', 'BOTH'),
                        'liquidationPrice': float(pos.get('liquidationPrice', 0))
                    })
        except Exception as e:
            logger.warning(f"获取合约持仓失败: {e}")

        return jsonify({
            'success': True,
            'data': {
                'positions': positions,
                'count': len(positions)
            }
        })

    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/place-order', methods=['POST'])
def place_unified_order():
    """统一下单接口（现货/合约）"""
    try:
        data = request.get_json()

        market_type = data.get('market_type', 'spot')
        symbol = data.get('symbol')
        side = data.get('side')
        order_type = data.get('type', 'MARKET')
        quantity = data.get('quantity')
        price = data.get('price')

        # 参数验证
        if not all([symbol, side, quantity]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol, side, quantity'
            }), 400

        if side not in ['BUY', 'SELL']:
            return jsonify({
                'success': False,
                'error': 'side 必须是 BUY 或 SELL'
            }), 400

        quantity = float(quantity)
        if quantity <= 0:
            return jsonify({
                'success': False,
                'error': 'quantity 必须大于 0'
            }), 400

        if order_type == 'LIMIT' and not price:
            return jsonify({
                'success': False,
                'error': '限价单必须提供 price'
            }), 400

        # 风控检查
        risk_control = RiskControlEngine()
        if not risk_control.check_order_allowed(symbol, side, quantity):
            return jsonify({
                'success': False,
                'error': '订单未通过风控检查'
            }), 403

        # 下单
        if market_type == 'spot':
            from src.api.binance_client import BinanceClient
            client = BinanceClient()

            if order_type == 'MARKET':
                result = client.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
            else:
                result = client.create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    quantity=quantity,
                    price=float(price),
                    timeInForce='GTC'
                )
        else:
            from src.api.binance_futures_client import BinanceFuturesClient
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=float(price) if price else None
            )

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


@bp.route('/cancel-order', methods=['DELETE'])
def cancel_unified_order():
    """取消订单"""
    try:
        data = request.get_json()

        market_type = data.get('market_type', 'spot')
        symbol = data.get('symbol')
        order_id = data.get('order_id')

        if not all([symbol, order_id]):
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol, order_id'
            }), 400

        if market_type == 'spot':
            from src.api.binance_client import BinanceClient
            client = BinanceClient()
            result = client.cancel_order(symbol, int(order_id))
        else:
            from src.api.binance_futures_client import BinanceFuturesClient
            client = BinanceFuturesClient()
            result = client.cancel_order(symbol, int(order_id))

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


@bp.route('/order-history', methods=['GET'])
def get_order_history():
    """获取订单历史"""
    try:
        market_type = request.args.get('market_type', 'spot')
        symbol = request.args.get('symbol')
        limit = request.args.get('limit', 100, type=int)

        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: symbol'
            }), 400

        if market_type == 'spot':
            from src.api.binance_client import BinanceClient
            client = BinanceClient()
            orders = client.get_all_orders(symbol, limit=limit)
        else:
            from src.api.binance_futures_client import BinanceFuturesClient
            client = BinanceFuturesClient()
            orders = client.get_all_orders(symbol, limit=limit)

        return jsonify({
            'success': True,
            'data': {
                'orders': orders,
                'count': len(orders)
            }
        })

    except Exception as e:
        logger.error(f"获取订单历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
