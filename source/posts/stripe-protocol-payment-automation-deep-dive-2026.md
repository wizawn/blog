---
title: "Stripe 协议支付自动化深度拆解：从 HAR 抓包到纯 API 全链路实现"
date: 2026-08-16T22:00:00+08:00
draft: false
weight: 1
categories: ["技术分析", "支付安全"]
tags: ["Stripe", "协议支付", "自动化", "ConfirmationToken", "PaymentIntent", "TLS指纹", "逆向工程", "Checkout Session", "支付安全", "API"]
description: "完整拆解 Stripe 协议支付的技术实现：从浏览器 HAR 抓包逆向 Stripe Checkout Session 全流程，到纯 API 无浏览器实现 ConfirmationToken 创建、PaymentIntent 确认、3DS 验证挑战，再到 TLS 指纹对抗、代理池架构和反欺诈绕过。附 5 套不同技术栈的完整实现源码下载。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **⚠️ 免责声明**：本文仅供安全研究与技术学习。文中描述的技术手段仅用于分析 Stripe 支付协议的工作原理，帮助支付系统开发者理解安全边界。请勿将相关技术用于任何未授权的操作。

---

## 前言

做过 SaaS 订阅的人都知道，Stripe 是全球最主流的支付处理商。几乎所有主流 AI 平台——从对话类到图像类——都用 Stripe 处理信用卡支付。

但很少有人去研究 Stripe Checkout 背后的协议细节。大多数人的认知停留在"调一下 API、跳个 Checkout 页面、信用卡扣完款就行了"。

实际上，Stripe 的 Checkout Session 协议远比你想象的复杂。从 `checkout_ui_mode` 的 `custom` 与 `hosted` 两种模式，到 `ConfirmationToken` 的创建机制，再到 `PaymentIntent` 的 `requires_action` 状态下 3DS 验证挑战的处理——每一步都有大量的协议细节、反欺诈检测和时序要求。

今天我把这些全拆开。从 HAR 抓包出发，逐层剖析 Stripe 协议支付的完整链路，并提供 5 套不同技术栈的实现源码。

---

## 零、方法论：如何逆向 Stripe 支付协议

在开始之前，先讲方法论。所有协议支付的起点都是 **HAR 抓包**。

### 0.1 什么是 HAR 文件

HAR（HTTP Archive）是浏览器开发者工具导出的完整 HTTP 交互记录。包含每个请求的 URL、Headers、Body、Response，以及精确的时序信息。

打开 Chrome DevTools → Network → 完成一次真实支付 → 右键 → Save all as HAR with content。

**这个 HAR 文件就是你的 ground truth**。所有协议支付的字段、值、顺序、编码方式，都以 HAR 为准。代码实现、第三方文档、安全审计报告——全部都可能过时或有误，只有 HAR 是当时浏览器真实发出的请求。

### 0.2 HAR 分析流程

1. **筛选关键域名**：`api.stripe.com`、`m.stripe.com`、`checkout.stripe.com`、平台 API 域名
2. **按时间排序**：找出完整的请求链路
3. **对比成功和失败**：同一流程的成功 HAR 和失败 HAR，diff 出关键差异
4. **提取稳定字段**：跨多个 HAR 都一致的值可以硬编码
5. **标记动态字段**：每次不同的值（Session ID、Token、时间戳）需要运行时获取

### 0.3 经过验证的 HAR 请求链路

通过分析多个成功支付的 HAR 文件，提取出标准的浏览器 Checkout 请求序列：

```
1. POST /api/v1/payments/checkout           → 创建 session (oaics_xxx)
2. GET  stripe/v1/elements/sessions          → 获取 Elements 配置 (deferred_intent)
3. POST /api/v1/payments/checkout/taxes      → 税务重算 (US免税地址可消除VAT)
4. GET  stripe/v1/elements/sessions          → 更新后的 amount
5. POST stripe/v1/confirmation_tokens        → 卡号 → ctoken_xxx
6. POST /api/v1/payments/checkout/confirm    → 平台确认 → pi_xxx client_secret
7. POST stripe/v1/payment_intents/{pi}/confirm → Stripe 侧扣款
8. GET  /checkout/verify                      → redirect_status=succeeded
```

