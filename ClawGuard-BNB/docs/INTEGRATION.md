# ClawGuard-BNB AI 集成指南

## 概述

ClawGuard-BNB 专为 AI 助手（如 OpenClaw）设计，提供 **5种集成方式**，支持自然语言交互，让 AI 能够轻松调用量化交易功能。

---

## 集成方式对比

| 方式 | 难度 | 灵活性 | 性能 | 适用场景 |
|-----|------|--------|------|---------|
| CLI + JSON | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 快速集成、脚本调用 |
| HTTP API | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 远程调用、Web应用 |
| Skills模块 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | OpenClaw标准集成 |
| NLP接口 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 自然语言交互 |
| Python API | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 深度定制、复杂逻辑 |

---

## 方式1: CLI + JSON 输出

### 特点
- ✅ 最简单的集成方式
- ✅ 无需额外服务
- ✅ 适合脚本和自动化
- ✅ 所有命令支持 `--json` 参数

### 使用方法

```bash
# 基础语法
python3 clawguard.py <command> [options] --json

# 跳过交互确认
python3 clawguard.py <command> [options] --json --yes
```

### 示例

#### 查询价格
```bash
python3 clawguard.py price BTC --json
```

**输出**:
```json
{
  "symbol": "BTCUSDT",
  "price": 68234.50,
  "change_percent": 2.34,
  "high": 69100.00,
  "low": 66500.00,
  "volume": 28456.78,
  "timestamp": 1709856000
}
```

#### 查询账户
```bash
python3 clawguard.py account --json
```

**输出**:
```json
{
  "can_trade": true,
  "can_withdraw": false,
  "balances": [
    {
      "asset": "BTC",
      "free": "0.12345678",
      "locked": "0.00000000",
      "total": "0.12345678"
    }
  ],
  "total_value_usdt": 8456.78
}
```

#### 技术分析
```bash
python3 clawguard.py analyze BTC --interval 1h --json
```

**输出**:
```json
{
  "symbol": "BTCUSDT",
  "current_price": 68234.50,
  "indicators": {
    "rsi": {"value": 65.23, "signal": "neutral"},
    "macd": {"trend": "bullish", "signal": "buy"},
    "bollinger_bands": {"position": "above_middle"},
    "ma": {"position": "above", "signal": "bullish"}
  },
  "overall_signal": "BUY",
  "confidence": 0.78
}
```

#### 创建网格策略
```bash
python3 clawguard.py grid create BTCUSDT \
  --lower 65000 \
  --upper 70000 \
  --grids 10 \
  --amount 1000 \
  --json \
  --yes
```

**输出**:
```json
{
  "success": true,
  "strategy_id": "grid_BTCUSDT_1709856000",
  "symbol": "BTCUSDT",
  "lower_price": 65000,
  "upper_price": 70000,
  "grid_count": 10,
  "investment": 1000,
  "orders_placed": 10,
  "message": "网格策略已启动"
}
```

### AI 集成示例

```python
import subprocess
import json

def call_clawguard(command: str) -> dict:
    """调用 ClawGuard CLI 并返回 JSON 结果"""
    cmd = f"python3 clawguard.py {command} --json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# 使用示例
price_data = call_clawguard("price BTC")
print(f"BTC价格: ${price_data['price']}")

account_data = call_clawguard("account")
print(f"账户余额: {account_data['balances']}")

analysis = call_clawguard("analyze ETH --interval 1h")
print(f"ETH信号: {analysis['overall_signal']}")
```

---

## 方式2: HTTP API 服务器

### 特点
- ✅ RESTful API 标准
- ✅ 支持远程调用
- ✅ 适合 Web 应用
- ✅ 20+ API 端点

### 启动服务器

```bash
# 默认端口 5000
python3 -m src.api.http_server

# 指定端口
python3 -m src.api.http_server --port 8080

# 后台运行
nohup python3 -m src.api.http_server > api.log 2>&1 &
```

### API 端点

#### 市场数据
```
GET  /api/v1/price/<symbol>           # 单个价格
GET  /api/v1/prices?symbols=BTC,ETH   # 多个价格
GET  /api/v1/klines/<symbol>          # K线数据
GET  /api/v1/depth/<symbol>           # 市场深度
GET  /api/v1/ticker/<symbol>          # 24h行情
```

#### 账户管理
```
GET  /api/v1/account                  # 账户信息
GET  /api/v1/balance/<asset>          # 资产余额
GET  /api/v1/status                   # 系统状态
```

