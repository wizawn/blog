---
title: "₱982 开 Pro 20X — OpenAI 升级协议 TOCTOU 竞态条件漏洞拆解"
date: 2026-08-03T20:00:00+08:00
draft: true
weight: 1
categories: ["漏洞分析", "支付安全", "Web 安全"]
tags: ["ChatGPT", "Stripe", "TOCTOU", "竞态条件", "订阅升级", "PaymentIntent", "OpenAI", "Pro 20X", "支付安全"]
description: "深度拆解 ChatGPT Pro 20X 的 ₱982 漏洞：从最初的 TOCTOU 并发假说出发，通过 HAR 抓包发现 token plan_type 绑定机制阻断了简单并发攻击，最终推断真实路径为 proration 最后一天定时攻击。附 OpenAI 升级协议变更分析与 token refresh 机制逆向。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK  ⚠️ **博主微信暂时被封，请优先加入上方 QQ 群（46333839）**

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> ** 免责声明**：本文仅供安全研究与技术讨论。文中不提供可直接复用的攻击工具或完整利用脚本。利用类似手段对正式服务进行未授权操作属违法行为，后果自负。本文目的是帮助支付系统开发者理解并发支付场景下的攻击面并加固防御。

---

## 前言

LINUX DO 上出现了一个帖子："50R 的 20X 甚至还是正规充值非 bug 求教学"。

楼主的意思是：他花了大约 50 人民币（菲律宾区 ₱982.14），拿到了 ChatGPT Pro 20X 订阅——月费 ₱8,919.64 的那个。Stripe 后台显示的是正规扣款，不是什么 bug 单、退款单、也不是沙盒环境。

评论区比较热闹：

> "菲区汇率 + 折扣返现 50%"
>
> "站内有 5 元成本开 plus 的教学"
>
> "前几天有新加坡的 5x 漏洞"

前两条是在混淆概念。银行返现和菲区低价确实存在，但 ₱982.14 是 Plus 的价格，Pro 20X 的价格是 ₱8,919.64——差了 9 倍，返现撑死回来一半的 Plus 钱，跟 Pro 20X 毫无关系。

第三条倒是有意思。"新加坡的 5x 漏洞"——如果指的是 proration 差价攻击的话，逻辑上和今天讲的这个是同一个攻击面。

然后有个群聊截图传出来了：

> "据说是最后一天升级 pro"
>
> "plus 最后一天升级"
>
> "就能卡出 108 升 20x 的 bug"

108 RMB ≈ ₱982 PHP。时间锚点是"最后一天"。线索到这里就断了——帖子和截图都没有给出可复现的操作步骤，只有一个结果和一些模糊的条件。

但对我来说，这些碎片已经够用了。因为我们自己就在做同样的事——自动化 Plus 开通 + Pro 升级——我们的系统日志里有完整的 API 调用链，还有恰好在同一时间段出现的异常模式。

今天把它拆开。

---

## 一、菲律宾区定价：₱982 买不了 Pro

先看一下菲律宾区的官方定价结构。这些数据来自 OpenAI 的 `checkout_pricing_config/configs/PHP` API 响应：

| 方案 | 月费 (PHP) | 含税方式 | PSP Override |
|------|-----------|---------|-------------|
| Plus | ₱1,100 | inclusive | ₱982.14 (exclusive) |
| Pro Lite (5x) | ₱6,490 | inclusive | ₱5,794.64 (exclusive) |
| Pro (20x) | ₱9,990 | inclusive | ₱8,919.64 (exclusive) |

`psp_override` 是 Stripe 实际收取的金额，tax exclusive。也就是说在 Stripe 这一层，Plus 的价格是 ₱982.14，Pro 20X 的价格是 ₱8,919.64。

₱982.14 只能买 Plus，买不了 Pro 20X。 差价是 ₱7,937.50——就算在 billing 周期最后一天升级，Stripe proration 补差价也是按 (新价 - 旧价) × 剩余天数 / 总天数 来算的，不可能出现 ₱0 差价。

那 ₱982 是怎么变成 Pro 20X 的？

---