每一步都有大量细节。下面逐一拆解。

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

### 2.3 决定性参数：`checkout_ui_mode`

通过大量测试验证，**决定返回 `oaics_` 还是 `cs_live_` 的唯一参数就是 `checkout_ui_mode`**。

```json
// 返回 oaics_ 的请求
{
  "entry_point": "all_plans_pricing_modal",
  "plan_name": "basic_plan",
  "billing_details": {"country": "PH", "currency": "PHP"},
  "checkout_ui_mode": "custom"
}

// 返回 cs_live_ 的请求
{
  "plan_name": "basic_plan",
  "billing_details": {"country": "PH", "currency": "PHP"},
  "checkout_ui_mode": "hosted",
  "cancel_url": "https://platform.example.com/#pricing",
  "locale": "zh-CN"
}
```

注意差异：
- **`entry_point`**：Custom 模式有，Hosted 模式没有
- **`cancel_url`**：Hosted 模式需要（Stripe 托管页面的返回按钮用）
- **`locale`**：Hosted 模式建议传（影响 Stripe 页面语言）

Hosted 模式的响应多一个 `url` 字段——这是 Stripe 托管页面的完整 URL，可以直接在浏览器中打开。

### 2.4 `_stripe_version` 的版本差异

这是一个极其容易忽略的细节。两种模式使用**不同的 `_stripe_version`**：

| 模式 | `_stripe_version` 值 |
|------|---------------------|
| Custom (oaics_) | `2025-03-31.basil` |
| Hosted (cs_live_) | `2025-03-31.basil; checkout_server_update_beta=v1; checkout_manual_approval_preview=v1` |

Hosted 模式的版本串后面带了两个 beta flag。如果在 cs_live_ 请求中用了 Custom 的短版本串，Stripe 会返回字段缺失或行为不一致。

### 2.5 两种模式的完整字段对比

| 字段 | Custom (oaics_) | Hosted (cs_live_) |
|------|-----------------|-------------------|
| 确认端点 | `payment_intents/{pi}/confirm` | `payment_pages/{cs_live}/confirm` |
| 顶层 `source` | `elements` | `checkout` |
| 顶层 `version` | `2021` | `custom` |
| `selection_flow` | `merchant_specified` | `automatic` |
| `elements_session_client` | 无 | 有（8 个子字段） |
| `elements_options_client` | 无 | 有（2 个子字段） |
| `link_brand` | 无 | `link` |
| `checkout_config_id` | 无 | 有（两层不同值） |
| hCaptcha 位置 | `pmd[radar_options][hcaptcha_token]` | `passive_captcha_token`（顶层） |
| `init_checksum` | 无 | 有 |
| `js_checksum` | 无 | 有 |
| `rv_timestamp` | 无 | 有 |
| `expected_amount` | 无 | 有 |

**这两套字段集完全不能混用**。这也是很多人协议支付做不通的原因——用了 oaics_ 的字段去调 cs_live_ 的接口，反过来也一样。

---

## 三、Custom 模式协议流程详解

Custom 模式是最干净的协议支付路径。完整流程 8 步：

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

#### 卡号格式细节

HAR 验证发现，浏览器发送的卡号**带空格**（`4004 1641 0185 9397`），而不是纯数字。不过 Stripe 接受两种格式。

#### guid/muid/sid 格式

这三个指纹 ID 的格式比很多人以为的更复杂。HAR 验证的正确格式是 **42 字符**：

```
guid = randomUUID() + randomHex(6)
     = xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx + 6位hex
     = 36字符UUID + 6字符 = 42字符
```

例如：`a1b2c3d4-e5f6-4789-abcd-ef0123456789abc123`

有些实现用 32 位纯 hex 也能工作，但 HAR 中浏览器发送的是 42 字符格式。

#### Attribution 元数据（两层结构）

`confirmation_tokens` 请求中有一组 `client_attribution_metadata` 字段，这些是 Stripe 用来追踪支付集成来源的元数据：

```
payment_user_agent = stripe.js/...
client_session_id = <UUID>                           # 每 session 唯一
merchant_integration_source = elements               # ← oaics_ 固定 "elements"
merchant_integration_version = 2021
merchant_integration_subtype = payment-element
payment_intent_creation_flow = deferred
payment_method_selection_flow = merchant_specified    # ← oaics_ 固定
additional_elements = [expressCheckout, payment, address]
```

