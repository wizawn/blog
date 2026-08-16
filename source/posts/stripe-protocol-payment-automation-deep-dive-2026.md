---
title: "Stripe 协议支付自动化深度拆解：从 HAR 抓包到纯 API 全链路实现"
date: 2026-08-16T22:00:00+08:00
draft: true
weight: 1
categories: ["技术分析", "支付安全"]
tags: ["Stripe", "协议支付", "自动化", "ConfirmationToken", "PaymentIntent", "TLS指纹", "逆向工程", "Checkout Session", "支付安全", "API"]
description: "完整拆解 Stripe 协议支付的技术实现：从浏览器 HAR 抓包逆向 Stripe Checkout Session 全流程，到纯 API 无浏览器实现 ConfirmationToken 创建、PaymentIntent 确认、3DS 验证挑战，再到 TLS 指纹对抗、代理池架构和反欺诈绕过。附 5 套不同技术栈的完整实现源码下载。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **⚠️ 免责声明**：本文仅供安全研究与技术学习。文中描述的技术手段仅用于分析 Stripe 支付协议的工作原理，帮助支付系统开发者理解安全边界。请勿将相关技术用于任何未授权的操作。

---

## 前言

做过 SaaS 订阅的人都知道，Stripe 是全球最主流的支付处理商。几乎所有主流 AI 平台——从对话类到图像类——都用 Stripe 处理信用卡支付。

但很少有人去研究 Stripe Checkout 背后的协议细节。大多数人的认知停留在"调一下 API、跳个 Checkout 页面、信用卡扣完款就行了"。

实际上，Stripe 的 Checkout Session 协议远比你想象的复杂。从 `checkout_ui_mode` 的 `custom` 与 `hosted` 两种模式，到 `ConfirmationToken` 的创建机制，再到 `PaymentIntent` 的 `requires_action` 状态下 3DS 验证挑战的处理——每一步都有大量的协议细节、反欺诈检测和时序要求。

今天我把这些全拆开。从 HAR 抓包出发，逐层剖析 Stripe 协议支付的完整链路，并提供 5 套不同技术栈的实现源码。

---

## 一、为什么要做"协议支付"

先搞清楚一个概念：什么是协议支付（Protocol Payment）？

**浏览器支付**：用户打开 Stripe Checkout 页面 → 手动填写信用卡号 → 点击支付 → 完成。这是正常流程。

**协议支付**：用纯 HTTP API 请求模拟浏览器的完整操作链路，包括 Stripe 的内部 API（不是官方 SDK 暴露的那些），直接在协议层完成支付，不需要浏览器。

为什么要这么做？

1. **自动化需求**：批量管理订阅时，手动操作不现实
2. **性能需求**：浏览器（Puppeteer/Playwright）启动慢、占内存大、不稳定；协议支付 <5s 完成
3. **环境隔离**：服务端运行，不需要 GUI 环境
4. **学习价值**：深入理解支付系统的工作原理

---

## 二、Stripe Checkout Session 的两种模式

Stripe Checkout 有两种 `checkout_ui_mode`，这是整个协议支付的第一个分叉点：

### 2.1 Custom 模式 (`oaics_` 前缀)

```
POST /payments/checkout
{
  "checkout_ui_mode": "custom",
  "currency": "PHP",
  "plan_type": "plus"
}
→ {"checkout_session_id": "oaics_xxx", "stripe_publishable_key": "pk_live_..."}
```

Custom 模式返回的 Session ID 以 `oaics_` 开头。这种模式下：
- 前端需要自己挂载 Stripe Elements
- 通过 Stripe.js 创建 `ConfirmationToken`
- 调用平台的 `confirm` 接口完成支付
- **直接**在 Stripe API 上确认 PaymentIntent

### 2.2 Hosted 模式 (`cs_live_` 前缀)

```
POST /payments/checkout
{
  "checkout_ui_mode": "hosted",
  "currency": "PHP",
  "plan_type": "plus"
}
→ {"checkout_session_id": "cs_live_xxx", "url": "https://checkout.stripe.com/..."}
```

Hosted 模式返回 `cs_live_` 前缀的 Session。这种模式下：
- Stripe 托管整个 Checkout 页面
- 走 Stripe Payment Page 的内部协议
- 流程更复杂，涉及 `ppage_` 初始化、`elements` Session、`inline_confirm`
- 需要额外处理平台侧的 `approve` 操作

两种模式的选择取决于平台的 billing 配置和你的需求。一般来说：
- 如果平台的计费货币与你的信用卡货币一致 → Custom 模式更简单
- 如果存在货币不匹配（比如用美元卡付菲律宾比索订阅）→ 可能只有 Hosted 模式可用