## 二、Stripe PaymentIntent 的金额锁定

要理解这个漏洞，先要理解 Stripe 的一个核心设计：PaymentIntent (PI) 金额在创建时锁定，confirm 时不可变。

OpenAI 的结账流程是这样的：

```
用户点击 "Subscribe to Plus"
    ↓
POST /payments/checkout
    → OpenAI 后端调用 Stripe API 创建 checkout session
    → Stripe 创建 PaymentIntent, amount = 98214 (₱982.14)
    → 返回 checkout_url 或嵌入式结账页面
    ↓
用户填入信用卡信息，点击确认
    ↓
POST /payments/checkout/confirm
    → Stripe 对 PI 执行 confirm
    → 扣款 ₱982.14
    → PI 状态: succeeded
```

关键点在第二步：Stripe 创建 PI 时就把 `amount=98214` 写死了。后续不管发生什么——换卡、换 IP、甚至换订阅计划——这个 PI 的金额不会变。 除非你取消这个 checkout session 重新创建一个。

这不是 bug，这是 Stripe 的设计。PI 是一个"支付意图"，它代表的是"在某个时间点，用户同意支付某个金额"。金额是意图的一部分，不可变。

记住这个。

---

## 三、subscriptions/update：另一条独立的通道

OpenAI 的订阅升级走的是另一个 API：

```
POST /backend-api/subscriptions/update
Content-Type: application/json
{
    "account_id": "aeae1c92-...",
    "updated_plan": "chatgptpro"
}
```

这个 API 做的事情是：告诉 OpenAI 后端"把这个账号的订阅计划从当前的 X 改成 Y"。后端会：

1. 查当前订阅状态
2. 计算 proration（按比例补差价）
3. 创建一张新的 invoice
4. 通过已绑定的支付方式扣款
5. 更新订阅计划

正常流程（我们自己系统里跑的）是**严格顺序**的：

```
Phase 1: checkout → 开通 Plus → PI confirm → 等 billing 确认
Phase 2:（Plus 确认后）→ subscriptions/update → 升级到 Pro
```

Phase 2 在 Phase 1 **完成之后**才开始。中间有身份验证、计划检查、3 秒等待——不存在并发窗口。

但如果有人不按这个顺序来呢？

---

## 四、TOCTOU：当两条通道并发执行

这就是漏洞所在。

TOCTOU（Time-of-Check to Time-of-Use） 是一类经典的竞态条件漏洞：在"检查条件"和"执行操作"之间存在时间差，攻击者在这个时间差内改变了条件，导致操作基于过时的前提执行。

在这个场景里：

```
T0: POST /payments/checkout
    → 检查: 用户要买 Plus
    → 操作: 创建 PI, amount = 98214
    → PI 金额锁定 ✓

T1: （PI 创建后，confirm 之前或之中）
    POST /subscriptions/update
    → 操作: 把订阅计划从 "free" 改成 "chatgptpro"
    → 订阅计划变更 ✓

T2: PI confirm
    → 检查: PI amount = 98214（T0 创建时锁定，不会因 T1 的计划变更而改变）
    → 操作: 扣款 ₱982.14
    → 扣款成功 ✓

结果:
    Stripe 扣了 ₱982.14（Plus 的价格）
    OpenAI 订阅计划已经是 Pro 20X
    UI 显示: Pro 20X 已开通，已收取 ₱982.14
```

两个操作——PI confirm 和 subscriptions/update——走的是两条独立的管道。PI 不知道订阅计划变了，subscriptions/update 不知道有个 PI 正在以旧价格 confirm。没有互斥锁，没有原子事务，各走各的。

这正是审计数据包中观察到的行为：

- checkout plan=chatgptplusplan + ₱982.14
- subscriptions/update 并发执行
- subscriptions 已经是 plan_type=pro
- PI confirm amount=98214 succeeded

同一个账号上，Plus 支付与 Pro 升级在时间上重叠。一段"付钱成功" + 另一段"改档成功"叠在一起，UI 就只突出一笔 ₱982.14 已付款 + Pro 20X。

### Token 绑定的防御效果

