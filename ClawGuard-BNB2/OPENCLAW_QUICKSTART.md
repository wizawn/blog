# OpenClaw 集成快速指南

## 🚀 一键配置和启动

### 方式1: 自动配置（推荐）

```bash
# 使用环境变量配置
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
export PROXY_URL="http://127.0.0.1:7890"  # 可选

# 运行自动配置
python3 openclaw_configure.py

# 启动服务器
python3 openclaw_server.py
```

### 方式2: 交互式配置

```bash
# 交互式配置向导
python3 openclaw_configure.py --interactive

# 启动服务器
python3 openclaw_server.py
```

### 方式3: 一键配置并启动

```bash
# 配置并启动
python3 openclaw_server.py --configure
```

---

## 📋 配置说明

### 环境变量

| 变量名 | 说明 | 必需 | 示例 |
|-------|------|------|------|
| `BINANCE_API_KEY` | 币安 API Key | 否* | `abc123...` |
| `BINANCE_API_SECRET` | 币安 API Secret | 否* | `xyz789...` |
| `PROXY_URL` | 代理服务器 | 否 | `http://127.0.0.1:7890` |

*如果不提供，将使用测试网模式

### 配置文件位置

- **主配置**: `~/.clawguard/config.yaml`
- **API密钥**: `~/.clawguard/secrets.enc` (加密)
- **OpenClaw配置**: `~/.clawguard/project.json`

---

## 🎯 OpenClaw 集成方式

### 1. CLI + JSON 模式

**特点**: 最简单，无需额外服务

```python
import subprocess
import json

def call_clawguard(command: str) -> dict:
    """调用 ClawGuard CLI"""
    cmd = f"python3 clawguard.py {command} --json --yes"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# 使用示例
price = call_clawguard("price BTC")
print(f"BTC价格: ${price['price']}")

account = call_clawguard("account")
print(f"余额: {account['balances']}")

analysis = call_clawguard("analyze ETH --interval 1h")
print(f"信号: {analysis['overall_signal']}")
```

**支持的命令**:
```bash
# 市场数据
python3 clawguard.py price BTC --json
python3 clawguard.py prices BTC,ETH,BNB --json

# 账户管理
python3 clawguard.py account --json
python3 clawguard.py balance BTC --json

# 技术分析
python3 clawguard.py analyze BTC --interval 1h --json

# 合约交易
python3 clawguard.py futures account --json
python3 clawguard.py futures position --json
python3 clawguard.py futures leverage BTCUSDT 5 --json --yes

# 策略管理
python3 clawguard.py grid create BTCUSDT --lower 65000 --upper 70000 --grids 10 --amount 1000 --json --yes
python3 clawguard.py grid status --json
```

---

### 2. HTTP API 模式

**特点**: RESTful API，支持远程调用

#### 启动服务器

```bash
# 默认启动 (0.0.0.0:5000)
python3 openclaw_server.py

# 指定端口
python3 openclaw_server.py --port 8080

# 调试模式
python3 openclaw_server.py --debug
```

#### Python 客户端

```python
import requests

class ClawGuardAPI:
    def __init__(self, base_url="http://localhost:5000/api/v1"):
        self.base_url = base_url

    def get_price(self, symbol: str):
        """获取价格"""
        response = requests.get(f"{self.base_url}/price/{symbol}")
        return response.json()

    def get_account(self):
        """获取账户信息"""
        response = requests.get(f"{self.base_url}/account")
        return response.json()

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float):
        """下单"""
        data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        response = requests.post(f"{self.base_url}/order", json=data)
        return response.json()

    def analyze(self, symbol: str, interval: str = "1h"):
        """技术分析"""
        response = requests.get(
            f"{self.base_url}/analysis/summary/{symbol}",
            params={"interval": interval}
        )
        return response.json()

# 使用示例
api = ClawGuardAPI()

# 查询价格
price = api.get_price("BTCUSDT")
print(f"BTC价格: ${price['data']['price']}")

# 技术分析
analysis = api.analyze("BTCUSDT", "1h")
print(f"信号: {analysis['data']['overall_signal']}")
```

#### cURL 示例

```bash
# 查询价格
curl http://localhost:5000/api/v1/price/BTCUSDT

# 查询账户
curl http://localhost:5000/api/v1/account

# 技术分析
curl "http://localhost:5000/api/v1/analysis/summary/BTCUSDT?interval=1h"

# 下单
curl -X POST http://localhost:5000/api/v1/order \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","side":"BUY","type":"MARKET","quantity":0.001}'
```

