---
title: "聊聊圈子里常说的 ChatGPT 提链：12 步提取本地支付跳转链接的协议原理与边界"
date: 2026-08-01T20:00:00+08:00
draft: false
categories: ["技术分析", "支付安全"]
tags: ["ChatGPT", "Stripe", "提链", "本地支付", "iDEAL", "UPI", "PIX", "Checkout Session"]
description: "梳理合租与代充圈常说的提链原理：为什么网页前端只摆出银行卡输入框，底层 Stripe Checkout 却能按区域吐出 iDEAL、UPI、PIX、Kakao Pay 等本地钱包跳转链接，顺带拆开 12 步状态机、pre_confirm 握手、SetupIntent 直卡分片发现与合规边界。"
weight: 10
---

混过海外 SaaS 交流群的人，多半听人嘴里蹦出过"提链"这个词：表面看就是把原本只能填信用卡号、有效期和 CVC 的 ChatGPT 网页结账单，变成一条可以直接在浏览器里拉起荷兰 iDEAL 网银、印度 UPI、巴西 PIX 扫码、韩国 Kakao Pay 或者菲律宾 GCash 的独立付款链接。

第一次见的人难免犯嘀咕：OpenAI 网页上明明只画了一张信用卡表单，这些五花八门的本地电子钱包是从哪变出来的？

秘密其实全在前端界面和底层收单网关的视野差里。全球有信用卡的人本来就只占少数，在印度大家习惯刷 UPI，巴西人离不开 PIX，荷兰人网购默认走 iDEAL。OpenAI 底层收单接的是 Stripe，而 Stripe 天然集成了几十种区域性本地支付方式（APM）。OpenAI 自家的网页前端故意只摆出银行卡输入框，主要是为了省掉各国复杂的反洗钱实名合规、五花八门的增值税发票格式以及不同钱包截然不同的拒付退款（Dispute / Chargeback）运营成本；但在后端 API 这一层，只要创建 Checkout Session 时传入了对应的国家与币种，Stripe 的 `payment_method_types` 数组里早就把当地主流钱包备好了。

所谓"提链"，干的就是绕开前端写死的单一卡片组件，按目标区域走完 Stripe 的有状态结账握手，把最后那条 `redirect_to_url` 第三方收银台跳转链接原封不动抠出来。下面的协议细节均基于 2026 年 7 至 8 月的抓包观察整理，用来帮大家看懂跨区收单的内部结构与合规边界。

## 0x00 八种区域本地钱包与 `pre_confirm` 隐藏分支

先看一眼当时从 Stripe 结账会话里实测能拉出来的八种区域支付通道（全都按 Stripe 官方价格表上的当地标准月费结算，不掺任何折扣码或金额篡改）：

| 国家/地区 | 计费币种 | 本地支付方式 | Stripe `PM Type` | 需前置 `pre_confirm` | 确认后跳转形态 | 当时挂牌月费参考 |
|---|---|---|---|---|---|---|
| 荷兰 (`NL`) | `EUR` | iDEAL | `ideal` | 否 | 银行列表选择页 | `€20` |
| 印度 (`IN`) | `INR` | UPI | `upi` | 否 | VPA 付款确认页 | `₹1,950` |
| 巴西 (`BR`) | `BRL` | PIX | `pix` | 否 | PIX 二维码扫码页 | `R$99.90` |
| 瑞士 (`CH`) | `CHF` | TWINT | `twint` | 否 | 钱包 App 唤起页 | `CHF 20` |
| 韩国 (`KR`) | `KRW` | Kakao Pay | `kakao_pay` | 是 | Kakao 授权确认页 | `₩26,400` |
| 波兰 (`PL`) | `PLN` | BLIK | `blik` | 否 | 6 位动态码输入页 | `zł79.99` |
| 越南 (`VN`) | `VND` | MoMo | `momo` | 是 | MoMo 钱包跳转页 | `₫460,000` |
| 菲律宾 (`PH`) | `PHP` | GCash | `gcash` | 否 | GCash 授权确认页 | `₱990` |

