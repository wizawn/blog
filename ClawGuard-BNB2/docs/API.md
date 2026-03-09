# ClawGuard-BNB HTTP API 文档

## 概述

ClawGuard-BNB 提供完整的 RESTful HTTP API，支持市场数据查询、账户管理、交易执行和技术分析。

**基础URL**: `http://localhost:5000/api/v1`

**响应格式**: JSON

**认证方式**: API密钥通过配置文件管理

---

## 启动API服务器

```bash
# 方式1: 直接运行
python3 -m src.api.http_server

# 方式2: 指定端口
python3 -m src.api.http_server --port 8080

# 方式3: 后台运行
nohup python3 -m src.api.http_server > api.log 2>&1 &
```

服务器默认运行在 `http://localhost:5000`

---

## API端点

### 1. 市场数据 (Market)

#### 1.1 获取单个币种价格

```http
GET /api/v1/price/<symbol>
```

**参数**:
- `symbol` (路径参数): 交易对，如 `BTCUSDT`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "price": "68234.50",
    "priceChangePercent": "2.34"
  }
}
```

#### 1.2 获取多个币种价格

```http
GET /api/v1/prices?symbols=BTC,ETH,BNB
```

**参数**:
- `symbols` (查询参数): 逗号分隔的币种列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTCUSDT",
      "price": "68234.50",
      "priceChangePercent": "2.34"
    },
    {
      "symbol": "ETHUSDT",
      "price": "3456.78",
      "priceChangePercent": "1.23"
    }
  ]
}
```

#### 1.3 获取K线数据

```http
GET /api/v1/klines/<symbol>?interval=1h&limit=100
```

**参数**:
- `symbol` (路径参数): 交易对
- `interval` (查询参数): 时间间隔 (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`)
- `limit` (查询参数): 数据条数，默认100

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "open_time": 1709856000000,
      "open": 68000.00,
      "high": 68500.00,
      "low": 67800.00,
      "close": 68234.50,
      "volume": 1234.56,
      "close_time": 1709859599999
    }
  ]
}
```

#### 1.4 获取市场深度

```http
GET /api/v1/depth/<symbol>?limit=20
```

**参数**:
- `symbol` (路径参数): 交易对
- `limit` (查询参数): 深度档位，默认20

**响应示例**:
```json
{
  "success": true,
  "data": {
    "bids": [
      ["68200.00", "1.234"],
      ["68190.00", "2.345"]
    ],
    "asks": [
      ["68210.00", "1.456"],
      ["68220.00", "2.567"]
    ]
  }
}
```

#### 1.5 获取24小时行情

```http
GET /api/v1/ticker/<symbol>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "priceChange": "1567.89",
    "priceChangePercent": "2.34",
    "lastPrice": "68234.50",
    "highPrice": "69100.00",
    "lowPrice": "66500.00",
    "volume": "28456.78",
    "quoteVolume": "1945678901.23"
  }
}
```

---

### 2. 账户管理 (Account)

#### 2.1 获取账户信息

```http
GET /api/v1/account
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "canTrade": true,
    "canWithdraw": false,
    "canDeposit": true,
    "balances": [
      {
        "asset": "BTC",
        "free": "0.12345678",
        "locked": "0.00000000"
      },
      {
        "asset": "USDT",
        "free": "10000.00",
        "locked": "500.00"
      }
    ]
  }
}
```

#### 2.2 获取单个资产余额

```http
GET /api/v1/balance/<asset>
```

**参数**:
- `asset` (路径参数): 资产名称，如 `BTC`, `USDT`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "asset": "BTC",
    "free": "0.12345678",
    "locked": "0.00000000",
    "total": "0.12345678"
  }
}
```

#### 2.3 获取账户状态

```http
GET /api/v1/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "api_connected": true,
    "can_trade": true,
    "can_withdraw": false,
    "proxy_enabled": true,
    "proxy_status": "connected"
  }
}
```

---

### 3. 交易管理 (Trading)

#### 3.1 下单

```http
POST /api/v1/order
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 0.001
}
```

**请求参数**:
- `symbol` (必需): 交易对
- `side` (必需): 买卖方向 (`BUY`, `SELL`)
- `type` (必需): 订单类型 (`MARKET`, `LIMIT`)
- `quantity` (必需): 数量
- `price` (LIMIT订单必需): 价格
- `quoteOrderQty` (可选): 以报价资产计价的数量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orderId": 123456789,
    "symbol": "BTCUSDT",
    "status": "FILLED",
    "side": "BUY",
    "type": "MARKET",
    "executedQty": "0.001",
    "cummulativeQuoteQty": "68.23"
  }
}
```

#### 3.2 查询订单

```http
GET /api/v1/orders?symbol=BTCUSDT&limit=10
```

