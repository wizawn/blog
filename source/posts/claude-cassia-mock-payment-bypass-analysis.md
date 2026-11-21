---
title: "不到 200 行油猴脚本撬动收银台：复盘网传 Claude 焚决的通道篡改与 SEPA 清算时间差"
date: 2026-07-26T04:49:00+08:00
draft: false
categories: ["漏洞分析", "支付安全"]
tags: ["Claude", "支付安全", "Tampermonkey", "SEPA", "客户端信任边界", "漏洞复盘"]
description: "复盘 2026 年夏流传的 Claude 油猴脚本：如何通过劫持 checkout_capabilities 响应把前端收银台切进欧元区 SEPA 直接借记（cassia）通道，利用 ISO 7064 MOD 97-10 纯数学格式校验与 T+1 至 T+3 银行清算时间差套取短期订阅，以及常见的会话失效报错原因与服务端根治方案。"
weight: 10
---

2026 年 7 月那阵子，圈子里神神秘秘传着一套号称"焚决"的 Claude 开号秘籍。名字起得跟玄幻小说似的，结果拿过来扒开源码一看，其实就是一段不到 200 行的 Tampermonkey 油猴脚本。

代码虽短，下刀的位置却找得极刁钻：趁你打开 `claude.ai` 点升级订阅的那一瞬间，脚本在浏览器内部半路把一个配置接口的响应体换掉，把页面上原本要验卡号、CVC 安全码和 3DS 挑战的信用卡表单，调包成了欧元区的 SEPA 银行账户直接借记（Direct Debit）输入框。接着随便去 `randomiban.com` 生成一串符合校验公式的虚拟德国 IBAN 填进去提交，欧洲银行间的批量清算还没来得及退单拒付，Claude 的高阶订阅就已经先给你开出来了。

这套路子早已随着上游补丁和风控收紧成了历史样本，但它把"前端信任边界失守"和"异步支付清算真空期"这两件事咬合得非常典型，很适合原原本本拆开做个复盘。

## 0x00 改一个字段换掉整张收银台，再借 SEPA 异步清算打时间差

正常登录 `claude.ai` 点升级套餐时，前端页面并不会写死只画信用卡输入框，第一步总会先发一条 GET 请求去问后端"当前这个组织该渲染哪条收银通道"：

```text
GET /api/organizations/{org_id}/subscription/checkout_capabilities
```

对绝大多数地区的用户，后端返回的 JSON 里写着 `"checkout_flow": "stripe"`，前端据此加载实时在线扣款的银行卡组件。而那段油猴脚本干的全部事情，就是把这个返回值改成了 Anthropic 内部代表欧元区 SEPA 直接借记通道的代号：

```json
{
  "checkout_flow": "cassia"
}
```

前端一看到 `cassia`，立马把收银台切换成银行账户扣款授权书（Mandate），只让你填一串欧洲银行的 IBAN 账号。

为什么随便拿在线工具捏一串虚拟德国 IBAN 填进去就能骗过第一关？这得把信用卡实时收单和欧洲 SEPA CORE 直接借记（覆盖 36 个国家/地区）的底层清算机制摆在一起比一下：

| 对比维度 | 信用卡收单（实时在线授权） | SEPA CORE 直接借记（异步批量拉款） |
|---|---|---|
| 结算币种 | 多币种 | 仅限欧元（`EUR` / `€`，绝不结算美元） |
| 提交瞬间的校验深度 | Luhn 校验 + CVC + 3DS 挑战 + 发卡行毫秒级在线冻结授信额度 | 若未接开放银行实时验户，当场仅跑一遍 ISO 7064 MOD 97-10 纯数学公式验格式 |
| 真实扣款反馈周期 | 当场返回扣款成功或发卡行拒付 | 扣款指令送进欧洲银行间批量清算网，要等 `T+1` 到 `T+3` 个工作日才出结果 |
| 账号不存在的后果 | 当场拦截，不开通任何权益 | 几个工作日后对方银行退回 ISO 20022 四位退单原因码（如 `AC01` 账号不正确/不存在、`AC04` 账户已销户、`AM04` 余额不足、`MD01` 无有效授权；注意早年有些文章写成了 `R02`/`R04`，那是美国本土 NACHA ACH 网络的退单码，跟欧洲 SEPA 不是一套标准） |

