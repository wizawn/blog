# 币安 API 配置与权限指南

**更新时间**: 2026-03-08 12:35 UTC
**API Key**: `5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M`

---

## ✅ 权限测试结果

| API 类型 | 端点 | 状态 | 说明 |
|----------|------|------|------|
| **现货账户** | `api.binance.com` | ✅ 成功 | BTC: 0.00000804 |
| **组合保证金 UM** | `papi.binance.com` | ✅ 成功 | 账户已开通，余额待充值 |
| **普通 UM 合约** | `fapi.binance.com` | ❌ 失败 | 需要单独启用 |
| **统一账户** | `dapi.binance.com` | ❌ 失败 | 需要启用统一账户权限 |

---

## 🔑 API Key 权限配置

### 当前状态
- ✅ 现货交易 - 已启用
- ✅ 现货提现 - 已启用
- ✅ 现货充值 - 已启用
- ✅ 组合保证金 - 已开通（测试成功）
- ❌ 普通合约交易 - 需手动启用
- ❌ 统一账户 - 需勾选

---

## 📊 组合保证金账户说明

### 什么是组合保证金？

组合保证金（Portfolio Margin）是币安为专业交易者设计的高级账户模式：

**优势**:
- 📈 跨资产保证金共享
- 💰 更高的资金利用率
- 🔄 统一风险管理
- 🎯 支持 UM+CM+杠杆混合交易

**要求**:
- 需要申请开通
- 有最低资金要求
- 需要完成风险测评

### 如何充值到组合保证金账户？

1. 登录币安官网
2. 进入 **钱包** → **资金划转**
3. 选择 **划转到组合保证金账户**
4. 从现货/合约账户划转资金

---

## 🔧 API 端点说明

### 1. 现货 API
```
Base URL: https://api.binance.com
```
**用途**: 现货交易、现货账户查询

### 2. 普通合约 API
```
Base URL: https://fapi.binance.com  (UM 合约)
Base URL: https://dapi.binance.com  (CM 合约)
```
**用途**: 标准合约交易

### 3. 组合保证金 API ⭐
```
Base URL: https://papi.binance.com
```
**用途**: 组合保证金账户交易（推荐）

**接口示例**:
- UM 下单：`POST /papi/v1/um/order`
- UM 账户：`GET /papi/v1/um/account`
- CM 下单：`POST /papi/v1/cm/order`
- 杠杆下单：`POST /papi/v1/margin/order`

---

## 💡 权限问题排查

### 错误代码 -2015
```json
{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action"}
```

**原因**:
1. API Key 未启用对应权限
2. IP 地址被限制
3. 账户类型不匹配

**解决方案**:
1. 登录币安 → API 管理
2. 编辑对应 API Key
3. 勾选需要的权限
4. 保存并完成验证

### 统一账户权限

**启用步骤**:
1. 登录币安官网
2. 进入 **API 管理**
3. 找到 API Key
4. 勾选 **"统一账户"** 选项
5. 保存

**注意**: 勾选"统一账户"后，API Key 可以同时访问：
- 现货账户
- 合约账户（UM+CM）
- 杠杆账户
- 组合保证金账户

---

## 🚀 推荐配置

### 方案 A: 使用组合保证金 API（推荐）

**优点**:
- ✅ 单一账户管理所有资产
- ✅ 更高的资金效率
- ✅ 统一的风险管理
- ✅ 支持混合策略

**配置**:
```python
API_KEY = 'your_key'
API_SECRET = 'your_secret'
BASE_URL = 'https://papi.binance.com'
```

### 方案 B: 使用普通 API

**优点**:
- ✅ 简单直接
- ✅ 文档丰富

**配置**:
```python
# 现货
SPOT_URL = 'https://api.binance.com'

# UM 合约
UM_URL = 'https://fapi.binance.com'

# CM 合约
CM_URL = 'https://dapi.binance.com'
```

---

## 📝 使用示例

### 组合保证金 UM 下单
```python
import requests
import hmac
import hashlib
import time

API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
API_SECRET = 'hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt'

def sign(params, secret):
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# UM 市价买入
timestamp = int(time.time() * 1000)
params = {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001,
    'timestamp': timestamp,
    'recvWindow': 5000
}
params['signature'] = sign(params, API_SECRET)

headers = {'X-MBX-APIKEY': API_KEY}
response = requests.post(
    'https://papi.binance.com/papi/v1/um/order',
    headers=headers,
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)

print(response.json())
```

### 查询组合保证金账户
```python
timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp, 'recvWindow': 5000}
params['signature'] = sign(params, API_SECRET)

response = requests.get(
    'https://papi.binance.com/papi/v1/um/account',
    headers=headers,
    params=params,
    proxies=proxies
)

account = response.json()
print(f"总权益：{account['totalWalletBalance']} USDT")
print(f"可用余额：{account['availableBalance']} USDT")
```

---

## ⚠️ 注意事项

### 1. 代理配置
币安 API 需要代理访问（中国大陆地区）：
```python
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}
```

### 2. 时间同步
服务器时间偏差不能超过 5 秒：
```bash
# Linux/Mac
sudo ntpdate pool.ntp.org

# Windows
w32tm /resync
```

### 3. 签名顺序
参数必须按字母顺序排序：
```python
# 正确
params = {'a': 1, 'b': 2, 'c': 3}
query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])

# 错误 - 可能导致签名验证失败
```

### 4. 接收窗口
默认 5000ms，可根据网络情况调整：
```python
params['recvWindow'] = 10000  # 10 秒
```

---

## 🔗 相关文档

- [组合保证金官方文档](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin)
- [统一账户文档](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/general-info)
- [API 错误代码](https://developers.binance.com/docs/zh-CN/derivatives/portfolio-margin/error-code)

---

*最后更新：2026-03-08 12:35 UTC*