仔细看上面表格里的第五列：八家里面有六家建好支付方式直接调 `confirm` 就能吐出跳转链接，唯独韩国的 `kakao_pay` 和越南的 `momo` 必须额外多走一步 `pre_confirm` 握手！如果你按通用模板跳过了这一步，后面的 `confirm` 就会死活停在 `incomplete` 状态，所有参数看着全对就是拿不到跳转 URL：

```http
POST https://api.stripe.com/v1/payment_pages/{session_id}/pre_confirm HTTP/2
Content-Type: application/x-www-form-urlencoded

expected_payment_method_type=kakao_pay
```

这种冷门分支在公开文档里半个字都不会提，全靠真机跑一遍完整 HAR 抓包才能揪出来（关于双模式结账底层的更多通用字段，可以对照站内另一篇 [Stripe 结账协议 HAR 分析](/posts/stripe-protocol-payment-automation-deep-dive-2026/)）。

## 0x01 从 `accessToken` 到抠出跳转 URL 的 12 步状态机

要把那条付款链接顺出来，并不是发一个 POST 请求就完事的，前后得严丝合缝走完 12 步有状态交互。

起点是登录态。在已经登录 `chatgpt.com` 的浏览器里打开 `https://chatgpt.com/api/auth/session`，返回的 JSON 里躺着一串有效期通常只有 5 到 10 分钟的标准 JWT `accessToken`（部分本地脚本也支持读 `__Secure-next-auth.session-token` 刷新换取新令牌）。这里照例敲一记安全警钟：永远不要把自己的 `accessToken` 或会话 Cookie 粘贴给任何来路不明的在线"一键提链网站"！那串令牌就是你账号的最高登录凭据，交出去别人不仅能看光你的历史对话，还能随时接管会话。

拿到自己的短期令牌后，第二步是调 OpenAI 的建单接口，在 `billing_details` 里指明目标国家与货币（以荷兰 iDEAL 为例）：

```http
POST https://chatgpt.com/backend-api/payments/checkout HTTP/2
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json

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

只要当前区域通道开着，后端就会返回定制包装前缀的 `checkout_session_id`（`oaics_xxx`，托管模式则为 `cs_live_xxx`）、`publishable_key` 以及包含 `["card", "ideal"]` 的 `payment_method_types`。

紧接着进入第 3 步 `POST https://api.stripe.com/v1/payment_pages/{session_id}/init` 拉取结账页初始状态，响应里会吐出商品明细和后续必用的商户引用号与客户会话密钥：

```json
{
  "payment_method_types": ["card", "ideal"],
  "line_items": [{
    "description": "ChatGPT Plus subscription",
    "amount": 2000,
    "currency": "eur"
  }],
  "payment_method_configuration": {
    "merchant_reference_id": "mri_xxx",
    "customer_session_client_secret": "cuss_xxx"
  },
  "session_id": "oaics_xxx"
}
```

往后的第 4 到第 12 步必须严格串行接力跑完：先调 OpenAI 侧接口更新税务地址（第 4 步 `Update OAI Taxes`），接着同步更新 Stripe 税务区域（第 5 步）和 Stripe 客户信息（第 6 步），保存 OpenAI 结账快照（第 7 步），遇到 Kakao Pay 或 MoMo 时插一步 `pre_confirm`（第 8 步），创建对应类型的 PaymentMethod（第 9 步，如 `type=ideal`），发起最终 `confirm`（第 10 步，若遇手动审批分支则走第 11 步 `approve`），最后在第 12 步从确认响应里把重定向链接抽出来：

```json
{
  "status": "requires_action",
  "next_action": {
    "type": "redirect_to_url",
    "redirect_to_url": {
      "url": "https://hooks.stripe.com/redirect/authenticate/..."
    }
  }
}
```

不管是老式 Source 风格的重定向串（`src_xxx`）还是新版 PaymentMethods 授权地址，用户在浏览器里打开这条 `url` 完成扫码或网银确认后，Stripe 就会发 Webhook 通知 OpenAI 把订阅激活。

## 0x02 手写提取脚本必踩的五个坑与社区参考套件