看清这张表，整个把戏就一点都不玄乎了。IBAN 依赖的 ISO 7064 MOD 97-10 算法只有四步纯算术：把开头的两位国家代码和两位校验码挪到字符串末尾，把字母按 `A=10, B=11, ..., Z=35` 替换成数字，对着拼出来的大整数算一次模 97，余数等于 `1` 就算格式合法。它只能抓出你手滑输错了一位数字，根本不可能知道这个银行账号在现实世界里存不存在；而且在欧洲各国里，德国（`DE`）的 IBAN 固定 22 位（`DE` + 2 位校验码 + 8 位银行代码 BLZ + 10 位账号），不像 27 位的法国 IBAN 那样叠加了额外的 RIB 密钥校验，也不像 24 位的西班牙 IBAN 带国家级 DC 校验位，造出合规格式串的阻力最小。

而平台当年连犯了两个错：既没有在提交结账的后端接口上复核这个账号到底有没有走欧元区 `cassia` 通道的资格，又在异步拉款还没拿到银行 `T+1` 至 `T+3` 清算确认之前，就把昂贵的 Claude Max / Pro 算力立刻交付了出去（这也是那阵子黑产卡网上到处叫卖"质保两天、用完即封"的廉价短命号的真实来历）。

## 0x01 细看那不到 200 行油猴脚本里的五个实现细节

虽然核心只是改一个 JSON 键值，但写这段脚本的人在浏览器注入上确实是个老手，几乎把前端拦截容易翻车的边角全堵严实了。

首先是脚本头部的三条元信息指令，直接决定了能不能抢在页面发包前接管上下文：

```javascript
// ==UserScript==
// @name         Cassia Response Mock Demo
// @match        *://claude.ai/*
// @match        *://*.claude.ai/*
// @run-at       document-start
// @grant        none
// @sandbox      raw
// ==/UserScript==
```

`@run-at document-start` 保证在 DOM 还没开始解析时先把钩子挂好（要是等默认的 `document-idle`，`checkout_capabilities` 请求早发完回来了）；而 `@sandbox raw` 配上 `@grant none` 则是为了跳出 Tampermonkey 默认的隔离沙箱，直接改写宿主页面自己用的那个 `window.fetch`。如果留在隔离沙箱里，你改破喉咙也碰不到业务前端真正调用的全局函数。

其次是精准制导的路径正则，连末尾带不带斜杠都兼容了，绝不乱碰其他业务请求免得页面出怪毛病：

```javascript
const TARGET_PATH = /^\/api\/organizations\/[^/]+\/subscription\/checkout_capabilities\/?$/;
```

第三个细节最贼：拦截 `window.fetch` 时采用的是"先真发请求、等真响应回来再内存换包"：

```javascript
const nativeFetch = window.fetch;

window.fetch = async function (input, init) {
  const method = init?.method || (input instanceof Request ? input.method : "GET");
  const targetUrl = getTargetUrl(input, method);
  const originalResponse = await nativeFetch.apply(this, arguments);

  if (!targetUrl) {
    return originalResponse;
  }
  return createMockResponse(originalResponse);
};
```

要是图省事在本地直接短路返回一个假 `Response` 不往外发包，服务端访问日志里就会出现"这个用户压根没查过 `checkout_capabilities`，却凭空提交了一笔结账单"的明显时序异常；先让真实 GET 请求照常走一遭拿到 `200`，再在浏览器内存里掉包，从服务端日志往外看一切如常。

第四个细节在重构 `Response` 响应头时的扫尾动作：

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

  return new Response(MOCK_BODY, { status: 200, statusText: "OK", headers });
}
```

服务端吐回来的原始响应十有八九带着 `gzip` 或 `br`（Brotli）压缩头 `content-encoding`，如果你塞进去的是明文 JSON 却忘了删掉 `content-encoding` 和旧的 `content-length`，浏览器拿着明文硬做解压当场就会报错抛异常；顺手删掉 `etag` / `content-md5` 并加上 `cache-control: no-store`，则是确保每次刷新页面都老老实实重新过一遍网络钩子，不会被浏览器缓存绕过去。

第五个细节是给 `XMLHttpRequest` 补上的双通道保险。防着前端某处依赖库回退到老式 XHR，脚本没用粗糙的直接赋值，而是先拿 `Object.getOwnPropertyDescriptor` 取出原型链上的原始属性描述符，检查 `configurable` 不为 `false` 后再用 `Object.defineProperty` 精细替换 `responseText`、`response`、`status` 等 getter（最后再往页面右下角塞一个 `#cassia-mock-badge` 小绿标提示脚本已挂载）：

