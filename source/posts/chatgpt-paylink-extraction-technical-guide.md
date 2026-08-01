---
title: "提链 — ChatGPT 跨区支付链接提取的完整技术拆解"
date: 2026-08-01T20:00:00+08:00
draft: false
weight: 1
categories: ["漏洞分析", "支付安全", "Web 安全"]
tags: ["ChatGPT", "Stripe", "提链", "跨区支付", "iDEAL", "UPI", "本地支付", "Checkout Session"]
description: "完整拆解 ChatGPT 提链技术：从 Session Token 出发，通过 12 步协议流程构造 Stripe Checkout Session，最终提取 iDEAL/UPI/PIX/Kakao Pay 等本地支付链接。附带八种支付方式的技术对比和完整代码分析。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **⚠️ 免责声明**：本文仅供安全研究与技术讨论。文中不提供可直接复用的攻击工具或完整利用脚本。本文目的是帮助开发者理解 Stripe 跨区支付的工作原理，以及为什么某些支付方式在不同区域可见性不同。提链工具不篡改金额、不注入优惠码，用户以正常价格通过本地支付方式完成订阅。

---

## 前言

"提链"这个词，最近在各种 ChatGPT 合租群、代充群里频繁出现。

什么意思呢？简单来说：**把 ChatGPT 的信用卡结账页面，转换成一个本地支付方式（iDEAL / UPI / PIX / Kakao Pay / GCash…）的跳转链接。**

你可能会问——OpenAI 不是只接受信用卡吗？

准确地说，**OpenAI 的前端只展示信用卡表单**。但后端用的是 Stripe，而 Stripe 在全球支持几十种本地支付方式。这些支付方式对应的国家、货币、支付类型都不同，OpenAI 在结账页面上做了筛选，只让你看到"信用卡 / 借记卡"一个选项。

但 Stripe 的能力是在的。只要你能在创建 Checkout Session 时告诉 Stripe "我要用荷兰 iDEAL 支付"——Stripe 就会老老实实返回一个 iDEAL 的跳转链接。

提链，就是**从 Stripe 的 Checkout Session 里把这个跳转链接提出来**。

上一篇文章我们拆了 [0 PHP 白嫖 ChatGPT Plus](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/) 的跨区定价混淆攻击。那个是利用区域信号碎片化 + 工具注入参数让金额变成 0——纯粹的漏洞利用，现在大概率已经被修了。

而提链不同。**提链是正常的商业行为**——用户以当地正常价格、通过当地正常的支付方式付款。只不过 OpenAI 的 UI 不展示这些选项，你得自己绕过前端的限制，直接和 Stripe 对话。

今天把它从协议层完整拆开。

---

## 一、为什么需要提链——信用卡的困境

全球 80 亿人，有信用卡的不到 20 亿。

印度人用 UPI，巴西人用 PIX，荷兰人用 iDEAL，韩国人用 Kakao Pay，越南人用 MoMo。这些不是什么小众支付方式——它们在各自国家的渗透率往往超过 70%。

但 OpenAI 的结账页面只给你一个 Stripe Elements 信用卡表单：卡号、有效期、CVC。没有信用卡？不好意思。

讽刺的是，Stripe 本身是支持这些本地支付方式的。OpenAI 创建 Checkout Session 时，就是通过 `billing_details.country` 和 `billing_details.currency` 来决定哪些支付方式可用。

| 国家 | 货币 | 可用支付方式 | 月费 |
|------|------|-------------|------|
| ??🇱 荷兰 | EUR | iDEAL | €20 |
| 🇮🇳 印度 | INR | UPI | ₹1,950 |
| 🇧🇷 巴西 | BRL | PIX | R$99.90 |
| ??🇭 瑞士 | CHF | TWINT | CHF 20 |
| 🇰🇷 韩国 | KRW | Kakao Pay | ₩26,400 |
| 🇵🇱 波兰 | PLN | BLIK | zł79.99 |
| 🇻🇳 越南 | VND | MoMo | ₫460,000 |
| ??🇭 菲律宾 | PHP | GCash | ₱990 |

这些价格不是我编的——它们真实存在于 Stripe 的 Checkout Session 响应里。OpenAI 按照区域设置了不同的定价，Stripe 负责处理。只是 OpenAI 的前端选择性地隐藏了这些支付方式。

提链工具要做的，就是**绕过前端的限制，以目标国家/货币创建 Checkout Session，然后从 Stripe 的 confirm 响应中提取第三方支付的跳转链接**。

---

## 二、提链的技术原理——四步拆解

### Step 1：获取 Access Token

登录 chatgpt.com，在浏览器中打开：