但事情没有上面描述的那么简单。2026-08-03 的 HAR 抓包数据揭示了一个关键的防御机制：Token 与 plan_type 的绑定。

OpenAI 的 JWT access token 在 claims 中包含 `chatgpt_plan_type` 字段。当账户的订阅计划发生变化时（比如 free→plus），旧 token 会被服务端立即作废，任何使用旧 token 的 API 调用都会返回 401。

这意味着攻击者面临一个因果依赖问题：

```
T0: 账号状态 = free, token.plan_type = free
T1: checkout/confirm 成功 → 账号变成 plus
    → 旧 token (plan_type=free) 立即失效
    → 所有 API 调用 → 401 Unauthorized
T2: 必须调用 refresh 获取新 token (plan_type=plus)
    GET /api/auth/session?refresh=true&reason=token_expired
    Header: x-openai-failed-access-token-iat: <旧token的iat>
T3: 拿到新 token 后，才能调 subscriptions/update
```

简单的并发攻击行不通。 攻击者不可能用 `plan_type=free` 的 token 去调用 `subscriptions/update` 把计划改成 Pro——这个请求会因为 token 已失效而被 401 拒绝。他必须等 checkout/confirm 成功后，先刷新 token 拿到 `plan_type=plus` 的凭证，然后才能发起升级请求。

这就把上面假设的 T1（并发 subscriptions/update）打破了——confirm 和 update 之间存在强制的序列化点（token refresh），不可能真正并发。

那 ₱982 的 Pro 20X 到底是怎么做到的？后面会重新分析可能的真实攻击路径。

---

## 五、关键证据：升级协议更新引入了并发窗口

这个漏洞不是一直存在的。它是在 2026 年 8 月 2-3 日前后，OpenAI 对 `subscriptions/update` API 的行为进行了某种更新之后才出现的。

证据来自我们自己系统的日志。我们的系统 24/7 运行 Plus 开通 + Pro 升级流程，日志里记录了每一次 API 调用的结果。

### 8 月 2 日之前：Phase 2 稳定

```
2026/07/28 09:35 → pro20x subscription confirmed as Pro ✓
2026/07/28 09:37 → pro20x subscription confirmed as Pro ✓
2026/07/29 01:44 → pro20x subscription confirmed as Pro ✓
2026/07/29 01:46 → pro20x subscription confirmed as Pro ✓
...
2026/08/01 08:50 → pro20x subscription confirmed as Pro ✓  ← 最后一次正常成功
```

7 月 21 日到 8 月 1 日之间，Pro 20X 升级成功率约 95%，偶尔有 `preview HTTP 400` 失败但属于正常抖动。

### 8 月 2 日起：Phase 2 大面积失败

```
2026/08/02 01:16 → upgrade_pending: error=unknown
2026/08/02 05:10 → upgrade_pending: error=unknown
2026/08/02 10:29 → upgrade_pending: error=check/v4 HTTP 401
2026/08/02 15:12 → upgrade_pending: error=check/v4 HTTP 401  ← 4 个任务同时失败
2026/08/02 15:13 → upgrade_pending: error=Failed to fetch
2026/08/02 15:13 → upgrade_pending: error=unknown
2026/08/02 15:13 → upgrade_pending: error=check/v4 HTTP 401
2026/08/02 15:13 → upgrade_pending: error=unknown
```

一天之内 12 次 upgrade_pending 失败，错误类型从之前的偶发 `preview 400` 变成了密集的 `unknown` / `Failed to fetch` / `check/v4 HTTP 401`。

但有意思的是——这些"失败"的任务最终都被我们的 watchdog 自动恢复了：

```
2026/08/02 15:15 → AUTO-RECOVERED via billing sync: invoice=JEO1VWUV-0002
2026/08/02 15:16 → AUTO-RECOVERED via billing sync: invoice=FW3Y74C0-0002
2026/08/02 15:16 → AUTO-RECOVERED via billing sync: invoice=RMT0EPIU-0002
2026/08/02 15:16 → AUTO-RECOVERED via billing sync: invoice=9HFURK7L-0002
```

