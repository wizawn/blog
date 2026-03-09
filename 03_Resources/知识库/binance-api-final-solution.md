# 币安 API 最终解决方案

**时间**: 2026-03-08 15:10 UTC
**根据币安官方客服解答排查**

---

## 🔍 官方客服 4 点排查结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 1. API 密钥错误 | ⚠️ 待验证 | 密钥格式正确（64 位），但可能已失效 |
| 2. API 密钥不在头部 | ✅ 已解决 | X-MBX-APIKEY 已正确设置 |
| 3. 基本 URL 错误 | ✅ 已解决 | 使用正确的端点 |
| 4. 权限不足 | ❌ **核心问题** | API Key 没有执行请求的权限 |

---

## ❌ 测试结果

### 现货账户测试
```
状态码：401
错误：{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action."}
```

### 统一账户 U 本位合约
```
状态码：404
错误：端点不存在
```

### 经典合约账户
```
状态码：401
错误：权限不足 - 统一账户模式下不能使用经典接口
```

---

## 🎯 核心问题分析

### 问题 1: -2015 权限错误

**错误代码**: `-2015 Invalid API-key, IP, or permissions for action`

**根据官方客服和测试结果，可能原因**:

1. **API Key 已失效或被禁用** ⭐ 最可能
2. **API Secret 不正确** - 签名验证失败
3. **统一账户权限未正确配置**
4. **IP 被风控限制**

### 问题 2: 统一账户接口 404

**说明**: `/api/v3/um/account` 端点返回 404

**可能原因**:
- 统一账户 API 路径不正确
- 需要使用其他端点

---

## ✅ 最终解决方案

### 方案 A: 重新创建 API Key（强烈推荐）

**这是最彻底的解决方案**：

#### 步骤 1: 删除旧 API Key

1. 登录币安官网
2. 访问：https://www.binance.com/zh-CN/my/settings/api-management
3. 找到 API Key: `5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M`
4. 点击 **删除**
5. 确认删除

#### 步骤 2: 创建新 API Key

1. 点击 **创建 API**
2. 填写 API 名称（如：ClawGuard-BNB-20260308）
3. 完成安全验证
4. **重要**: 立即复制并保存：
   - API Key（公钥）
   - Secret Key（私钥，只显示一次！）

#### 步骤 3: 配置权限

**经典账户模式**（推荐，简单直接）:

- [x] ✅ 启用现货及杠杆交易
- [x] ✅ 启用合约交易
- [x] ✅ 允许读取
- [ ] ❌ 允许提现（可选，不需要可不开）
- [ ] ❌ 开启统一账户交易（不要勾选！）

**统一账户模式**（高级用户）:

- [x] ✅ 启用现货及杠杆交易
- [x] ✅ 启用合约交易
- [x] ✅ 开启统一账户交易
- [x] ✅ 允许读取

#### 步骤 4: 配置 IP 白名单

1. 选择 **只访问受信任的 IP**
2. 添加当前代理 IP: `66.90.98.146`
3. 或者添加多个 IP（用逗号分隔）
4. 保存

#### 步骤 5: 等待生效

- ⏳ 等待 **15-30 分钟** 让权限生效
- ⏳ 期间不要频繁测试

#### 步骤 6: 更新配置

```bash
# 编辑配置文件
nano /root/.openclaw/workspace/ClawGuard-BNB/.env

# 更新 API Key 和 Secret
BINANCE_API_KEY=新的 API Key
BINANCE_API_SECRET=新的 Secret Key
```

#### 步骤 7: 测试

```python
# 测试现货账户
python3 << 'PYEOF'
import requests, hmac, hashlib, time

API_KEY = '新的 API Key'
API_SECRET = '新的 Secret Key'

timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp}
query = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

r = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)
print(r.json())
PYEOF
```

---

### 方案 B: 验证当前 API Secret

**如果不想重新创建 API Key**:

