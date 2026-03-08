#!/usr/bin/env python3
"""
ClawGuard-BNB Web 管理界面 - 后端服务器
提供可视化的交易管理、策略监控和系统配置界面
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import logging

from src.config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__, static_folder='static')

    # 加载配置
    config_manager = ConfigManager()
    app.config['SECRET_KEY'] = 'clawguard-web-secret-key-change-in-production'

    # 启用 CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册路由
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from routes import dashboard, trading, strategy, analysis, risk, settings

    app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')
    app.register_blueprint(trading.bp, url_prefix='/api/trading')
    app.register_blueprint(strategy.bp, url_prefix='/api/strategy')
    app.register_blueprint(analysis.bp, url_prefix='/api/analysis')
    app.register_blueprint(risk.bp, url_prefix='/api/risk')
    app.register_blueprint(settings.bp, url_prefix='/api/settings')

    # 健康检查端点
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'ClawGuard-BNB Web Interface',
            'version': '1.0.0'
        })

    # 服务前端静态文件
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path)

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    return app


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='ClawGuard-BNB Web 管理界面')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8080, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    print("=" * 70)
    print("🌐 ClawGuard-BNB Web 管理界面")
    print("=" * 70)
    print(f"📍 访问地址: http://{args.host}:{args.port}")
    print(f"🏥 健康检查: http://{args.host}:{args.port}/health")
    print(f"🔧 调试模式: {'开启' if args.debug else '关闭'}")
    print("💡 提示: 数据通过轮询更新，无需 WebSocket")
    print("=" * 70)
    print()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