```
https://chatgpt.com/api/auth/session
```

返回一个 JSON：

```json
{
  "user": { "id": "user-xxx", "name": "...", "email": "..." },
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

`accessToken` 是一个标准 JWT，有效期通常 5~10 分钟。它是后续所有 API 调用的认证凭据。

> 提链工具同时也支持直接粘贴 `__Secure-next-auth.session-token` cookie——这个 cookie 可以用来换取新的 access token。但最简单的方式还是直接复制上面的 JSON。

### Step 2：创建 Checkout Session

用 Access Token 调用 OpenAI 的 checkout API：

```http
POST https://chatgpt.com/backend-api/payments/checkout
Authorization: Bearer eyJ...

{
  "entry_point": "all_plans_pricing_modal",
  "plan_name": "chatgptplusplan",
  "billing_details": {
    "country": "NL",
    "currency": "EUR"
  },
  "checkout_ui_mode": "custom"
}
```

关键参数是 `billing_details` 里的 `country` 和 `currency`。这两个字段决定了 Stripe 在初始化支付页面时会提供哪些支付方式。传 `NL` + `EUR`，Stripe 就会在 `payment_method_types` 里包含 `ideal`。

响应：

```json
{
  "checkout_session_id": "oaics_xxxxxxxxxxxx",
  "processor_entity": "openai_llc",
  "publishable_key": "pk_live_xxxxxxxxxxxx",
  "payment_method_types": ["card", "ideal"]
}
```

`oaics_` 前缀是 OpenAI 定制的 Stripe Checkout Session ID 格式。

### Step 3：Stripe 协议流程

拿到 Checkout Session ID 后，需要完成一系列 Stripe API 调用。这是提链的核心技术含量所在——不是简单地 POST 一个接口就完事了。

完整的协议流程有 12 步：

```
┌──────────────────────────┐
│  1. Session Refresh       │  (用 cookie 换新的 AT)
│  2. Create Checkout       │  (拿 AT 创建 checkout session)
│  3. Stripe Init           │  (初始化支付页面状态)
│  4. Update OAI Taxes      │  (通知 OpenAI 更新税务)
│  5. Stripe Tax Region     │  (更新 Stripe 税务区域)
│  6. Stripe Customer Data  │  (更新客户信息)
│  7. OAI Checkout Snapshot │  (保存 checkout 快照)
│  8. Pre-Confirm           │  (部分支付方式需要)
│  9. Create Payment Method │  (创建 PM，类型=ideal/upi/pix...)
│ 10. Confirm               │  (确认支付，触发重定向)
│ 11. Approve               │  (如果需要额外批准)
│ 12. Extract Redirect URL  │  (从 confirm 响应中提取跳转链接)
└──────────────────────────┘
```

每一步都有自己的参数格式和必要的状态管理。Stripe 的 Checkout Session 是有状态的——它跟踪你的 `eid`（element ID）、`mrid`（merchant reference ID）、`expected_amount` 等等。如果你跳过了某一步或者参数不对，后续步骤就会报错。

### Step 4：提取支付链接

第 10 步 `Confirm` 之后，如果支付方式是重定向类型（iDEAL、UPI、PIX 等都是），Stripe 会在响应中返回一个 `redirect_url`：

```json
{
  "status": "requires_action",
  "next_action": {
    "type": "redirect_to_url",
    "redirect_to_url": {
      "url": "https://hooks.stripe.com/redirect/authenticate/src_xxx?client_secret=..."
    }
  }
}
```

这个 URL 就是最终的支付链接。用户在浏览器中打开它，会被重定向到对应的支付方式页面（iDEAL 的银行选择页、UPI 的付款确认页、PIX 的二维码页面等）。完成支付后，Stripe webhook 通知 OpenAI，OpenAI 确认订阅生效。

**整个流程，金额由 Stripe 的价格表决定，提链工具不篡改任何金额字段。** 用户付的就是对应国家/地区的标准月费。

---

## 三、Stripe Checkout Session 的内部结构

拆开看，Stripe Checkout Session 里藏了不少有趣的东西。

第 3 步 `Stripe Init` 调用的是：

```http
POST https://api.stripe.com/v1/payment_pages/{oaics_xxx}/init
```

响应中最关键的几个字段：

```json
{
  "payment_method_types": ["card", "ideal"],
  "line_items": [{
    "description": "ChatGPT Plus subscription",
    "amount": 2000,
    "currency": "eur"
  }],
  "shipping_address_collection": null,
  "payment_method_configuration": {
    "merchant_reference_id": "mri_xxx",
    "customer_session_client_secret": "cuss_xxx"
  },
  "session_id": "oaics_xxx"
}
```

`payment_method_types` 是关键——它决定了这个 Checkout Session 支持哪些支付方式。同一个接口，传不同的 `country` / `currency`，返回的 `payment_method_types` 就不同。

这也解释了为什么 OpenAI 前端只显示信用卡——它在创建 Checkout Session 时没有传目标国家的 `billing_details`，或者传的是用户账号的注册国家（通常是 US），所以 Stripe 只返回 `["card"]`。

---

## 四、八种支付方式的技术对比

每种支付方式在 Stripe 层面的行为略有不同：

| 支付方式 | PM Type | 国家 | 货币 | 需要 pre_confirm | 重定向类型 | 特殊处理 |
|---------|---------|------|------|:---:|------|------|
| iDEAL | `ideal` | NL | EUR | ✗ | 银行选择页 | 无 |
| UPI | `upi` | IN | INR | ✗ | VPA 输入页 | 无 |
| PIX | `pix` | BR | BRL | ✗ | 二维码页 | 无 |
| TWINT | `twint` | CH | CHF | ✗ | App 跳转 | 无 |
| Kakao Pay | `kakao_pay` | KR | KRW | ✓ | Kakao 确认页 | 需要 pre_confirm 调用 |
| BLIK | `blik` | PL | PLN | ✗ | 6位码输入 | 无 |
| MoMo | `momo` | VN | VND | ✓ | MoMo App | 需要 pre_confirm 调用 |
| GCash | `gcash` | PH | PHP | ✗ | GCash 确认页 | 无 |

大多数支付方式流程一致：创建 PM → Confirm → 提取 redirect URL。但 Kakao Pay 和 MoMo 需要额外的 `pre_confirm` 调用——如果跳过这一步，Confirm 会返回 `incomplete` 状态，没有 redirect URL。

`pre_confirm` 的请求格式：

```http
POST https://api.stripe.com/v1/payment_pages/{oaics_xxx}/pre_confirm
Content-Type: application/x-www-form-urlencoded