#### 交易
```
POST   /api/v1/order                  # 下单
GET    /api/v1/orders                 # 查询订单
DELETE /api/v1/order/<order_id>       # 取消订单
```

#### 技术分析
```
GET  /api/v1/analysis/indicators/<symbol>  # 技术指标
GET  /api/v1/analysis/trend/<symbol>       # 趋势分析
GET  /api/v1/analysis/summary/<symbol>     # 综合分析
```

### AI 集成示例

```python
import requests

class ClawGuardAPI:
    def __init__(self, base_url="http://localhost:5000/api/v1"):
        self.base_url = base_url

    def get_price(self, symbol: str) -> dict:
        """获取价格"""
        response = requests.get(f"{self.base_url}/price/{symbol}")
        return response.json()

    def get_account(self) -> dict:
        """获取账户信息"""
        response = requests.get(f"{self.base_url}/account")
        return response.json()

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> dict:
        """下单"""
        data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        if price:
            data["price"] = price

        response = requests.post(f"{self.base_url}/order", json=data)
        return response.json()

    def analyze(self, symbol: str, interval: str = "1h") -> dict:
        """技术分析"""
        response = requests.get(f"{self.base_url}/analysis/summary/{symbol}?interval={interval}")
        return response.json()

# 使用示例
api = ClawGuardAPI()

# 查询价格
price = api.get_price("BTCUSDT")
print(f"BTC价格: ${price['data']['price']}")

# 技术分析
analysis = api.analyze("BTCUSDT", "1h")
print(f"信号: {analysis['data']['overall_signal']}")

# 下单
order = api.place_order("BTCUSDT", "BUY", "MARKET", 0.001)
print(f"订单ID: {order['data']['orderId']}")
```

---

## 方式3: Skills 模块

### 特点
- ✅ OpenClaw 标准接口
- ✅ 结构化调用
- ✅ 易于维护
- ✅ 支持多个 Skills

### 可用 Skills

| Skill | 功能 | 动作数量 |
|-------|------|---------|
| binance_spot | 现货交易 | 6个 |
| binance_futures | 合约交易 | 5个 |
| market_analysis | 市场分析 | 3个 |
| risk_management | 风险管理 | 4个 |

### 使用方法

```python
from skills.binance_spot.handler import BinanceSpotSkill

# 创建 Skill 实例
skill = BinanceSpotSkill()

# 执行动作
result = skill.execute(action, params)
```

### binance_spot Skill

#### 动作列表
- `query_price` - 查询价格
- `query_account` - 查询账户
- `query_balance` - 查询余额
- `place_order` - 下单
- `query_orders` - 查询订单
- `cancel_order` - 取消订单

#### 示例

```python
from skills.binance_spot.handler import BinanceSpotSkill

skill = BinanceSpotSkill()

# 查询价格
result = skill.execute('query_price', {'symbol': 'BTCUSDT'})
print(result)
# {'success': True, 'data': {'symbol': 'BTCUSDT', 'price': '68234.50', ...}}

# 查询账户
result = skill.execute('query_account', {})
print(result)
# {'success': True, 'data': {'balances': [...], ...}}

# 下单
result = skill.execute('place_order', {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001
})
print(result)
# {'success': True, 'data': {'orderId': 123456789, ...}}
```

### market_analysis Skill

```python
from skills.market_analysis.handler import MarketAnalysisSkill

skill = MarketAnalysisSkill()

# 分析技术指标
result = skill.execute('analyze_indicators', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(result['data']['indicators'])

# 分析趋势
result = skill.execute('analyze_trend', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(f"趋势: {result['data']['trend']}")

# 获取建议
result = skill.execute('get_recommendation', {
    'symbol': 'BTCUSDT',
    'interval': '1h'
})
print(f"建议: {result['data']['recommendation']}")
```

---

## 方式4: 自然语言接口 (NLP)

### 特点
- ✅ 理解自然语言指令
- ✅ 最友好的交互方式
- ✅ 支持17种意图
- ✅ 自动实体提取

### 支持的意图类型

#### 查询类
- 查询价格: "BTC现在多少钱？"
- 查询账户: "我的账户余额是多少？"
- 查询持仓: "我现在有什么持仓？"
- 技术分析: "帮我分析一下BTC的走势"

