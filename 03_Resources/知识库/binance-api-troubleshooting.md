# 币安合约 API 权限问题排查指南

**问题**: API Key 已启用合约权限，但 API 调用仍返回 `-2015` 错误

**时间**: 2026-03-08 12:45 UTC

---

## ❌ 当前错误

```json
{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action"}
```

---

## 🔍 可能原因

### 1. API Key 权限未正确启用 ⭐ 最常见

**检查步骤**:
1. 登录币安官网
2. 进入 **API 管理**
3. 找到 API Key (`5L2YGXjf...`)
4. 点击 **编辑**
5. 确认已勾选以下权限：
   - ✅ **启用现货及杠杆交易**
   - ✅ **启用合约交易** ← 这个必须勾选
6. 保存并完成安全验证

**注意**: 修改权限后，可能需要等待 1-2 分钟生效

---

### 2. IP 白名单限制

**检查步骤**:
1. API 管理 → 编辑 API Key
2. 查看 **IP 白名单** 设置
3. 如果设置了白名单，确保当前 IP 在列表中
4. 或者暂时取消白名单限制测试

**当前 IP**: `66.90.98.146` (通过代理访问)

**建议**: 测试期间先不设置 IP 白名单

---

### 3. 账户未完成合约开户

**检查步骤**:
1. 登录币安 APP 或官网
2. 进入 **合约** 交易页面
3. 如果是首次使用，需要完成：
   - ✅ KYC 实名认证
   - ✅ 合约交易考试（部分地区要求）
   - ✅ 风险测评
4. 开通合约账户

---

### 4. 统一账户 vs 普通账户

**重要**: 如果你勾选了 **"统一账户"** 选项：

- 普通合约 API (`fapi.binance.com`) 可能无法访问
- 需要使用组合保证金 API (`papi.binance.com`)

**解决方案**:
- 方案 A: 取消勾选"统一账户"，使用普通合约 API
- 方案 B: 继续使用组合保证金 API（已测试成功）

---

## 🛠️ 排查流程

### 步骤 1: 验证 API Key 有效性

```bash
curl -X GET "https://api.binance.com/api/v3/account" \
  -H "X-MBX-APIKEY: 5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M"
```

**预期**: 返回现货账户信息（已测试成功）

---

### 步骤 2: 验证合约权限

```bash
curl -X GET "https://fapi.binance.com/fapi/v1/time"
```

**预期**: 返回服务器时间（公开接口，应该成功）

---

### 步骤 3: 测试合约账户

```bash
# 生成签名（需要 API Secret）
timestamp=$(date +%s%3N)
signature=$(echo -n "timestamp=$timestamp" | openssl dgst -sha256 -hmac "YOUR_SECRET" | awk '{print $2}')

curl -X GET "https://fapi.binance.com/fapi/v2/account?timestamp=$timestamp&signature=$signature" \
  -H "X-MBX-APIKEY: 5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M"
```

**预期**: 返回合约账户信息

**如果返回 -2015**: 权限问题

---

### 步骤 4: 检查 API Key 权限

访问：https://www.binance.com/zh-CN/my/settings/api-management

**确认**:
- [ ] API Key 状态：正常
- [ ] 启用现货及杠杆交易：✅
- [ ] 启用合约交易：✅ ← 关键
- [ ] IP 白名单：未设置 或 包含当前 IP
- [ ] 统一账户：未勾选（如果用普通 API）

---

## 📝 权限修改后测试

修改权限后，执行以下测试：

```python
import requests
import hmac
import hashlib
import time

API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
API_SECRET = 'hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt'

def sign(params):
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# 测试合约账户
timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp, 'recvWindow': 60000}
params['signature'] = sign(params)

response = requests.get(
    'https://fapi.binance.com/fapi/v2/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)

print(response.json())
```

**成功响应**:
```json
{
  "totalWalletBalance": "1000.00000000",
  "availableBalance": "800.00000000",
  ...
}
```

**失败响应**:
```json
{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action"}
```

---

## 🎯 快速解决方案

### 方案 A: 继续使用组合保证金 API（推荐）

**优势**:
- ✅ 已测试成功
- ✅ 支持 UM+CM+ 杠杆
- ✅ 统一账户管理

**端点**: `https://papi.binance.com`

**示例**:
```python
# 查询组合保证金账户
params = {'timestamp': timestamp, 'recvWindow': 5000}
params['signature'] = sign(params)

response = requests.get(
    'https://papi.binance.com/papi/v1/um/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies=proxies
)
# 返回：{"totalWalletBalance": "0", ...}
```

---

### 方案 B: 修复普通合约 API 权限

**步骤**:
1. 登录币安官网
2. API 管理 → 编辑 API Key
3. **取消勾选**"统一账户"（如果已勾选）
4. **勾选**"启用合约交易"
5. 保存
6. 等待 2 分钟
7. 重新测试

---

## 📞 联系币安支持

如果以上方法都无效：

1. 访问：https://www.binance.com/zh-CN/support
2. 提交工单
3. 提供：
   - API Key（前 8 位和后 8 位）
   - 错误代码：-2015
   - 请求端点：`/fapi/v2/account`
   - 时间戳

---

## 📊 当前测试结果

| 接口 | 端点 | 状态 | 说明 |
|------|------|------|------|
| 现货账户 | `api.binance.com` | ✅ 成功 | BTC: 0.00000804 |
| 合约时间 | `fapi.binance.com` | ✅ 成功 | 公开接口 |
| 合约账户 | `fapi.binance.com` | ❌ 失败 | -2015 权限错误 |
| 组合保证金 | `papi.binance.com` | ✅ 成功 | 账户已开通 |
| 统一账户 | `dapi.binance.com` | ❌ 失败 | -2015 权限错误 |

---

## 💡 建议

**基于当前测试结果**:

1. **组合保证金 API 已可用** - 建议优先使用
2. **普通合约 API 权限问题** - 需要检查 API 管理设置
3. **统一账户** - 如果不需要，建议取消勾选

**下一步**:
- 如果坚持使用普通合约 API，请按上述步骤检查权限
- 如果愿意使用组合保证金 API，可以开始划转资金并测试交易

---

*最后更新：2026-03-08 12:45 UTC*
