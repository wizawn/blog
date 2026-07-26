---
title: "焚决 Claude — Tampermonkey API 响应劫持绕过支付，Max/Pro 订阅 0 元购技术全拆解"
date: 2026-07-26T04:49:00+08:00
draft: false
weight: 1
categories: ["漏洞分析", "支付安全", "Web 安全"]
tags: ["Claude", "订阅漏洞", "API 劫持", "Tampermonkey", "SEPA", "支付安全", "漏洞复现", "客户端安全"]
description: "深入拆解传说中的「焚决」——通过 Tampermonkey 油猴脚本劫持 checkout_capabilities API 响应，前端注入 cassia 支付流，配合随机德国 IBAN 实现 Claude Max/Pro 零元订阅。完整分析脚本的 Fetch/XHR 双重拦截机制、SEPA 异步扣款原理、及此类客户端信任边界漏洞的防御思路。"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **⚠️ 时效性提醒**：本文发布于 2026 年 7 月，文中所述 API 端点、支付流参数均为当前有效值。Anthropic 随时可能修改 `checkout_capabilities` 响应格式或后端校验逻辑，届时本方法将失效。本文保留仅供安全研究与客户端安全防御参考。

---

## 前言

今天来拆一个圈子里传得很火的玩意儿——**「焚决」**。

名字听着挺玄乎，其实就是一个 Tampermonkey 油猴脚本，配合 Claude 网页版支付页面操作，能让你绕过正常的信用卡验证，用虚拟的德国银行卡号直接完成 Claude Max（原 Pro）订阅。

说白了就是**客户端 API 响应劫持 + SEPA 异步扣款系统设计缺陷**的组合拳。

这玩意在外面流传得很广，各种卡网卖的便宜 Claude 会员有不少就是靠这个。今天咱们给它拆个底朝天——不光讲怎么用，更要讲为什么能成，以及这种攻击模式背后的通用规律。

---

## 一、先看懂这玩意干了啥

### 正常流程 vs 劫持后流程

**正常情况下**，你打开 Claude 网页版点订阅按钮，前端会发一个 GET 请求询问后端：

```
GET /api/organizations/{org_id}/subscription/checkout_capabilities
```

后端根据你的 IP、账号地区、浏览器信息返回对应的支付流标识，比如：

```json
{
  "checkout_flow": "stripe"
}
```

然后前端根据这个值渲染不同的支付界面——Stripe 就是信用卡表单，要填卡号、有效期、CVV，还得过 3DS 验证。

**劫持后**，脚本把所有符合条件的响应全部改写为：

```json
{
  "checkout_flow": "cassia"
}
```

前端一看是 `cassia`，直接渲染 SEPA 银行转账界面——你看到的就不是信用卡表单了，而是一个 IBAN 输入框。

