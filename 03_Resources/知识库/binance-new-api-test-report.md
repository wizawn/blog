# 新 API Key 测试报告

**时间**: 2026-03-08 15:25 UTC
**API Key**: `8PGspkk...Ld8K`

---

## 🧪 测试结果

| 测试项 | 状态 | 错误信息 | 分析 |
|--------|------|----------|------|
| **时间接口** | ✅ 成功 | 无 | 网络正常，时间差 0.65 秒 |
| **现货账户** | ❌ 失败 | -1022 签名无效 | **API Secret 可能错误** |
| **合约账户** | ❌ 失败 | -2015 权限不足 | 权限问题 |

---

## ⚠️ 核心问题

### 签名验证失败 (-1022)

**错误**: `Signature for this request is not valid.`

**Secret Key 验证**:
```
Secret: FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q
长度：64 ✅
格式：正确 ✅
```

**可能原因**:
1. ❌ **Secret Key 复制时包含不可见字符**（空格、换行符）
2. ❌ **Secret Key 已失效或被重置**
3. ❌ **API Key 和 Secret Key 不匹配**

---

## ✅ 解决方案

### 立即行动：重新复制 Secret Key

**步骤**:

1. **登录币安官网**
   - https://www.binance.com/zh-CN/my/settings/api-management

2. **找到 API Key**
   - 找到：`8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K`

3. **重新查看 Secret Key**
   - 点击"查看 Secret Key"
   - 完成安全验证
   - **仔细复制**（不要多选或少选字符）

4. **验证 Secret Key**
   ```bash
   # 在终端执行
   echo "FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q" | wc -c
   # 应该输出：65（64 个字符 + 1 个换行符）
   ```

5. **更新配置**
   ```bash
   nano /root/.openclaw/workspace/ClawGuard-BNB/.env
   
   # 更新为正确的 Secret Key
   BINANCE_API_SECRET=正确的 Secret Key
   ```

6. **重新测试**

---

## 📝 测试命令

```python
import requests
import hmac
import hashlib
import time

API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
API_SECRET = '正确的 Secret Key'

timestamp = int(time.time() * 1000)
params = {'timestamp': timestamp}
query = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

response = requests.get(
    'https://api.binance.com/api/v3/account',
    headers={'X-MBX-APIKEY': API_KEY},
    params=params,
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)

if response.status_code == 200:
    print("✅ 成功！API Secret 正确")
    print(response.json())
else:
    print(f"❌ 失败：{response.json()}")
```

---

## 🎯 如果仍然失败

**最后手段**: 删除并重新创建 API Key

1. 删除当前 API Key
2. 创建全新的 API Key
3. 立即复制并保存 API Key 和 Secret Key
4. 配置权限
5. 等待 15-30 分钟
6. 测试

---

*最后更新：2026-03-08 15:25 UTC*
