"""
仪表盘路由 - 提供账户概览、实时价格、策略状态等信息
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.api.binance_client import BinanceClient
from src.trading.trading_mode_manager import TradingModeManager
from src.trading.unified_client import UnifiedTradingClient
from src.config.config_manager import ConfigManager
import logging

bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)


@bp.route('/overview', methods=['GET'])
def get_overview():
    """获取仪表盘概览数据"""
    try:
        # 获取交易模式
        mode_manager = TradingModeManager()
        current_mode = mode_manager.get_current_mode()

        # 获取客户端
        client = UnifiedTradingClient()

        # 获取账户信息
        account_info = client.get_account_info()

        # 计算总资产
        total_balance = 0
        balances = []

        if 'balances' in account_info:
            for balance in account_info['balances']:
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                total = free + locked

                if total > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': total
                    })

                    # 简化计算：USDT 直接计入，其他币种需要转换
                    if balance['asset'] == 'USDT':
                        total_balance += total

        # 获取持仓信息
        positions = []
        for balance in balances:
            if balance['asset'] != 'USDT' and balance['total'] > 0:
                try:
                    symbol = balance['asset'] + 'USDT'
                    ticker = client.get_ticker_price(symbol)
                    price = float(ticker.get('price', 0))
                    value = balance['total'] * price

                    positions.append({
                        'symbol': symbol,
                        'asset': balance['asset'],
                        'amount': balance['total'],
                        'price': price,
                        'value': value
                    })

                    total_balance += value
                except Exception as e:
                    logger.warning(f"获取 {symbol} 价格失败: {e}")
                    continue

        # 今日盈亏计算（从交易历史）
        today_pnl = 0
        today_pnl_percent = 0

        try:
            from datetime import datetime, timedelta
            from src.strategies.strategy_manager import get_strategy_manager

            # 获取今日开始时间
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # 从策略管理器获取今日交易
            strategy_manager = get_strategy_manager()
            all_strategies = strategy_manager.list_strategies()

            for strategy in all_strategies:
                strategy_detail = strategy_manager.get_strategy(strategy['id'])
                if strategy_detail and 'orders' in strategy_detail:
                    for order in strategy_detail['orders']:
                        # 检查是否是今日订单
                        order_time_str = order.get('timestamp') or order.get('time', '')
                        if order_time_str:
                            try:
                                order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                                if order_time >= today_start:
                                    # 累计今日盈亏
                                    pnl = order.get('pnl_percent', 0)
                                    if pnl:
                                        today_pnl += pnl
                            except:
                                continue

            # 计算今日盈亏百分比
            if total_balance > 0:
                today_pnl_percent = (today_pnl / total_balance) * 100

        except Exception as e:
            logger.error(f"计算今日盈亏失败: {e}")
            today_pnl = 0
            today_pnl_percent = 0

        return jsonify({
            'success': True,
            'data': {
                'trading_mode': current_mode.value,
                'total_balance': round(total_balance, 2),
                'today_pnl': round(today_pnl, 2),
                'today_pnl_percent': round(today_pnl_percent, 2),
                'balances': balances,
                'positions': positions,
                'position_count': len(positions),
                'timestamp': int(client.get_server_time() / 1000) if hasattr(client, 'get_server_time') else 0
            }
        })

    except Exception as e:
        logger.error(f"获取仪表盘概览失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/prices', methods=['GET'])
def get_prices():
    """获取实时价格列表"""
    try:
        # 获取要监控的交易对
        symbols = request.args.get('symbols', 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT').split(',')

        client = UnifiedTradingClient()
        prices = []

        for symbol in symbols:
            try:
                ticker = client.get_ticker_price(symbol)
                prices.append({
                    'symbol': symbol,
                    'price': float(ticker.get('price', 0)),
                    'change_percent': float(ticker.get('priceChangePercent', 0)),
                    'high': float(ticker.get('highPrice', 0)),
                    'low': float(ticker.get('lowPrice', 0)),
                    'volume': float(ticker.get('volume', 0))
                })
            except Exception as e:
                logger.warning(f"获取 {symbol} 价格失败: {e}")

        return jsonify({
            'success': True,
            'data': prices
        })

    except Exception as e:
        logger.error(f"获取价格列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/strategies', methods=['GET'])
def get_strategies_status():
    """获取策略运行状态"""
    try:
        # 从策略管理器获取运行中的策略
        from src.strategies.strategy_manager import get_strategy_manager
        strategy_manager = get_strategy_manager()

        all_strategies = strategy_manager.list_strategies()

        # 格式化策略数据
        strategies = []
        for s in all_strategies:
            strategies.append({
                'id': s['id'],
                'name': f"{s['symbol']} {s['type']} 策略",
                'symbol': s['symbol'],
                'status': s['status'],
                'profit': s['stats']['total_profit'],
                'profit_percent': s['stats']['total_profit'] / s['config'].get('amount', 1) * 100 if s['config'].get('amount') else 0,
                'orders': s['stats']['total_trades'],
                'start_time': s['started_at'] or s['created_at']
            })

        return jsonify({
            'success': True,
            'data': {
                'total': len(strategies),
                'running': sum(1 for s in strategies if s['status'] == 'running'),
                'stopped': sum(1 for s in strategies if s['status'] == 'stopped'),
                'strategies': strategies
            }
        })

    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        return jsonify({
            'success': True,
            'data': {
                'total': 0,
                'running': 0,
                'stopped': 0,
                'strategies': []
            }
        })


@bp.route('/recent-orders', methods=['GET'])
def get_recent_orders():
    """获取最近订单"""
    try:
        limit = int(request.args.get('limit', 10))

        client = UnifiedTradingClient()

        # 从策略管理器获取所有策略的订单
        from src.strategies.strategy_manager import get_strategy_manager
        strategy_manager = get_strategy_manager()

        all_orders = []

        # 收集所有策略的订单
        for strategy in strategy_manager.list_strategies():
            strategy_detail = strategy_manager.get_strategy(strategy['id'])
            if strategy_detail and 'orders' in strategy_detail:
                for order in strategy_detail['orders']:
                    all_orders.append({
                        'id': order.get('order_id', 'N/A'),
                        'strategy_id': strategy['id'],
                        'strategy_name': f"{strategy['symbol']} {strategy['type']}",
                        'symbol': strategy['symbol'],
                        'side': order.get('side', order.get('type', 'BUY')),
                        'price': order.get('price', 0),
                        'quantity': order.get('quantity', 0),
                        'status': 'FILLED',
                        'time': order.get('timestamp', order.get('time', '')),
                        'pnl': order.get('pnl_percent', 0)
                    })

        # 按时间倒序排序
        all_orders.sort(key=lambda x: x['time'], reverse=True)

        # 限制返回数量
        orders = all_orders[:limit]

        return jsonify({
            'success': True,
            'data': orders
        })

    except Exception as e:
        logger.error(f"获取最近订单失败: {e}")
        return jsonify({
            'success': True,
            'data': []  # 失败时返回空列表，不影响前端显示
        })


@bp.route('/system-status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        config_manager = ConfigManager()
        mode_manager = TradingModeManager()

        # 检查 API 连接
        api_connected = False
        try:
            client = UnifiedTradingClient()
            client.get_server_time()
            api_connected = True
        except:
            pass

        # 检查代理状态
        proxy_config = config_manager.get_proxy_config()
        proxy_enabled = proxy_config.get('enabled', False)

        return jsonify({
            'success': True,
            'data': {
                'trading_mode': mode_manager.get_current_mode().value,
                'api_connected': api_connected,
                'proxy_enabled': proxy_enabled,
                'proxy_status': 'connected' if proxy_enabled and api_connected else 'disconnected',
                'system_health': 'healthy' if api_connected else 'degraded'
            }
        })

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
