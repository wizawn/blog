# 币安组合保证金 (Portfolio Margin) API 知识库

**学习时间**: 2026-03-08 12:15 UTC
**文档来源**: https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/trade

---

## 📋 概述

组合保证金账户（Portfolio Margin）是币安为专业交易者设计的高级账户模式，支持：
- **UM 合约** (USDⓈ-M Futures) - USDT 本位合约
- **CM 合约** (COIN-M Futures) - 币本位合约
- **杠杆账户** (Margin Account) - 现货杠杆交易

---

## 🔑 API 基础信息

### 基础端点
```
https://papi.binance.com
```

### 认证方式
- **Header**: `X-MBX-APIKEY: <your_api_key>`
- **签名**: HMAC SHA256
- **时间戳**: `timestamp` (毫秒级)
- **接收窗口**: `recvWindow` (默认 5000ms)

### 签名算法
```python
import hmac
import hashlib

query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
signature = hmac.new(
    api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

---

## 📊 UM 合约交易 (USDⓈ-M)

### 1. 下单 (POST /papi/v1/um/order)

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对，如 BTCUSDT |
| side | ENUM | YES | 方向：BUY/SELL |
| positionSide | ENUM | NO | 持仓方向：BOTH/LONG/SHORT |
| type | ENUM | YES | 类型：LIMIT/MARKET |
| timeInForce | ENUM | NO | 有效方式：GTC/IOC/FOK/GTD |
| quantity | DECIMAL | NO | 下单数量 |
| price | DECIMAL | NO | 委托价格 |
| reduceOnly | STRING | NO | 只减仓：true/false |
| newClientOrderId | STRING | NO | 自定义订单 ID |
| newOrderRespType | ENUM | NO | 响应类型：ACK/RESULT |
| priceMatch | ENUM | NO | 价格匹配：OPPONENT/QUEUE 等 |
| selfTradePreventionMode | ENUM | NO | 自成交防护 |
| goodTillDate | LONG | NO | GTD 自动取消时间 |
| recvWindow | LONG | NO | 接收窗口 |
| timestamp | LONG | YES | 时间戳 |

**订单类型参数要求**:
- **LIMIT**: timeInForce, quantity, price
- **MARKET**: quantity

**响应示例**:
```json
{
  "clientOrderId": "testOrder",
  "cumQty": "0",
  "cumQuote": "0",
  "executedQty": "0",
  "orderId": 22542179,
  "avgPrice": "0.00000",
  "origQty": "10",
  "price": "0",
  "reduceOnly": false,
  "side": "BUY",
  "positionSide": "SHORT",
  "status": "NEW",
  "symbol": "BTCUSDT",
  "timeInForce": "GTD",
  "type": "MARKET",
  "selfTradePreventionMode": "NONE",
  "goodTillDate": 1693207680000,
  "updateTime": 1566818724722,
  "priceMatch": "NONE"
}
```

### 2. 撤销订单 (DELETE /papi/v1/um/order)

**参数**:
- symbol (必填)
- orderId 或 origClientOrderId (二选一)

### 3. 查询订单 (GET /papi/v1/um/order)

**参数**:
- symbol (必填)
- orderId 或 origClientOrderId (二选一)

### 4. 查询当前挂单 (GET /papi/v1/um/openOrders)

**参数**:
- symbol (可选)

### 5. 撤销全部订单 (DELETE /papi/v1/um/allOpenOrders)

**参数**:
- symbol (必填)

### 6. 查询账户 (GET /papi/v1/um/account)

**响应**:
```json
{
  "totalWalletBalance": "1000.00000000",
  "availableBalance": "800.00000000",
  "totalUnrealizedPnl": "50.00000000",
  "assets": [...]
}
```

### 7. 查询持仓 (GET /papi/v1/um/positionRisk)

**响应**:
```json
[
  {
    "symbol": "BTCUSDT",
    "positionAmt": "0.1",
    "entryPrice": "65000.0",
    "markPrice": "66000.0",
    "unRealizedProfit": "100.0",
    "positionSide": "BOTH"
  }
]
```

---

## 🪙 CM 合约交易 (COIN-M)

### 1. 下单 (POST /papi/v1/cm/order)

**参数与 UM 类似，区别**:
- symbol: 如 BTCUSD_PERP
- quantity: 以"张"为单位

### 2. 撤销订单 (DELETE /papi/v1/cm/order)

### 3. 查询订单 (GET /papi/v1/cm/order)

### 4. 查询当前挂单 (GET /papi/v1/cm/openOrders)

### 5. 撤销全部订单 (DELETE /papi/v1/cm/allOpenOrders)

### 6. 查询账户 (GET /papi/v1/cm/account)

### 7. 查询持仓 (GET /papi/v1/cm/positionRisk)

---

## 💰 杠杆账户交易 (Margin)

### 1. 下单 (POST /papi/v1/margin/order)

**参数**:
- symbol (必填)
- side (必填): BUY/SELL
- type (必填): LIMIT/MARKET
- quantity (可选)
- price (可选)
- timeInForce (可选): GTC/IOC/FOK
- isIsolated (可选): 是否逐仓杠杆

### 2. 借贷 (POST /papi/v1/margin/loan)

**参数**:
- asset (必填): 币种，如 USDT
- amount (必填): 借入数量
- isIsolated (可选): 是否逐仓
- symbol (逐仓必填): 交易对

### 3. 归还借贷 (POST /papi/v1/margin/repay)

**参数**:
- asset (必填)
- amount (必填)
- isIsolated (可选)
- symbol (逐仓必填)

### 4. 查询账户 (GET /papi/v1/margin/account)

**响应**:
```json
{
  "totalAssetOfBtc": "1.5",
  "totalLiabilityOfBtc": "0.5",
  "totalNetAssetOfBtc": "1.0",
  "assets": [...]
}
```

### 5. 查询订单 (GET /papi/v1/margin/order)

### 6. 撤销订单 (DELETE /papi/v1/margin/order)

---

## 🔧 特殊参数说明

### positionSide (持仓方向)
- **BOTH**: 单向持仓模式（默认）
- **LONG**: 双向持仓 - 多头
- **SHORT**: 双向持仓 - 空头

### timeInForce (有效方式)
- **GTC**: Good Till Cancel - 撤单前有效
- **IOC**: Immediate Or Cancel - 立即成交或取消
- **FOK**: Fill Or Kill - 全部成交或取消
- **GTD**: Good Till Date - 指定时间前有效

### priceMatch (价格匹配)
- **OPPONENT**: 对手价
- **OPPONENT_5**: 对手价第 5 档
- **OPPONENT_10**: 对手价第 10 档
- **QUEUE**: 排队价
- **QUEUE_5**: 排队第 5 档
- 不能与 price 同时传

### selfTradePreventionMode (自成交防护)
- **NONE**: 无防护（默认）
- **EXPIRE_TAKER**: 取消吃单方
- **EXPIRE_MAKER**: 取消挂单方
- **EXPIRE_BOTH**: 双方都取消

---

## ⚠️ 注意事项

### 1. 权限要求
- API Key 需启用"组合保证金"权限
- 需在币安后台申请开通组合保证金账户

### 2. 请求权重
- 下单接口权重：1
- 查询接口权重：1-10 不等
- 注意 API 限流

### 3. 时间戳
- 服务器时间偏差不能超过 5 秒
- 建议使用 NTP 同步时间

### 4. 签名安全
- API Secret 不能泄露
- 请求参数按字母顺序排序
- 签名使用 UTF-8 编码

### 5. 错误代码
- **-2015**: Invalid API-key, IP, or permissions
- **-1001**: 内部错误
- **-1013**: 订单被拒绝
- **-1021**: 时间戳偏差

---

## 📝 使用示例

### UM 市价买入
```python
client.um_market_buy('BTCUSDT', quantity=0.001)
```

### UM 限价卖出
```python
client.um_limit_sell('BTCUSDT', quantity=0.001, price=70000)
```

### CM 市价买入
```python
client.cm_market_buy('BTCUSD_PERP', quantity=10)
```

### 杠杆借贷
```python
client.margin_borrow('USDT', amount=1000)
```

### 查询持仓
```python
positions = client.um_position()
for pos in positions:
    if float(pos['positionAmt']) != 0:
        print(f"{pos['symbol']}: {pos['positionAmt']}")
```

---

## 🔗 相关文档

- [组合保证金概述](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/general-info)
- [错误代码](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/error-code)
- [UM 条件单](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/trade/New-UM-Conditional-Order)
- [CM 条件单](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/trade/New-CM-Conditional-Order)

---

*最后更新：2026-03-08 12:15 UTC*
