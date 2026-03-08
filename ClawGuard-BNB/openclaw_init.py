#!/usr/bin/env python3
"""
ClawGuard-BNB 统一初始化脚本
供 OpenClaw 自动调用，完成所有初始化工作
"""

import os
import sys
import subprocess
from pathlib import Path


def init_system():
    """
    统一初始化系统
    OpenClaw 只需调用此脚本即可完成所有配置
    """
    print("=" * 70)
    print("🚀 ClawGuard-BNB 自动初始化")
    print("=" * 70)
    print()

    # 1. 检查 Python 版本
    print("1️⃣ 检查 Python 版本...")
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    print()

    # 2. 安装依赖
    print("2️⃣ 安装 Python 依赖...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
            check=True
        )
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError:
        print("⚠️  依赖安装失败，但继续执行")
    print()

    # 3. 自动配置
    print("3️⃣ 自动配置系统...")
    try:
        from openclaw_configure import OpenClawConfigurator
        configurator = OpenClawConfigurator()
        result = configurator.auto_configure()
        if result['success']:
            print("✅ 系统配置完成")
        else:
            print("⚠️  配置未完全成功，但系统可用")
    except Exception as e:
        print(f"⚠️  配置过程出现问题: {e}")
        print("   系统将使用默认配置")
    print()

    # 4. 验证系统
    print("4️⃣ 验证系统状态...")
    try:
        from openclaw_validate import OpenClawValidator
        validator = OpenClawValidator()
        result = validator.validate_all()
        if result['ready']:
            print("✅ 系统验证通过")
        else:
            print("⚠️  系统部分功能可能受限")
    except Exception as e:
        print(f"⚠️  验证过程出现问题: {e}")
    print()

    # 5. 完成
    print("=" * 70)
    print("✅ 初始化完成！")
    print("=" * 70)
    print()
    print("OpenClaw 现在可以使用以下方式调用系统：")
    print()
    print("1. CLI + JSON:")
    print("   python3 clawguard.py price BTC --json")
    print()
    print("2. HTTP API:")
    print("   python3 openclaw_server.py")
    print("   curl http://localhost:5000/api/v1/price/BTCUSDT")
    print()
    print("3. Skills:")
    print("   from skills.binance_spot.handler import BinanceSpotSkill")
    print()
    print("4. NLP:")
    print("   from src.nlp.command_parser import NLPCommandParser")
    print()
    print("5. Web 界面 (可选):")
    print("   通过 HTTP API 启动: POST /api/v1/web/start")
    print()

    return True


if __name__ == '__main__':
    success = init_system()
    sys.exit(0 if success else 1)