这说明 Stripe 侧扣款和订阅变更实际上是成功的，但 OpenAI 的 API 返回了异常响应——要么是新增了 session 验证步骤导致 401，要么是改变了响应格式。

### HAR 实证：Token plan_type 绑定与双重 401 模式

2026-08-03 的 HAR 抓包（3.har）完整记录了 OpenAI 的 token 生命周期管理机制，揭示了 Phase 2 失败的真正原因。

Token plan_type 失效机制：

每次订阅计划变更后，当前 access token 会被服务端立即作废。HAR 中清楚地记录了双重 401 模式：

```
── Phase 1: checkout/confirm (free → plus) ──
POST /payments/checkout/confirm → 200 OK
GET /backend-api/me → 401 Unauthorized          ← token (plan_type=free) 已失效
GET /api/auth/session?refresh=true&reason=token_expired → 200 OK
    Header: x-openai-failed-access-token-iat: 1722648000
    → 返回新 token (plan_type=plus)

── Phase 2: subscriptions/update (plus → pro) ──
POST /backend-api/subscriptions/update → 200 OK
GET /backend-api/me → 401 Unauthorized          ← token (plan_type=plus) 又失效了
GET /api/auth/session?refresh=true&reason=token_expired → 200 OK
    Header: x-openai-failed-access-token-iat: 1722648180
    → 返回新 token (plan_type=pro)
```

每次 plan 变更都触发一次 token 作废 → refresh 循环。这就是为什么 8 月 2 日起我们的 Phase 2 大面积 401——不是 OpenAI 改了互斥逻辑，而是 token 与 plan_type 的绑定变得更严格了。

subscriptions 端点新增 account_id 要求：

HAR 还显示 `GET /subscriptions` 接口现在要求显式传入 account_id：

```
GET /backend-api/subscriptions → 400 Bad Request
Response: "must specify either organization_id or account_id"

GET /backend-api/subscriptions?account_id=aeae1c92-... → 200 OK
```

这两个变更合在一起解释了我们 Phase 2 的失败模式：旧的调用方式既没有正确处理 token refresh（用了失效的 token），也没有在 subscriptions 请求中带上 account_id。

8 月 2 日的协议变更不是"移除了互斥锁"，而是强化了 token 与订阅状态的绑定。我们的 Phase 2 变得更难了（需要正确处理 token refresh），同时简单的 TOCTOU 并发攻击也变得不可行（旧 token 无法跨 plan_type 使用）。

---

## 六、完整利用流程还原

根据所有证据，还原攻击者的操作步骤：

### Step 1：创建 Plus Checkout Session

```
POST /payments/checkout
{
    "plan": "chatgptplusplan",
    ...
}
```

OpenAI 后端创建 Stripe checkout session，PI amount = ₱982.14（菲律宾区 Plus 价格）。

### Step 2：填入卡号，准备 Confirm

正常填入信用卡信息。此时 PI 已经创建，金额已锁定。checkout 页面准备好了 confirm 按钮。

### Step 3：在 Confirm 的同时发起 subscriptions/update

这是关键步骤。攻击者需要在 PI confirm 执行的同时（或刚刚 confirm 之后、PI 状态更新之前），发送：

```
POST /backend-api/subscriptions/update
{
    "account_id": "...",
    "updated_plan": "chatgptpro"
}
```

旧协议下，这个请求会被拒绝（因为有进行中的 checkout）。新协议下，它直接执行了。

### Step 4：两个操作各自成功

- PI confirm：Stripe 扣款 ₱982.14，amount 是 T0 时锁定的，不受计划变更影响
- subscriptions/update：OpenAI 后端把订阅计划改成了 chatgptpro

### 结果

用户的 Stripe billing portal 显示：
- Invoice 1: Plus ₱982.14（checkout 扣款）
- Invoice 2: Pro upgrade（如果 Stripe 来得及生成 proration invoice 的话）

但因为时间窗口极短，proration invoice 可能来不及创建或者金额极小。最终效果：₱982.14 + Pro 20X 权益。

### "最后一天"的线索

