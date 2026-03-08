#!/usr/bin/env python3
"""
OpenClaw 集成验证工具
验证系统配置和集成状态
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class OpenClawValidator:
    """OpenClaw 集成验证器"""

    def __init__(self):
        self.config_dir = Path.home() / ".clawguard"
        self.config_file = self.config_dir / "config.yaml"
        self.secrets_file = self.config_dir / "secrets.enc"
        self.openclaw_config_file = self.config_dir / "project.json"

        self.checks = []
        self.warnings = []
        self.errors = []

    def validate_all(self) -> Dict:
        """执行所有验证"""
        print("=" * 70)
        print("🔍 OpenClaw 集成验证")
        print("=" * 70)
        print()

        # 1. 配置文件检查
        print("📁 检查配置文件...")
        self._check_config_files()
        print()

        # 2. API 密钥检查
        print("🔑 检查 API 密钥...")
        self._check_api_keys()
        print()

        # 3. 代理配置检查
        print("🌐 检查代理配置...")
        self._check_proxy()
        print()

        # 4. 依赖检查
        print("📦 检查依赖...")
        self._check_dependencies()
        print()

        # 5. 网络连接检查
        print("🔌 检查网络连接...")
        self._check_network()
        print()

        # 6. Skills 模块检查
        print("🎯 检查 Skills 模块...")
        self._check_skills()
        print()

        # 7. NLP 模块检查
        print("🗣️ 检查 NLP 模块...")
        self._check_nlp()
        print()

        # 8. HTTP API 检查
        print("🌐 检查 HTTP API...")
        self._check_http_api()
        print()

        # 生成报告
        return self._generate_report()

    def _check_config_files(self):
        """检查配置文件"""
        # 检查配置目录
        if self.config_dir.exists():
            self.checks.append(("配置目录存在", True, str(self.config_dir)))
        else:
            self.errors.append(("配置目录不存在", str(self.config_dir)))

        # 检查主配置文件
        if self.config_file.exists():
            self.checks.append(("主配置文件存在", True, str(self.config_file)))

            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    self.checks.append(("配置文件可读", True, "YAML 格式正确"))

                    # 检查必需的配置项
                    required_keys = ['binance', 'proxy', 'risk', 'openclaw']
                    for key in required_keys:
                        if key in config:
                            self.checks.append((f"配置项 '{key}' 存在", True, ""))
                        else:
                            self.warnings.append((f"配置项 '{key}' 缺失", "可能影响功能"))

            except Exception as e:
                self.errors.append(("配置文件读取失败", str(e)))
        else:
            self.errors.append(("主配置文件不存在", "运行 openclaw_configure.py 创建"))

        # 检查 OpenClaw 配置
        if self.openclaw_config_file.exists():
            self.checks.append(("OpenClaw 配置存在", True, str(self.openclaw_config_file)))
        else:
            self.warnings.append(("OpenClaw 配置不存在", "运行 openclaw_configure.py 创建"))

    def _check_api_keys(self):
        """检查 API 密钥"""
        # 检查环境变量
        env_key = os.getenv('BINANCE_API_KEY')
        env_secret = os.getenv('BINANCE_API_SECRET')

        if env_key and env_secret:
            self.checks.append(("环境变量 API 密钥", True, "已设置"))
        else:
            self.warnings.append(("环境变量 API 密钥", "未设置，将使用配置文件或测试网"))

        # 检查加密文件
        if self.secrets_file.exists():
            self.checks.append(("加密 API 密钥文件", True, str(self.secrets_file)))

            # 检查文件权限
            mode = self.secrets_file.stat().st_mode
            if oct(mode)[-3:] == '600':
                self.checks.append(("密钥文件权限", True, "600 (安全)"))
            else:
                self.warnings.append(("密钥文件权限", f"{oct(mode)[-3:]} (建议 600)"))
        else:
            self.warnings.append(("加密 API 密钥文件", "不存在，将使用测试网"))

    def _check_proxy(self):
        """检查代理配置"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                proxy_config = config.get('proxy', {})

                if proxy_config.get('enabled'):
                    self.checks.append(("代理已启用", True, f"{proxy_config.get('type')}://{proxy_config.get('host')}:{proxy_config.get('port')}"))

                    # 测试代理连接
                    try:
                        import requests
                        proxy_url = f"{proxy_config['type']}://{proxy_config['host']}:{proxy_config['port']}"
                        proxies = {'http': proxy_url, 'https': proxy_url}

                        response = requests.get('https://api.binance.com/api/v3/ping',
                                              proxies=proxies, timeout=5)
                        if response.status_code == 200:
                            self.checks.append(("代理连接测试", True, "成功"))
                        else:
                            self.warnings.append(("代理连接测试", f"失败 (状态码: {response.status_code})"))
                    except Exception as e:
                        self.warnings.append(("代理连接测试", f"失败: {str(e)}"))
                else:
                    self.checks.append(("代理配置", True, "未启用"))
        except:
            pass

    def _check_dependencies(self):
        """检查依赖"""
        required_packages = [
            'requests', 'yaml', 'cryptography', 'flask', 'flask_cors'
        ]

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.checks.append((f"依赖 {package}", True, "已安装"))
            except ImportError:
                self.errors.append((f"依赖 {package}", "未安装"))

    def _check_network(self):
        """检查网络连接"""
        try:
            import requests

            # 测试币安 API
            response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
            if response.status_code == 200:
                self.checks.append(("币安 API 连接", True, "正常"))
            else:
                self.warnings.append(("币安 API 连接", f"异常 (状态码: {response.status_code})"))
        except Exception as e:
            self.errors.append(("币安 API 连接", f"失败: {str(e)}"))

    def _check_skills(self):
        """检查 Skills 模块"""
        skills_dir = Path(__file__).parent / "skills"

        if skills_dir.exists():
            self.checks.append(("Skills 目录", True, str(skills_dir)))

            # 检查各个 Skill
            skills = ['binance_spot', 'market_analysis']
            for skill in skills:
                skill_dir = skills_dir / skill
                if skill_dir.exists():
                    handler_file = skill_dir / "handler.py"
                    if handler_file.exists():
                        self.checks.append((f"Skill '{skill}'", True, "已安装"))
                    else:
                        self.warnings.append((f"Skill '{skill}'", "handler.py 不存在"))
                else:
                    self.warnings.append((f"Skill '{skill}'", "目录不存在"))
        else:
            self.errors.append(("Skills 目录", "不存在"))

    def _check_nlp(self):
        """检查 NLP 模块"""
        nlp_dir = Path(__file__).parent / "src" / "nlp"

        if nlp_dir.exists():
            self.checks.append(("NLP 目录", True, str(nlp_dir)))

            # 检查 NLP 组件
            components = ['command_parser.py', 'intent_recognizer.py', 'entity_extractor.py']
            for component in components:
                component_file = nlp_dir / component
                if component_file.exists():
                    self.checks.append((f"NLP 组件 '{component}'", True, "存在"))
                else:
                    self.errors.append((f"NLP 组件 '{component}'", "不存在"))
        else:
            self.errors.append(("NLP 目录", "不存在"))

    def _check_http_api(self):
        """检查 HTTP API"""
        try:
            import requests
            response = requests.get('http://localhost:5000/health', timeout=2)
            if response.status_code == 200:
                self.checks.append(("HTTP API 服务器", True, "运行中"))
            else:
                self.warnings.append(("HTTP API 服务器", "响应异常"))
        except:
            self.warnings.append(("HTTP API 服务器", "未运行 (使用 openclaw_server.py 启动)"))

    def _generate_report(self) -> Dict:
        """生成验证报告"""
        print("=" * 70)
        print("📊 验证报告")
        print("=" * 70)
        print()

        # 成功的检查
        if self.checks:
            print(f"✅ 通过检查: {len(self.checks)}")
            for name, status, detail in self.checks:
                if detail:
                    print(f"   ✓ {name}: {detail}")
                else:
                    print(f"   ✓ {name}")
            print()

        # 警告
        if self.warnings:
            print(f"⚠️  警告: {len(self.warnings)}")
            for name, detail in self.warnings:
                print(f"   ⚠ {name}: {detail}")
            print()

        # 错误
        if self.errors:
            print(f"❌ 错误: {len(self.errors)}")
            for name, detail in self.errors:
                print(f"   ✗ {name}: {detail}")
            print()

        # 总结
        total = len(self.checks) + len(self.warnings) + len(self.errors)
        success_rate = len(self.checks) / total * 100 if total > 0 else 0

        print("=" * 70)
        print(f"总计: {total} 项检查")
        print(f"通过: {len(self.checks)} | 警告: {len(self.warnings)} | 错误: {len(self.errors)}")
        print(f"成功率: {success_rate:.1f}%")
        print("=" * 70)
        print()

        # 建议
        if self.errors:
            print("🔧 修复建议:")
            if any("配置文件" in e[0] for e in self.errors):
                print("   1. 运行配置脚本: python3 openclaw_configure.py")
            if any("依赖" in e[0] for e in self.errors):
                print("   2. 安装依赖: pip install -r requirements.txt")
            if any("API 连接" in e[0] for e in self.errors):
                print("   3. 检查网络连接和代理配置")
            print()

        if not self.errors and not self.warnings:
            print("🎉 所有检查通过！系统已准备就绪。")
            print()
            print("快速开始:")
            print("  1. CLI 模式: python3 clawguard.py price BTC --json")
            print("  2. HTTP API: python3 openclaw_server.py")
            print("  3. 示例代码: python3 openclaw_examples.py")
            print()

        return {
            'total': total,
            'passed': len(self.checks),
            'warnings': len(self.warnings),
            'errors': len(self.errors),
            'success_rate': success_rate,
            'ready': len(self.errors) == 0
        }


def main():
    """主函数"""
    validator = OpenClawValidator()
    result = validator.validate_all()

    # 返回状态码
    if result['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
