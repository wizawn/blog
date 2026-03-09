# 币安 API 权限排查报告

**时间**: 2026-03-08 14:35 UTC
**API Key**: `5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M`

---

## 🔍 测试结果

### API 接口测试

| 接口类型 | 端点 | 状态码 | 错误信息 | 分析 |
|----------|------|--------|----------|------|
| **时间接口** | `api.binance.com/api/v3/time` | ✅ 200 | 无 | 网络正常 |
| **PING 接口** | `api.binance.com/api/v3/ping` | ✅ 200 | 无 | 基础连接正常 |
| **现货账户** | `api.binance.com/api/v3/account` | ❌ 400 | -1022 签名无效 | **API Secret 可能错误** |
| **普通合约** | `fapi.binance.com/fapi/v2/account` | ❌ 401 | -2015 权限不足 | 权限问题 |
| **组合保证金** | `papi.binance.com/papi/v1/um/account` | ❌ 400 | -1022 签名无效 | **API Secret 可能错误** |

---

## ⚠️ 核心问题

### 问题 1: 签名验证失败 (-1022)

**错误信息**: `Signature for this request is not valid.`

**可能原因**:
1. ❌ **API Secret 错误** - 最可能
2. ❌ 时间戳偏差超过 5 分钟（已排除，时间差仅 1 秒）
3. ❌ 签名算法错误（已验证算法正确）
4. ❌ 参数排序问题（已按字母顺序排序）

**测试结果**:
```
时间戳：1772981297552
API Secret: hfZ0WFSBgY...g5MLXs1YSt
Secret 长度：64
查询字符串：recvWindow=60000&timestamp=1772981297552
签名：b51d7626d1e8a3e2158e1f64b5c62f22...
```

**结论**: API Secret 可能不正确或有误

---

### 问题 2: 合约权限不足 (-2015)

**错误信息**: `Invalid API-key, IP, or permissions for action`

**根据用户提供的排查指南，可能原因**:

1. ⚠️ **统一账户已启用** - 用户确认已勾选统一账户权限
2. ⚠️ **没有单独的"合约交易"勾选项** - 统一账户模式下不显示
3. ⚠️ **应该使用统一账户专属接口** - 不能使用 fapi/dapi

---

## ✅ 解决方案

### 方案 A: 验证 API Secret（最高优先级）

**步骤**:

1. **登录币安官网**
   - 访问：https://www.binance.com/zh-CN/my/settings/api-management

2. **找到 API Key**
   - 找到 `5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M`

3. **重新查看 Secret Key**
   - 点击"查看 Secret Key"
   - **完整复制** Secret Key（不要遗漏任何字符）
   - 确保没有空格、换行符

4. **更新配置**
   ```bash
   # 编辑配置文件
   nano /root/.openclaw/workspace/ClawGuard-BNB/.env
   
   # 更新 API Secret
   BINANCE_API_SECRET=正确的 Secret Key
   ```

5. **重新测试**
   ```python
   # 测试现货账户
   python3 -c "
   import requests, hmac, hashlib, time
   API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
   API_SECRET = '新的 Secret Key'
   timestamp = int(time.time() * 1000)
   params = {'timestamp': timestamp}
   query = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
   params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
   r = requests.get('https://api.binance.com/api/v3/account', headers={'X-MBX-APIKEY': API_KEY}, params=params)
   print(r.json())
   "
   ```

---

### 方案 B: 使用统一账户专属接口

**根据用户描述"已启用统一账户权限且已勾选所有能勾选的权限"**：

**统一账户应该使用的接口**:

| 业务 | 经典账户端点 | 统一账户端点 |
|------|-------------|-------------|
| 现货 | `api.binance.com` | `api.binance.com` |
| U 本位合约 | `fapi.binance.com` | `api.binance.com` (路径不同) |
| C 本位合约 | `dapi.binance.com` | `api.binance.com` (路径不同) |
| 杠杆 | `api.binance.com` | `api.binance.com` |

**统一账户接口路径**:
```
# 统一账户 U 本位合约
POST /api/v3/um/order  # 下单
GET /api/v3/um/account  # 账户信息
GET /api/v3/um/positionRisk  # 持仓查询

# 统一账户 C 本位合约
POST /api/v3/cm/order
GET /api/v3/cm/account

# 统一账户杠杆
POST /api/v3/margin/order
GET /api/v3/margin/account
```

**注意**: 统一账户**不使用** `fapi.binance.com` 和 `dapi.binance.com`！

---

### 方案 C: 重新创建 API Key（最后手段）

**如果以上都无效**:

1. **删除旧 API Key**
   - API 管理 → 删除 `5L2YGXjf...`

2. **创建新 API Key**
   - 创建新的 API Key
   - **立即勾选所有权限**:
     - ✅ 启用现货及杠杆交易
     - ✅ 启用合约交易（如果有此选项）
     - ✅ 开启统一账户交易（如果用统一账户）
     - ✅ 允许读取
     - ✅ 允许提现（如果需要）

3. **设置 IP 白名单**
   - 添加当前 IP: `66.90.98.146` (代理出口 IP)
   - 或者暂时不设置（测试用）

4. **等待 15 分钟**
   - 权限修改需要 5-15 分钟生效

5. **重新测试**

---

## 📝 当前配置

### 测试代码

```python
import requests
import hmac
import hashlib
import time

API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
API_SECRET = 'hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt'
PROXY = 'http://127.0.0.1:7890'

def sign(params, secret):
    sorted_params = sorted(params.items())
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# 测试现货账户
timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp, 'recvWindow': 60000}
params['signature'] = sign(params, API_SECRET)

response = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': PROXY, 'https': PROXY}
)

print(response.json())
```

**预期结果**:
- ✅ 成功：返回账户信息
- ❌ -1022：签名无效 → API Secret 错误
- ❌ -1021：时间戳偏差 → 校准时间
- ❌ -2015：权限不足 → 检查权限配置

---

## 🎯 下一步行动

**按优先级执行**:

1. **立即**: 重新核对并复制 API Secret Key
2. **然后**: 更新配置文件中的 Secret
3. **测试**: 运行测试代码验证现货 API
4. **如果成功**: 测试统一账户合约接口
5. **如果失败**: 重新创建 API Key

---

## 📞 联系币安客服

**如果以上都无效**:

1. 访问：https://www.binance.com/zh-CN/support
2. 提交工单
3. 提供信息:
   - API Key: `5L2YGXjf***nt64K`
   - 错误代码：-1022, -2015
   - 问题描述：签名验证失败，权限不足
   - 已尝试的解决方案

---

*最后更新：2026-03-08 14:35 UTC*