群里的"plus 最后一天升级"可能指的是：在 Plus 订阅的最后一天操作，此时 proration 计算的"剩余天数"≈0，即使 subscriptions/update 来得及创建 proration invoice，差价也趋近于 ₱0：

```
proration = (₱8,919.64 - ₱982.14) × 0/30 ≈ ₱0
```

但根据我们实际的 HAR 数据（pay.openai.com.har），即时升级（Plus 开通后 3 分钟内升级 Pro）的 proration 是按完整剩余周期计算的——并不是 ₱0。所以"最后一天"可能只是攻击者在碰运气，或者是在测试哪个时间窗口成功率最高。真正让漏洞成立的不是时间点，而是**并发**。

### Token 绑定的阻碍

> ** 重要更新**：上述 Step 3 面临 token 绑定问题。
>
> 根据 2026-08-03 的 HAR 分析，攻击者在 Step 3 中无法简单地"在 confirm 的同时发起 subscriptions/update"。原因是：
>
> - 在 checkout/confirm 之前，token 的 `plan_type=free`
> - 用 `plan_type=free` 的 token 调 subscriptions/update 升级到 Pro，服务端会因为 token 与账户状态不匹配而拒绝
> - checkout/confirm 成功后，旧 token 立即作废，必须先 refresh 拿到 `plan_type=plus` 的新 token
> - 这个 refresh 步骤引入了强制的序列化点，打破了并发窗口
>
> 因此，上述"简单 TOCTOU"攻击路径在 token 绑定机制下可能不成立。真实的攻击路径更可能是利用 proration 计算逻辑——见后文"真实攻击路径推测"一节。

---

## 七、Stripe 的 HAR 实锤

我们自己的 HAR 数据（来自 2026-07-29 的 pay.openai.com billing portal）清楚地显示了正常升级时 Stripe 是怎么处理 proration 的：

```json
// subscriptions/update/preview 返回:
{
    "total_amount": 793753,
    "positive_line_item_total": 891964,      // Pro 月费 ₱8,919.64
    "negative_line_item_total": -98211,       // 退回未用 Plus ₱982.11
    "renewal_date": "2026-07-28T06:28:11Z"   // 保持原 Plus 到期日
}
```

正常路径下，升级 Pro 需要补差价 ₱7,937.53。但如果 subscriptions/update 和 checkout PI confirm **并发执行**，PI 已经以 ₱982.14 confirm 了，subscriptions/update 虽然改了计划但它的 proration invoice 可能落空（因为支付已经通过另一条管道完成了）。

---

## 八、漏洞分类学：这是第四种

到 2026 年 8 月为止，我们已经见过四种不同的 AI 订阅定价漏洞。它们的攻击面和原理各不相同：

| # | 漏洞 | 原理 | 攻击面 | 需要什么 |
|---|------|------|--------|---------|
| 1 | [0 PHP 跨区定价混淆](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/) | 区域信号碎片化 + 第三方工具注入 promo_campaign | Checkout session 创建 | 特定工具 |
| 2 | [prorationMode Hook](/posts/google-play-ccmax-proration-vulnerability-2026/) | Google Play `putInt` 从 mode 1 改成 mode 3 | Google Play Billing | Frida/Xposed |
| 3 | [RevenueCat 凭证转移](/posts/gpt-plus-exploit-revenuecat-vulnerability/) | 匿名购买 + restore 归属偷渡 | RevenueCat receipt | 两个设备 |
| 4 | ₱982 Pro 20X (本文) | TOCTOU: PI 金额锁定 + 计划独立变更 | subscriptions/update 并发 | 精确时序 |

前三种都需要在客户端侧做手脚——Hook 参数、注入请求、操纵凭证。第四种什么都不需要改。 不需要 Frida，不需要 Xposed，不需要中间人。只需要在正确的时间窗口里发两个合法的 HTTP 请求。

这也是它最危险的地方：攻击面完全在服务端，客户端侧无法检测也无法防御。

---

## 九、真实攻击路径推测

既然简单的客户端 TOCTOU 并发被 token plan_type 绑定挡住了，那 ₱982 的 Pro 20X 到底是怎么做到的？

