# 币安 API 最终配置方案

**更新时间**: 2026-03-08 12:55 UTC
**API Key**: `5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M`

---

## 🎯 当前状态

### 已测试接口

| API 类型 | 端点 | 状态 | 说明 |
|----------|------|------|------|
| **现货账户** | `api.binance.com` | ✅ 成功 | BTC: 0.00000804 |
| **组合保证金** | `papi.binance.com` | ✅ 成功 | 账户已开通 |
| **普通合约** | `fapi.binance.com` | ❌ 失败 | -2015 权限错误 |

### 权限配置

- ✅ 现货交易 - 已启用
- ✅ 现货提现 - 已启用
- ✅ 现货充值 - 已启用
- ✅ 统一账户 - 已取消勾选
- ⚠️ 合约交易 - 显示已启用，但 API 测试失败

---

## 🔍 问题分析

### 为什么合约 API 仍然失败？

**可能原因**:

1. **权限修改未生效** - 需要等待 1-2 分钟
2. **IP 白名单限制** - 代理 IP 不在白名单
3. **合约账户未开户** - 需要完成合约开户流程
4. **API Secret 错误** - 可能性低（现货 API 正常）

---

## ✅ 推荐解决方案

### 方案 A: 使用组合保证金 API（立即可用）

**推荐理由**:
1. ✅ 已测试成功
2. ✅ 支持 UM+CM+ 杠杆交易
3. ✅ 统一账户管理
4. ✅ 币安主推的高级账户模式

**配置**:
```python
API_KEY = '5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M'
API_SECRET = 'hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt'
BASE_URL = 'https://papi.binance.com'  # 组合保证金专用
PROXY = 'http://127.0.0.1:7890'
```

**使用步骤**:
1. 登录币安官网
2. 钱包 → 资金划转
3. 划转到组合保证金账户
4. 开始交易

**示例代码**:
```python
from src.portfolio_margin import BinancePortfolioMargin

client = BinancePortfolioMargin(API_KEY, API_SECRET, PROXY)

# 查询账户
account = client.um_account()
print(f"总权益：{account['totalWalletBalance']} USDT")

# UM 市价买入
result = client.um_market_buy('BTCUSDT', quantity=0.001)

# 查询持仓
positions = client.um_position()
```

---

### 方案 B: 继续排查普通合约 API

**排查步骤**:

#### 1. 确认权限已保存

访问：https://www.binance.com/zh-CN/my/settings/api-management

**确认**:
- [ ] 启用现货及杠杆交易 ✅
- [ ] 启用合约交易 ✅
- [ ] 统一账户 ❌ (已取消)
- [ ] IP 白名单：未设置 或 包含 `66.90.98.146`

#### 2. 等待权限生效

权限修改后需要 **1-2 分钟** 生效。

**测试命令**:
```bash
# 等待 2 分钟后执行
curl -X GET "https://fapi.binance.com/fapi/v2/account" \
  -H "X-MBX-APIKEY: 5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M"
```

#### 3. 检查合约开户

访问：https://www.binance.com/zh-CN/futures

**确认**:
- [ ] 已完成 KYC 实名认证
- [ ] 已开通合约账户
- [ ] 已完成风险测评

#### 4. 重新创建 API Key（最后手段）

如果以上都无效：
1. 删除当前 API Key
2. 创建新的 API Key
3. 立即勾选"启用合约交易"
4. 不要勾选"统一账户"
5. 不设置 IP 白名单（测试期间）
6. 保存后等待 2 分钟
7. 重新测试

---

## 📝 ClawGuard-BNB 配置

### 推荐配置（使用组合保证金）

编辑 `/root/.openclaw/workspace/ClawGuard-BNB/.env`:

```bash
# 币安 API 配置（组合保证金）
BINANCE_API_KEY=5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M
BINANCE_API_SECRET=hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt

# 使用组合保证金 API
BINANCE_API_TYPE=portfolio_margin
BINANCE_API_BASE_URL=https://papi.binance.com

# 代理配置
PROXY_URL=http://127.0.0.1:7890

# 交易配置
FUTURES_ENABLED=true
MAX_LEVERAGE=5
```

### 使用示例

```python
# 导入模块
from src.portfolio_margin import BinancePortfolioMargin

# 初始化
client = BinancePortfolioMargin(
    api_key='5L2YGXjf1463J3F5TVJUS1HGOLnzv41i8Li4h5QhtGijWUmIP73M2AJeOZiMNF1M',
    api_secret='hfZ0WFSBgYcQfDRjmrbVVzbjqSaLBdUJ6arInvSNztVqOSbd7EMrClg5MLXs1YSt',
    proxy='http://127.0.0.1:7890'
)

# 查询账户余额
account = client.um_account()
print(f"总权益：{account['totalWalletBalance']} USDT")

# 市价买入 BTC
result = client.um_market_buy('BTCUSDT', quantity=0.001)
print(f"订单 ID: {result['orderId']}")

# 查询持仓
positions = client.um_position()
for pos in positions:
    if float(pos['positionAmt']) != 0:
        print(f"{pos['symbol']}: {pos['positionAmt']}")

# 限价卖出
result = client.um_limit_sell('BTCUSDT', quantity=0.001, price=70000)

# 撤销订单
client.um_cancel_order('BTCUSDT', orderId=result['orderId'])
```

---

## 📊 测试清单

### 组合保证金 API 测试

- [ ] 查询账户余额
- [ ] 划转资金到组合保证金账户
- [ ] UM 市价下单
- [ ] UM 限价下单
- [ ] 查询持仓
- [ ] 撤销订单
- [ ] CM 合约下单（可选）
- [ ] 杠杆账户交易（可选）

### 普通合约 API 测试（如果继续排查）

- [ ] 等待 2 分钟后重试
- [ ] 测试 fapi/v2/account
- [ ] 测试 fapi/v2/positionRisk
- [ ] 测试 fapi/v1/order
- [ ] 如果仍然失败，重新创建 API Key

---

## 💡 最终建议

**基于当前测试结果，强烈推荐使用方案 A（组合保证金 API）**：

1. ✅ 已测试成功，无需等待
2. ✅ 功能更强大（支持 UM+CM+ 杠杆）
3. ✅ 币安主推的高级账户模式
4. ✅ 代码已实现，立即可用

**唯一步骤**: 划转资金到组合保证金账户

---

## 🔗 相关文档

- `binance-portfolio-margin-api.md` - API 接口文档
- `binance-api-setup-guide.md` - 配置指南
- `binance-api-troubleshooting.md` - 排查指南
- `ClawGuard-BNB/src/portfolio_margin.py` - Python 实现

---

*最后更新：2026-03-08 12:55 UTC*