expected_payment_method_type=kakao_pay
```

看起来简单，但如果你不知道有这一步，Kakao Pay 的提链就会卡在最后一步——所有参数都对了，就是拿不到链接。这类细节只有通过 HAR 抓包 Stripe 的完整结账流程才能发现。

---

## 五、从 0 PHP 到提链——漏洞与工具的边界

上一篇文章分析了 [0 PHP 攻击](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/)，里面提到第三方工具在创建 Checkout Session 时可能注入了零元参数（如 `promo_campaign`）。那么问题来了：

**提链工具和那个"CDK 提炼"工具是一回事吗？**

不是。区别在于：

| | 0 PHP "提炼"工具 | 正常提链工具 |
|---|---|---|
| 目的 | 白嫖（amount = 0） | 正常付款 |
| 是否注入优惠码 | 是（`promo_campaign`、`discount` 等） | 否 |
| 金额来源 | 工具操纵 | Stripe 价格表 |
| 合法性 | 灰色/违法 | 正常商业行为 |

正常的提链工具**不注入任何优惠参数**。它只是：

1. 用你的 AT 创建一个以目标国家/货币计价的 Checkout Session
2. 走完 Stripe 的协议流程
3. 把 redirect URL 返回给你

你付的是 Stripe 价格表上对应区域的标准价格——荷兰 €20/月，印度 ₹1,950/月，巴西 R$99.90/月。没有优惠码，没有金额篡改。

这也是我们的工具（[redeemai.me/paylink](https://redeemai.me/paylink)）的设计原则：**不注入 `promo_campaign`，不传 `discount`，不覆盖 `amount`。** 工具只做一件事——把 Stripe 的本地支付能力释放出来，让没有信用卡的用户也能正常订阅。

---

## 六、协议细节——那些让你卡住的坑

如果你自己尝试过写提链脚本，你一定踩过这些坑。

### 坑 1：IP 一致性

Stripe Checkout Session 在创建和确认时需要使用同一个 IP。如果你用代理 A 创建了 Checkout Session，又用代理 B 去 Confirm——Stripe 会返回 `invalid_request_error`。

这不是 Stripe 的 bug，是安全机制。Stripe 检测到 session 的创建 IP 和确认 IP 不一致，会认为可能是中间人攻击。

解决方案：**整个 12 步流程使用同一个 HTTP client（或 cookie jar），确保所有请求走同一个出口 IP。**

### 坑 2：`expected_amount`

Stripe 的 Confirm 请求需要传 `expected_amount` 参数，值必须和 Checkout Session 的金额一致。这个值从哪来？

最准确的来源是第 4 步 `Update Taxes` 的响应。这一步把账单地址传给 OpenAI，OpenAI 计算含税金额后写入 Checkout Session，然后返回一个 snapshot，里面有 `amount_total`：

```json
{
  "snapshot": {
    "amount_total": 2000,
    "currency": "eur"
  }
}
```

如果你用 Init 步骤的金额去 Confirm，可能会因为税后金额不一致而失败。

### 坑 3：Stripe Session State

Stripe 的 Checkout Session 维护了一个内部状态。每次 API 调用后，响应里都会更新 `eid`、`mrid` 等字段。下一次调用必须带上最新的状态值。

这意味着你不能简单地并行调用 12 步——必须严格按顺序执行，每一步用上一步返回的最新状态。

### 坑 4：`Accept-Language` 和 `guid`

这两个是容易忽略的细节：

- Stripe API 会根据 `Accept-Language` 请求头返回不同的 `locale` 配置。如果你不传，默认是 `en-US`，但某些支付方式在特定 locale 下行为不同。
- Stripe 的某些内部 API 需要一个 `guid` 参数，格式是 `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`（UUID v4）。不是随便写的——格式不对会被拒绝。

### 坑 5：超时

整个流程从创建 Checkout Session 到拿到 redirect URL，通常需要 10~30 秒。某些支付方式（如 Kakao Pay）可能需要更长时间，因为 Stripe 需要和第三方支付系统交互。

如果 Confirm 之后没有立刻返回 redirect URL，需要轮询 Init 接口。URL 可能在 Confirm 后几秒到几十秒内才出现。我们的工具最多等 90 秒——超过这个时间通常意味着哪里出了问题。

---

## 七、我们的实现——redeemai.me/paylink

说了这么多原理，说说我们自己怎么做的。

工具地址：[https://redeemai.me/paylink](https://redeemai.me/paylink)

### 技术栈

- **后端**：Go（跑在 Linux 服务器上，走代理池确保 IP 一致性）
- **前端**：Vue 3 + TypeScript（三步向导 UI，支持中/英/俄三语）
- **反滥用**：Cloudflare Turnstile（每次提取前验证人机）
- **速率限制**：每 IP 每分钟 5 次

### 使用流程

1. 登录 chatgpt.com，打开 `chatgpt.com/api/auth/session`，复制全部 JSON（或者只复制 `accessToken` 字段）
2. 到 [redeemai.me/paylink](https://redeemai.me/paylink)，粘贴 JSON，选择支付方式和套餐
3. 通过 Turnstile 验证，点击"提取支付链接"
4. 等待 10~90 秒，得到支付链接
5. 在浏览器中打开链接，完成支付

### 支持的组合

- **支付方式**：iDEAL / UPI / PIX / TWINT / Kakao Pay / BLIK / MoMo / GCash
- **套餐**：Plus ($20) / Pro ($200) / Pro 5X ($100)

### 代理池

整个 12 步流程通过我们的代理池执行，确保所有请求使用同一个出口 IP。如果当前代理被 OpenAI 标记（返回 401/403），系统会自动轮转到下一个代理重试。

### 不做什么

- **不存储你的 Access Token**——用完即弃，不写数据库
- **不注入优惠码**——没有 `promo_campaign`，没有 `discount`
- **不篡改金额**——Stripe 价格表说多少就是多少
- **不代付**——链接直接返回给你，你自己在浏览器里完成支付

---

## 八、为什么 OpenAI 不直接提供这些支付方式？

好问题。Stripe 支持它们，OpenAI 用的是 Stripe，为什么不在结账页面上显示？

几个可能的原因：

1. **合规成本**：每个国家的本地支付方式有不同的合规要求（反洗钱、实名验证等）。支持 iDEAL 意味着要满足荷兰的金融监管要求。

2. **退款风险**：某些本地支付方式的退款/dispute 流程和信用卡不同。PIX 的退款机制、UPI 的 chargeback 流程，都需要额外的运营投入。

3. **税务复杂度**：不同国家的增值税率不同，账单格式要求不同。OpenAI 需要为每个国家维护正确的税务处理。

4. **优先级**：信用卡覆盖了 OpenAI 的核心市场（北美、欧洲）。本地支付方式对应的市场（东南亚、拉美、南亚）目前可能不是优先级。

但 Stripe 的能力已经在那里了。`payment_method_types` 里已经包含了这些方式。OpenAI 只需要在前端把选项打开。在此之前——提链工具就是桥梁。

---

## 九、和 0 PHP 漏洞的关系——一张图说清

```
                ┌───────────────────────────────────┐
                │         正常提链工具               │
                │  country=NL, currency=EUR          │
                │  NO promo_campaign                 │
                │  → amount = €20 (Stripe 价格表)    │
                │  → redirect URL → iDEAL 付款       │
                └───────────┬───────────────────────┘
                            │
          同一个 API        │        同一个 API
                            │
                ┌───────────▼───────────────────────┐
                │   OpenAI /payments/checkout API    │
                │   + Stripe Checkout Session        │
                └───────────┬───────────────────────┘
                            │
                ┌───────────▼───────────────────────┐
                │        0 PHP 攻击工具              │
                │  country=PH, currency=PHP          │
                │  + promo_campaign injection         │
                │  + cross-region confusion           │
                │  → amount = ₱0 (被操纵)            │
                │  → PH BIN 卡完成支付               │
                └───────────────────────────────────┘
