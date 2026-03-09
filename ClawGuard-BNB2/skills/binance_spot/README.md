# 币安现货交易 Skill

## 概述

币安现货交易 Skill 提供完整的现货交易功能，包括价格查询、账户管理、订单操作等。

## 功能列表

### 1. 查询价格 (query_price)
查询指定交易对的实时价格和24小时统计数据。

**参数：**
- `symbol` (string, 必需): 交易对符号，如 BTCUSDT

**示例：**
```python
result = skill.execute('query_price', {'symbol': 'BTC'})
```

**返回：**
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "price": 68500.50,
    "change_percent": 2.5,
    "high_24h": 69000.0,
    "low_24h": 67000.0,
    "volume_24h": 12345.67
  }
}
```

### 2. 查询账户 (query_account)
查询账户信息和所有资产余额。

**参数：** 无

**示例：**
```python
result = skill.execute('query_account', {})
```

**返回：**
```json
{
  "success": true,
  "data": {
    "account_type": "SPOT",
    "can_trade": true,
    "can_withdraw": true,
    "can_deposit": true,
    "balances": [
      {
        "asset": "USDT",
        "free": 1000.0,
        "locked": 0.0,
        "total": 1000.0
      }
    ]
  }
}
```

### 3. 查询余额 (query_balance)
查询指定资产或所有资产的余额。

**参数：**
- `asset` (string, 可选): 资产符号，如 USDT

**示例：**
```python
# 查询 USDT 余额
result = skill.execute('query_balance', {'asset': 'USDT'})

# 查询所有余额
result = skill.execute('query_balance', {})
```

### 4. 下单 (place_order)
下市价单或限价单。

**参数：**
- `symbol` (string, 必需): 交易对符号
- `side` (string, 必需): 买卖方向，BUY 或 SELL
- `type` (string, 必需): 订单类型，MARKET 或 LIMIT
- `quantity` (number, 必需): 数量
- `price` (number, LIMIT订单必需): 价格

**示例：**
```python
# 市价买入
result = skill.execute('place_order', {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001
})

# 限价卖出
result = skill.execute('place_order', {
    'symbol': 'BTCUSDT',
    'side': 'SELL',
    'type': 'LIMIT',
    'quantity': 0.001,
    'price': 70000.0
})
```

### 5. 查询订单 (query_orders)
查询指定交易对的订单历史。

**参数：**
- `symbol` (string, 必需): 交易对符号
- `limit` (number, 可选): 数量限制，默认 10

**示例：**
```python
result = skill.execute('query_orders', {
    'symbol': 'BTCUSDT',
    'limit': 5
})
```

### 6. 取消订单 (cancel_order)
取消指定订单。

**参数：**
- `symbol` (string, 必需): 交易对符号
- `order_id` (number, 必需): 订单ID

**示例：**
```python
result = skill.execute('cancel_order', {
    'symbol': 'BTCUSDT',
    'order_id': 12345678
})
```

## 使用方法

### Python 集成

```python
from skills.binance_spot.handler import create_skill

# 创建 Skill 实例
skill = create_skill()

# 查询价格
result = skill.execute('query_price', {'symbol': 'BTC'})
if result['success']:
    print(f"BTC 价格: ${result['data']['price']}")

# 查询账户
result = skill.execute('query_account', {})
if result['success']:
    for balance in result['data']['balances']:
        print(f"{balance['asset']}: {balance['total']}")

# 下单
result = skill.execute('place_order', {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001
})
if result['success']:
    print(f"订单ID: {result['data']['order_id']}")
```

### OpenClaw 集成

```python
from skills.base_skill import execute_skill, register_skill
from skills.binance_spot.handler import create_skill

# 注册 Skill
skill = create_skill()
register_skill(skill)

# 通过注册表执行
result = execute_skill('binance_spot', 'query_price', {'symbol': 'BTC'})
```

## 错误处理

所有方法都返回统一的响应格式：

**成功响应：**
```json
{
  "success": true,
  "data": { ... }
}
```

**错误响应：**
```json
{
  "success": false,
  "error": "错误信息"
}
```

## 注意事项

1. **API 密钥配置**：使用前需要配置币安 API 密钥
2. **风险控制**：下单前会经过风控系统检查
3. **网络代理**：支持通过代理访问币安 API
4. **测试网支持**：可以在测试网环境测试功能

## 更多信息

- 项目文档: https://github.com/wizawn/lobsterguard
- API 参考: 查看 skill.json 文件