这些字段在 `confirmation_tokens` 请求中出现两次——一次在 `payment_method_data` 内部，一次在顶层。**两层的值大部分相同，但 `merchant_integration_source` 在 confirm 请求中变成 `l1`**。这个细节从 HAR 中才能发现。

#### 请求头

HAR 中 Stripe API 请求的完整请求头：

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
Accept: application/json
Content-Type: application/x-www-form-urlencoded
Origin: https://js.stripe.com
Referer: https://js.stripe.com/
Sec-CH-UA: "Not=A?Brand";v="99", "Chromium";v="151"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
Sec-Fetch-Site: same-site
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Accept-Language: en-US,en;q=0.9
```

注意 `Accept-Language` 必须存在。这是纯协议支付跑通的关键 bug 之一——缺少这个 header 会导致 Stripe 返回非预期的响应格式。

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

### 3.3 Elements Session — 获取支付配置

在创建 ConfirmationToken 之前，需要先调用 Stripe 的 `elements/sessions` API 获取支付配置信息。这一步在 HAR 中被调用**两次**——一次在税务更新前，一次在税务更新后。

```http
GET https://api.stripe.com/v1/elements/sessions?deferred_intent[mode]=subscription
    &deferred_intent[amount]=98214
    &deferred_intent[currency]=php
    &deferred_intent[setup_future_usage]=off_session
    &deferred_intent[payment_method_types][0]=card
    &type=deferred_intent
    &key=pk_live_xxx
    &_stripe_version=2025-03-31.basil
```

关键返回值：
- **`elements_session_id`**：`elements_session_xxx`，后续 confirm 请求需要
- **`customer_session_client_secret`**：`cuss_xxx`，客户会话密钥
- **`payment_method_configuration`**：`pmc_xxx`，支付方式配置 ID

### 3.4 税务地址优化 — US 免税地址消除 VAT

这是一个实际操作中极其重要的技巧。

很多 SaaS 平台默认按账号注册地收税。比如菲律宾区的订阅，标价 ₱982.14 但实际会加 12% VAT 变成 ₱1,100+。

**解决方案**：在 `taxes` API 调用中使用美国免税州地址。

```http
POST /api/v1/payments/checkout/taxes
{
  "checkout_session_id": "oaics_xxx",
  "billing_details": {
    "name": "John Doe",
    "address": {
      "country": "US",
      "state": "OR",
      "city": "Portland",
      "postal_code": "97201",
      "line1": "123 Main St"
    }
  }
}
```

美国有 5 个无销售税的州：
- **Oregon (OR)** — 无销售税
- **Montana (MT)** — 无销售税
- **Delaware (DE)** — 无销售税
- **New Hampshire (NH)** — 无销售税
- **Alaska (AK)** — 大部分地区无销售税

HAR 验证：使用 US 地址后 tax=0，最终金额保持 ₱982.14。

**重要**：`taxes` 和后续 `confirmation_tokens` 中的地址必须一致。同一个 session 内选择一个地址后全程复用。

### 3.5 PaymentIntent 确认 — Stripe 侧扣款

平台的 `/confirm` 返回 `client_secret`（格式：`pi_xxx_secret_xxx`）后，需要调用 Stripe 的 `payment_intents/confirm` 完成实际扣款：

```http
POST https://api.stripe.com/v1/payment_intents/{pi_id}/confirm