#### 交易类
- 市价买入: "用1000 USDT买入BTC"
- 限价卖出: "在70000价格卖出0.1个BTC"
- 止损设置: "给我的BTC持仓设置止损"

#### 策略类
- 启动策略: "��动BTC的网格交易"
- 停止策略: "停止所有策略"
- 查询策略: "我的策略运行得怎么样？"

#### 配置类
- 设置杠杆: "把BTC的杠杆调到5倍"
- 配置代理: "设置代理服务器"
- 风控设置: "调整风控参数"

### 使用方法

```python
from src.nlp.command_parser import NLPCommandParser

# 创建解析器
parser = NLPCommandParser()

# 解析自然语言
result = parser.parse("用1000 USDT买入BTC")

print(result)
# {
#   'intent': 'place_buy_order',
#   'entities': {
#     'symbol': 'BTCUSDT',
#     'amount': 1000,
#     'type': 'market'
#   },
#   'command': {
#     'action': 'place_order',
#     'params': {
#       'symbol': 'BTCUSDT',
#       'side': 'BUY',
#       'type': 'MARKET',
#       'quoteOrderQty': 1000
#     }
#   },
#   'confidence': 0.95,
#   'confirmation_required': True,
#   'confirmation_message': '确认用 1000 USDT 市价买入 BTC？'
# }
```

### AI 集成示例

```python
from src.nlp.command_parser import NLPCommandParser
from src.api.binance_client import BinanceClient

class AITradingAssistant:
    def __init__(self):
        self.parser = NLPCommandParser()
        self.client = BinanceClient()

    def process_command(self, user_input: str) -> str:
        """处理用户的自然语言指令"""
        # 解析指令
        parsed = self.parser.parse(user_input)

        if parsed['confidence'] < 0.7:
            return "抱歉，我没有理解您的意思，请重新表述。"

        # 如果需要确认
        if parsed.get('confirmation_required'):
            # 这里应该向用户请求确认
            confirmed = self.ask_user_confirmation(parsed['confirmation_message'])
            if not confirmed:
                return "操作已取消。"

        # 执行命令
        try:
            result = self.execute_command(parsed['command'])
            return self.generate_response(parsed['intent'], result)
        except Exception as e:
            return f"执行失败: {str(e)}"

    def execute_command(self, command: dict) -> dict:
        """执行命令"""
        action = command['action']
        params = command['params']

        if action == 'query_price':
            return self.client.get_ticker_price(params['symbol'])
        elif action == 'place_order':
            return self.client.place_market_order(
                params['symbol'],
                params['side'],
                params.get('quantity') or params.get('quoteOrderQty')
            )
        # ... 其他动作

    def generate_response(self, intent: str, result: dict) -> str:
        """生成友好的响应"""
        if intent == 'query_price':
            return f"{result['symbol']} 当前价格: ${result['price']}"
        elif intent == 'place_buy_order':
            return f"买入成功！订单ID: {result['orderId']}"
        # ... 其他响应

# 使用示例
assistant = AITradingAssistant()

# 处理用户指令
response = assistant.process_command("BTC现在多少钱？")
print(response)  # "BTCUSDT 当前价格: $68234.50"

response = assistant.process_command("用1000 USDT买入BTC")
print(response)  # "买入成功！订单ID: 123456789"

response = assistant.process_command("帮我分析一下ETH的走势")
print(response)  # "ETH 当前趋势: 看涨，建议买入"
```

### 上下文管理

NLP 接口支持多轮对话，可以记住之前的上下文：

```python
parser = NLPCommandParser()

# 第一轮
result1 = parser.parse("查询BTC价格")
# entities: {'symbol': 'BTCUSDT'}

# 第二轮（省略币种）
result2 = parser.parse("帮我分析一下")
# entities: {'symbol': 'BTCUSDT'}  # 自动从上下文获取

# 第三轮
result3 = parser.parse("买入1000 USDT")
# entities: {'symbol': 'BTCUSDT', 'amount': 1000}  # 自动填充币种
```

---

## 方式5: Python API

### 特点
- ✅ 最灵活的集成方式
- ✅ 完全控制
- ✅ 适合复杂逻辑
- ✅ 直接访问所有功能

### 核心模块