这时候去 [randomiban.com](http://randomiban.com) 随便生成一个德国 IBAN，填进去，点支付。前端校验只检查 IBAN 格式（德国 IBAN 固定 22 位，前两位 DE，后面是校验码+银行代码+账号），格式对了就放行。

**然后呢？然后 Claude 就给你开通了。**

---

## 二、为什么填个假的 IBAN 也能过？

这里涉及到 SEPA 直接借记（SEPA Direct Debit，德国叫 Lastschriftverfahren）的核心设计缺陷。

### 信用卡 vs SEPA 的区别

| | 信用卡 | SEPA 直接借记 |
|---|---|---|
| **授权方式** | 实时授权（online authorization） | 异步扣款（asynchronous pull） |
| **校验时机** | 交易发起时立刻校验卡号+CVV+3DS | 交易发起时只校验 IBAN 格式（MOD 97 校验） |
| **资金确认** | 银行实时返回授权结果 | 银行不返回任何确认，直接排队等待清算 |
| **退款机制** | Chargeback（争议处理） | 用户有 8 周无条件撤回权 |
| **扣款周期** | 即时 | T+1 到 T+3 工作日 |

### 关键问题

SEPA 直接借记在交易发起时**不去银行查询这个账户是否真实存在，也不查询余额是否充足**。

它的工作流程是这样的：

```
你提交 IBAN
  ↓
系统做 MOD 97-10 校验（检查 IBAN 格式是否正确）
  ↓
校验通过 → 交易"成功"
  ↓
Claude 给你开通订阅
  ↓
...几天后...
  ↓
银行间清算系统开始处理这笔借记请求
  ↓
发现账号不存在/余额不足 → 扣款失败
  ↓
Anthropic 收到扣款失败通知 → 关你订阅
```

**看到了吧？这里有一个巨大的时间窗口**：从你提交到银行清算完，至少 1-3 个工作日。在这期间，你的 Claude Max 订阅是生效的。

而且更骚的是，很多卡网卖家根本不在乎这个时间窗口——他们开完号立刻卖掉，等 Anthropic 反应过来，早就赚完走人了。

### 为什么是德国？

因为 SEPA 系统内不同国家的 IBAN 校验松紧程度不一样。德国 DE 开头的 IBAN 在各大支付网关里的通过率最高——没有额外的 Luhn 算法叠加，纯粹靠 MOD 97，而且随机生成的 IBAN 有相当大比例恰好能通过校验。

`randomiban.com` 生成的 DE IBAN 就是利用这个特性——它生成的 IBAN **格式合法**，恰好满足前端校验最宽松的要求。

---

## 三、脚本技术逐行拆解

现在咱们把这脚本拆开来看，每一部分的设计都有讲究。

### 3.1 元数据声明

```javascript
// @name         TestExample Cassia Response Mock
// @match        *://claude.ai/*
// @match        *://*.claude.ai/*
// @run-at       document-start
// @grant        none
// @sandbox      raw
```

几个关键点：

- **`@run-at document-start`**：不等人。页面 DOM 都还没开始构建，脚本已经注入完毕。这是整个攻击成功的前提——必须在第一个 API 请求发出之前就完成 Hook。
- **`@sandbox raw`**：原始沙箱。绕过 Tampermonkey 自身的安全限制，确保 Hook 代码不会被干扰。
- **`@grant none`**：不申请 GM 权限。降低权限请求意味着更少的安全警告，更隐蔽。

### 3.2 目标路径匹配

```javascript
const TARGET_PATH =
  /^\/api\/organizations\/[^/]+\/subscription\/checkout_capabilities\/?$/;
```

只拦截这一个接口，精确到路经层。多一个斜杠少一个斜杠都考虑了。

为什么是这个接口？因为 Claude 前端在渲染支付页面之前，一定会调用这个接口来查询"当前账号支持哪些支付方式"。这是整个支付流的**决策点**——控制了这里，就控制了前端看到的支付选项。

### 3.3 Fetch 拦截

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

注意这里的调用顺序：**先把真正的请求发出去**，等拿到响应后再替换。

为什么不直接构造一个假响应返回？

因为 Anthropic 可能在请求日志里追踪 API 调用——如果 `checkout_capabilities` 直接被拦截没发出去，后端能看出来。但如果你让请求正常发出，只是在返回时把结果替换了，从服务端日志看完全正常。

**这才是这个脚本最巧妙的地方——它不阻断通信，只篡改结果。**

### 3.4 Response 重构

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

注意它删掉了哪些头：

- **`content-encoding`**：如果原始响应是 gzip 压缩的，删掉这个头后浏览器会按无压缩处理我们构造的 JSON。不删的话，Content-Length 对不上直接炸。
- **`etag` / `content-md5`**：完整性校验头，删掉防止缓存层校验内容是否被篡改。
- **`cache-control: no-store`**：强制不缓存，避免前端拿到之前的真实响应后不再请求。

### 3.5 XMLHttpRequest 双重保险

脚本对 `XMLHttpRequest` 也做了一套完整的 Hook——包括 `responseText`、`response`、`status`、`statusText`、`getResponseHeader`、`getAllResponseHeaders`。

为什么要双保险？因为有些老旧代码或者第三方库可能用的是 XHR 而不是 fetch。少 Hook 一个，就可能漏掉一条漏网之鱼。

而且注意 `replaceXhrGetter` 的实现：

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

它没有简单地覆盖属性，而是通过 `Object.defineProperty` 精确替换了 getter 函数。这比直接赋值更健壮——即使别的地方用 `Object.freeze()` 锁了原型，这个方法也能提前检测并优雅降级。

### 3.6 状态标记

```javascript
const badge = document.createElement("div");
badge.id = "cassia-mock-badge";
badge.textContent = "Cassia Mock ON";
```

页面右下角显示一个绿色的小标记，类似于"脚本已激活"。这是为了方便使用者确认脚本是否生效。

---

## 四、举一反三：这类漏洞的通用模式

分析完这个脚本，我们总结一下它的**漏洞本质**：

> **客户端信任边界缺失**：服务端将支付流决策权交给了客户端，而客户端的状态可以被任意操纵。

这不是一个孤例。回顾我们之前分析过的几个支付漏洞：

| 漏洞案例 | 攻击点 | 信任边界 |
|---------|--------|---------|
| **🔥 焚决（本例）** | `checkout_capabilities` 响应劫持 | 前端信任 API 返回值决定支付流 |
| GPT Plus offerToken 注入 | Google Play Billing token 替换 | 服务端未校验 token 与账号的绑定 |
| GPT iOS 收据复用 | Base64 收据重复提交 | 服务端不验证收据与账号的对应关系 |
| Cloudflare Pro 竞态 | 请求重放 + 状态不同步 | 权限发放与支付确认的时序错位 |
| RevenueCat 回调 | fetch_token 跨账号复用 | 第三方回调接口未作鉴权 |

**共性规律**：

1. **决策点前置到客户端**：服务端本应独立判断"这个账号能享受什么支付方式"，却把决策依据放在一个客户端可读写的 API 响应里。
2. **异步系统的时间窗口**：SEPA 清算延迟、收据验证延迟——异步系统的确认间隙就是攻击窗口。
3. **格式校验 ≠ 实质校验**：IBAN 格式合法 ≠ 账户真实存在。`checkout_flow: "cassia"` 通过前端校验 ≠ 用户真的有德国银行账户。

### 通用攻击框架

这类漏洞可以抽象为一个通用模型：

```
1. 定位决策接口
   → 找到决定支付流/功能开关/权限计算的 API 端点

2. 注入篡改数据
   → 通过油猴脚本、MITM、Frida Hook 等方式替换响应

3. 利用异步确认间隙
   → 选择确认延迟最长的支付方式（SEPA、部分地区的银行转账）

4. 前端校验 + 后端真空
   → 通过前端校验后，后端在异步确认完成前不暂停服务
```

**这个框架可以复用到任何订阅制服务上**。只要服务满足以下条件：
- 支付的"确认"和"服务开通"之间存在时间差
- 支付方式的选择依赖客户端状态
- 前端校验和后端校验不在同一时间点完成

---

## 五、防御思路

### 对服务端开发者

1. **永远不要相信客户端传来的支付流标识**。`checkout_flow` 应该是服务端根据用户地区、账号状态在**后端**决定的，前端只是渲染器。
2. **同步支付确认和权限开通**。在 SEPA/银行转账等异步支付方式中，应该在收到银行确认后才能开通服务，而不是提交表单的那一刻。
3. **签名校验**。对 API 响应做 HMAC 签名，前端在消费前验证签名。虽然不能根治（签名密钥在前端），但提高了攻击门槛。
4. **服务端二次确认**。支付完成后的权限变更请求，必须由服务端向支付网关发起二次确认，而不是依赖客户端回传的结果。
5. **IBAN 预验证**。对于 SEPA 支付，可以在提交时通过银行系统的 IBAN 验证服务（如 Deutsche Bundesbank 的 IBAN 验证接口）进行实时校验，而不是只做本地 MOD 97。

### 对安全研究者

这类漏洞的挖掘路径非常清晰——打开 DevTools 的 Network 面板，找到所有跟支付流、区域检测、定价相关的 API 端点，挨个测试响应注入。

一些常见的"信号接口"：
- `checkout_capabilities` / `payment_methods` / `available_plans`
- `region` / `locale` / `country_detection`
- `eligible_promotions` / `offers` / `discounts`
- `feature_flags` / `entitlements`

任何一个返回了影响支付逻辑的数据，且这个数据可以被前端篡改的，都有潜在风险。

---

## 六、总结

焚决这个东西，本质上是一个**客户端状态注入**工具，攻击的不是 Claude 的认证系统，不是 Anthropic 的服务器，而是**前端与后端之间的信任边界**。

它的精妙之处在于：
- 不阻断通信，只改返回值——服务端日志正常
- 双重 Hook（fetch + XHR）——覆盖面全
- 利用 SEPA 异步扣款的时间差——核心漏洞点
- 几乎零门槛——一个油猴插件 + 一个随机 IBAN 网站就能操作

而这类漏洞背后的通用规律，才是我们真正需要吃透的东西。

**不是学一个脚本，而是学会"看穿一类漏洞"。**

---

## 相关阅读

- [GPT Plus 订阅漏洞深度分析 — Google Play Billing 鉴权缺失](/posts/gpt-plus-exploit-revenuecat-vulnerability/)
- [GPT Plus 收据复用漏洞 — iOS 收据验证缺陷](/posts/gpt-plus-receipt-vulnerability-2026/)
- [Cloudflare 计费逻辑缺陷 — 请求重放绕过订阅支付](/posts/manual-sec-20260519-cloudflare-billing-race-condition/)

---

**标签**: #Claude #支付安全 #API劫持 #客户端安全 #SEPA #Tampermonkey #漏洞分析 #焚决