根据 HAR 证据和群聊线索，以下是三个可能的真实攻击路径，按可能性排序：

### 假说 1：Proration 最后一天定时攻击（最可能）

群聊截图里的关键线索："plus 最后一天升级"。

Stripe 的 proration 计算公式：
```
补差 = (新价 - 旧价) × 剩余天数 / 总天数
```

如果攻击者在 Plus 订阅周期的**最后一天**（甚至最后几小时）发起升级：

```
补差 = (₱8,919.64 - ₱982.14) × 0/30 = ₱0
     或
补差 = (₱8,919.64 - ₱982.14) × 1/30 ≈ ₱264.58
```

关键问题在于"剩余天数"怎么算。如果 Stripe 或 OpenAI 的 proration 逻辑在 billing cycle 的最后一天计算剩余天数为 0（或者使用 `floor` 而非 `ceil`），那补差就是 ₱0。

这个攻击不需要并发，不需要竞态条件，也不受 token 绑定的影响——它完全按照正常的顺序流程操作：

```
Day 1:  checkout/confirm → 开通 Plus, 付 ₱982.14
Day 30: subscriptions/update → 升级 Pro, proration ≈ ₱0
        Stripe 生成 invoice, amount ≈ ₱0, 自动扣款成功
        下个月开始按 Pro 价格续费（但攻击者可以取消自动续费）
```

这与"最后一天"的线索完全吻合，也与 ₱982.14 的实际扣款金额完全匹配。

### 假说 2：Delinquent / Grace Period 异常 proration

如果账号处于欠费（delinquent）或宽限期（grace period）状态，proration 计算可能出现异常：

- 欠费状态下，Stripe 可能认为当前订阅"已过期"，剩余价值 = 0
- 升级补差 = 新价 - 0 = 全价，但如果宽限期的 credit 计算有 bug，可能出现负数或零

这条路径更投机，需要特定的账号状态配合。

### 假说 3：服务端 Webhook 竞态窗口

虽然 token 绑定阻止了客户端侧的并发，但 Stripe webhook 处理和 OpenAI 内部订阅状态更新之间可能存在服务端竞态：

```
T0: Stripe PI confirm 成功 → 发送 webhook
T1: OpenAI webhook handler 开始处理
    → 更新 payment 状态
    → 但还没更新 subscription plan
T2: 在 T1 和 subscription plan 更新之间，存在一个窗口
    → 如果攻击者在这个窗口内调 subscriptions/update
    → 服务端看到 payment 已成功但 plan 还是 free/plus
    → 可能跳过 proration 检查
```

这条路径需要极精确的时序，且攻击者无法从客户端控制 webhook 处理时间。但它不受 token 绑定的影响——因为竞态发生在服务端内部，token 只管客户端认证。

### 小结

综合来看，proration 最后一天定时攻击是最合理的解释。它不需要竞态条件，不受 token 绑定限制，与所有已知线索（₱982 金额、"最后一天升级"、Stripe 正规扣款记录）吻合。TOCTOU 并发假说理论上成立，但在 token plan_type 绑定机制下有实际障碍。

---

## 十、为什么我们不受影响

我们的自动化系统（Chrome Extension + Go 后端）使用的是严格顺序的两阶段流程：

```
Phase 1:
  1. 打开 checkout 页面
  2. 自动填入卡号
  3. 等待 PI confirm
  4. 等待 billing 确认（轮询 check/v4 接口）
  5. 确认 Plus 已生效

Phase 2:（Phase 1 完成后）
  1. 导航到 chatgpt.com
  2. 等待 8 秒
  3. 验证 session 身份（/backend-api/me）
  4. 调用 subscriptions/update/preview
  5. 调用 subscriptions/update
  6. 轮询 check/v4 确认升级
  7. 取消自动续费
```

Phase 2 在 Phase 1 **完全完成**之后才开始。中间有身份验证、计划检查、多次等待——不存在并发窗口。即使 Phase 2 的 subscriptions/update 在新协议下频繁返回 401/unknown，我们的 watchdog 也会通过 billing sync 自动恢复。

