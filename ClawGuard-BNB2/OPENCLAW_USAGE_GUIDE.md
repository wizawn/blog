# ClawGuard-BNB - OpenClaw 使用指南

## 🎯 设计理念

ClawGuard-BNB 专为 OpenClaw 设计，实现**零手动操作**：

- ✅ OpenClaw 自动初始化
- ✅ OpenClaw 自动配置
- ✅ OpenClaw 控制所有功能
- ✅ 用户只需上传文件和提供 API 密钥

---

## 🚀 OpenClaw 使用流程

### 步骤 1: 上传项目

将整个 `ClawGuard-BNB` 目录上传到 OpenClaw workspace。

### 步骤 2: 自动初始化

OpenClaw 执行一键初始化：

```bash
python3 openclaw_init.py
```

这个脚本会自动完成：
- ✅ 检查 Python 版本
- ✅ 安装所有依赖
- ✅ 自动配置系统
- ✅ 验证系统状态

**无需任何手动操作！**

### 步骤 3: 提供 API 密钥（可选）

如果需要实盘交易，OpenClaw 可以通过环境变量提供：

```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
```

或者通过配置文件：

```bash
python3 openclaw_configure.py --api-key "your_key" --api-secret "your_secret"
```

**如果不提供，系统自动使用模拟盘模式。**

### 步骤 4: 使用系统

OpenClaw 可以通过 5 种方式使用系统：

#### 方式 1: CLI + JSON（最简单）

```bash
# 查询价格
python3 clawguard.py price BTC --json

# 查询账户
python3 clawguard.py account --json

# 技术分析
python3 clawguard.py analyze ETH --interval 1h --json

# 所有命令都支持 --json 和 --yes 参数
```

#### 方式 2: HTTP API（推荐）

```bash
# OpenClaw 启动 API 服务器
python3 openclaw_server.py &

# 然后调用 API
curl http://localhost:5000/api/v1/price/BTCUSDT
curl http://localhost:5000/api/v1/account
```

#### 方式 3: Skills 模块

```python
# 现货交易
from skills.binance_spot.handler import BinanceSpotSkill
skill = BinanceSpotSkill()
result = skill.execute('query_price', {'symbol': 'BTCUSDT'})

# 市场分析
from skills.market_analysis.handler import MarketAnalysisSkill
skill = MarketAnalysisSkill()
result = skill.execute('analyze', {'symbol': 'BTCUSDT'})

# Web 管理（由 OpenClaw 控制）
from skills.web_management.handler import WebManagementSkill
skill = WebManagementSkill()
result = skill.execute('start', {})  # 启动 Web 界面
```

#### 方式 4: 自然语言（最智能）

```python
from src.nlp.command_parser import NLPCommandParser

parser = NLPCommandParser()

# OpenClaw 可以理解这些中文指令
commands = [
    "BTC现在多少钱？",
    "用1000 USDT买入BTC",
    "帮我分析一下ETH的走势",
    "我的账户余额是多少？",
    "启动BTC的网格交易"
]

for text in commands:
    result = parser.parse(text)
    # OpenClaw 根据解析结果执行相应操作
```

#### 方式 5: Web 界面（由 OpenClaw 控制）

OpenClaw 通过 API 或 Skills 启动 Web 界面：

```python
# 方式 A: 通过 HTTP API
import requests
requests.post('http://localhost:5000/api/v1/web/start')

# 方式 B: 通过 Skills
from skills.web_management.handler import execute_skill
result = execute_skill('start', {})

# Web 界面将在 http://localhost:8080 启动
# 用户可以通过浏览器访问
```

---

## 🔧 OpenClaw 控制的功能

### 1. 交易模式切换

OpenClaw 可以随时切换交易模式：

```python
from src.trading.trading_mode_manager import TradingModeManager, TradingMode

manager = TradingModeManager()

# 切换到模拟盘
manager.set_mode(TradingMode.PAPER)

# 切换到测试网
manager.set_mode(TradingMode.TESTNET)

# 切换到实盘（需要 API 密钥）
manager.set_mode(TradingMode.LIVE)
```

### 2. Web 界面管理

OpenClaw 完全控制 Web 界面的启动和停止：

```python
from skills.web_management.handler import execute_skill

# 启动 Web 界面
result = execute_skill('start', {})
# 返回: {'success': True, 'url': 'http://localhost:8080'}

# 检查状态
result = execute_skill('status', {})
# 返回: {'success': True, 'status': 'running'}
```

### 3. 策略管理

OpenClaw 可以创建、启动、停止策略：

```bash
# 创建网格策略
python3 clawguard.py grid create BTCUSDT --lower 65000 --upper 70000 --grids 20 --amount 1000 --json --yes

# 查询策略状态
python3 clawguard.py grid status --json

# 停止策略
python3 clawguard.py grid stop --json --yes
```

### 4. 配置管理

OpenClaw 可以动态修改配置：

