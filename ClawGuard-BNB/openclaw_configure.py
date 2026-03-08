#!/usr/bin/env python3
"""
OpenClaw 自动配置脚本
一键配置 ClawGuard-BNB 以供 OpenClaw 使用
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Optional


class OpenClawConfigurator:
    """OpenClaw 自动配置器"""

    def __init__(self):
        self.config_dir = Path.home() / ".clawguard"
        self.config_file = self.config_dir / "config.yaml"
        self.openclaw_config_file = self.config_dir / "project.json"

    def auto_configure(self, api_key: Optional[str] = None,
                      api_secret: Optional[str] = None,
                      proxy_url: Optional[str] = None) -> Dict:
        """
        自动配置系统

        Args:
            api_key: 币安 API Key（可选，从环境变量读取）
            api_secret: 币安 API Secret（可选，从环境变量读取）
            proxy_url: 代理URL（可选，格式: http://host:port）

        Returns:
            配置结果
        """
        print("🚀 OpenClaw 自动配置开始...")

        # 1. 创建配置目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 配置目录: {self.config_dir}")

        # 2. 从环境变量读取 API 密钥
        api_key = api_key or os.getenv('BINANCE_API_KEY')
        api_secret = api_secret or os.getenv('BINANCE_API_SECRET')

        if not api_key or not api_secret:
            print("⚠️  未检测到 API 密钥，将使用测试网模式")
            use_testnet = True
        else:
            print("✅ 检测到 API 密钥")
            use_testnet = False

        # 3. 解析代理配置
        proxy_config = self._parse_proxy(proxy_url or os.getenv('PROXY_URL'))

        # 4. 生成配置
        config = self._generate_config(use_testnet, proxy_config)

        # 5. 保存配置
        self._save_config(config)

        # 6. 保存 API 密钥（加密）
        if api_key and api_secret:
            self._save_credentials(api_key, api_secret)

        # 7. 生成 OpenClaw 配置
        openclaw_config = self._generate_openclaw_config()
        self._save_openclaw_config(openclaw_config)

        # 8. 验证配置
        validation = self._validate_configuration()

        print("\n" + "=" * 60)
        print("✅ OpenClaw 配置完成！")
        print("=" * 60)
        print(f"配置文件: {self.config_file}")
        print(f"OpenClaw配置: {self.openclaw_config_file}")
        print("\n使用方法:")
        print("  1. CLI模式: python3 clawguard.py price BTC --json")
        print("  2. HTTP API: python3 openclaw_server.py")
        print("  3. Skills: from skills import execute_skill")
        print("  4. NLP: from src.nlp import NLPCommandParser")
        print("=" * 60)

        return {
            'success': True,
            'config_dir': str(self.config_dir),
            'config_file': str(self.config_file),
            'openclaw_config': str(self.openclaw_config_file),
            'use_testnet': use_testnet,
            'proxy_enabled': proxy_config['enabled'],
            'validation': validation
        }

    def _parse_proxy(self, proxy_url: Optional[str]) -> Dict:
        """解析代理URL"""
        if not proxy_url:
            return {'enabled': False}

        try:
            # 解析格式: http://host:port 或 socks5://host:port
            from urllib.parse import urlparse
            parsed = urlparse(proxy_url)

            return {
                'enabled': True,
                'type': parsed.scheme,
                'host': parsed.hostname,
                'port': parsed.port or 7890,
                'username': parsed.username,
                'password': parsed.password
            }
        except Exception as e:
            print(f"⚠️  代理URL解析失败: {e}")
            return {'enabled': False}

    def _generate_config(self, use_testnet: bool, proxy_config: Dict) -> Dict:
        """生成配置"""
        return {
            'binance': {
                'base_url': 'https://testnet.binance.vision' if use_testnet else 'https://api.binance.com',
                'use_testnet': use_testnet,
                'timeout': 10,
                'max_retries': 3,
                'endpoints': {
                    'global': 'https://api.binance.com',
                    'us': 'https://api.binance.us',
                    'testnet': 'https://testnet.binance.vision'
                },
                'active_endpoint': 'testnet' if use_testnet else 'global',
                'auto_switch': True
            },
            'proxy': proxy_config,
            'futures': {
                'enabled': False,
                'testnet_url': 'https://testnet.binancefuture.com',
                'mainnet_url': 'https://fapi.binance.com'
            },
            'futures_risk': {
                'max_leverage': 5,
                'max_position_value': 10000,
                'liquidation_buffer': 0.1,
                'max_funding_rate': 0.01
            },
            'risk': {
                'max_order_value': 10000,
                'max_daily_loss': 1000,
                'max_position_size': 0.1,
                'enable_stop_loss': True,
                'default_stop_loss_percent': 0.05
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'cors_enabled': True
            },
            'logging': {
                'level': 'INFO',
                'file': str(self.config_dir / 'clawguard.log'),
                'max_size': 10485760,
                'backup_count': 5
            },
            'openclaw': {
                'enabled': True,
                'json_output': True,
                'auto_confirm': True,
                'nlp_enabled': True,
                'skills_enabled': True,
                'http_api_enabled': True
            }
        }

    def _save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ 配置已保存: {self.config_file}")

    def _save_credentials(self, api_key: str, api_secret: str):
        """保存加密的 API 密钥"""
        from cryptography.fernet import Fernet

        # 生成或读取加密密钥
        key_file = self.config_dir / ".key"
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)
        else:
            key = key_file.read_bytes()

        cipher = Fernet(key)

        # 加密并保存
        secrets = {
            'api_key': api_key,
            'api_secret': api_secret
        }

        encrypted = cipher.encrypt(json.dumps(secrets).encode())
        secrets_file = self.config_dir / "secrets.enc"
        secrets_file.write_bytes(encrypted)
        secrets_file.chmod(0o600)

        print("✅ API 密钥已加密保存")

    def _generate_openclaw_config(self) -> Dict:
        """生成 OpenClaw 专用配置"""
        return {
            'name': 'ClawGuard-BNB',
            'version': '3.0.0',
            'description': '专业量化交易平台，支持现货和合约交易',
            'integration_methods': [
                {
                    'name': 'CLI + JSON',
                    'command': 'python3 clawguard.py {action} {params} --json --yes',
                    'example': 'python3 clawguard.py price BTC --json'
                },
                {
                    'name': 'HTTP API',
                    'base_url': 'http://localhost:5000/api/v1',
                    'start_command': 'python3 openclaw_server.py',
                    'endpoints': {
                        'price': 'GET /price/{symbol}',
                        'account': 'GET /account',
                        'order': 'POST /order',
                        'analysis': 'GET /analysis/summary/{symbol}'
                    }
                },
                {
                    'name': 'Skills',
                    'import': 'from skills import execute_skill',
                    'example': "execute_skill('binance_spot', 'query_price', {'symbol': 'BTCUSDT'})"
                },
                {
                    'name': 'NLP',
                    'import': 'from src.nlp.command_parser import NLPCommandParser',
                    'example': "parser.parse('用1000 USDT买入BTC')"
                },
                {
                    'name': 'Python API',
                    'import': 'from src.api.binance_client import BinanceClient',
                    'example': "client.get_ticker_price('BTCUSDT')"
                }
            ],
            'capabilities': {
                'spot_trading': True,
                'futures_trading': True,
                'technical_analysis': True,
                'backtesting': True,
                'natural_language': True,
                'risk_management': True
            },
            'supported_commands': [
                'price', 'account', 'analyze', 'order', 'position',
                'futures', 'grid', 'strategy', 'backtest'
            ],
            'nlp_intents': [
                'query_price', 'query_account', 'place_buy_order', 'place_sell_order',
                'analyze_trend', 'strategy_start', 'strategy_stop', 'set_leverage'
            ]
        }

    def _save_openclaw_config(self, config: Dict):
        """保存 OpenClaw 配置"""
        with open(self.openclaw_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ OpenClaw配置已保存: {self.openclaw_config_file}")

    def _validate_configuration(self) -> Dict:
        """验证配置"""
        validation = {
            'config_file_exists': self.config_file.exists(),
            'config_readable': False,
            'api_keys_configured': False,
            'proxy_configured': False,
            'openclaw_config_exists': self.openclaw_config_file.exists()
        }

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                validation['config_readable'] = True
                validation['proxy_configured'] = config.get('proxy', {}).get('enabled', False)
        except:
            pass

        secrets_file = self.config_dir / "secrets.enc"
        validation['api_keys_configured'] = secrets_file.exists()

        return validation


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='OpenClaw 自动配置工具')
    parser.add_argument('--api-key', help='币安 API Key')
    parser.add_argument('--api-secret', help='币安 API Secret')
    parser.add_argument('--proxy', help='代理URL (例: http://127.0.0.1:7890)')
    parser.add_argument('--interactive', action='store_true', help='交互式配置')

    args = parser.parse_args()

    configurator = OpenClawConfigurator()

    if args.interactive:
        print("🎯 OpenClaw 交互式配置")
        print("=" * 60)

        # 交互式输入
        api_key = input("币安 API Key (留空使用环境变量): ").strip() or None
        api_secret = input("币安 API Secret (留空使用环境变量): ").strip() or None
        proxy_url = input("代理URL (留空跳过，格式: http://host:port): ").strip() or None

        result = configurator.auto_configure(api_key, api_secret, proxy_url)
    else:
        result = configurator.auto_configure(args.api_key, args.api_secret, args.proxy)

    if result['success']:
        print("\n✅ 配置成功！")
        sys.exit(0)
    else:
        print("\n❌ 配置失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