---

### 3. Skills 模块

**特点**: OpenClaw 标准接口

```python
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

# 下单
result = spot_skill.execute('place_order', {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001
})
print(f"订单: {result['data']}")

# 市场分析 Skill
analysis_skill = MarketAnalysisSkill()

# 分析趋势
result = analysis_skill.execute('analyze_trend', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(f"趋势: {result['data']['trend']}")

# 获取建议
result = analysis_skill.execute('get_recommendation', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(f"建议: {result['data']['recommendation']}")
```

**可用的 Skills**:

| Skill | 动作 | 说明 |
|-------|------|------|
| binance_spot | query_price | 查询价格 |
| binance_spot | query_account | 查询账户 |
| binance_spot | query_balance | 查询余额 |
| binance_spot | place_order | 下单 |
| binance_spot | query_orders | 查询订单 |
| binance_spot | cancel_order | 取消订单 |
| market_analysis | analyze_indicators | 分析指标 |
| market_analysis | analyze_trend | 分析趋势 |
| market_analysis | get_recommendation | 获取建议 |

---

### 4. 自然语言接口 (NLP)

**特点**: 理解自然语言指令

```python
from src.nlp.command_parser import NLPCommandParser

parser = NLPCommandParser()

# 解析自然语言指令
commands = [
    "BTC现在多少钱？",
    "用1000 USDT买入BTC",
    "在70000价格卖出0.1个BTC",
    "帮我分析一下ETH的走势",
    "我的账户余额是多少？",
    "启动BTC的网格交易",
    "把BTC的杠杆调到5倍"
]

for text in commands:
    result = parser.parse(text)

    print(f"指令: {text}")
    print(f"意图: {result['intent']}")
    print(f"实体: {result['entities']}")
    print(f"命令: {result['command']}")

    # 如果需要确认
    if result.get('confirmation_required'):
        print(f"确认: {result['confirmation_message']}")

    print()
```

**支持的意图**:

| 意图 | 示例 |
|-----|------|
| query_price | "BTC现在多少钱？" |
| query_account | "我的账户余额是多少？" |
| place_buy_order | "用1000 USDT买入BTC" |
| place_sell_order | "卖出0.1个BTC" |
| analyze_trend | "帮我分析一下ETH的走势" |
| strategy_start | "启动BTC的网格交易" |
| set_leverage | "把BTC的杠杆调到5倍" |

---

### 5. Python API

**特点**: 最灵活，完全控制

```python
from src.api.binance_client import BinanceClient
from src.api.binance_futures_client import BinanceFuturesClient
from src.analysis.indicators import TechnicalIndicators
from src.strategies.ma_crossover_strategy import MACrossoverStrategy
from src.backtest.backtest_engine import BacktestEngine

# 现货交易
client = BinanceClient()

# 查询价格
ticker = client.get_ticker_price('BTCUSDT')
print(f"BTC价格: {ticker['price']}")

# 查询账户
account = client.get_account_info()
for balance in account['balances']:
    if float(balance['free']) > 0:
        print(f"{balance['asset']}: {balance['free']}")

# 下单
order = client.place_market_order('BTCUSDT', 'BUY', 0.001)
print(f"订单ID: {order['orderId']}")

# 合约交易
futures = BinanceFuturesClient()

# 查询持仓
positions = futures.get_position_risk('BTCUSDT')
for pos in positions:
    if float(pos['positionAmt']) != 0:
        print(f"持仓: {pos['positionAmt']}")

# 设置杠杆
futures.change_leverage('BTCUSDT', 5)

# 技术分析
indicators = TechnicalIndicators(client)
klines = indicators.get_klines('BTCUSDT', '1h', limit=100)

rsi = indicators.calculate_rsi(klines)
print(f"RSI: {rsi[-1]:.2f}")

macd = indicators.calculate_macd(klines)
print(f"MACD: {macd['macd'][-1]:.2f}")

# 交易策略
strategy = MACrossoverStrategy('BTCUSDT', fast_period=10, slow_period=30)
signal = strategy.generate_signal()
print(f"信号: {signal['signal']}")

# 回测
engine = BacktestEngine(initial_capital=10000)

def my_strategy(klines):
    if len(klines) < 30:
        return {'signal': 'HOLD'}
    # 策略逻辑
    return {'signal': 'BUY'}

performance = engine.run_backtest(klines, my_strategy)
print(f"收益率: {performance['total_return']:.2f}%")
```