**参数**:
- `symbol` (查询参数): 交易对
- `limit` (查询参数): 返回数量，默认10

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "orderId": 123456789,
      "symbol": "BTCUSDT",
      "status": "FILLED",
      "side": "BUY",
      "type": "MARKET",
      "price": "68234.50",
      "origQty": "0.001",
      "executedQty": "0.001",
      "time": 1709856000000
    }
  ]
}
```

#### 3.3 取消订单

```http
DELETE /api/v1/order/<order_id>?symbol=BTCUSDT
```

**参数**:
- `order_id` (路径参数): 订单ID
- `symbol` (查询参数): 交易对

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orderId": 123456789,
    "status": "CANCELED"
  }
}
```

---

### 4. 技术分析 (Analysis)

#### 4.1 获取技术指标

```http
GET /api/v1/analysis/indicators/<symbol>?interval=1h
```

**参数**:
- `symbol` (路径参数): 交易对
- `interval` (查询参数): 时间间隔，默认 `1h`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "indicators": {
      "rsi": {
        "value": 65.23,
        "signal": "neutral",
        "description": "RSI在50-70之间，市场中性"
      },
      "macd": {
        "macd": 234.56,
        "signal": 189.23,
        "histogram": 45.33,
        "trend": "bullish",
        "description": "MACD金叉，看涨信号"
      },
      "bollinger_bands": {
        "upper": 69500.00,
        "middle": 68000.00,
        "lower": 66500.00,
        "position": "above_middle",
        "description": "价格在中轨上方，偏强"
      },
      "ma": {
        "ma20": 67800.00,
        "ma50": 66500.00,
        "position": "above",
        "description": "价格在均线上方，看涨"
      }
    }
  }
}
```

#### 4.2 获取趋势分析

```http
GET /api/v1/analysis/trend/<symbol>?interval=1h
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "trend": "bullish",
    "strength": "moderate",
    "confidence": 0.75,
    "description": "中等强度看涨趋势"
  }
}
```

#### 4.3 获取综合分析

```http
GET /api/v1/analysis/summary/<symbol>?interval=1h
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "current_price": 68234.50,
    "overall_signal": "BUY",
    "confidence": 0.78,
    "bullish_indicators": 3,
    "bearish_indicators": 1,
    "neutral_indicators": 1,
    "recommendation": "建议买入，多个指标显示看涨信号"
  }
}
```

---

## 错误处理

所有API端点在发生错误时返回以下格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

**HTTP状态码**:
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## 使用示例

### Python

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# 查询价格
response = requests.get(f"{BASE_URL}/price/BTCUSDT")
data = response.json()
print(f"BTC价格: {data['data']['price']}")

# 下单
order_data = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 0.001
}
response = requests.post(f"{BASE_URL}/order", json=order_data)
print(response.json())

# 技术分析
response = requests.get(f"{BASE_URL}/analysis/indicators/BTCUSDT?interval=1h")
indicators = response.json()['data']['indicators']
print(f"RSI: {indicators['rsi']['value']}")
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:5000/api/v1";

// 查询价格
fetch(`${BASE_URL}/price/BTCUSDT`)
  .then(res => res.json())
  .then(data => console.log(`BTC价格: ${data.data.price}`));

// 下单
fetch(`${BASE_URL}/order`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    quantity: 0.001
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### cURL

```bash
# 查询价格
curl http://localhost:5000/api/v1/price/BTCUSDT

# 下单
curl -X POST http://localhost:5000/api/v1/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 0.001
  }'

# 技术分析
curl "http://localhost:5000/api/v1/analysis/indicators/BTCUSDT?interval=1h"
```

---

## 速率限制

为了保护API服务器和币安API，建议：

- 价格查询: 最多 10次/秒
- 账户查询: 最多 5次/秒
- 下单操作: 最多 1次/秒
- 技术分析: 最多 2次/秒

---

## 最佳实践

1. **错误处理**: 始终检查 `success` 字段
2. **重试机制**: 对于网络错误，实现指数退避重试
3. **缓存**: 对于不常变化的数据（如K线），使用缓存
4. **批量请求**: 使用 `/api/v1/prices` 而不是多次调用 `/api/v1/price`
5. **WebSocket**: 对于实时数据，考虑使用WebSocket而不是轮询

---

## 安全建议

1. **HTTPS**: 生产环境使用HTTPS
2. **认证**: 添加API密钥认证
3. **限流**: 实现IP限流和用户限流
4. **CORS**: 配置适当的CORS策略
5. **日志**: 记录所有API请求用于审计

---

## 更新日志

### v3.0.0 (2024-03)
- ✅ 初始版本发布
- ✅ 支持市场数据、账户管理、交易、技术分析
- ✅ 15个API端点
- ✅ JSON响应格式
- ✅ 错误处理机制

---

## 支持

如有问题，请提交 Issue 或联系开发者。
