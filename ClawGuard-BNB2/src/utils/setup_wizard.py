#!/usr/bin/env python3
"""
ClawGuard 交互式配置向导
引导用户完成初始配置
"""

import sys
import getpass
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger("setup_wizard")


class SetupWizard:
    """交互式配置向导"""

    def __init__(self):
        self.config_dir = Path.home() / ".clawguard"
        self.config_file = self.config_dir / "config" / "config.yaml"

    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "="*60)
        print("🎉 欢迎使用 ClawGuard - 币安安全交易助手")
        print("="*60)
        print("\n本向导将帮助您完成初始配置，大约需要 3-5 分钟\n")
        print("💡 提示: 按 Ctrl+C 可随时退出\n")

    def print_step(self, step: int, total: int, title: str):
        """打印步骤标题"""
        print(f"\n{'─'*60}")
        print(f"📍 步骤 {step}/{total}: {title}")
        print(f"{'─'*60}\n")

    def get_input(self, prompt: str, default: Optional[str] = None,
                   password: bool = False) -> str:
        """
        获取用户输入

        Args:
            prompt: 提示信息
            default: 默认值
            password: 是否为密码输入

        Returns:
            用户输入
        """
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "

        if password:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt).strip()

        return value if value else (default or "")

    def get_choice(self, prompt: str, choices: list, default: int = 0) -> str:
        """
        获取用户选择

        Args:
            prompt: 提示信息
            choices: 选项列表
            default: 默认选项索引

        Returns:
            用户选择
        """
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            marker = "→" if i - 1 == default else " "
            print(f"  {marker} {i}. {choice}")

        while True:
            choice = input(f"\n请选择 [1-{len(choices)}] (默认: {default + 1}): ").strip()

            if not choice:
                return choices[default]

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
                else:
                    print(f"❌ 请输入 1-{len(choices)} 之间的数字")
            except ValueError:
                print("❌ 请输入有效的数字")

    def confirm(self, prompt: str, default: bool = True) -> bool:
        """
        确认提示

        Args:
            prompt: 提示信息
            default: 默认值

        Returns:
            用户确认结果
        """
        default_str = "Y/n" if default else "y/N"
        choice = input(f"{prompt} [{default_str}]: ").strip().lower()

        if not choice:
            return default

        return choice in ['y', 'yes', '是']

    def step_environment(self) -> str:
        """步骤1: 选择环境"""
        self.print_step(1, 5, "选择运行环境")

        print("ClawGuard 支持两种环境:")
        print("  • 测试网 (Testnet): 使用虚拟资金，适合学习和测试")
        print("  • 主网 (Mainnet): 使用真实资金，需谨慎操作")
        print("\n💡 建议: 新手请先使用测试网熟悉功能\n")

        env = self.get_choice(
            "请选择环境:",
            ["测试网 (Testnet) - 推荐新手", "主网 (Mainnet) - 真实交易"],
            default=0
        )

        return "testnet" if "测试网" in env else "mainnet"

    def step_api_key(self, environment: str) -> tuple:
        """步骤2: 配置API密钥"""
        self.print_step(2, 5, "配置币安API密钥")

        if environment == "testnet":
            print("📝 测试网API密钥获取方法:")
            print("  1. 访问: https://testnet.binance.vision/")
            print("  2. 使用GitHub账号登录")
            print("  3. 生成API密钥\n")
        else:
            print("📝 主网API密钥获取方法:")
            print("  1. 登录币安官网: https://www.binance.com")
            print("  2. 进入 [API管理] 页面")
            print("  3. 创建新的API密钥")
            print("\n⚠️  安全提示:")
            print("  • 仅开启 [现货交易] 权限")
            print("  • 不要开启 [提现] 权限")
            print("  • 建议配置IP白名单\n")

        if not self.confirm("是否已准备好API密钥?"):
            print("\n💡 请先获取API密钥，然后重新运行 'clawguard setup'")
            sys.exit(0)

        print()
        api_key = self.get_input("请输入API Key")
        api_secret = self.get_input("请输入API Secret", password=True)

        if not api_key or not api_secret:
            print("\n❌ API密钥不能为空")
            sys.exit(1)

        return api_key, api_secret

    def step_risk_control(self) -> dict:
        """步骤3: 配置风控参数"""
        self.print_step(3, 5, "配置风控参数")

        print("风控参数用于保护您的资金安全\n")

        print("📊 单笔交易限额 (占账户权益的百分比)")
        print("  • 建议值: 10% (保守)")
        print("  • 激进值: 20% (风险较高)\n")

        max_position = self.get_input(
            "单笔交易限额 (%)",
            default="10"
        )

        print("\n📊 单日亏损限额 (占账户权益的百分比)")
        print("  • 建议值: 5% (保守)")
        print("  • 激进值: 10% (风险较高)\n")

        max_daily_loss = self.get_input(
            "单日亏损限额 (%)",
            default="5"
        )

        print("\n📊 最大滑点容忍度 (%)")
        print("  • 建议值: 2% (正常)")
        print("  • 激进值: 5% (容忍度高)\n")

        max_slippage = self.get_input(
            "最大滑点 (%)",
            default="2"
        )

        try:
            return {
                "max_position_pct": float(max_position) / 100,
                "max_daily_loss_pct": float(max_daily_loss) / 100,
                "max_slippage_pct": float(max_slippage) / 100
            }
        except ValueError:
            print("\n❌ 请输入有效的数字")
            sys.exit(1)

    def step_notification(self) -> dict:
        """步骤4: 配置通知设置"""
        self.print_step(4, 5, "配置通知设置 (可选)")

        print("ClawGuard 可以在重要事件发生时通知您\n")

        enable_notification = self.confirm("是否启用通知功能?", default=False)

        if not enable_notification:
            return {"enabled": False}

        print("\n通知方式:")
        method = self.get_choice(
            "请选择通知方式:",
            ["邮件通知", "Telegram通知", "暂不配置"],
            default=2
        )

        if "暂不配置" in method:
            return {"enabled": False}

        # 这里可以扩展具体的通知配置
        return {
            "enabled": True,
            "method": "email" if "邮件" in method else "telegram"
        }

    def step_confirm(self, config: dict) -> bool:
        """步骤5: 确认配置"""
        self.print_step(5, 5, "确认配置")

        print("请确认以下配置信息:\n")
        print(f"  环境: {config['environment']}")
        print(f"  API Key: {config['api_key'][:8]}...{config['api_key'][-4:]}")
        print(f"  单笔交易限额: {config['risk_control']['max_position_pct']*100}%")
        print(f"  单日亏损限额: {config['risk_control']['max_daily_loss_pct']*100}%")
        print(f"  最大滑点: {config['risk_control']['max_slippage_pct']*100}%")
        print(f"  通知功能: {'已启用' if config.get('notification', {}).get('enabled') else '未启用'}")

        print()
        return self.confirm("确认以上配置?", default=True)

    def save_config(self, config: dict):
        """保存配置"""
        try:
            from ..config.config_manager import ConfigManager

            # 创建配置管理器
            config_manager = ConfigManager()

            # 保存API密钥（加密存储）
            config_manager.set_api_key(
                api_key=config['api_key'],
                api_secret=config['api_secret'],
                testnet=(config['environment'] == 'testnet')
            )

            # 保存其他配置
            import yaml

            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                'environment': config['environment'],
                'risk_control': config['risk_control'],
                'notification': config.get('notification', {'enabled': False}),
                'cache': {
                    'enabled': True,
                    'ttl': 3
                },
                'logging': {
                    'level': 'INFO',
                    'file': str(Path.home() / ".clawguard" / "logs" / "clawguard.log")
                }
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

            logger.info("配置已保存")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}", exc_info=True)
            return False

    def test_connection(self):
        """测试API连接"""
        print("\n" + "─"*60)
        print("🔍 测试API连接...")
        print("─"*60 + "\n")

        try:
            from ..api.binance_client import BinanceClient

            client = BinanceClient()

            # 测试服务器连接
            print("  ⏳ 连接币安服务器...")
            server_time = client.get_server_time()
            print(f"  ✅ 服务器连接成功 (时间: {server_time.get('serverTime', 'N/A')})")

            # 测试API密钥
            print("  ⏳ 验证API密钥...")
            account_info = client.get_account_info()
            print(f"  ✅ API密钥验证成功")

            # 测试行情查询
            print("  ⏳ 测试行情查询...")
            price = client.get_ticker_price("BTCUSDT")
            print(f"  ✅ 行情查询成功 (BTC价格: ${price.get('price', 'N/A')})")

            print("\n✅ 所有测试通过！\n")
            return True

        except Exception as e:
            print(f"\n❌ 连接测试失败: {str(e)}\n")
            print("💡 可能的原因:")
            print("  • API密钥错误")
            print("  • 网络连接问题")
            print("  • API权限不足")
            print("\n请检查配置后重试\n")
            return False

    def print_success(self):
        """打印成功信息"""
        print("\n" + "="*60)
        print("🎉 配置完成！")
        print("="*60)
        print("\n您现在可以开始使用 ClawGuard 了！\n")
        print("📚 快速开始:")
        print("  • 查看帮助: clawguard --help")
        print("  • API安全审计: clawguard audit")
        print("  • 查询价格: clawguard price BTCUSDT")
        print("  • 健康检查: clawguard health")
        print("\n📖 完整文档: 请查看 README.md")
        print("\n💡 提示: 建议先运行 'clawguard audit' 检查API安全性")
        print("="*60 + "\n")

    def run(self):
        """运行配置向导"""
        try:
            self.print_welcome()

            # 步骤1: 选择环境
            environment = self.step_environment()

            # 步骤2: 配置API密钥
            api_key, api_secret = self.step_api_key(environment)

            # 步骤3: 配置风控参数
            risk_control = self.step_risk_control()

            # 步骤4: 配置通知
            notification = self.step_notification()

            # 组装配置
            config = {
                'environment': environment,
                'api_key': api_key,
                'api_secret': api_secret,
                'risk_control': risk_control,
                'notification': notification
            }

            # 步骤5: 确认配置
            if not self.step_confirm(config):
                print("\n❌ 配置已取消")
                sys.exit(0)

            # 保存配置
            print("\n⏳ 正在保存配置...")
            if not self.save_config(config):
                print("\n❌ 配置保存失败")
                sys.exit(1)

            print("✅ 配置已保存")

            # 测试连接
            if self.confirm("\n是否测试API连接?", default=True):
                if not self.test_connection():
                    if not self.confirm("连接测试失败，是否继续?", default=False):
                        sys.exit(1)

            # 打印成功信息
            self.print_success()

        except KeyboardInterrupt:
            print("\n\n❌ 配置已取消")
            sys.exit(0)
        except Exception as e:
            logger.error(f"配置向导异常: {e}", exc_info=True)
            print(f"\n❌ 配置失败: {str(e)}")
            sys.exit(1)


def run_setup_wizard():
    """运行配置向导（便捷函数）"""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    run_setup_wizard()