2026 年 7 月前后，社区里有人在 MIT 协议下开源过一套叫 `ideal-link-extractor` 的研究脚本集（主脚本 `ideal_qr_extract.py` 有三千两百多行，底下按目录拆了 `upi_extract.py`、`pix_extract.py`、`twint_extract.py`、`kakao_extract.py`、`blik_qr_extract.py` 和按国家探测可用渠道的 `detect_payment_methods.py`，另有一套默认只读探测越南通道的 `momo_channel_probe.py` / `momo_probe.py`）。翻看这些脚本里的容错逻辑（比如 `proxy_state.json` 代理冷却计数和日志自动脱敏），正好能串起手写协议时最常翻车的五个细节。

头号铁律还是出口 IP 一致性：创建 Checkout Session 和最后调 Stripe `confirm` 必须走同一个 HTTP 会话和同一个代理出口 IP，半路一旦切了节点，Stripe 检测到创建 IP 与确认 IP 对不上，当场就会回 `invalid_request_error`。

第二个坑在 `expected_amount` 金额核对上。调 `confirm` 时必须传 `expected_amount`，如果你偷懒直接填第 3 步 `init` 刚返回时的裸价，一旦第 4 步 `Update Taxes` 算完当地增值税把总价改了，两边差一分钱都会报错；最稳的取值来源永远是税务更新后快照里的 `snapshot.amount_total`。

第三个坑是内部状态串行接力。Stripe 在每一步响应里都会滚动更新 `eid`（Element ID）、`mrid` 等内部追踪字段，下一步请求必须拿上一步刚吐出来的新值接着传，没法偷懒并发乱发。第四个细节是 `guid` 必须生成合规的 UUIDv4 格式，且别漏传影响本地钱包界面语种的 `Accept-Language` 请求头。第五个则是外部网关延迟：像 Kakao Pay 这类第三方钱包和 Stripe 后端握手偏慢，有时 `confirm` 刚返回还没吐出链接，得接着轮询十来秒（一般设 90 秒上限）才能拿到最终 URL。

同时必须单独点明一条红线：早年流传的部分脚本分支里曾夹带过 `promo_campaign` 注入或 `REQUIRE_ZERO` 开关，那是冲着我们在 [0 PHP 跨区定价混淆复盘](/posts/chatgpt-plus-0php-cross-region-pricing-exploit-2026/) 里聊过的零元漏洞去的，早已被上游封堵且直接踩在违规红线上。哪怕是不改一分钱价格的常规提链，也要客观看清它的边界：本地居民拿自己国家的真实账单信息调出本国钱包付款合情合理，但如果你人不在当地，为了蹭汇率差强行在账号里伪造异国 `billing_details.country` 跨区下单，依然违背了平台服务条款里的真实账单区域规定，存在触发跨区风控的隐患。

## 0x03 附：走官方 `SetupIntent` 分片自动发现的直卡绑定路子

其实如果你手里本来就有一张能过 Stripe 校验的国际信用卡或正规虚拟卡，只是嫌结账页偶尔风控抽风，压根犯不着去跑上面那套繁琐的 12 步提链状态机，直接走官方预留的"先绑卡、后结账"接口反而干净得多。

OpenAI 后端有个 `/backend-api/payments/payment_method` 接口，底层对接的是标准的 Stripe `SetupIntent`（只验卡绑卡、当场不扣费）。研究这处接口时有个挺有意思的架构发现：OpenAI 当时把用户分流在了两个不同的 Stripe 商户分片账号底下（公钥特征串分别带 `KslHRdbaPg` 和 `C6h1nxGoI3`）。在 `chatgpt.com` 同源控制台里做合规自测时，先调业务接口拿到 `SetupIntent` 的 `client_secret`，用 `retrieveSetupIntent` 自动试出当前账号归属哪一个商户公钥分片，挂载官方原生的 Stripe Card Element 组件填卡后调一次 `confirmCardSetup` 就能把卡设成默认付款方式：

```javascript
const result = await stripe.confirmCardSetup(clientSecret, {
  payment_method: {
    card: cardElement,
    billing_details: { name: cardholderName },
    allow_redisplay: "always"
  },
  set_as_default_payment_method: true
});
```

绑好之后调一把 `GET /backend-api/payments/payment_methods` 就能看到新卡稳稳躺在默认槽位上，再去点正常订阅结账，比折腾跨区重定向省心太多了。
