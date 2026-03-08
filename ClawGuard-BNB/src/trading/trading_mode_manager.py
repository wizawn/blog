#!/usr/bin/env python3
"""
交易模式管理器
管理三种交易模式：模拟盘、测试网、实盘
"""

import os
from enum import Enum
from typing import Optional
from pathlib import Path
import yaml


class TradingMode(Enum):
    """交易模式枚举"""
    PAPER = "paper"      # 模拟盘（本地模拟）
    TESTNET = "testnet"  # 测试网（币安测试网）
    LIVE = "live"        # 实盘（真实交易）


class TradingModeManager:
    """交易模式管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".clawguard"
        self.config_file = self.config_dir / "config.yaml"
        self.mode_file = self.config_dir / "trading_mode.txt"

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_current_mode(self) -> TradingMode:
        """
        获取当前交易模式

        优先级：环境变量 > 配置文件 > 默认值（模拟盘）
        """
        # 1. 检查环境变量
        env_mode = os.getenv('TRADING_MODE')
        if env_mode:
            try:
                return TradingMode(env_mode.lower())
            except ValueError:
                pass

        # 2. 检查模式文件
        if self.mode_file.exists():
            try:
                mode_str = self.mode_file.read_text().strip()
                return TradingMode(mode_str)
            except:
                pass

        # 3. 检查配置文件
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    mode_str = config.get('trading', {}).get('mode', 'paper')
                    return TradingMode(mode_str)
            except:
                pass

        # 4. 默认使用模拟盘（最安全）
        return TradingMode.PAPER

    def set_mode(self, mode: TradingMode) -> bool:
        """
        设置交易模式

        Args:
            mode: 交易模式

        Returns:
            是否设置成功
        """
        try:
            # 1. 保存到模式文件
            self.mode_file.write_text(mode.value)

            # 2. 更新配置文件
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

            if 'trading' not in config:
                config['trading'] = {}

            config['trading']['mode'] = mode.value

            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            return True
        except Exception as e:
            print(f"设置交易模式失败: {e}")
            return False

    def get_mode_info(self) -> dict:
        """获取当前模式的详细信息"""
        mode = self.get_current_mode()

        info = {
            'mode': mode.value,
            'name': self._get_mode_name(mode),
            'description': self._get_mode_description(mode),
            'risk_level': self._get_risk_level(mode),
            'requires_api_key': self._requires_api_key(mode),
            'real_money': self._is_real_money(mode),
            'features': self._get_mode_features(mode)
        }

        return info

    def _get_mode_name(self, mode: TradingMode) -> str:
        """获取模式名称"""
        names = {
            TradingMode.PAPER: "模拟盘",
            TradingMode.TESTNET: "测试网",
            TradingMode.LIVE: "实盘"
        }
        return names.get(mode, "未知")

    def _get_mode_description(self, mode: TradingMode) -> str:
        """获取模式描述"""
        descriptions = {
            TradingMode.PAPER: "本地模拟交易，不连接真实API，适合学习和测试策略",
            TradingMode.TESTNET: "币安测试网络，使用测试币，适合验证API集成",
            TradingMode.LIVE: "真实交易，使用真实资金，请谨慎操作"
        }
        return descriptions.get(mode, "")

    def _get_risk_level(self, mode: TradingMode) -> str:
        """获取风险等级"""
        levels = {
            TradingMode.PAPER: "无风险",
            TradingMode.TESTNET: "低风险",
            TradingMode.LIVE: "高风险"
        }
        return levels.get(mode, "未知")

    def _requires_api_key(self, mode: TradingMode) -> bool:
        """是否需要API密钥"""
        return mode in [TradingMode.TESTNET, TradingMode.LIVE]

    def _is_real_money(self, mode: TradingMode) -> bool:
        """是否使用真实资金"""
        return mode == TradingMode.LIVE

    def _get_mode_features(self, mode: TradingMode) -> list:
        """获取模式特性"""
        features = {
            TradingMode.PAPER: [
                "本地模拟，无需API密钥",
                "模拟价格波动",
                "完整的账户和持仓管理",
                "交易历史记录",
                "可随时重置",
                "零风险学习环境"
            ],
            TradingMode.TESTNET: [
                "币安官方测试网",
                "需要测试网API密钥",
                "真实的API交互",
                "测试币交易",
                "验证策略和集成",
                "无真实资金风险"
            ],
            TradingMode.LIVE: [
                "真实交易环境",
                "需要主网API密钥",
                "使用真实资金",
                "完整的交易功能",
                "实时市场数据",
                "⚠️ 高风险，请谨慎"
            ]
        }
        return features.get(mode, [])

    def switch_mode_interactive(self):
        """交互式切换模式"""
        print("=" * 60)
        print("交易模式切换")
        print("=" * 60)
        print()

        current_mode = self.get_current_mode()
        print(f"当前模式: {self._get_mode_name(current_mode)} ({current_mode.value})")
        print()

        print("可用模式:")
        print("  1. 模拟盘 (paper) - 本地模拟，零风险")
        print("  2. 测试网 (testnet) - 币安测试网，低风险")
        print("  3. 实盘 (live) - 真实交易，高风险")
        print()

        choice = input("请选择模式 (1/2/3) 或按 Enter 保持当前: ").strip()

        mode_map = {
            '1': TradingMode.PAPER,
            '2': TradingMode.TESTNET,
            '3': TradingMode.LIVE
        }

        if choice in mode_map:
            new_mode = mode_map[choice]

            # 显示模式信息
            info = self.get_mode_info()
            print()
            print(f"模式: {info['name']}")
            print(f"描述: {info['description']}")
            print(f"风险: {info['risk_level']}")
            print(f"需要API密钥: {'是' if info['requires_api_key'] else '否'}")
            print(f"真实资金: {'是' if info['real_money'] else '否'}")
            print()

            # 实盘需要额外确认
            if new_mode == TradingMode.LIVE:
                print("⚠️  警告: 实盘模式将使用真实资金进行交易！")
                confirm = input("确认切换到实盘模式？(yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("已取消切换")
                    return

            # 切换模式
            if self.set_mode(new_mode):
                print(f"✅ 已切换到 {self._get_mode_name(new_mode)} 模式")
            else:
                print("❌ 切换失败")
        else:
            print("保持当前模式")

    def print_mode_info(self):
        """打印当前模式信息"""
        info = self.get_mode_info()

        print("=" * 60)
        print("当前交易模式")
        print("=" * 60)
        print(f"模式: {info['name']} ({info['mode']})")
        print(f"描述: {info['description']}")
        print(f"风险等级: {info['risk_level']}")
        print(f"需要API密钥: {'是' if info['requires_api_key'] else '否'}")
        print(f"真实资金: {'是' if info['real_money'] else '否'}")
        print()
        print("特性:")
        for feature in info['features']:
            print(f"  • {feature}")
        print("=" * 60)


# 全局实例
_trading_mode_manager = None


def get_trading_mode_manager() -> TradingModeManager:
    """获取交易模式管理器单例"""
    global _trading_mode_manager
    if _trading_mode_manager is None:
        _trading_mode_manager = TradingModeManager()
    return _trading_mode_manager


def get_current_trading_mode() -> TradingMode:
    """快捷函数：获取当前交易模式"""
    return get_trading_mode_manager().get_current_mode()


def is_paper_trading() -> bool:
    """快捷函数：是否为模拟盘模式"""
    return get_current_trading_mode() == TradingMode.PAPER


def is_testnet() -> bool:
    """快捷函数：是否为测试网模式"""
    return get_current_trading_mode() == TradingMode.TESTNET


def is_live_trading() -> bool:
    """快捷函数：是否为实盘模式"""
    return get_current_trading_mode() == TradingMode.LIVE


# 使用示例
if __name__ == '__main__':
    manager = get_trading_mode_manager()

    # 显示当前模式
    manager.print_mode_info()

    print()

    # 交互式切换
    manager.switch_mode_interactive()

    print()

    # 再次显示
    manager.print_mode_info()