return_url = https://platform.example.com/checkout/verify?stripe_session_id=oaics_xxx
confirmation_token = ctoken_xxx
key = pk_live_xxx
_stripe_version = 2025-03-31.basil
client_secret = pi_xxx_secret_xxx
client_attribution_metadata[client_session_id] = <UUID>
client_attribution_metadata[merchant_integration_source] = l1
```

注意这里 `merchant_integration_source` 变成了 `l1`，不再是 `elements`。

#### PI 拒卡重试

HAR 验证了一个重要特性：**同一个 PaymentIntent 被拒卡后可以用新的 ConfirmationToken 重试**。

流程：
1. 第一张卡 → `generic_decline` → PI 状态 `requires_payment_method`
2. 创建新的 `confirmation_token`（用另一张卡）
3. 再次调用 `payment_intents/confirm`
4. 第二张卡 → `succeeded`

**这意味着拒卡不需要重建整个 Checkout Session**，只需要换卡重建 token。

### 3.6 Cookie 隔离架构

协议支付需要严格的 Cookie 隔离。一个常见的 bug 是平台的 Cookie 被发送到 Stripe API，或反过来。

最佳实践：使用两个独立的 HTTP 客户端：

```python
# 平台客户端 — 带 Cookie（session token）
platform_http = HttpClient(cookies_enabled=True)
platform_http.set_cookie("__Secure-platform-auth", session_token)

# Stripe 客户端 — 不带 Cookie
stripe_http = HttpClient(cookies_enabled=False)
```

**绝不**让 Stripe 客户端发送平台 Cookie，也不要让平台客户端发送 Stripe 的 Cookie。

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

### 4.2 Elements Session（Hosted 模式特殊字段）

Hosted 模式的 `elements/sessions` 请求比 Custom 模式多出很多字段：

```http
POST https://api.stripe.com/v1/elements/sessions

deferred_intent[mode] = subscription
deferred_intent[amount] = 98214
deferred_intent[currency] = php
deferred_intent[setup_future_usage] = off_session
deferred_intent[payment_method_types][0] = card
deferred_intent[payment_method_configuration][id] = pmc_xxx
currency = php
elements_init_source = custom_checkout
referrer_host = platform.example.com
stripe_js_id = <UUID>
locale = zh
type = deferred_intent
checkout_session_id = cs_live_xxx
_stripe_version = 2025-03-31.basil; checkout_server_update_beta=v1; ...
```

关键差异：
- 需要传 `checkout_session_id`（Custom 模式不需要）
- `elements_init_source` 是 `custom_checkout`（不是 `elements`）
- 需要传 `referrer_host`、`stripe_js_id`、`locale`
- 使用**长版本**的 `_stripe_version`

返回值中有一个重要字段 `passive_captcha.rqdata`——这是 hCaptcha Enterprise 的 `rqdata`，后续 confirm 如果触发 challenge 需要用到。

### 4.3 Hosted 模式的 Confirm 请求

cs_live_ 的 confirm 走的是 `payment_pages/confirm`，不是 `payment_intents/confirm`：

```http
POST https://api.stripe.com/v1/payment_pages/{cs_live_xxx}/confirm
```

这个请求的 body 字段比 Custom 模式多很多：

```
elements_session_client[client_betas][0] = custom_checkout_server_updates_1
elements_session_client[client_betas][1] = custom_checkout_manual_approval_1
elements_session_client[elements_init_source] = custom_checkout
elements_session_client[referrer_host] = platform.example.com
elements_session_client[session_id] = elements_session_xxx
elements_session_client[stripe_js_id] = <UUID>
elements_session_client[locale] = zh
elements_session_client[is_aggregation_expected] = false
elements_options_client[saved_payment_method][enable_save] = auto
elements_options_client[saved_payment_method][enable_redisplay] = auto
init_checksum = <checksum>
js_checksum = <checksum>
rv_timestamp = <timestamp>
expected_amount = 98214
expected_payment_method_type = card
version = <build_hash>
```

`js_checksum` 和 `rv_timestamp` 是从 Stripe.js 部署状态动态提取的，`init_checksum` 来自 init 响应。

### 4.4 Approve 机制与 Sentinel Token

Hosted 模式下，`payment_pages/confirm` 成功后，状态不会直接变成 `succeeded`，而是进入 `requires_approval`（HAR 中 confirm 返回 `status=open`）。这时需要调用平台的 approve 接口：

```http
POST /api/v1/payments/checkout/approve
Authorization: Bearer {access_token}
X-Vendor-Challenge-Token: {sentinel_token}
```

#### Sentinel Token 结构

这里的 `challenge_token` 是一个编码后的 JSON 对象，内部包含多个通过算力证明（PoW）和 Turnstile 验证生成的字段：

```json
{
  "p": "gAAAAAB...",     // 主负载（加密后的 PoW + session 信息）
  "c": "...",            // enforcement_token（基于 FNV-1a 的算力证明结果）
  "id": "<UUID>",        // 一次性标识
  "flow": "platform_checkout",  // 标记来源流程
  "t": "<turnstile_dx_token>"  // 4000+ 字符的 Turnstile 验证 token
}
```

**`t` 字段是核心**——如果为空字符串，approve 立即返回 `blocked`。它来自 Cloudflare Turnstile 的隐式挑战验证（不是肉眼可见的验证码）。

#### Sentinel Token 生成流程

完整的 Sentinel 生成需要两个组件协作：

```
1. 生成 requirements_token（本地 seed + difficulty "0"）
2. POST sentinel.platform.com/backend-api/sentinel/req
   → 返回 {turnstile: {dx: "..."}, ...}