---

## 🔧 配置验证

### 检查配置状态

```bash
# 运行配置验证
python3 -c "
from openclaw_configure import OpenClawConfigurator
configurator = OpenClawConfigurator()
validation = configurator._validate_configuration()
print('配置验证结果:')
for key, value in validation.items():
    status = '✅' if value else '❌'
    print(f'{status} {key}: {value}')
"
```

### 健康检查

```bash
# CLI 健康检查
python3 clawguard.py health --json

# API 健康检查
curl http://localhost:5000/health
```

---

## 📚 完整示例

### OpenClaw AI 助手集成

```python
from src.nlp.command_parser import NLPCommandParser
from src.api.binance_client import BinanceClient
from skills.binance_spot.handler import BinanceSpotSkill

class OpenClawAssistant:
    """OpenClaw AI 交易助手"""

    def __init__(self):
        self.nlp = NLPCommandParser()
        self.client = BinanceClient()
        self.skill = BinanceSpotSkill()

    def process_command(self, user_input: str) -> str:
        """处理用户指令"""
        # 解析自然语言
        parsed = self.nlp.parse(user_input)

        if parsed['confidence'] < 0.7:
            return "抱歉，我没有理解您的意思。"

        # 如果需要确认
        if parsed.get('confirmation_required'):
            # 这里应该请求用户确认
            confirmed = True  # 假设用户确认

            if not confirmed:
                return "操作已取消。"

        # 执行命令
        try:
            result = self._execute_command(parsed)
            return self._generate_response(parsed['intent'], result)
        except Exception as e:
            return f"执行失败: {str(e)}"

    def _execute_command(self, parsed: dict) -> dict:
        """执行命令"""
        command = parsed['command']
        action = command['action']
        params = command['params']

        # 使用 Skills 执行
        if action == 'query_price':
            return self.skill.execute('query_price', params)
        elif action == 'place_order':
            return self.skill.execute('place_order', params)
        # ... 其他动作

    def _generate_response(self, intent: str, result: dict) -> str:
        """生成响应"""
        if not result['success']:
            return f"操作失败: {result.get('error')}"

        if intent == 'query_price':
            data = result['data']
            return f"{data['symbol']} 当前价格: ${data['price']}"
        elif intent == 'place_buy_order':
            return f"买入成功！订单ID: {result['data']['orderId']}"
        # ... 其他响应

# 使用
assistant = OpenClawAssistant()

# 处理用户指令
response = assistant.process_command("BTC现在多少钱？")
print(response)  # "BTCUSDT 当前价格: $68234.50"

response = assistant.process_command("用1000 USDT买入BTC")
print(response)  # "买入成功！订单ID: 123456789"
```

---

## 🚨 故障排查

### 问题1: 配置文件不存在

```bash
# 解决方案: 运行自动配置
python3 openclaw_configure.py
```

### 问题2: API 密钥未配置

```bash
# 解决方案: 设置环境变量
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"

# 或使用交互式配置
python3 openclaw_configure.py --interactive
```

### 问题3: 代理连接失败

```bash
# 检查代理配置
python3 clawguard.py health --json

# 测试代理
curl --proxy http://127.0.0.1:7890 https://api.binance.com/api/v3/ping
```

### 问题4: HTTP API 无法访问

```bash
# 检查服务器是否运行
curl http://localhost:5000/health

# 如果未运行，启动服务器
python3 openclaw_server.py
```

---

## 📖 更多资源

- **API 文档**: `docs/API.md`
- **策略文档**: `docs/STRATEGIES.md`
- **集成指南**: `docs/INTEGRATION.md`
- **测试指南**: `tests/README.md`

---

## 🎯 快速命令参考

```bash
# 配置
python3 openclaw_configure.py                    # 自动配置
python3 openclaw_configure.py --interactive      # 交互式配置

# 启动服务
python3 openclaw_server.py                       # 启动 HTTP API
python3 openclaw_server.py --port 8080           # 指定端口
python3 openclaw_server.py --configure           # 配置并启动

# 示例
python3 openclaw_examples.py                     # 运行集成示例

# CLI 使用
python3 clawguard.py price BTC --json            # 查询价格
python3 clawguard.py account --json              # 查询账户
python3 clawguard.py analyze ETH --json          # 技术分析
python3 clawguard.py futures position --json     # 合约持仓
```

---

<div align="center">

**ClawGuard-BNB × OpenClaw**

*无缝集成，开箱即用*

</div>
