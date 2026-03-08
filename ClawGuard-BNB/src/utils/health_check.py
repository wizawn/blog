#!/usr/bin/env python3
"""
ClawGuard 健康检查和诊断工具
检查系统配置、依赖、API连接等
"""

import sys
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

from .logger import get_logger

logger = get_logger("health_check")


class HealthChecker:
    """系统健康检查器"""

    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []

    def check_python_version(self) -> Tuple[bool, str]:
        """检查Python版本"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"✅ Python版本: {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要 >= 3.8)"

    def check_dependencies(self) -> Tuple[bool, str]:
        """检查依赖包"""
        required_packages = {
            'requests': '2.31.0',
            'cryptography': '41.0.0',
            'yaml': '6.0.0'
        }

        missing = []
        outdated = []

        for package, min_version in required_packages.items():
            try:
                if package == 'yaml':
                    mod = importlib.import_module('yaml')
                else:
                    mod = importlib.import_module(package)

                # 检查版本
                if hasattr(mod, '__version__'):
                    version = mod.__version__
                    logger.debug(f"{package}: {version}")
                else:
                    logger.debug(f"{package}: 已安装（版本未知）")

            except ImportError:
                missing.append(package)

        if missing:
            return False, f"❌ 缺少依赖包: {', '.join(missing)}"
        elif outdated:
            return True, f"⚠️  部分依赖包版本较旧: {', '.join(outdated)}"
        else:
            return True, f"✅ 所有依赖包已安装"

    def check_directories(self) -> Tuple[bool, str]:
        """检查必要的目录结构"""
        base_dir = Path.home() / ".clawguard"
        required_dirs = [
            base_dir,
            base_dir / "config",
            base_dir / "logs",
            base_dir / "data",
        ]

        missing = []
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建目录: {dir_path}")
                except Exception as e:
                    missing.append(str(dir_path))
                    logger.error(f"无法创建目录 {dir_path}: {e}")

        if missing:
            return False, f"❌ 无法创建目录: {', '.join(missing)}"
        else:
            return True, f"✅ 目录结构完整"

    def check_config(self) -> Tuple[bool, str]:
        """检查配置文件"""
        config_file = Path.home() / ".clawguard" / "config" / "config.yaml"

        if not config_file.exists():
            return False, f"⚠️  配置文件不存在: {config_file}\n   请运行 'clawguard setup' 进行配置"

        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config:
                return False, "❌ 配置文件为空"

            # 检查必要的配置项
            required_keys = ['environment']
            missing_keys = [key for key in required_keys if key not in config]

            if missing_keys:
                return False, f"❌ 配置文件缺少必要项: {', '.join(missing_keys)}"

            return True, f"✅ 配置文件正常"

        except Exception as e:
            return False, f"❌ 配置文件读取失败: {str(e)}"

    def check_api_credentials(self) -> Tuple[bool, str]:
        """检查API凭证"""
        try:
            from ..config.config_manager import ConfigManager

            config = ConfigManager()
            creds = config.get_api_credentials()

            if not creds or not creds.get('api_key'):
                return False, "⚠️  未配置API密钥\n   请运行 'clawguard setup' 进行配置"

            # 脱敏显示
            api_key = creds['api_key']
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"

            return True, f"✅ API密钥已配置: {masked_key}"

        except Exception as e:
            return False, f"❌ API密钥检查失败: {str(e)}"

    def check_api_connectivity(self) -> Tuple[bool, str]:
        """检查API连接"""
        try:
            from ..api.binance_client import BinanceClient

            client = BinanceClient()

            # 测试连接
            try:
                server_time = client.get_server_time()
                return True, f"✅ API连接正常 (服务器时间: {server_time.get('serverTime', 'N/A')})"
            except Exception as e:
                return False, f"❌ API连接失败: {str(e)}"

        except ImportError as e:
            return False, f"❌ 无法导入API客户端: {str(e)}"
        except Exception as e:
            return False, f"❌ API连接检查失败: {str(e)}"

    def check_permissions(self) -> Tuple[bool, str]:
        """检查文件权限"""
        config_dir = Path.home() / ".clawguard" / "config"

        if not config_dir.exists():
            return True, "⚠️  配置目录不存在，跳过权限检查"

        try:
            # 检查是否可写
            test_file = config_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()

            return True, "✅ 文件权限正常"

        except Exception as e:
            return False, f"❌ 文件权限不足: {str(e)}"

    def check_network(self) -> Tuple[bool, str]:
        """检查网络连接"""
        import socket

        try:
            # 测试DNS解析
            socket.gethostbyname("api.binance.com")

            # 测试HTTPS连接
            import requests
            response = requests.get("https://api.binance.com/api/v3/ping", timeout=5)

            if response.status_code == 200:
                return True, "✅ 网络连接正常"
            else:
                return False, f"⚠️  网络连接异常 (状态码: {response.status_code})"

        except socket.gaierror:
            return False, "❌ DNS解析失败，请检查网络连接"
        except requests.exceptions.Timeout:
            return False, "❌ 网络连接超时"
        except Exception as e:
            return False, f"❌ 网络检查失败: {str(e)}"

    def check_proxy(self) -> Tuple[bool, str]:
        """检查代理配置和连接"""
        try:
            from ..config.config_manager import ConfigManager
            from ..network.proxy_manager import ProxyManager

            config = ConfigManager()
            proxy_config = config.get_proxy_config()

            if not proxy_config or not proxy_config.get('enabled'):
                return True, "⚠️  代理未启用"

            # 创建代理管理器
            proxy_manager = ProxyManager(proxy_config)

            # 测试代理连接
            if proxy_manager.test_proxy():
                proxy_info = proxy_manager.current_proxy
                return True, f"✅ 代理连接正常: {proxy_info.proxy_type}://{proxy_info.host}:{proxy_info.port}"
            else:
                return False, f"❌ 代理连接失败"

        except ImportError as e:
            return False, f"❌ 无法导入代理模块: {str(e)}"
        except Exception as e:
            return False, f"❌ 代理检查失败: {str(e)}"

    def run_all_checks(self, verbose: bool = False) -> Dict:
        """
        运行所有健康检查

        Args:
            verbose: 是否显示详细信息

        Returns:
            检查结果字典
        """
        checks = [
            ("Python版本", self.check_python_version),
            ("依赖包", self.check_dependencies),
            ("目录结构", self.check_directories),
            ("文件权限", self.check_permissions),
            ("配置文件", self.check_config),
            ("API密钥", self.check_api_credentials),
            ("代理配置", self.check_proxy),
            ("网络连接", self.check_network),
            ("API连接", self.check_api_connectivity),
        ]

        results = {
            "passed": [],
            "warnings": [],
            "failed": [],
            "total": len(checks)
        }

        print("\n" + "="*60)
        print("🔍 ClawGuard 系统健康检查")
        print("="*60 + "\n")

        for name, check_func in checks:
            try:
                passed, message = check_func()

                if verbose or not passed:
                    print(f"{name}: {message}")

                if passed:
                    if "⚠️" in message:
                        results["warnings"].append((name, message))
                    else:
                        results["passed"].append((name, message))
                else:
                    results["failed"].append((name, message))

            except Exception as e:
                error_msg = f"❌ 检查失败: {str(e)}"
                print(f"{name}: {error_msg}")
                results["failed"].append((name, error_msg))
                logger.error(f"{name} 检查异常", exc_info=True)

        # 输出总结
        print("\n" + "="*60)
        print("📊 检查结果总结")
        print("="*60)
        print(f"✅ 通过: {len(results['passed'])}")
        print(f"⚠️  警告: {len(results['warnings'])}")
        print(f"❌ 失败: {len(results['failed'])}")
        print(f"📈 总计: {results['total']}")

        # 计算健康分数
        score = (len(results['passed']) + len(results['warnings']) * 0.5) / results['total'] * 100
        results["health_score"] = round(score, 1)

        print(f"\n🏥 健康评分: {results['health_score']}/100")

        if results['failed']:
            print("\n⚠️  发现问题，请根据上述提示进行修复")
            print("💡 提示: 运行 'clawguard setup' 可以自动修复大部分问题")
        elif results['warnings']:
            print("\n✅ 系统基本正常，但有一些警告需要注意")
        else:
            print("\n✅ 系统完全正常，可以开始使用！")

        print("="*60 + "\n")

        return results

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        import platform

        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "architecture": platform.machine(),
        }

        # 获取配置目录大小
        config_dir = Path.home() / ".clawguard"
        if config_dir.exists():
            total_size = sum(f.stat().st_size for f in config_dir.rglob('*') if f.is_file())
            info["config_dir_size_mb"] = round(total_size / (1024 * 1024), 2)

        return info

    def print_system_info(self):
        """打印系统信息"""
        info = self.get_system_info()

        print("\n" + "="*60)
        print("💻 系统信息")
        print("="*60)
        print(f"操作系统: {info['os']}")
        print(f"系统版本: {info['os_version']}")
        print(f"Python版本: {info['python_version']}")
        print(f"架构: {info['architecture']}")

        if "config_dir_size_mb" in info:
            print(f"配置目录大小: {info['config_dir_size_mb']} MB")

        print("="*60 + "\n")


def run_health_check(verbose: bool = False) -> Dict:
    """
    运行健康检查（便捷函数）

    Args:
        verbose: 是否显示详细信息

    Returns:
        检查结果
    """
    checker = HealthChecker()
    return checker.run_all_checks(verbose)


def print_system_info():
    """打印系统信息（便捷函数）"""
    checker = HealthChecker()
    checker.print_system_info()


if __name__ == "__main__":
    # 测试健康检查
    print_system_info()
    results = run_health_check(verbose=True)

    # 返回退出码
    sys.exit(0 if not results["failed"] else 1)