#### 现货交易
```python
from src.api.binance_client import BinanceClient

client = BinanceClient()

# 查询价格
ticker = client.get_ticker_price('BTCUSDT')
print(f"价格: {ticker['price']}")

# 查询账户
account = client.get_account_info()
for balance in account['balances']:
    if float(balance['free']) > 0:
        print(f"{balance['asset']}: {balance['free']}")

# 下单
order = client.place_market_order('BTCUSDT', 'BUY', 0.001)
print(f"订单ID: {order['orderId']}")

# 查询订单
orders = client.get_open_orders('BTCUSDT')
print(f"活跃订单: {len(orders)}")
```

#### 合约交易
```python
from src.api.binance_futures_client import BinanceFuturesClient

futures = BinanceFuturesClient()

# 查询合约账户
account = futures.get_account_info()
print(f"总余额: {account['totalWalletBalance']}")

# 查询持仓
positions = futures.get_position_risk('BTCUSDT')
for pos in positions:
    if float(pos['positionAmt']) != 0:
        print(f"持仓: {pos['positionAmt']}")
        print(f"未实现盈亏: {pos['unRealizedProfit']}")

# 设置杠杆
futures.change_leverage('BTCUSDT', 5)

# 下单
order = futures.place_order(
    symbol='BTCUSDT',
    side='BUY',
    order_type='LIMIT',
    quantity=0.001,
    price=68000
)
```

#### 技术分析
```python
from src.analysis.indicators import TechnicalIndicators

indicators = TechnicalIndicators()

# 获取K线
klines = indicators.get_klines('BTCUSDT', '1h', limit=100)

# 计算指标
rsi = indicators.calculate_rsi(klines, period=14)
print(f"RSI: {rsi[-1]:.2f}")

macd_data = indicators.calculate_macd(klines)
print(f"MACD: {macd_data['macd'][-1]:.2f}")

bb = indicators.calculate_bollinger_bands(klines, period=20)
print(f"布林带上轨: {bb['upper'][-1]:.2f}")

# 新增指标
atr = indicators.calculate_atr(klines, period=14)
print(f"ATR: {atr[-1]:.2f}")

kdj = indicators.calculate_kdj(klines)
print(f"KDJ: K={kdj['k'][-1]:.2f}, D={kdj['d'][-1]:.2f}, J={kdj['j'][-1]:.2f}")
```

#### 交易策略
```python
from src.strategies.ma_crossover_strategy import MACrossoverStrategy

# 创建策略
strategy = MACrossoverStrategy(
    symbol='BTCUSDT',
    fast_period=10,
    slow_period=30,
    interval='1h'
)

# 生成信号
signal = strategy.generate_signal()
print(f"信号: {signal['signal']}")
print(f"原因: {signal['reason']}")

# 执行交易
if signal['signal'] == 'BUY':
    result = strategy.execute_signal(signal, quantity=0.001)
    print(result)
```

#### 回测
```python
from src.backtest.backtest_engine import BacktestEngine

# 创建回测引擎
engine = BacktestEngine(initial_capital=10000, commission=0.001)

# 定义策略
def my_strategy(klines):
    if len(klines) < 30:
        return {'signal': 'HOLD'}

    closes = [k['close'] for k in klines]
    fast_ma = sum(closes[-10:]) / 10
    slow_ma = sum(closes[-30:]) / 30

    if fast_ma > slow_ma:
        return {'signal': 'BUY'}
    elif fast_ma < slow_ma:
        return {'signal': 'SELL'}
    return {'signal': 'HOLD'}

# 运行回测
performance = engine.run_backtest(klines, my_strategy)

# 查看结果
print(f"总收益率: {performance['total_return']:.2f}%")
print(f"胜率: {performance['win_rate']:.2f}%")
print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
```

---

## 完整示例: AI 交易助手