3. 用 server seed 生成 enforcement_token（FNV-1a 算力证明）
4. 在 Node.js VM 中执行 Turnstile SDK（需要 jsdom 模拟 DOM 环境）
   → 返回 turnstile token（~4388 字符）
5. 组装 JSON → Base64 → 设为请求头
```

关键点：
- PoW 使用 **FNV-1a** 哈希算法，difficulty 对 checkout 流程通常是 "0"（即几乎不需要算力）
- Turnstile SDK 必须在**真实的 DOM 环境**中执行——简单的字符串拼接无法通过验证
- 实际生产中需要 Node.js + jsdom 来执行官方 Turnstile VM
- SDK 代码需要定期更新（随平台版本迭代）

#### Approve 的正确时机

**关键发现**：Approve 不应该主动调用。正确的流程是 **fall-through**：

```
confirm → status=open, requires_approval
                       ↓
               等待 Stripe 回调
                       ↓
    平台自动完成 approve（不需要客户端调）
                       ↓
    poll payment_page → PI 出现
                       ↓
    可能 requires_action → verify_challenge
                       ↓
    poll 到 succeeded → 完成
```

但某些边缘情况下（平台回调未触发），客户端需要手动 approve。此时 Sentinel token 是必须的。

- Approve 是**一次性操作**，同一 session 不可重复
- 如果 `t` 字段为空或格式错误 → 返回 `blocked` → session 作废
- 成功的 approve 返回 `{"result":"approved"}`

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

### 5.2 verify_challenge 完整请求格式

HAR 中验证的 `verify_challenge` 完整请求：

```http
POST https://api.stripe.com/v1/payment_intents/{pi_id}/verify_challenge

