"""
设置路由 - 提供系统配置功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Blueprint, jsonify, request
from src.config.config_manager import ConfigManager
from src.trading.trading_mode_manager import TradingModeManager, TradingMode
from src.nlp.command_parser import NLPCommandParser
import logging

bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)


@bp.route('/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        config_manager = ConfigManager()
        config = config_manager.config

        # 隐藏敏感信息
        if 'api_key' in config:
            config['api_key'] = '***'
        if 'api_secret' in config:
            config['api_secret'] = '***'

        return jsonify({
            'success': True,
            'data': config
        })

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        data = request.get_json()
        config_manager = ConfigManager()

        # 更新配置项
        for key, value in data.items():
            if key not in ['api_key', 'api_secret']:  # 不允许通过此接口更新密钥
                config_manager.set(key, value)

        config_manager.save()

        return jsonify({
            'success': True,
            'message': '配置已更新'
        })

    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/trading-mode', methods=['GET'])
def get_trading_mode():
    """获取交易模式"""
    try:
        mode_manager = TradingModeManager()
        current_mode = mode_manager.get_current_mode()

        return jsonify({
            'success': True,
            'data': {
                'current_mode': current_mode.value,
                'available_modes': [mode.value for mode in TradingMode]
            }
        })

    except Exception as e:
        logger.error(f"获取交易模式失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/trading-mode', methods=['POST'])
def set_trading_mode():
    """设置交易模式"""
    try:
        data = request.get_json()
        mode = data.get('mode')

        if not mode:
            return jsonify({
                'success': False,
                'error': '缺少 mode 参数'
            }), 400

        mode_manager = TradingModeManager()
        mode_manager.set_mode(TradingMode(mode))

        return jsonify({
            'success': True,
            'data': {
                'mode': mode,
                'message': f'交易模式已切换到 {mode}'
            }
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'无效的交易模式: {mode}'
        }), 400
    except Exception as e:
        logger.error(f"设置交易模式失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/proxy', methods=['GET'])
def get_proxy_config():
    """获取代理配置"""
    try:
        config_manager = ConfigManager()
        proxy_config = config_manager.get_proxy_config()

        # 隐藏密码
        if 'password' in proxy_config:
            proxy_config['password'] = '***'

        return jsonify({
            'success': True,
            'data': proxy_config
        })

    except Exception as e:
        logger.error(f"获取代理配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/proxy', methods=['POST'])
def update_proxy_config():
    """更新代理配置"""
    try:
        data = request.get_json()
        config_manager = ConfigManager()

        # 更新代理配置
        if 'enabled' in data:
            config_manager.set('proxy.enabled', data['enabled'])
        if 'type' in data:
            config_manager.set('proxy.type', data['type'])
        if 'host' in data:
            config_manager.set('proxy.host', data['host'])
        if 'port' in data:
            config_manager.set('proxy.port', data['port'])
        if 'username' in data:
            config_manager.set('proxy.username', data['username'])
        if 'password' in data and data['password'] != '***':
            config_manager.set('proxy.password', data['password'])

        config_manager.save()

        return jsonify({
            'success': True,
            'message': '代理配置已更新'
        })

    except Exception as e:
        logger.error(f"更新代理配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/proxy/test', methods=['POST'])
def test_proxy():
    """测试代理连接"""
    try:
        import requests
        from src.config.config_manager import ConfigManager

        config_manager = ConfigManager()
        proxy_config = config_manager.get_proxy_config()

        if not proxy_config.get('enabled'):
            return jsonify({
                'success': False,
                'error': '代理未启用'
            }), 400

        proxy_url = f"{proxy_config['type']}://{proxy_config['host']}:{proxy_config['port']}"
        proxies = {'http': proxy_url, 'https': proxy_url}

        response = requests.get('https://api.binance.com/api/v3/ping', proxies=proxies, timeout=5)

        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'connected',
                    'message': '代理连接成功'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'代理连接失败，状态码: {response.status_code}'
            }), 500

    except Exception as e:
        logger.error(f"测试代理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/nlp/parse', methods=['POST'])
def parse_nlp():
    """解析自然语言指令"""
    try:
        data = request.get_json()
        text = data.get('text')

        if not text:
            return jsonify({
                'success': False,
                'error': '缺少 text 参数'
            }), 400

        parser = NLPCommandParser()
        result = parser.parse(text)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"NLP 解析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    try:
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', 'all')

        # TODO: 从日志文件读取日志

        logs = [
            {
                'time': '2024-03-08 15:00:00',
                'level': 'INFO',
                'message': '系统启动成功'
            }
        ]

        return jsonify({
            'success': True,
            'data': logs
        })

    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
