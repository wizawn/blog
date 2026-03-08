#!/usr/bin/env python3
"""
配置管理器 - 安全的配置和密钥管理
支持多环境、加密存储、环境变量优先
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
import base64
import hashlib


class ConfigManager:
    """统一配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录路径，默认为 ~/.clawguard
        """
        if config_dir:
            self.config_dir = Path(config_dir).expanduser()
        else:
            self.config_dir = Path.home() / ".clawguard"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.yaml"
        self.secrets_file = self.config_dir / "secrets.enc"

        # 加载配置
        self._config = self._load_config()
        self._cipher = self._init_cipher()

    def _init_cipher(self) -> Fernet:
        """初始化加密器"""
        key_file = self.config_dir / ".key"

        if not key_file.exists():
            # 生成新密钥
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # 仅所有者可读写

        key = key_file.read_bytes()
        return Fernet(key)

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_file.exists():
            return self._default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️  配置文件加载失败: {e}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "binance": {
                "base_url": "https://api.binance.com",
                "testnet_url": "https://testnet.binance.vision",
                "use_testnet": True,
                "timeout": 10,
                "max_retries": 3,
                "endpoints": {
                    "global": "https://api.binance.com",
                    "us": "https://api.binance.us",
                    "testnet": "https://testnet.binance.vision"
                },
                "active_endpoint": "global",
                "auto_switch": True
            },
            "proxy": {
                "enabled": False,
                "type": "http",  # http, https, socks5
                "host": "127.0.0.1",
                "port": 7890,
                "username": None,
                "password": None,
                "pool": {
                    "enabled": False,
                    "proxies": []
                },
                "failover": {
                    "enabled": True,
                    "retry_count": 3,
                    "timeout": 10
                }
            },
            "futures": {
                "enabled": False,
                "testnet_url": "https://testnet.binancefuture.com",
                "mainnet_url": "https://fapi.binance.com"
            },
            "futures_risk": {
                "max_leverage": 5,
                "max_position_value": 10000,
                "liquidation_buffer": 0.1,
                "max_funding_rate": 0.01
            },
            "risk_control": {
                "max_position_pct": 0.1,  # 单笔最大仓位10%
                "max_total_position_pct": 0.8,  # 总仓位最大80%
                "max_daily_loss_pct": 0.05,  # 单日最大亏损5%
                "max_slippage_pct": 0.02,  # 最大滑点2%
                "order_timeout_seconds": 30  # 订单超时30秒
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 3,  # 缓存3秒
                "max_size": 1000
            },
            "logging": {
                "level": "INFO",
                "file": "~/.clawguard/logs/clawguard.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5
            },
            "security": {
                "require_ip_whitelist": False,
                "allow_withdrawal": False,
                "require_2fa": False,
                "audit_log_retention_days": 90
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）
        优先级: 环境变量 > 配置文件 > 默认值

        Args:
            key: 配置键，支持 "binance.timeout" 格式
            default: 默认值

        Returns:
            配置值
        """
        # 1. 检查环境变量
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(f"CLAWGUARD_{env_key}")
        if env_value is not None:
            return self._parse_env_value(env_value)

        # 2. 从配置文件读取
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def _parse_env_value(self, value: str) -> Any:
        """解析环境变量值"""
        # 尝试解析为JSON
        try:
            return json.loads(value)
        except:
            pass

        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except:
            pass

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")

    # ============= 密钥管理 =============

    def set_api_key(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        安全存储API密钥（加密）

        Args:
            api_key: API Key
            api_secret: API Secret
            testnet: 是否为测试网密钥
        """
        if not api_key or not api_secret:
            raise ValueError("API Key 和 Secret 不能为空")

        # 验证密钥格式
        if len(api_key) < 32 or len(api_secret) < 32:
            raise ValueError("API Key 格式不正确（长度过短）")

        secrets = {
            "api_key": api_key,
            "api_secret": api_secret,
            "testnet": testnet
        }

        # 加密存储
        encrypted = self._cipher.encrypt(json.dumps(secrets).encode())
        self.secrets_file.write_bytes(encrypted)
        self.secrets_file.chmod(0o600)

        print("✅ API密钥已安全存储（加密）")
        print(f"   位置: {self.secrets_file}")
        print(f"   Key: {api_key[:8]}...{api_key[-8:]}")
        print(f"   环境: {'测试网' if testnet else '主网'}")

    def get_api_credentials(self) -> Optional[Dict[str, str]]:
        """
        获取API密钥（解密）
        优先级: 环境变量 > 加密文件

        Returns:
            {"api_key": "xxx", "api_secret": "xxx", "testnet": True/False}
        """
        # 1. 优先从环境变量读取
        env_key = os.getenv('BINANCE_API_KEY')
        env_secret = os.getenv('BINANCE_SECRET_KEY')

        if env_key and env_secret:
            return {
                "api_key": env_key,
                "api_secret": env_secret,
                "testnet": os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
            }

        # 2. 从加密文件读取
        if not self.secrets_file.exists():
            return None

        try:
            encrypted = self.secrets_file.read_bytes()
            decrypted = self._cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            print(f"⚠️  密钥解密失败: {e}")
            return None

    def remove_api_key(self):
        """删除存储的API密钥"""
        if self.secrets_file.exists():
            self.secrets_file.unlink()
            print("✅ API密钥已删除")
        else:
            print("⚠️  未找到存储的密钥")

    def check_api_key_security(self) -> Dict[str, Any]:
        """
        检查API密钥安全性

        Returns:
            安全检查结果
        """
        creds = self.get_api_credentials()
        if not creds:
            return {"status": "error", "message": "未配置API密钥"}

        issues = []
        warnings = []

        # 检查1: 密钥长度
        if len(creds['api_key']) < 64:
            warnings.append("API Key 长度较短，建议使用更长的密钥")

        # 检查2: 是否使用测试网
        if not creds['testnet']:
            warnings.append("当前使用主网密钥，请确保已充分测试")

        # 检查3: 环境变量存储
        if os.getenv('BINANCE_API_KEY'):
            warnings.append("密钥存储在环境变量中，请确保环境安全")

        return {
            "status": "ok" if not issues else "warning",
            "issues": issues,
            "warnings": warnings
        }

    def get_proxy_config(self) -> Dict:
        """
        获取代理配置

        Returns:
            代理配置字典
        """
        return self.get('proxy', {})


# ============= 使用示例 =============

if __name__ == "__main__":
    # 初始化配置管理器
    config = ConfigManager()

    print("=" * 50)
    print("ClawGuard 配置管理器")
    print("=" * 50)
    print()

    # 示例1: 读取配置
    print("📋 当前配置:")
    print(f"  币安API地址: {config.get('binance.base_url')}")
    print(f"  使用测试网: {config.get('binance.use_testnet')}")
    print(f"  最大仓位: {config.get('risk_control.max_position_pct') * 100}%")
    print(f"  缓存启用: {config.get('cache.enabled')}")
    print()

    # 示例2: 设置API密钥（交互式）
    print("🔐 API密钥配置")
    print("提示: 请使用测试网密钥进行开发")
    print()

    # 检查是否已有密钥
    creds = config.get_api_credentials()
    if creds:
        print(f"✅ 已配置密钥: {creds['api_key'][:8]}...{creds['api_key'][-8:]}")
        print(f"   环境: {'测试网' if creds['testnet'] else '主网'}")
    else:
        print("⚠️  未配置API密钥")
        print()
        print("配置方法:")
        print("  方法1: 环境变量")
        print("    export BINANCE_API_KEY=your_key")
        print("    export BINANCE_SECRET_KEY=your_secret")
        print()
        print("  方法2: Python代码")
        print("    config.set_api_key('your_key', 'your_secret', testnet=True)")

    print()
    print("=" * 50)