---

## 三、Custom 模式协议流程详解

Custom 模式是最干净的协议支付路径。完整流程只需 7 步：

```
┌──────────────────────────────────────┐
│ 1. 刷新 Session（获取最新 Token）      │
│ 2. 查询账号信息（确认当前订阅状态）     │
│ 3. 获取定价信息（币种+金额）           │
│ 4. 创建 Checkout Session              │
│ 5. 更新税务信息（Billing 地址）        │
│ 6. 创建 ConfirmationToken（卡号→Token）│
│ 7. 确认支付（Confirm Checkout）        │
│ 8. 确认 PaymentIntent（Stripe 侧）     │
└──────────────────────────────────────┘
```

### 3.1 创建 ConfirmationToken

这是协议支付最核心的一步。浏览器里，Stripe.js 会在 iframe 中收集卡号，然后调用 Stripe 的内部 API 创建一个 `ConfirmationToken`（`ctoken_` 前缀）。

协议支付需要直接模拟这个请求：

```http
POST https://api.stripe.com/v1/confirmation_tokens
Content-Type: application/x-www-form-urlencoded

type=card
&payment_method_data[type]=card
&payment_method_data[card][number]=4242424242424242
&payment_method_data[card][exp_month]=12
&payment_method_data[card][exp_year]=2029
&payment_method_data[card][cvc]=123
&payment_method_data[billing_details][name]=John Doe
&payment_method_data[billing_details][address][country]=US
&payment_method_data[billing_details][address][postal_code]=97201
&key=pk_live_xxx
&_stripe_version=2025-03-31.basil
```

几个关键细节：

1. **`key` 必须是平台的 Stripe Publishable Key**，不是你自己的
2. **`_stripe_version` 必须匹配**当前 Stripe.js 的 API 版本
3. **需要传 Stripe.js 的指纹参数**：`guid`、`muid`、`sid`、`time_on_page`
4. **Referer 必须是平台域名**，Stripe 会校验

返回值：

```json
{
  "id": "ctoken_1xxx",
  "type": "card",
  "payment_method_preview": {
    "card": {
      "brand": "visa",
      "last4": "4242"
    }
  }
}
```

### 3.2 确认 Checkout

拿到 `ConfirmationToken` 后，调用平台的 confirm 接口：

```http
POST /api/v1/payments/checkout/confirm
{
  "checkout_session_id": "oaics_xxx",
  "confirmation_token": "ctoken_1xxx"
}
```

这一步平台会拿着你的 token 去 Stripe 创建 PaymentIntent 并尝试扣款。

如果一切顺利（卡余额充足、无 3DS 要求），PaymentIntent 直接变成 `succeeded`，订阅激活。

如果遇到 3DS 验证，流程会更复杂——我们在第五节讲。

---

## 四、Hosted 模式协议流程详解

Hosted 模式（`cs_live_`）的流程更复杂，因为需要模拟 Stripe Payment Page 的完整内部协议。

```
┌────────────────────────────────────────────────┐
│ 1. 创建 Checkout (hosted) → cs_live_ session    │
│ 2. 更新税务                                      │
│ 3. 分配信用卡                                    │
│ 4. 初始化 Payment Page → ppage_ token            │
│ 5. 获取 Elements Session                         │
│ 6. 创建 ConfirmationToken                        │
│ 7. 确认 Checkout (内部 confirm)                   │
│ 8. 平台 Approve 操作                              │
│ 9. 轮询 PaymentIntent 状态                       │
│ 10. 处理 3DS Challenge（如果需要）                 │
│ 11. 验证最终状态                                  │
└────────────────────────────────────────────────┘
```

### 4.1 Payment Page 初始化

```http
GET https://checkout.stripe.com/api/payment-page/{cs_live_xxx}/init
→ {"ppage_token": "ppage_xxx", "merchant_name": "..."}
```

这是 Hosted 模式独有的。返回一个 `ppage_` token，后续所有 Stripe Payment Page API 都需要这个 token。

### 4.2 Elements Session

```http
POST https://api.stripe.com/v1/elements/sessions
{
  "type": "payment_intent",
  "locale": "auto",
  "payment_method_types[]": "card",
  "deferred_intent[mode]": "payment",
  "deferred_intent[setup_future_usage]": "off_session"
}
```

这一步获取 Stripe Elements 的会话信息，包含可用的支付方式和 UI 配置。

### 4.3 Approve 机制

Hosted 模式下，Stripe 确认支付后，状态不会直接变成 `succeeded`，而是进入 `requires_approval`。这时需要调用平台的 approve 接口：

