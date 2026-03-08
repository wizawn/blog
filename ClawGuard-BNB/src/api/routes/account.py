#!/usr/bin/env python3
"""
账户管理 API 路由
提供账户信息、余额查询等接口
"""

from flask import Blueprint, jsonify, request
from ..binance_client import BinanceClient
import logging

logger = logging.getLogger(__name__)

account_bp = Blueprint('account', __name__, url_prefix='/api/v1/account')


@account_bp.route('/info', methods=['GET'])
def get_account_info():
    """
    获取账户信息

    Returns:
        JSON 格式的账户数据
    """
    try:
        client = BinanceClient()
        account = client.get_account_info()

        # 格式化余额数据
        balances = []
        for balance in account.get('balances', []):
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance.get('asset'),
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })

        return jsonify({
            'success': True,
            'data': {
                'account_type': account.get('accountType'),
                'can_trade': account.get('canTrade'),
                'can_withdraw': account.get('canWithdraw'),
                'can_deposit': account.get('canDeposit'),
                'update_time': account.get('updateTime'),
                'balances': balances,
                'permissions': account.get('permissions', [])
            }
        })

    except Exception as e:
        logger.error(f"获取账户信息失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@account_bp.route('/balance', methods=['GET'])
def get_balance():
    """
    获取账户余额

    Query params:
        asset: 资产符号 (可选，如: USDT)

    Returns:
        JSON 格式的余额数据
    """
    try:
        asset = request.args.get('asset', '').upper()

        client = BinanceClient()
        account = client.get_account_info()

        balances = []
        for balance in account.get('balances', []):
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            total = free + locked

            if total > 0:
                balance_data = {
                    'asset': balance.get('asset'),
                    'free': free,
                    'locked': locked,
                    'total': total
                }

                # 如果指定了资产，只返回该资产
                if asset:
                    if balance.get('asset') == asset:
                        return jsonify({
                            'success': True,
                            'data': balance_data
                        })
                else:
                    balances.append(balance_data)

        if asset:
            # 指定资产但未找到
            return jsonify({
                'success': True,
                'data': {
                    'asset': asset,
                    'free': 0,
                    'locked': 0,
                    'total': 0
                }
            })

        return jsonify({
            'success': True,
            'data': balances
        })

    except Exception as e:
        logger.error(f"获取余额失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@account_bp.route('/status', methods=['GET'])
def get_account_status():
    """
    获取账户状态

    Returns:
        JSON 格式的账户状态
    """
    try:
        client = BinanceClient()
        account = client.get_account_info()

        return jsonify({
            'success': True,
            'data': {
                'can_trade': account.get('canTrade', False),
                'can_withdraw': account.get('canWithdraw', False),
                'can_deposit': account.get('canDeposit', False),
                'account_type': account.get('accountType', 'UNKNOWN'),
                'permissions': account.get('permissions', []),
                'update_time': account.get('updateTime')
            }
        })

    except Exception as e:
        logger.error(f"获取账户状态失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
