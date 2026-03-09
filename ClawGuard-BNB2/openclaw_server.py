#!/usr/bin/env python3
"""
OpenClaw 专用 HTTP API 服务器
优化的启动脚本，支持自动配置和健康检查
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.api.http_server import create_app
from src.config.config_manager import ConfigManager


def check_configuration():
    """检查配置是否完整"""
    config_dir = Path.home() / ".clawguard"
    config_file = config_dir / "config.yaml"

    if not config_file.exists():
        print("⚠️  配置文件不存在，正在自动配置...")
        from openclaw_configure import OpenClawConfigurator
        configurator = OpenClawConfigurator()
        result = configurator.auto_configure()

        if not result['success']:
            print("❌ 自动配置失败，请手动运行: python3 openclaw_configure.py")
            return False

    return True


def start_server(host='0.0.0.0', port=5000, debug=False):
    """启动 HTTP API 服务器"""

    print("=" * 70)
    print("🚀 ClawGuard-BNB OpenClaw API Server")
    print("=" * 70)

    # 检查配置
    if not check_configuration():
        sys.exit(1)

    # 加载配置
    config_manager = ConfigManager()
    api_config = config_manager.get('api', {})

    host = api_config.get('host', host)
    port = api_config.get('port', port)
    debug = api_config.get('debug', debug)

    print(f"📍 服务器地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🏥 健康检查: http://{host}:{port}/health")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print()
    print("可用的集成方式:")
    print("  1. HTTP API: curl http://localhost:5000/api/v1/price/BTCUSDT")
    print("  2. CLI + JSON: python3 clawguard.py price BTC --json")
    print("  3. Skills: from skills import execute_skill")
    print("  4. NLP: from src.nlp import NLPCommandParser")
    print("=" * 70)
    print()

    # 创建并启动应用
    app = create_app()

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='OpenClaw HTTP API 服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认启动 (0.0.0.0:5000)
  python3 openclaw_server.py

  # 指定端口
  python3 openclaw_server.py --port 8080

  # 调试模式
  python3 openclaw_server.py --debug

  # 仅本地访问
  python3 openclaw_server.py --host 127.0.0.1
        """
    )

    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--configure', action='store_true', help='运行配置向导后启动')

    args = parser.parse_args()

    # 如果需要配置
    if args.configure:
        print("🔧 运行配置向导...")
        from openclaw_configure import OpenClawConfigurator
        configurator = OpenClawConfigurator()
        result = configurator.auto_configure()

        if not result['success']:
            print("❌ 配置失败")
            sys.exit(1)

        print("\n" + "=" * 70)
        input("按 Enter 键启动服务器...")

    # 启动服务器
    start_server(args.host, args.port, args.debug)


if __name__ == '__main__':
    main()