```http
POST /api/v1/payments/checkout/approve
Authorization: Bearer {access_token}
X-Vendor-Challenge-Token: {challenge_token}
```

**关键发现**：
- Approve 是**一次性操作**，同一 session 不可重复
- 需要携带反欺诈挑战 token（包含 Turnstile/PoW 验证结果）
- 如果返回 `blocked`，该 session 作废，必须创建新的

---

## 五、3DS 验证挑战

当 Stripe 判断交易需要额外验证时，PaymentIntent 会进入 `requires_action` 状态，附带 3DS challenge 信息。

### 5.1 Challenge 类型

Stripe 使用 hCaptcha Enterprise 作为 3DS 验证手段：

```json
{
  "status": "requires_action",
  "next_action": {
    "type": "verify_with_challenge",
    "verify_with_challenge": {
      "url": "https://challenges.stripe.com/...",
      "challenge_type": "hcaptcha"
    }
  }
}
```

### 5.2 验证流程

1. 从 challenge 字段提取 hCaptcha `siteKey` 和 `rqdata`
2. 解出 hCaptcha token（本地或远程打码服务）
3. 调用 `verify_challenge` 接口：

```http
POST https://api.stripe.com/v1/payment_intents/{pi_id}/verify_challenge
{
  "challenge_response": "{hcaptcha_token}",
  "challenge_type": "hcaptcha"
}
```

### 5.3 时效性问题

这里有一个重要的坑：**hCaptcha token 有时效性**。浏览器里 ~4 秒解出，但远程打码服务可能需要 30-120 秒。如果 token 过期，`verify_challenge` 会返回 `payment_intent_authentication_failure`。

解决方案：
- 使用本地 headless 解码（延迟 <5s）
- 或使用支持 Enterprise rqdata 的快速打码服务

---

## 六、TLS 指纹对抗

纯 HTTP 请求最大的挑战不是协议逻辑，而是 **TLS 指纹**。

Stripe 和 Cloudflare 都会检查 TLS Client Hello 的指纹（JA3/JA4），如果发现你的 TLS 握手特征不像浏览器，直接返回 403/429。

### 6.1 指纹伪装

Python 项目使用 `curl_cffi` 库，支持模拟多种浏览器的 TLS 指纹：

```python
PROFILES = [
    ("chrome131", "Mozilla/5.0 ... Chrome/131.0"),
    ("chrome124", "Mozilla/5.0 ... Chrome/124.0"),
    ("safari18",  "Mozilla/5.0 ... Safari/605.1"),
    ("firefox117", "Mozilla/5.0 ... Firefox/117.0"),
]
```

Node.js 项目使用 `CycleTLS`：

```javascript
import initCycleTLS from 'cycletls';
const cycleTLS = await initCycleTLS();
const response = await cycleTLS(url, {
  ja3: '771,4865-4866-4867...',
  userAgent: 'Mozilla/5.0 ...'
});
```

### 6.2 指纹轮换策略

当遇到 403/429 时，自动切换到下一个 TLS 指纹配置：

```python
class TLSFingerprintManager:
    def rotate_on_failure(self):
        self.exclude_current()
        return self.pick_next()
```

最多重试 3 次，每次使用不同的浏览器指纹。

---

## 七、Stripe.js 指纹参数

Stripe 的 `confirmation_tokens` 和 `payment_intents/confirm` 接口都需要一组指纹参数。这些参数由 Stripe.js 在前端收集，协议支付需要正确模拟：

| 参数 | 含义 | 生成方式 |
|------|------|---------|
| `guid` | 全局唯一 ID | UUID v4 格式 (`xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx`) |
| `muid` | 设备 ID | 随机 hex，32 字符 |
| `sid` | 会话 ID | 随机 hex，32 字符 |
| `time_on_page` | 页面停留时间 | 随机 8-30 秒（模拟真实用户） |
| `key` | Publishable Key | 从 Checkout Session 获取 |
| `_stripe_version` | API 版本 | 从 Stripe.js 的 basil 部署中提取 |

### 7.1 动态提取 Stripe.js 版本

Stripe.js 的版本（`_stripe_version`）和构建哈希（`rv`/`sv`）不是固定的，需要从 Stripe 的部署状态接口动态提取：

```javascript
// 获取当前 Stripe.js 部署信息
const status = await fetch('https://js.stripe.com/deploy_status_henson.json');
const { basil } = await status.json();
// basil.rv = "2025-03-31" → _stripe_version = "2025-03-31.basil"
```

---

## 八、代理池架构

协议支付的另一个核心组件是代理池。Stripe 和平台都会检查请求的源 IP，用数据中心 IP 直连容易被标记。

