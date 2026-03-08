#!/usr/bin/env python3
"""
OpenClaw 集成示例
展示如何在 OpenClaw 中使用 ClawGuard-BNB
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


class OpenClawIntegration:
    """OpenClaw 集成类"""

    def __init__(self):
        """初始化集成"""
        self.setup_complete = False

    def quick_start(self):
        """快速开始"""
        print("=" * 70)
        print("🚀 ClawGuard-BNB OpenClaw 集成示例")
        print("=" * 70)
        print()

        # 方式1: CLI + JSON
        print("📌 方式1: CLI + JSON 输出")
        print("-" * 70)
        self.demo_cli_json()
        print()

        # 方式2: HTTP API
        print("📌 方式2: HTTP API")
        print("-" * 70)
        self.demo_http_api()
        print()

        # 方式3: Skills
        print("📌 方式3: Skills 模块")
        print("-" * 70)
        self.demo_skills()
        print()

        # 方式4: NLP
        print("📌 方式4: 自然语言接口")
        print("-" * 70)
        self.demo_nlp()
        print()

        # 方式5: Python API
        print("📌 方式5: Python API")
        print("-" * 70)
        self.demo_python_api()
        print()

    def demo_cli_json(self):
        """演示 CLI + JSON 模式"""
        import subprocess
        import json

        print("代码示例:")
        print("""
import subprocess
import json

def call_clawguard(command: str) -> dict:
    cmd = f"python3 clawguard.py {command} --json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# 查询价格
price = call_clawguard("price BTC")
print(f"BTC价格: ${price['price']}")

# 查询账户
account = call_clawguard("account")
print(f"余额: {account['balances']}")
        """)

        print("\n实际执行:")
        try:
            result = subprocess.run(
                "python3 clawguard.py price BTC --json",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                print(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"⚠️  命令执行失败: {result.stderr}")
        except Exception as e:
            print(f"⚠️  演示跳过: {e}")

    def demo_http_api(self):
        """演示 HTTP API"""
        print("代码示例:")
        print("""
import requests

class ClawGuardAPI:
    def __init__(self, base_url="http://localhost:5000/api/v1"):
        self.base_url = base_url

    def get_price(self, symbol: str):
        response = requests.get(f"{self.base_url}/price/{symbol}")
        return response.json()

    def get_account(self):
        response = requests.get(f"{self.base_url}/account")
        return response.json()

    def analyze(self, symbol: str, interval: str = "1h"):
        response = requests.get(
            f"{self.base_url}/analysis/summary/{symbol}",
            params={"interval": interval}
        )
        return response.json()

# 使用
api = ClawGuardAPI()
price = api.get_price("BTCUSDT")
print(f"BTC价格: ${price['data']['price']}")
        """)

        print("\n实际执行:")
        try:
            import requests
            response = requests.get("http://localhost:5000/health", timeout=2)
            if response.status_code == 200:
                print("✅ API服务器运行中")
                # 尝试获取价格
                price_response = requests.get("http://localhost:5000/api/v1/price/BTCUSDT", timeout=5)
                if price_response.status_code == 200:
                    print(f"✅ 价格查询成功: {price_response.json()}")
            else:
                print("⚠️  API服务器未运行，请先启动: python3 openclaw_server.py")
        except Exception as e:
            print(f"⚠️  API服务器未运行: {e}")
            print("   启动命令: python3 openclaw_server.py")

    def demo_skills(self):
        """演示 Skills 模块"""
        print("代码示例:")
        print("""
from skills.binance_spot.handler import BinanceSpotSkill
from skills.market_analysis.handler import MarketAnalysisSkill

# 现货交易 Skill
spot_skill = BinanceSpotSkill()

# 查询价格
result = spot_skill.execute('query_price', {'symbol': 'BTCUSDT'})
print(f"价格: {result['data']['price']}")

# 查询账户
result = spot_skill.execute('query_account', {})
print(f"账户: {result['data']}")

# 市场分析 Skill
analysis_skill = MarketAnalysisSkill()

# 分析趋势
result = analysis_skill.execute('analyze_trend', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(f"趋势: {result['data']['trend']}")
        """)

        print("\n实际执行:")
        try:
            from skills.binance_spot.handler import BinanceSpotSkill

            skill = BinanceSpotSkill()
            result = skill.execute('query_price', {'symbol': 'BTCUSDT'})

            if result['success']:
                print(f"✅ Skills调用成功: {result}")
            else:
                print(f"⚠️  Skills调用失败: {result.get('error')}")
        except Exception as e:
            print(f"⚠️  演示跳过: {e}")

    def demo_nlp(self):
        """演示 NLP 接口"""
        print("代码示例:")
        print("""
from src.nlp.command_parser import NLPCommandParser

parser = NLPCommandParser()

# 解析自然语言指令
commands = [
    "BTC现在多少钱？",
    "用1000 USDT买入BTC",
    "帮我分析一下ETH的走势",
    "把BTC的杠杆调到5倍"
]

for text in commands:
    result = parser.parse(text)
    print(f"指令: {text}")
    print(f"意图: {result['intent']}")
    print(f"实体: {result['entities']}")
    print(f"命令: {result['command']}")
    print()
        """)

        print("\n实际执行:")
        try:
            from src.nlp.command_parser import NLPCommandParser

            parser = NLPCommandParser()

            test_commands = [
                "BTC现在多少钱？",
                "用1000 USDT买入BTC"
            ]

            for text in test_commands:
                result = parser.parse(text)
                print(f"✅ 指令: {text}")
                print(f"   意图: {result['intent']}")
                print(f"   置信度: {result['confidence']:.2f}")
                print()
        except Exception as e:
            print(f"⚠️  演示跳过: {e}")

    def demo_python_api(self):
        """演示 Python API"""
        print("代码示例:")
        print("""
from src.api.binance_client import BinanceClient
from src.analysis.indicators import TechnicalIndicators
from src.strategies.ma_crossover_strategy import MACrossoverStrategy

# 现货交易
client = BinanceClient()
ticker = client.get_ticker_price('BTCUSDT')
print(f"BTC价格: {ticker['price']}")

# 技术分析
indicators = TechnicalIndicators(client)
klines = indicators.get_klines('BTCUSDT', '1h', limit=100)
rsi = indicators.calculate_rsi(klines)
print(f"RSI: {rsi[-1]:.2f}")

# 交易策略
strategy = MACrossoverStrategy('BTCUSDT', fast_period=10, slow_period=30)
signal = strategy.generate_signal()
print(f"信号: {signal['signal']}")
        """)

        print("\n实际执行:")
        try:
            from src.api.binance_client import BinanceClient

            client = BinanceClient()
            ticker = client.get_ticker_price('BTCUSDT')

            print(f"✅ BTC价格: ${ticker.get('price', 'N/A')}")
        except Exception as e:
            print(f"⚠️  演示跳过: {e}")


def main():
    """主函数"""
    integration = OpenClawIntegration()
    integration.quick_start()

    print("=" * 70)
    print("📚 更多信息:")
    print("  - API文档: docs/API.md")
    print("  - 策略文档: docs/STRATEGIES.md")
    print("  - 集成指南: docs/INTEGRATION.md")
    print("=" * 70)


if __name__ == '__main__':
    main()
