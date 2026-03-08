#!/usr/bin/env python3
"""
ClawGuard-BNB Web 管理界面启动脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")

    # 检查 Python 依赖
    required_packages = ['flask', 'flask_cors', 'flask_socketio']
    missing = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"缺少 Python 依赖: {', '.join(missing)}")
        print("安装依赖: pip install flask flask-cors flask-socketio")
        return False

    return True

def start_backend(host='0.0.0.0', port=8080, debug=False):
    """启动后端服务器"""
    print("=" * 70)
    print("🚀 启动后端服务器...")
    print("=" * 70)

    backend_dir = Path(__file__).parent / 'backend'
    os.chdir(backend_dir)

    cmd = [
        sys.executable,
        'app.py',
        '--host', host,
        '--port', str(port)
    ]

    if debug:
        cmd.append('--debug')

    subprocess.run(cmd)

def build_frontend():
    """构建前端"""
    print("=" * 70)
    print("📦 构建前端...")
    print("=" * 70)

    frontend_dir = Path(__file__).parent / 'frontend'

    if not (frontend_dir / 'node_modules').exists():
        print("安装前端依赖...")
        subprocess.run(['npm', 'install'], cwd=frontend_dir)

    print("构建前端...")
    subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir)

    print("✅ 前端构建完成")

def dev_frontend():
    """开发模式运行前端"""
    print("=" * 70)
    print("🔧 启动前端开发服务器...")
    print("=" * 70)

    frontend_dir = Path(__file__).parent / 'frontend'

    if not (frontend_dir / 'node_modules').exists():
        print("安装前端依赖...")
        subprocess.run(['npm', 'install'], cwd=frontend_dir)

    subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir)

def main():
    parser = argparse.ArgumentParser(description='ClawGuard-BNB Web 管理界面')
    parser.add_argument('--host', default='0.0.0.0', help='后端监听地址')
    parser.add_argument('--port', type=int, default=8080, help='后端监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--build', action='store_true', help='构建前端')
    parser.add_argument('--dev', action='store_true', help='开发模式（前端热重载）')

    args = parser.parse_args()

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 构建前端
    if args.build:
        build_frontend()
        return

    # 开发模式
    if args.dev:
        print("开发模式：前端和后端分别运行")
        print("前端: http://localhost:3000")
        print(f"后端: http://{args.host}:{args.port}")
        print()

        # 在新终端启动后端
        import threading
        backend_thread = threading.Thread(
            target=start_backend,
            args=(args.host, args.port, args.debug)
        )
        backend_thread.daemon = True
        backend_thread.start()

        # 启动前端开发服务器
        dev_frontend()
    else:
        # 生产模式：先构建前端，然后启动后端
        print("生产模式：构建前端并启动后端")
        build_frontend()
        start_backend(args.host, args.port, args.debug)

if __name__ == '__main__':
    main()
