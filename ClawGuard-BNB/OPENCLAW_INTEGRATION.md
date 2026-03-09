
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

# OpenClaw 集成指南

## 📍 项目位置

**主项目路径**: `/root/.openclaw/workspace/ClawGuard-BNB`
**备份路径**: `/root/.openclaw/workspace/ClawGuard-BNB2`

---

## 🎯 可调用的核心模块

### 1. 智能交易系统 ⭐

#### 趋势预测
```python
from src.prediction.trend_predictor import TrendPredictor

predictor = TrendPredictor()
result = predictor.predict_trend(
    symbol='BTCUSDT',
    interval='1h',
    periods=24
)
# 返回: {'current_price', 'predicted_price', 'confidence', 'trend'}
```

#### 事件分析
```python
from src.prediction.event_analyzer import EventAnalyzer

analyzer = EventAnalyzer()
events = analyzer.analyze_market_events(symbol='BTCUSDT')
# 返回: [{'type', 'severity', 'signal', 'description'}]
```

#### 自动交易引擎
```python
from src.prediction.auto_trading_engine import AutoTradingEngine

config = {
    'symbols': ['BTCUSDT'],
    'check_interval': 300,
    'min_confidence': 75,
    'position_size': 0.05,
    'stop_loss': 0.03,
    'take_profit': 0.05
}

engine = AutoTradingEngine(config)
engine.start()  # 启动自动交易
status = engine.get_status()  # 查看状态
engine.stop()  # 停止交易
```

### 2. 策略管理器

```python
from src.strategies.strategy_manager import StrategyManager

manager = StrategyManager()

# 创建网格策略
strategy_id = manager.create_strategy(
    strategy_type='grid',
    symbol='BTCUSDT',
    config={
        'lower_price': 40000,
        'upper_price': 50000,
        'grid_num': 10,
        'amount_per_grid': 100
    },
    auto_start=True
)

# 管理策略
manager.start_strategy(strategy_id)
manager.stop_strategy(strategy_id)
status = manager.get_strategy(strategy_id)
```

### 3. 统一交易客户端

```python
from src.trading.unified_client import UnifiedTradingClient

client = UnifiedTradingClient()

# 现货交易
order = client.place_spot_order(
    symbol='BTCUSDT',
    side='BUY',
    order_type='MARKET',
    quantity=0.001
)

# 合约交易
order = client.place_futures_order(
    symbol='BTCUSDT',
    side='BUY',
    order_type='LIMIT',
    quantity=0.01,
    price=45000,
    leverage=10
)

# 查询账户
balance = client.get_account_balance()
positions = client.get_positions()
```

### 4. 技术分析

```python
from src.analysis.indicators import TechnicalIndicators

indicators = TechnicalIndicators()

# 计算所有指标
result = indicators.calculate_all(
    symbol='BTCUSDT',
    interval='1h'
)
# 返回: RSI, MACD, 布林带, KDJ等21个指标

# 获取交易建议
signals = indicators.get_trading_signals(
    symbol='BTCUSDT',
    interval='1h'
)
```

### 5. 风控系统

```python
from src.risk.risk_control import RiskControlEngine

risk = RiskControlEngine()

# 交易前检查
allowed, reason = risk.pre_trade_check(
    symbol='BTCUSDT',
    side='BUY',
    amount=1000,
    account_balance=10000,
    current_price=45000,
    has_real_trade_permission=True
)

# 查看风控状态
stats = risk.get_risk_stats()
```

---

## 🌐 HTTP API 端点

### 启动API服务器
```bash
cd /root/.openclaw/workspace/ClawGuard-BNB
python3 openclaw_server.py
```

### 智能交易API
```bash
# 趋势预测
curl "http://localhost:5000/api/smart-trading/predict/trend?symbol=BTCUSDT&interval=1h&periods=24"

# 事件分析
curl "http://localhost:5000/api/smart-trading/analyze/events?symbol=BTCUSDT"

# 综合信号
curl "http://localhost:5000/api/smart-trading/smart-signal?symbol=BTCUSDT"

# 启动自动交易
curl -X POST http://localhost:5000/api/smart-trading/auto-trading/start \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTCUSDT"],
    "check_interval": 300,
    "min_confidence": 75
  }'

# 查看状态
curl http://localhost:5000/api/smart-trading/auto-trading/status
```

### 交易API
```bash
# 下单
curl -X POST http://localhost:5000/api/trading/spot/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 0.001
  }'

# 查询余额
curl http://localhost:5000/api/trading/balance

# 查询持仓
curl http://localhost:5000/api/trading/positions
```

### 策略API
```bash
# 创建策略
curl -X POST http://localhost:5000/api/strategy/create \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "grid",
    "symbol": "BTCUSDT",
    "config": {
      "lower_price": 40000,
      "upper_price": 50000,
      "grid_num": 10
    }
  }'

# 列出策略
curl http://localhost:5000/api/strategy/list
```

---

## 🔧 配置说明

### 环境变量
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
export BINANCE_TESTNET="true"  # 测试网
export FLASK_SECRET_KEY="your_flask_secret"
```

### 配置文件
位置: `~/.clawguard/config.yaml`

```yaml
api:
  binance:
    api_key: "your_key"
    secret_key: "your_secret"
    testnet: true

trading:
  mode: "paper"  # paper/testnet/live
  default_leverage: 10

risk:
  max_position_pct: 0.1
  max_total_position_pct: 0.8
  max_daily_loss_pct: 0.05
```

---

## 📊 返回数据格式

### 趋势预测
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "current_price": 45000.0,
    "predicted_price": 46500.0,
    "change_percent": 3.33,
    "trend": "UP",
    "confidence": 78.5,
    "action": "BUY",
    "timestamp": "2026-03-09T12:00:00Z"
  }
}
```

### 事件分析
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "events": [
      {
        "type": "volume_spike",
        "severity": "high",
        "signal": "bullish",
        "description": "交易量激增300%"
      }
    ],
    "action": "BUY",
    "confidence": 82.0
  }
}
```

---

## ⚠️ 注意事项

1. **API密钥安全**: 不要在代码中硬编码API密钥
2. **测试网优先**: 先在测试网充分测试
3. **风控限制**: 系统有内置风控，会自动拒绝高风险交易
4. **并发限制**: Binance API有频率限制
5. **错误处理**: 所有API调用都应该有异常处理

---

## 🔍 调试技巧

### 查看日志
```bash
tail -f ~/.clawguard/logs/clawguard.log
```

### 测试连接
```python
from src.api.binance_client import BinanceClient

client = BinanceClient()
info = client.get_account_info()
print(f"账户余额: {info}")
```

### 健康检查
```bash
curl http://localhost:5000/health
```

---

## 📞 OpenClaw调用示例

```python
# OpenClaw可以这样调用ClawGuard-BNB

import sys
sys.path.insert(0, '/root/.openclaw/workspace/ClawGuard-BNB')

from src.prediction.trend_predictor import TrendPredictor
from src.prediction.auto_trading_engine import AutoTradingEngine

# 获取趋势预测
predictor = TrendPredictor()
trend = predictor.predict_trend('BTCUSDT', '1h', 24)

# 启动自动交易
engine = AutoTradingEngine({
    'symbols': ['BTCUSDT'],
    'check_interval': 300,
    'min_confidence': 75
})
engine.start()
```

---

**更新时间**: 2026-03-09
**项目版本**: v4.0.1
**状态**: ✅ 生产就绪
