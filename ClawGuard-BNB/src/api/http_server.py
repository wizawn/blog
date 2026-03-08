#!/usr/bin/env python3
"""
ClawGuard HTTP API 服务器
提供 RESTful API 接口供 OpenClaw 和其他客户端调用
"""

import time
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path

from .routes import market_bp, account_bp, trading_bp, analysis_bp
from ..config.config_manager import ConfigManager
from ..utils.logger import get_logger

logger = get_logger("http_server")


def create_app(config=None):
    """
    创建 Flask 应用

    Args:
        config: 配置对象（可选）

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)

    # 加载配置
    if config is None:
        config = ConfigManager()

    app.config['CONFIG_MANAGER'] = config

    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册蓝图
    app.register_blueprint(market_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(analysis_bp)

    # 请求前处理
    @app.before_request
    def before_request():
        """记录请求开始时间"""
        request.environ['REQUEST_TIME'] = time.time()

    # 请求后处理
    @app.after_request
    def after_request(response):
        """记录请求日志"""
        if 'REQUEST_TIME' in request.environ:
            elapsed = time.time() - request.environ['REQUEST_TIME']
            logger.info(f"{request.method} {request.path} - {response.status_code} - {elapsed:.3f}s")

        # 添加响应头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        return response

    # 根路由
    @app.route('/')
    def index():
        """API 根路径"""
        return jsonify({
            'name': 'ClawGuard API',
            'version': 'v1.0.0',
            'description': 'RESTful API for Binance trading',
            'endpoints': {
                'market': '/api/v1/market',
                'account': '/api/v1/account',
                'trading': '/api/v1/trading',
                'analysis': '/api/v1/analysis'
            },
            'documentation': 'https://github.com/wizawn/lobsterguard'
        })

    # 健康检查
    @app.route('/health')
    def health():
        """健康检查端点"""
        return jsonify({
            'status': 'healthy',
            'timestamp': int(time.time() * 1000)
        })

    # Web 界面管理端点
    @app.route('/api/v1/web/start', methods=['POST'])
    def start_web_interface():
        """启动 Web 管理界面"""
        try:
            import subprocess
            import threading
            from pathlib import Path

            web_dir = Path(__file__).parent.parent.parent / 'web'

            def run_web():
                subprocess.run([
                    'python3',
                    str(web_dir / 'backend' / 'app.py'),
                    '--host', '0.0.0.0',
                    '--port', '8080'
                ])

            # 在后台线程启动 Web 服务器
            thread = threading.Thread(target=run_web, daemon=True)
            thread.start()

            return jsonify({
                'success': True,
                'message': 'Web 界面已启动',
                'url': 'http://localhost:8080'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/v1/web/status', methods=['GET'])
    def web_interface_status():
        """检查 Web 界面状态"""
        try:
            import requests
            response = requests.get('http://localhost:8080/health', timeout=2)
            if response.status_code == 200:
                return jsonify({
                    'success': True,
                    'status': 'running',
                    'url': 'http://localhost:8080'
                })
        except:
            pass

        return jsonify({
            'success': True,
            'status': 'stopped'
        })

    # API 信息
    @app.route('/api/v1/info')
    def api_info():
        """API 信息"""
        return jsonify({
            'success': True,
            'data': {
                'version': 'v1.0.0',
                'endpoints': {
                    'market': {
                        'price': 'GET /api/v1/market/price/<symbol>',
                        'prices': 'GET /api/v1/market/prices?symbols=BTC,ETH',
                        'klines': 'GET /api/v1/market/klines/<symbol>?interval=1h&limit=100',
                        'depth': 'GET /api/v1/market/depth/<symbol>?limit=20',
                        'ticker': 'GET /api/v1/market/ticker/<symbol>'
                    },
                    'account': {
                        'info': 'GET /api/v1/account/info',
                        'balance': 'GET /api/v1/account/balance?asset=USDT',
                        'status': 'GET /api/v1/account/status'
                    },
                    'trading': {
                        'place_order': 'POST /api/v1/trading/order',
                        'get_orders': 'GET /api/v1/trading/order/<symbol>',
                        'cancel_order': 'DELETE /api/v1/trading/order/<symbol>/<order_id>',
                        'open_orders': 'GET /api/v1/trading/orders/open'
                    },
                    'analysis': {
                        'indicators': 'GET /api/v1/analysis/indicators/<symbol>?interval=1h',
                        'trend': 'GET /api/v1/analysis/trend/<symbol>',
                        'summary': 'GET /api/v1/analysis/summary/<symbol>'
                    }
                }
            }
        })

    # 404 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404 错误处理"""
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'path': request.path
        }), 404

    # 500 错误处理
    @app.errorhandler(500)
    def internal_error(error):
        """500 错误处理"""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    # 通用异常处理
    @app.errorhandler(Exception)
    def handle_exception(error):
        """通用异常处理"""
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(error)
        }), 500

    return app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    运行 HTTP 服务器

    Args:
        host: 监听地址
        port: 监听端口
        debug: 是否启用调试模式
    """
    app = create_app()

    logger.info("=" * 60)
    logger.info("ClawGuard HTTP API 服务器")
    logger.info("=" * 60)
    logger.info(f"监听地址: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/api/v1/info")
    logger.info(f"健康检查: http://{host}:{port}/health")
    logger.info("=" * 60)

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}", exc_info=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='ClawGuard HTTP API 服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    run_server(host=args.host, port=args.port, debug=args.debug)