captcha_response = {hcaptcha_token}     # P0开头的长字符串
captcha_vendor_name = hcaptcha           # 固定值
captcha_sitekey = xxxxxxxx-xxxx-xxxx    # Stripe 的 hCaptcha sitekey
expected_amount = 98214                  # 交易金额
expected_currency = php                  # 币种
key = pk_live_xxx                        # Publishable Key
_stripe_version = 2025-03-31.basil; checkout_server_update_beta=v1; ...
client_secret = pi_xxx_secret_xxx        # PI 的 client_secret
```

注意：
- 字段名是 `captcha_response` 而不是 `challenge_response`
- 需要同时传 `captcha_vendor_name` 和 `captcha_sitekey`
- 需要传 `expected_amount`/`expected_currency` 做一致性校验
- 使用**长版本** `_stripe_version`（与 Hosted 模式一致）

### 5.3 hCaptcha Enterprise 的特殊性

Stripe 使用的不是普通 hCaptcha，而是 **hCaptcha Enterprise**。区别：

1. **有 `rqdata` 参数**：普通 hCaptcha 不需要 rqdata，Enterprise 必须传
2. **sitekey 是 Stripe 专有的**：从 `elements/sessions` 响应的 `passive_captcha` 字段中提取
3. **invisible 模式**：浏览器里看不到验证码图片，但后台在做风控评估

```python
# 从 elements_session 响应中提取
rqdata = elements_session["passive_captcha"]["rqdata"]
sitekey = elements_session["passive_captcha"]["sitekey"]
```

### 5.4 时效性问题

**hCaptcha token 有时效性**——浏览器里 ~4 秒解出即有效，但远程打码服务可能需要 30-120 秒。如果超时：
- `verify_challenge` 返回 `payment_intent_authentication_failure`
- 但 PI 状态仍然是 `requires_action`——**可以重新 verify_challenge**

解决方案分级：
1. **最优**：本地 headless 浏览器解 hCaptcha（<5s，成功率 95%+）
2. **次优**：支持 Enterprise rqdata 的快速打码 API（如 YesCaptcha，~15s）
3. **兜底**：如果 PI 已经进入 `requires_action`，可以循环重试 verify_challenge（每次用新 captcha token）

### 5.5 3DS vs hCaptcha 的区别

**重要澄清**：Stripe 的 `verify_with_challenge` 并非传统银行 3DS 验证（3D Secure）。它是 Stripe 自有的风控挑战，使用 hCaptcha 作为人机验证手段。

真正的银行 3DS（如 Visa Secure）会打开银行页面要求输入 OTP/密码，这个在纯协议支付中**无法绕过**——但使用虚拟信用卡（VCC）通常不会触发银行 3DS，只会触发 Stripe 自身的 hCaptcha challenge。

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

### 6.3 TLS 指纹与 User-Agent 一致性

一个常见错误是 TLS 指纹和 User-Agent 不匹配。比如用 Chrome 131 的 TLS 指纹配置但 User-Agent 写的是 Chrome 124，Cloudflare 的 bot detection 会立即发现这种不一致。

**正确做法**：TLS profile 和 UA 必须成对配置：

```python
PROFILES = [
    {
        "tls": "chrome131",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/131.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Not=A?Brand";v="99", "Chromium";v="131"'
    },
    {
        "tls": "safari18",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) ... Safari/605.1.15",
        "sec_ch_ua": None  # Safari 不发 sec-ch-ua
    }
]
```

### 6.4 HTTP 协议版本

另一个细节：Stripe 的 API 请求在浏览器中走 **HTTP/2**，但 `payment_intents/confirm` 在某些实现中用 HTTP/1.1 反而更稳定。

HAR 中观察到：
- `confirmation_tokens`：HTTP/2
- `payment_intents/confirm`：可以 HTTP/1.1
- `payment_pages/confirm`：HTTP/2

使用 `curl_cffi` 时默认走 HTTP/2（如果服务端支持），CycleTLS 需要在选项中显式指定。

---

## 七、Stripe.js 指纹参数

Stripe 的 `confirmation_tokens` 和 `payment_intents/confirm` 接口都需要一组指纹参数。这些参数由 Stripe.js 在前端收集，协议支付需要正确模拟：

| 参数 | 含义 | 生成方式 |
|------|------|---------|
| `guid` | 全局唯一 ID | UUID + 6位 hex = 42 字符（见 3.1 节） |
| `muid` | 设备 ID | 同 guid 格式，42 字符 |
| `sid` | 会话 ID | 同 guid 格式，42 字符 |
| `time_on_page` | 页面停留时间 | 随机 8-30 秒（模拟真实用户） |
| `key` | Publishable Key | 从 Checkout Session 获取 |
| `_stripe_version` | API 版本 | 从 Stripe.js 的 basil 部署中提取 |

### 7.1 m.stripe.com/6 — 指纹注册

在所有业务请求之前，Stripe.js 会向 `m.stripe.com/6` 发送 4 次 POST 请求注册设备指纹。HAR 中的完整调用链：

```
POST https://m.stripe.com/6  (×4)
```

每次请求的 body 是 `application/x-www-form-urlencoded`，包含：

```
v2 = 1
id = <stripe_js_id>     # 与 confirmation_tokens 中的 guid 不同
tag = <event_tag>
src = js
a = <JSON编码的分析数据>
```

`tag` 的值依次为：
1. `stripejs-init-started`
2. `stripejs-init-complete`
3. `adyen-component-loaded`（如果有 Adyen）
4. `payment-element-mounted`

`a` 字段包含浏览器环境的详细指纹数据（屏幕尺寸、时区、语言、plugin 列表等）。

**实际影响**：不发这些请求也能支付成功，但长期使用同一个 `guid`/`muid` 而从未注册过指纹可能触发 Stripe Radar 的异常检测。建议至少发一次 `stripejs-init-complete`。

### 7.2 r.stripe.com/b — 遥测上报

Stripe.js 还会持续向 `r.stripe.com/b` 发送遥测数据：

```
POST https://r.stripe.com/b
Content-Type: text/plain