```python
from src.nlp.command_parser import NLPCommandParser
from src.api.binance_client import BinanceClient
from src.analysis.indicators import TechnicalIndicators
from src.strategies.ma_crossover_strategy import MACrossoverStrategy

class AITradingBot:
    def __init__(self):
        self.nlp = NLPCommandParser()
        self.client = BinanceClient()
        self.indicators = TechnicalIndicators(self.client)
        self.strategies = {}

    def process_natural_language(self, text: str) -> dict:
        """处理自然语言指令"""
        parsed = self.nlp.parse(text)

        if parsed['confidence'] < 0.7:
            return {'success': False, 'message': '无法理解指令'}

        intent = parsed['intent']

        # 路由到不同的处理函数
        if intent.startswith('query_'):
            return self.handle_query(parsed)
        elif intent.startswith('place_'):
            return self.handle_trade(parsed)
        elif intent.startswith('analyze_'):
            return self.handle_analysis(parsed)
        elif intent.startswith('strategy_'):
            return self.handle_strategy(parsed)

    def handle_query(self, parsed: dict) -> dict:
        """处理查询类指令"""
        intent = parsed['intent']
        entities = parsed['entities']

        if intent == 'query_price':
            ticker = self.client.get_ticker_price(entities['symbol'])
            return {
                'success': True,
                'message': f"{entities['symbol']} 价格: ${ticker['price']}",
                'data': ticker
            }

        elif intent == 'query_account':
            account = self.client.get_account_info()
            return {
                'success': True,
                'message': '账户信息已获取',
                'data': account
            }

    def handle_trade(self, parsed: dict) -> dict:
        """处理交易类指令"""
        command = parsed['command']
        params = command['params']

        # 风险检查
        if not self.check_risk(params):
            return {'success': False, 'message': '风险检查未通过'}

        # 执行交易
        order = self.client.place_market_order(
            params['symbol'],
            params['side'],
            params.get('quantity')
        )

        return {
            'success': True,
            'message': f"交易成功，订单ID: {order['orderId']}",
            'data': order
        }

    def handle_analysis(self, parsed: dict) -> dict:
        """处理分析类指令"""
        entities = parsed['entities']
        symbol = entities['symbol']
        interval = entities.get('interval', '1h')

        # 获取K线
        klines = self.indicators.get_klines(symbol, interval, limit=100)

        # 计算指标
        rsi = self.indicators.calculate_rsi(klines)[-1]
        macd_data = self.indicators.calculate_macd(klines)

        # 生成分析报告
        analysis = {
            'symbol': symbol,
            'rsi': rsi,
            'macd_trend': 'bullish' if macd_data['histogram'][-1] > 0 else 'bearish',
            'recommendation': 'BUY' if rsi < 70 and macd_data['histogram'][-1] > 0 else 'HOLD'
        }

        return {
            'success': True,
            'message': f"{symbol} 分析完成",
            'data': analysis
        }

    def handle_strategy(self, parsed: dict) -> dict:
        """处理策略类指令"""
        intent = parsed['intent']
        entities = parsed['entities']

        if intent == 'strategy_start':
            # 创建并启动策略
            strategy = MACrossoverStrategy(
                symbol=entities['symbol'],
                fast_period=10,
                slow_period=30
            )
            self.strategies[entities['symbol']] = strategy

            return {
                'success': True,
                'message': f"{entities['symbol']} 策略已启动"
            }

    def check_risk(self, params: dict) -> bool:
        """风险检查"""
        # 实现风险检查逻辑
        return True

# 使用示例
bot = AITradingBot()

# 自然语言交互
result = bot.process_natural_language("BTC现在多少钱？")
print(result['message'])

result = bot.process_natural_language("用1000 USDT买入BTC")
print(result['message'])

result = bot.process_natural_language("帮我分析一下ETH的走势")
print(result['message'])
```

---

## 最佳实践

### 1. 错误处理
```python
try:
    result = api.get_price("BTCUSDT")
    if result['success']:
        print(result['data'])
    else:
        print(f"错误: {result['error']}")
except Exception as e:
    print(f"异常: {str(e)}")
```

### 2. 重试机制
```python
import time

def retry_api_call(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 指数退避
```

### 3. 日志记录
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("开始执行交易")
logger.error("交易失败", exc_info=True)
```

### 4. 配置管理
```python
# 使用环境变量
import os

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
```

---

## 常见问题

### Q: 哪种集成方式最好？
A: 取决于需求：
- 快速集成 → CLI + JSON
- Web应用 → HTTP API
- OpenClaw → Skills
- 自然交互 → NLP
- 深度定制 → Python API

### Q: 如何处理API限流？
A: 使用内置的 RateLimiter，或添加请求间隔。

### Q: 支持异步调用吗？
A: HTTP API 和 Python API 都支持异步。

### Q: 如何保证安全？
A: 使用 HTTPS、API密钥加密、请求签名验证。

---

## 更新日志

### v3.0.0 (2024-03)
- ✅ 5种集成方式
- ✅ 自然语言接口
- ✅ 完整的 HTTP API
- ✅ Skills 模块
- ✅ JSON 输出模式

---

## 支持

如有问题，请查看完整文档或提交 Issue。