```

同一个 API，两种用法：

- **提链**：合法利用 Stripe 的本地支付能力，正常价格
- **0 PHP**：利用跨区信号碎片化 + 参数注入，把价格打到零

提链不是漏洞利用。它只是 Stripe 本来就有的能力，被 OpenAI 前端隐藏了而已。

---

## 十、写在最后

提链的本质是一个简单的事实：**Stripe 是一个全球支付平台，它天然支持几十种本地支付方式。OpenAI 的 UI 做了限制，但 API 没有。**

从技术角度看，12 步协议流程的每一步都有其必要性——IP 一致性、状态管理、税务更新、pre_confirm。跳过任何一步都会导致最终拿不到 redirect URL。这也是为什么"提链"不是简单地抓个包就能搞定的——你需要理解 Stripe 的完整 Checkout 流程。

从商业角度看，提链让全球用户有了一种不依赖信用卡的方式来使用 ChatGPT。在信用卡渗透率不到 10% 的印度，UPI 是 8 亿人的默认支付方式。提链工具不是在做什么灰色的事——它只是把 Stripe 的能力释放给了真正需要的人。

工具地址：[https://redeemai.me/paylink](https://redeemai.me/paylink)

试试看？

---

## 附录：直卡绑定——另一条路

除了提链，还有一种完全不同的思路：**直接给 ChatGPT 账号绑一张卡，然后正常走 checkout。**

这就是"直卡焚决"方法的核心。它不绕过前端、不走第三方支付——它解决的是"没有美区信用卡"这个前置问题。

### 原理

OpenAI 的 `/backend-api/payments/payment_method` 接口支持创建 Stripe `SetupIntent`——这是 Stripe 的"先绑卡不扣款"机制。绑上之后，下次走 checkout 时就有卡可用了。

配套的控制台脚本（在 chatgpt.com 的 Console 里运行）做了这几件事：

1. **自动发现 Stripe 公钥**——OpenAI 有两个 Stripe 商户分片（`KslHRdbaPg` 和 `C6h1nxGoI3`），脚本通过 `retrieveSetupIntent` 自动匹配当前账号属于哪个分片
2. **创建 SetupIntent**——调用 OpenAI 的 `payment_method` API，拿到 `client_secret`
3. **渲染 Stripe Card Element**——在页面上弹出一个模态框，内嵌 Stripe 的标准卡输入组件
4. **确认绑定**——`stripe.confirmCardSetup` + `set_as_default_payment_method: true`

```javascript
// 关键调用
const result = await stripe.confirmCardSetup(clientSecret, {
  payment_method: {
    card: cardElement,
    billing_details: { name },
    allow_redisplay: 'always'
  },
  set_as_default_payment_method: true
});
```

绑卡成功后，脚本还会调用 `/backend-api/payments/payment_methods` 拉取当前账号的所有支付方式列表，用 `console.table` 打印出来。你可以看到新绑的卡已经成为默认支付方式。

### 和提链的关系

- **直卡绑定**：解决"没有卡"的问题。需要有一张能过 Stripe AVS/3DS 验证的实体或虚拟卡。
- **提链**：解决"不想/不能用信用卡"的问题。走本地支付方式，完全不涉及信用卡。

两种方法互补——有卡的用直卡，没卡的用提链。

---

## 相关阅读

- [0 PHP 白嫖 ChatGPT Plus — 跨区定价混淆攻击的完整技术拆解](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/)
- [ChatGPT Plus Google Play 订阅转移漏洞分析](/posts/gpt-plus-google-play-subscription-transfer/)
- [RevenueCat 凭证转移漏洞——匿名购买 + restore 归属偷渡](/posts/gpt-plus-exploit-revenuecat-vulnerability/)
- [Google Play CC Max 比例分配漏洞](/posts/google-play-ccmax-proration-vulnerability-2026/)