### 8.1 双代理池

最佳实践是使用两个独立的代理池：
- **平台代理池**：用于访问 SaaS 平台的 API（需要与账号注册地匹配）
- **Stripe 代理池**：用于访问 Stripe API（需要住宅 IP，避免被 Radar 标记）

### 8.2 代理健康检查

```python
class ProxyVerifier:
    def verify(self, proxy_url: str, expected_country: str):
        resp = requests.get("https://ipapi.co/json/", proxies=proxy_url)
        actual = resp.json()["country_code"]
        if actual != expected_country:
            raise ProxyCountryMismatchError(expected_country, actual)
```

### 8.3 出口 IP 一致性

**关键规则**：创建 Checkout Session 和确认支付时，必须使用**同一个出口 IP**。Stripe 会比对两次请求的 IP，如果不一致会拒绝交易。

---

## 九、状态机设计

完整的协议支付需要处理多种失败场景和重试逻辑。最佳实践是使用状态机：

```
初始化 → 刷新Session → 检查权限 → 获取定价 → 创建Checkout
    ↓           ↓           ↓           ↓           ↓
  失败→退出   失败→退出  已有订阅→跳过  失败→退出   失败→退出
                                                    ↓
                                              更新税务 → 创建Token → 确认支付
                                                ↓           ↓           ↓
                                              失败→退出   卡被拒→换卡   3DS→验证
                                                                        ↓
                                                                    成功 / 失败
```

每个状态转移都需要处理：
- **卡被拒（Card Declined）**：分类拒绝原因（余额不足/CVV错误/风控拒绝），决定是换卡重试还是放弃
- **3DS 验证**：进入 Challenge 流程
- **Session 过期**：创建新 Session 重试
- **Rate Limiting**：TLS 指纹轮换 + 退避重试

---

## 十、安全边界与最佳实践

### 10.1 Session 隔离

每次支付使用独立的 Session，不复用已失败的 Session。特别是 Hosted 模式下，`approve` 操作后的 Session 不可再次使用。

### 10.2 Dry-Run 模式

所有实现都应支持 Dry-Run 模式——执行完整流程但不提交最终的 `confirm`：

```python
if config.commit_payments:
    result = stripe.confirm_payment_intent(pi_id, token)
else:
    logger.info("Dry-run: skipping confirm")
```

### 10.3 不要存储敏感数据

- 信用卡号仅在内存中使用，支付完成后立即清除
- Session token 不应写入日志
- 代理凭据不要硬编码

---

## 十一、实现对比

文末提供的 5 套实现覆盖了不同的技术栈和使用场景：

| 实现 | 语言/框架 | 模式 | 特点 |
|------|----------|------|------|
| **saas-pay-sdk** | Python / CLI | Custom | 最精简的 CLI 工具，TLS 指纹轮换，daemon 上报 |
| **subscription-manager** | Python Flask / Web UI | Both | 完整 Web 管理面板，支持绑卡、查账单、升级降级 |
| **payment-gateway** | Python Flask / Web UI | Both | 批量支付面板，账号池管理，barrier 模式批量确认 |
| **checkout-server** | Python / Local HTTP | Both | 本地支付编排服务器，Playwright 降级，SQLite 持久化 |
| **protocol-engine** | Node.js / Modules | Both | 模块化协议引擎，CycleTLS，动态 Stripe.js 版本抓取 |

每个实现都有自己的优缺点：
- 想要最快上手 → `saas-pay-sdk`（纯 CLI，pip install 即可）
- 想要可视化管理 → `subscription-manager`（Web UI）
- 想要批量处理 → `payment-gateway`（账号池 + 批量模式）
- 想要理解底层 → `protocol-engine`（模块化，可以单独引用任何一层）

---

## 下载

以下是 5 套完整实现的源码下载链接：

| 项目 | 下载链接 | 说明 |
|------|---------|------|
| saas-pay-sdk | [下载](/downloads/saas-pay-sdk.zip) | Python CLI 工具 |
| subscription-manager | [下载](/downloads/subscription-manager.zip) | Flask Web 管理面板 |
| payment-gateway | [下载](/downloads/payment-gateway.zip) | 批量支付网关面板 |
| checkout-server | [下载](/downloads/checkout-server.zip) | 本地支付编排服务器 |
| protocol-engine | [下载](/downloads/protocol-engine.zip) | Node.js 协议引擎模块 |

> **注意**：所有源码中的 API Key、域名、账号信息均已替换为占位符。使用前需要根据你的实际环境配置 `.env` 文件。

---

*如果你对支付安全感兴趣，欢迎加微信群交流。*