我们受到的影响是**间接的**：升级协议更新导致 Phase 2 成功率下降（从 ~95% 降至 ~60%），更多任务需要走 watchdog 恢复路径。但最终交付不受影响。

在 HAR 分析之后，我们改进了 token refresh 机制，采用了 OpenAI 官方客户端的 `reason=token_expired` + `x-openai-failed-access-token-iat` 模式：

```
GET /api/auth/session?refresh=true&reason=token_expired
Header: x-openai-failed-access-token-iat: <旧token的iat时间戳>
```

这修复了 Phase 2 中因 token plan_type 变更导致的 401 失败，使升级成功率恢复到正常水平。

---

## 十一、防御建议

给正在做订阅系统的开发者的一些建议：

### 1. Checkout 和 Upgrade 互斥锁

```
if (hasActiveCheckoutSession(accountId)) {
    return 423; // Locked
}
```

这是最基本的防御。如果一个账号有进行中的 checkout session（PI 已创建但未 settle），拒绝 subscriptions/update 请求。这正是旧协议在做的事情。

### 2. PI Confirm 后验证计划一致性

```
onPaymentIntentSucceeded(pi) {
    const intendedPlan = pi.metadata.plan; // checkout 创建时记录的目标计划
    const currentPlan = getSubscription(pi.metadata.accountId).plan;
    if (currentPlan !== intendedPlan) {
        refund(pi); // 计划不一致，退款
        revertSubscription(pi.metadata.accountId);
    }
}
```

在 PI confirm 成功后，检查当前订阅计划是否还是 checkout 创建时的目标计划。如果被改过了，说明有并发操作，应该退款并回滚。

### 3. Webhook 交叉审计

Stripe webhook 里的 `checkout.session.completed` 事件包含了 PI 金额和订阅信息。在 webhook handler 里交叉验证金额和计划是否匹配。

### 4. 金额/计划绑定

在创建 checkout session 时，在 PI metadata 里记录目标计划。confirm 时验证 metadata 中的计划与当前订阅计划一致。任何不一致都触发告警。

---

## 结语

这篇文章的分析经历了一次有意思的修正。

最初的假设是经典 TOCTOU：checkout confirm 和 subscriptions/update 并发执行，PI 金额锁定 + 计划独立变更 = 以 Plus 价格拿 Pro。理论上很优雅，逻辑上也自洽。

但 2026-08-03 的 HAR 抓包打破了这个假设。Token 与 plan_type 的绑定机制在 confirm 和 update 之间插入了一个强制的序列化点——旧 token 在计划变更后立即失效，攻击者必须 refresh 拿到新 token 才能继续操作。这让简单的客户端并发攻击变得不可行。

真实的攻击路径更可能是 proration 最后一天定时攻击——在 Plus 订阅周期的最后一天升级 Pro，利用 proration 剩余天数趋近于 0 来规避补差价。这与群聊截图中"最后一天升级"的线索完全吻合，也不需要任何竞态条件。

同时，8 月 2 日的协议更新实际上是强化了 token 与订阅状态的绑定，而非移除互斥锁。这个变更导致了我们 Phase 2 的 401 失败潮——因为我们的旧代码没有正确处理 token refresh。在用 HAR 数据逆向出官方的 `reason=token_expired` + `x-openai-failed-access-token-iat` 模式后，问题得到了解决。

从 [0 PHP 跨区混淆](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/)到 [prorationMode Hook](/posts/google-play-ccmax-proration-vulnerability-2026/)到今天的 proration 定时攻击——每一个漏洞都指向同一个根本问题：支付系统中，任何两步操作之间如果没有原子性保证，就是潜在的攻击面。 价格检查和扣款之间、计划变更和金额计算之间、proration 计算和时间边界之间——每一个"之间"都是攻击者的机会。

而且有时候，第一个假设不是对的那个。拿到数据再说话。

下次再拆别的。

---

*本文基于公开信息、系统日志分析和 Stripe API 文档推断。部分结论（如具体的协议变更内容）为合理推断，非 OpenAI 官方确认。*