{JSON payload}
```

这个请求的 payload 是 JSON（不是 form-urlencoded），包含支付流程中的各种事件指标（加载时间、渲染时间、错误数）。

```json
{
  "type": "measurement",
  "event_name": "paymentElement.mount",
  "metrics": {"duration": 342},
  "client_session_id": "<UUID>",
  "publish_key": "pk_live_xxx"
}
```

**实际影响**：纯可选。不发不影响支付成功。但如果你的实现在生产中运行，偶尔发几次遥测可以让你的流量看起来更像真实浏览器。

### 7.3 动态提取 Stripe.js 版本

Stripe.js 的版本（`_stripe_version`）和构建哈希（`rv`/`sv`）不是固定的，需要从 Stripe 的部署状态接口动态提取：

```javascript
// 获取当前 Stripe.js 部署信息
const status = await fetch('https://js.stripe.com/deploy_status_henson.json');
const { basil } = await status.json();
// basil.rv = "2025-03-31" → _stripe_version = "2025-03-31.basil"
```

Custom 模式只需要基础版本：`2025-03-31.basil`

Hosted 模式需要追加 beta flags：
```
2025-03-31.basil; checkout_server_update_beta=v1; custom_checkout_beta=v1; ...
```

这些 beta flags 从 `deploy_status_henson.json` 的 metadata 或 checkout 页面的初始化脚本中提取。Stripe 大约每 1-2 周更新一次部署版本。

### 7.4 js_checksum 和 rv_timestamp

Hosted 模式的 `payment_pages/confirm` 需要两个动态校验值：

- **`js_checksum`**：当前 Stripe.js bundle 的 SHA 校验和，从 deploy status 提取
- **`rv_timestamp`**：当前 Stripe.js 的部署时间戳（Unix 毫秒），也从 deploy status 提取

这两个值随 Stripe.js 版本更新而变化。如果使用过期的 checksum/timestamp，confirm 可能会被静默拒绝。

```python
deploy = requests.get("https://js.stripe.com/deploy_status_henson.json").json()
js_checksum = deploy["basil"]["js_checksum"]
rv_timestamp = deploy["basil"]["rv_timestamp"]
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

这意味着整个支付流程中的所有请求（从创建 session 到 confirm）必须绑定同一个代理出口。如果代理池做了负载均衡，需要在支付流程中"钉住"一个代理节点。

### 8.4 代理类型选择

| 代理类型 | 适用场景 | 风险 |
|---------|---------|------|
| 住宅代理（Residential） | Stripe API / 平台 API | 最安全，IP 信誉高 |
| ISP 代理（Static Residential） | 长期固定使用 | 中等，某些已被标记 |
| 数据中心代理（Datacenter） | 测试/开发 | 高风险，Stripe Radar 会标记 |
| 移动代理（Mobile） | 高价值交易 | 最安全但最贵 |

生产环境建议住宅代理。数据中心 IP 在 Stripe 的风控系统中通常有较高的 risk score。

### 8.5 代理故障降级

代理不可用时的处理策略：

```python
async def get_proxy_with_fallback(pool, country):
    proxy = await pool.acquire(country=country)
    if proxy:
        return proxy
    # 降级：尝试其他国家的代理
    proxy = await pool.acquire(country="US")
    if proxy:
        return proxy
    # 最终降级：直连（仅限测试环境）
    if config.allow_direct:
        return None
    raise NoProxyAvailableError()
```

**注意**：不要在生产环境用直连降级——数据中心 IP 直连 Stripe 几乎必被拒。

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

### 9.1 Decline 错误分类

Stripe 的卡拒绝错误不是一个笼统的"失败"，而是分为可重试和不可重试两类：

**可重试（换卡后重试）**：
- `generic_decline` — 最常见，通常是风控拒绝，换卡几乎总能过
- `insufficient_funds` — 余额不足，充值后或换卡可过
- `processing_error` — Stripe 侧临时错误，直接重试