```python
from src.config.config_manager import ConfigManager

config = ConfigManager()

# 修改风控配置
config.set('risk.max_order_value', 5000)
config.set('risk.max_daily_loss', 500)
config.save()

# 修改代理配置
config.set('proxy.enabled', True)
config.set('proxy.host', '127.0.0.1')
config.set('proxy.port', 7890)
config.save()
```

---

## 📊 数据更新机制

### 不使用独立的 WebSocket

根据您的要求，系统**不使用独立的推送通道**：

- ❌ 不使用 WebSocket 推送
- ❌ 不使用 Server-Sent Events
- ✅ 使用 OpenClaw 的通知机制
- ✅ Web 界面通过轮询更新数据

### 前端数据更新

Web 界面通过定时轮询获取数据：

```javascript
// 每 5 秒更新一次价格
setInterval(() => {
  fetch('/api/dashboard/prices')
    .then(res => res.json())
    .then(data => updatePrices(data))
}, 5000)

// 每 10 秒更新一次账户
setInterval(() => {
  fetch('/api/dashboard/overview')
    .then(res => res.json())
    .then(data => updateAccount(data))
}, 10000)
```

### OpenClaw 通知

OpenClaw 可以通过自己的通道推送通知：

```python
# OpenClaw 监控价格变化
while True:
    price = get_price('BTCUSDT')
    if price_changed_significantly(price):
        openclaw.notify(f"BTC 价格变化: {price}")
    time.sleep(5)
```

---

## 🎯 最佳实践

### 1. 初始化检查

OpenClaw 在使用前应该检查系统状态：

```python
from openclaw_validate import OpenClawValidator

validator = OpenClawValidator()
result = validator.validate_all()

if result['ready']:
    print("✅ 系统就绪")
else:
    print("⚠️  系统未完全就绪")
    print(f"错误: {result['errors']}")
```

### 2. 错误处理

所有 API 调用都应该处理错误：

```python
try:
    result = skill.execute('query_price', {'symbol': 'BTCUSDT'})
    if result['success']:
        price = result['data']['price']
    else:
        openclaw.notify(f"错误: {result['error']}")
except Exception as e:
    openclaw.notify(f"异常: {str(e)}")
```

### 3. 日志记录

系统自动记录所有操作：

```python
# 日志文件位置
~/.clawguard/clawguard.log

# OpenClaw 可以读取日志
with open(os.path.expanduser('~/.clawguard/clawguard.log')) as f:
    logs = f.readlines()
```

---

## 🔐 安全建议

### 1. API 密钥保护

- ✅ 使用环境变量
- ✅ 加密存储在 `~/.clawguard/secrets.enc`
- ❌ 不要硬编码在代码中

### 2. 默认使用模拟盘

- ✅ 未提供 API 密钥时自动使用模拟盘
- ✅ 模拟盘无需真实 API 连接
- ✅ 安全练习和测试

### 3. 风控保护

- ✅ 所有交易都经过风控检查
- ✅ 可配置的风控参数
- ✅ 自动拒绝超限订单

---

## 📚 完整示例

### OpenClaw 自动化工作流

```python
#!/usr/bin/env python3
"""
OpenClaw 自动化交易工作流示例
"""

import subprocess
import time
from skills.binance_spot.handler import BinanceSpotSkill
from skills.web_management.handler import execute_skill as web_skill
from src.nlp.command_parser import NLPCommandParser

# 1. 初始化系统
print("初始化系统...")
subprocess.run(['python3', 'openclaw_init.py'])

# 2. 启动 HTTP API 服务器
print("启动 API 服务器...")
subprocess.Popen(['python3', 'openclaw_server.py'])
time.sleep(2)

# 3. 启动 Web 界面（可选）
print("启动 Web 界面...")
result = web_skill('start', {})
if result['success']:
    print(f"Web 界面: {result['url']}")

# 4. 使用 Skills 查询价格
print("查询价格...")
skill = BinanceSpotSkill()
result = skill.execute('query_price', {'symbol': 'BTCUSDT'})
if result['success']:
    print(f"BTC 价格: {result['data']['price']}")

# 5. 使用 NLP 理解用户指令
print("处理自然语言指令...")
parser = NLPCommandParser()
result = parser.parse("帮我分析一下BTC的走势")
print(f"意图: {result['intent']}")
print(f"命令: {result['command']}")

# 6. 执行命令
if result['success']:
    # OpenClaw 根据解析结果执行相应操作
    pass

print("✅ 工作流完成")
```

---

## 🎉 总结

ClawGuard-BNB 为 OpenClaw 提供：

- ✅ **零手动操作** - 一键初始化
- ✅ **完全控制** - OpenClaw 控制所有功能
- ✅ **多种接口** - CLI、API、Skills、NLP、Web
- ✅ **智能理解** - 自然语言处理
- ✅ **安全可靠** - 完善的风控和加密
- ✅ **灵活部署** - 模拟盘/测试网/实盘

**OpenClaw 只需一行命令即可开始使用**：

```bash
python3 openclaw_init.py
```

之后的所有操作都由 OpenClaw 自动完成！