#### 步骤 1: 重新复制 Secret Key

1. 登录币安官网
2. API 管理 → 找到 API Key
3. 点击 **查看 Secret Key**
4. 完成安全验证
5. **完整复制** Secret Key（64 个字符，不要遗漏）
6. 确保没有空格、换行符

#### 步骤 2: 更新配置

```bash
nano /root/.openclaw/workspace/ClawGuard-BNB/.env

# 更新为新的 Secret Key
BINANCE_API_SECRET=新复制的 Secret Key
```

#### 步骤 3: 测试

```python
python3 << 'PYEOF'
import requests, hmac, hashlib, time

API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
API_SECRET = '新复制的 Secret Key'

timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp}
query = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

r = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)

if r.status_code == 200:
    print("✅ API Secret 正确！")
    print(r.json())
elif r.status_code == 400:
    error = r.json()
    if error.get('code') == -1022:
        print("❌ 签名无效 - API Secret 仍然错误")
        print("请再次确认 Secret Key 是否正确")
    else:
        print(f"❌ 错误：{error}")
else:
    print(f"❌ 错误：{r.text}")
PYEOF
```

---

### 方案 C: 联系币安客服

**如果以上都无效**:

1. 访问：https://www.binance.com/zh-CN/support
2. 点击 **在线咨询** 或 **提交工单**
3. 提供以下信息：
   ```
   问题描述：API 调用返回 -2015 错误
   API Key: 5L2YGXjf***nt64K（提供前 8 位和后 8 位）
   错误代码：-2015
   错误信息：Invalid API-key, IP, or permissions for action
   已尝试的解决方案:
   1. 验证 API Key 格式（64 位）
   2. 验证请求头设置（X-MBX-APIKEY）
   3. 验证基本 URL（api.binance.com）
   4. 重新复制 API Secret
   5. 等待权限生效 15-30 分钟
   
   请求：请帮助检查 API Key 状态和权限配置
   ```

---

## 📝 正确的 API 调用示例

### 现货账户查询

```python
import requests
import hmac
import hashlib
import time

API_KEY = '你的 API Key'
API_SECRET = '你的 Secret Key'

def sign(params, secret):
    sorted_params = sorted(params.items())
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

timestamp = int(time.time() * 1000)
params = {
    'timestamp': timestamp,
    'recvWindow': 60000
}
params['signature'] = sign(params, API_SECRET)

response = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)

print(response.json())
```

### 经典合约账户查询

```python
# 使用 fapi.binance.com（经典账户）
response = requests.get(
    'https://fapi.binance.com/fapi/v2/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies=proxies
)
```

### 统一账户合约查询

```python
# 使用 api.binance.com（统一账户）
# 注意：统一账户的接口路径可能不同
response = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies=proxies
)
```

---

## ⚠️ 常见错误代码

| 错误代码 | 错误信息 | 解决方案 |
|----------|----------|----------|
| **-1022** | Signature for this request is not valid | API Secret 错误，重新复制 |
| **-2015** | Invalid API-key, IP, or permissions | API Key 权限不足，检查权限配置 |
| **-1021** | Timestamp for this request is ahead of the server's time | 时间戳偏差，校准系统时间 |
| **-1003** | Too much request weight used | API 限流，降低请求频率 |
| **404** | Not Found | 端点 URL 错误，检查路径 |

---

## 🎯 推荐方案

**基于当前情况，强烈推荐方案 A（重新创建 API Key）**：

1. ✅ 彻底解决权限问题
2. ✅ 避免 Secret Key 泄露风险
3. ✅ 可以重新配置所有权限
4. ✅ 只需等待 15-30 分钟

**步骤总结**:
1. 删除旧 API Key
2. 创建新 API Key
3. 勾选所有需要的权限
4. 配置 IP 白名单
5. 等待 15-30 分钟
6. 更新配置
7. 测试

---

*最后更新：2026-03-08 15:10 UTC*