**不可重试（放弃本次 session）**：
- `stolen_card` / `lost_card` — 卡已被标记，不能再用
- `card_not_supported` — 卡类型不支持（如某些预付卡）
- `currency_not_supported` — 卡不支持目标币种

**需要特殊处理**：
- `incorrect_cvc` — CVC 错误，检查是否传错了
- `expired_card` — 卡过期，需要从卡池中移除
- `card_velocity_exceeded` — 卡的交易频率超限，冷却后可重试

### 9.2 Fast-Path 优化

一个重要的状态机优化：**如果 PI 已经 `succeeded`，跳过 hCaptcha**。

HAR 中发现，有时 confirm 返回 `requires_action`（hCaptcha challenge），但 PI 实际上已经扣款成功。这时如果盲目去解 captcha，反而可能出错。

正确做法是在收到 `requires_action` 后，**先查询 PI 状态**：

```python
pi = stripe.get(f"/v1/payment_intents/{pi_id}", key=pk_live)
if pi["status"] == "succeeded":
    # 已经扣款成功，跳过 captcha
    return PaymentResult.SUCCESS
elif pi["status"] == "requires_action":
    # 确实需要解 captcha
    solve_hcaptcha(pi)
```

### 9.3 Hosted 模式轮询

cs_live_ 模式在 confirm 之后需要轮询 `payment_page` 状态：

```
POST https://api.stripe.com/v1/payment_pages/{cs_live_xxx}/poll
→ {"payment_intent": "pi_xxx", "status": "open"}  // 等待中
→ {"payment_intent": "pi_xxx", "payment_object_status": "requires_action"}  // 需要 captcha
→ {"payment_intent": "pi_xxx", "payment_object_status": "succeeded"}  // 完成
```

轮询间隔建议 2-3 秒，最多轮询 60 秒。如果超时未变化，检查是否需要手动 approve。

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

这对于调试非常重要：你可以验证整个流程（创建 session、生成 token、税务计算）都正确，而不实际扣钱。

### 10.3 不要存储敏感数据

- 信用卡号仅在内存中使用，支付完成后立即清除
- Session token 不应写入日志（log 中用 `***` 替代）
- 代理凭据不要硬编码，用环境变量或加密存储
- Stripe Publishable Key 可以写入代码（它本来就是公开的），但 Secret Key 绝不能出现在客户端

### 10.4 请求节奏模拟

纯协议支付的一个风险是请求速度**太快**。浏览器用户从打开支付页面到点击确认，通常需要 15-60 秒。如果你的自动化在 2 秒内完成全部请求，Stripe Radar 可能标记为异常。

建议在关键步骤间加入随机延迟：

```python
await sleep(random.uniform(1.5, 3.0))   # 创建 session 后
await sleep(random.uniform(0.8, 2.0))   # 更新税务后
await sleep(random.uniform(1.0, 2.5))   # 创建 token 后
await sleep(random.uniform(0.5, 1.5))   # confirm 前
```

总时间控制在 8-30 秒之间比较自然。

### 10.5 并发控制

批量处理多个账号时，不要让所有请求同时发出：

- **Stripe API**：有 rate limit，同一 publishable key 下大量并发 confirm 会触发 429
- **平台 API**：多个账号同时操作可能触发风控
- **代理池**：每个代理 IP 上同时只运行 1-2 个支付流程

建议使用信号量（semaphore）限制并发：

```python
sem = asyncio.Semaphore(3)  # 最多同时处理 3 个支付
async with sem:
    await process_payment(account)
```

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

## 推荐：虚拟卡平台

协议支付离不开信用卡。如果你需要一张支持 Stripe 的虚拟信用卡用于订阅海外 SaaS 服务（ChatGPT、Claude、Cursor 等），推荐 **ZovoCard**：

- 支持 Visa / Mastercard，全球 Stripe 商户可用
- 即开即用，无需实体卡，支持 USDT 充值
- 多卡管理，适合批量订阅场景

<a href="https://zovocard.com/register?invite=DW6AYPAP" target="_blank" rel="noopener" style="display:inline-block;padding:8px 20px;font-size:14px;color:#fff;background:#6366f1;border-radius:6px;text-decoration:none;font-weight:600;">注册 ZovoCard →</a>

---

*如果你对支付安全感兴趣，欢迎加微信群交流。*