```javascript
function replaceXhrGetter(propertyName, replacement) {
  const descriptor = Object.getOwnPropertyDescriptor(XMLHttpRequest.prototype, propertyName);
  if (!descriptor || typeof descriptor.get !== "function" || descriptor.configurable === false) {
    return;
  }
  const nativeGetter = descriptor.get;
  Object.defineProperty(XMLHttpRequest.prototype, propertyName, {
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

## 0x02 点提交瞬间撞见"验证失败并清除旧会话"到底是谁的锅

不管是正常拿信用卡付钱，还是当年有人跑自动化脚本测试，点下 Claude 收银台提交按钮的那一刻经常会迎面撞上下面这两行同时蹦出来的红字报错：

![Claude支付失败截图](/images/claude-payment-session-error.png)

上面写着"未提交付款：发生了意外错误，请检查表单后重试"，底下紧跟着一句"验证失败并清除旧会话"。

一看见底下那句清除旧会话，其实就不用去怀疑卡里没钱或者表单填错了：请求压根还没走到后面的支付网关，在 Anthropic 自己的前置登录会话校验网关那一步就已经被拍死了。

在 `claude.ai` 网页端体系里，维持登录态的核心凭据是名为 `sessionKey` 的 Cookie（值以 `sk-ant-sid01-...` 开头，所以圈子里常简称为 SK Cookie；注意别跟 ChatGPT 网页端用的 NextAuth Cookie `__Secure-next-auth.session-token` 搞串台了）。平时把这枚会话搞崩的原因逃不出五种：

第一种是 `sessionKey` 自然到期，比如账号在自动化任务队列里排了几个钟头，填完表单点提交时刚好踩在 TTL 过期的点上；第二种是多端互踢，好几个浏览器窗口或脚本 Worker 共用同一串 `sessionKey`，旁边的窗口刚好做了一次请求触发会话令牌轮换，把正在收银台点提交的这个窗口当场挤下了线；第三种最常见，就是中途代理断线重拨导致出口 IP 漂移，建会话时还在 `45.67.xx.xx`，点提交前一秒跳到了另一个国家的 `89.12.xx.xx`，后端风控直接判会话异常踢出；第四种是在支付页面挂机太久导致底层的结账 Intent 过期；第五种则是同一个 `org_id` 同时开了两个标签页并发点升级，后建的结账会话把前一个顶废了。

平时正经绑卡遇到这提示，关掉多余标签页、固定死一条稳当的代理出口重新登一次账号，快进快出填完提交基本就过了。

## 0x03 服务端该怎么彻底堵死"前端选路 + 异步交货"漏洞

把这起案例跟站内复盘过的 [Google Play `prorationMode` 篡改](/posts/google-play-ccmax-proration-vulnerability-2026/)、[ChatGPT 0 PHP 跨区定价混淆](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/) 和 [Cloudflare 计费并发竞态](/posts/manual-sec-20260519-cloudflare-billing-race-condition/) 摆在一块儿看，底子其实都是同一类毛病：把原本该由后端独占裁决的路由或计费状态，放心大胆交给了用户浏览器。

讨论修法的时候，曾有人提议"让服务端给 `checkout_capabilities` 的响应体加一层 HMAC 签名，前端渲染前先验签"。仔细推敲一下就会发现这招防君子不防小人：对称 HMAC 的密钥放进公开的前端 JS 包里等于明文送人；就算换成非对称公钥验签，既然攻击者已经用 `@sandbox raw` 把整个页面上下文接管了，顺手把前端的验签函数一块儿 Hook 成永远返回 `true` 也不过是多敲几行代码的事。

真正管用的防御必须百分之百收回到服务端自己手里。

第一条铁律是结账落单接口必须在后端独立重算通道资格。前端调 `checkout_capabilities` 拿回来的字段只能当纯 UI 排版参考；等用户真正把 IBAN 或支付令牌 POST 到后端创建订阅时，后端必须根据账户归属地、风控评分和白名单重新算一遍"这个组织到底允不允许走 `cassia`（SEPA）"，不符合条件的直接回 `403` 拒单。

第二条是所有异步清算渠道一律实行"到账再给正式额度"。像 SEPA 直接借记、银行电汇这种天然要等 `T+1` 到 `T+3` 工作日才能确认真金白银落袋的支付方式，在清算回执落地前只显示"支付处理中"（或仅给极低成本的防刷试用配额），绝不能钱影儿还没见着就把几百欧元的算力敞开供应。

第三条是在欧洲收单时接上实时账户核验。针对高客单价的 SEPA 授权，要么强制引导走一遍 Open Banking AIS（开放银行账户信息服务）网银实时登录验户，要么接入欧盟推行的 SEPA VoP（Verification of Payee，收付款人户名与账户存在性实时核验）接口，当场就能把在线生成器算出来的幽灵 IBAN 挡在大门外头。
