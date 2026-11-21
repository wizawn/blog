---
title: "从一份 HAR 抓包看懂 Stripe 结账协议：Custom 与 Hosted 双流差异、指纹校验与容错状态机"
date: 2026-08-16T22:00:00+08:00
draft: false
categories: ["技术分析", "支付安全"]
tags: ["Stripe", "支付协议", "ConfirmationToken", "PaymentIntent", "TLS指纹", "Checkout Session", "支付安全"]
description: "基于真实浏览器 HAR 抓包，梳理 Stripe Checkout 在 Custom（oaics_）与 Hosted（cs_live_）两种模式下的底层 HTTP 协议字段、部署版本动态同步、风控信号边界与客户端容错状态机，附 5 套不同技术栈的架构参考源码。"
weight: 10
---

平时接海外 SaaS 支付，绝大多数开发者的视野停在"后端调一下 SDK 拿个会话、前端挂个组件等 Webhook 回调"就收工了，很少有人真去扒开浏览器的 Network 面板，看看点下支付按钮那十来秒里，前端跟 `api.stripe.com`、`m.stripe.com`、`r.stripe.com`、`checkout.stripe.com` 之间到底来回推了多少个包。

直到自己动手做订阅网关兼容和自动化回归测试时才切身体会到，Stripe Checkout 底下的私有编排协议远比公开文档暴露出来的那几个顶层接口琐碎得多：光 `checkout_ui_mode` 在 `custom` 和 `hosted` 之间切一下，底层的确认端点、归因元数据（Attribution Metadata）乃至 `_stripe_version` 尾巴上的预览开关就全换了一套；少传一个 `Accept-Language` 头、搞反了跨域安全 iframe 的 `Origin` 归属，或者半道代理跳了一下出口 IP，整笔请求就会在风控层一声不吭地卡死。

这篇笔记顺着浏览器导出的真实 HAR 交互记录，把双模式结账协议从头到尾顺一遍，文末附上 5 套剥离了业务敏感配置的多语言工程骨架代码供对照参考。

## 0x00 拿 HAR 当唯一事实源，先分清 `custom` 和 `hosted` 两条岔路

研究复杂前端支付协议最忌讳对着旧文档瞎猜。打开 Chrome DevTools 勾上 Preserve log，拿官方测试卡号（如 `4242 4242 4242 4242`）跑完一次完整结账，再故意用拒付卡跑一次失败流，右键 `Save all as HAR with content` 把两份 HAR 拉出来做 diff，哪些是写死的协议常量、哪些是上一步响应吐出来的动态令牌，一眼就能看透。

在接了 Stripe 的主流订阅平台里，向业务后端请求创建结账会话时，真正决定后续整条协议走向的分水岭参数只有一个 `checkout_ui_mode`。比如请求嵌入式 Custom 流（常见返回平台包装前缀如 `oaics_xxx`）时，载荷长这样：

```json
{
  "entry_point": "all_plans_pricing_modal",
  "plan_name": "basic_plan",
  "billing_details": {"country": "PH", "currency": "PHP"},
  "checkout_ui_mode": "custom"
}
```

如果把 `checkout_ui_mode` 切成托管式 Hosted 流（返回标准 `cs_live_xxx` 与 `checkout.stripe.com` 完整 URL），请求体就变成了下面这套：

```json
{
  "plan_name": "basic_plan",
  "billing_details": {"country": "PH", "currency": "PHP"},
  "checkout_ui_mode": "hosted",
  "cancel_url": "https://platform.example.com/#pricing",
  "locale": "zh-CN"
}
```

很多人写客户端调不通接口，十有八九是把这两套模式的专属字段混在一锅炖了。把 HAR 里最要命的几处差异拎到一张表里看最清楚：

| 协议维度 | Custom 嵌入式流（如 `oaics_`） | Hosted 托管页流（`cs_live_`） |
|---|---|---|
| 最终确认端点 | `POST /v1/payment_intents/{pi}/confirm` | `POST /v1/payment_pages/{cs_live}/confirm` |
| `_stripe_version` 参数 | 短版本号，如 `2025-03-31.basil` | 长版本号，后跟 `; checkout_server_update_beta=v1; checkout_manual_approval_preview=v1` 等开关 |
| 归因 `source` / `version` | 初建为 `elements` / `2021`（确认步切为 `l1`） | `checkout` / `custom` |
| `selection_flow` | `merchant_specified` | `automatic` |
| 额外会话与构建校验块 | 不需要 | 必传 `elements_session_client`（8 个子项）、`init_checksum`、`js_checksum`、`rv_timestamp`、`expected_amount` |

连上面的 `_stripe_version` 和构建哈希都不能在代码里写死。Stripe 大概每隔一两周就会滚动更新一次前端静态包，Hosted 模式下必传的 `js_checksum` 和 `rv_timestamp`（部署毫秒时间戳），实际都是运行时从公开的部署状态清单里动态读出来的：

```python
deploy = http.get("https://js.stripe.com/deploy_status_henson.json").json()
basil_rv = deploy["basil"]["rv"]          # 例如拼出 "2025-03-31.basil"
js_checksum = deploy["basil"]["js_checksum"]
rv_timestamp = deploy["basil"]["rv_timestamp"]
```

抱着几个月前的旧 `js_checksum` 硬发 `payment_pages/confirm`，请求分分钟会被服务端静默拒掉。

## 0x01 Custom 嵌入式流的 8 步时序与四个高频暗坑

Custom 模式走的是前端挂载 Stripe Elements 的标准路径，完整跑通一单在 HAR 里一共 8 步：刷新平台登录会话 -> 查当前订阅状态 -> 拉区域定价 -> 调业务端创建 `oaics_` 结账会话 -> 调业务端 `/checkout/taxes` 算税（算税前后各拉一次 `GET /v1/elements/sessions`） -> 调 `/v1/confirmation_tokens` 把卡要素封成一次性 `ctoken_` -> 调业务端 `/checkout/confirm` 换回 `pi_xxx_secret_xxx` -> 调 Stripe `/v1/payment_intents/{pi}/confirm` 扣款，最后跳 `/checkout/verify` 验状态。

这套看似平顺的流程底下藏着四个光翻官方文档绝对注意不到的坑点。

第一个坑在两次 `elements/sessions` 拉取与税务地址一致性上。算税前后前端各调了一次配置接口：

```http
GET https://api.stripe.com/v1/elements/sessions?deferred_intent[mode]=subscription&deferred_intent[amount]=98214&deferred_intent[currency]=php&deferred_intent[setup_future_usage]=off_session&deferred_intent[payment_method_types][0]=card&type=deferred_intent&key=pk_live_xxx&_stripe_version=2025-03-31.basil HTTP/2
```

这里吐回来的 `elements_session_id`、`customer_session_client_secret`（`cuss_xxx`）和 `payment_method_configuration`（`pmc_xxx`）后面全要用。中间调平台的 `/checkout/taxes` 更新账单地址时，服务端会按税区重算增值税（比如菲律宾区默认加收 12% VAT，而美国俄勒冈 `OR`、蒙大拿 `MT`、特拉华 `DE`、新罕布什尔 `NH` 和阿拉斯加 `AK` 大部没有州级销售税）。这里一方面要确保 `taxes` 传的账单地址跟后面 `confirmation_tokens` 里填的 `billing_details.address` 严丝合缝一致；另一方面从风控与合规角度也得心里有数，跨国硬填与实际居住地不符的免税州地址，不仅本身存在税务合规瑕疵，一旦"账单地址国、卡头 BIN 发行国、当前会话出口 IP 归属国"三方互殴，会直接拉高 Stripe Radar 的欺诈评分。

第二个大坑在 `confirmation_tokens` 的请求头归属与双客户端 Cookie 隔离上。很多人想当然以为请求是从商户网页发出去的，所以把 HTTP 请求头里的 `Referer` 填成了商户自己的域名。其实在真实浏览器里，收集卡号的输入框跑在 `https://js.stripe.com` 的安全隔离 iframe 里！因此发往 `api.stripe.com` 的请求，`Origin` 和 `Referer` 必须是 `https://js.stripe.com`（同属 `stripe.com` 主站，所以 `Sec-Fetch-Site` 是 `same-site`），真正的商户域名只出现在表单参数或后续 `return_url` 里；而且请求头里千万不能漏掉 `Accept-Language`（浏览器发送的卡号字符串带不带四位一格的空格 Stripe 都认）：

```http
POST https://api.stripe.com/v1/confirmation_tokens HTTP/2
Accept: application/json
Content-Type: application/x-www-form-urlencoded
Origin: https://js.stripe.com
Referer: https://js.stripe.com/
Sec-Fetch-Site: same-site
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Accept-Language: en-US,en;q=0.9

type=card&payment_method_data[type]=card&payment_method_data[card][number]=4242+4242+4242+4242&payment_method_data[card][exp_month]=12&payment_method_data[card][exp_year]=2029&payment_method_data[card][cvc]=123&payment_method_data[billing_details][address][country]=US&payment_method_data[billing_details][address][postal_code]=97201&key=pk_live_xxx&_stripe_version=2025-03-31.basil
```

同时在代码架构上，必须把请求业务后端的 HTTP 实例和请求 `*.stripe.com` 的 HTTP 实例彻底拆成两个独立的客户端，绝不允许把平台的登录 Cookie 误发给 Stripe，也别把 Stripe 的响应 Cookie 混进业务接口：

```python
# 业务平台客户端：携带登录会话 Cookie
platform_http = HttpClient(cookies_enabled=True)

# Stripe 协议客户端：严格关闭跨站 Cookie 混传
stripe_http = HttpClient(cookies_enabled=False)
```

第三个细节是 42 位前端指纹串、两层归因块与信标上报。HAR 里传给 Stripe 的 `guid`、`muid`、`sid` 比 36 位裸 UUID 多了一截尾巴，实际由 `36 位标准 UUIDv4 + 6 位随机十六进制字符` 拼成 42 位字符串，外加一个模拟真人在页面停留填表的秒数 `time_on_page`（取 8 到 30 秒之间的随机数最自然）。在组件挂载阶段，`Stripe.js` 会往 `https://m.stripe.com/6` 连发四条表单信标（`tag` 依次为 `stripejs-init-started`、`stripejs-init-complete`、可选的渠道组件加载及 `payment-element-mounted`），并往 `https://r.stripe.com/b` 发 `Content-Type: text/plain` 的 JSON 性能遥测（如 `paymentElement.mount` 耗时）；长期固定复用一串从未在 `m.stripe.com/6` 露过面的 `guid`/`muid` 很容易招来 Radar 侧目。另外注意 `client_attribution_metadata` 在 `confirmation_tokens` 请求里会在顶层和 `payment_method_data` 内部各写一遍（`merchant_integration_source = elements`），可到了下一步调 `POST /v1/payment_intents/{pi_id}/confirm` 时，这个字段必须跟着变成 `l1`。

第四个实用特性是同一个 `PaymentIntent` 原地换卡重试。如果第一张卡撞上 `generic_decline`、`insufficient_funds` 或 `processing_error` 临时报错，`PaymentIntent` 会退回 `requires_payment_method` 状态。这时候压根不需要废掉外层的 Checkout Session 重头算税，直接拿备选卡重新调一次 `/v1/confirmation_tokens` 产出一枚新 `ctoken_xxx`，再对同一个 `payment_intents/{pi_id}/confirm` 发一次确认就能救回来；但要是收到 `stolen_card`、`lost_card`、`card_not_supported` 或 `currency_not_supported` 这类不可逆错误，状态机就得立刻熔断停手，遇到 `card_velocity_exceeded` 则做冷却退避。

## 0x02 Hosted 托管流的 8 字段会话块、`fall-through` 审批与验证边界

一旦切进 Hosted（`cs_live_`）模式，协议复杂度立马翻倍：得先 `GET https://checkout.stripe.com/api/payment-page/{cs_live}/init` 拿到 `ppage_token` 和 `init_checksum`；调 `POST /v1/elements/sessions` 时不仅得换成长版本号，还得补齐 `checkout_session_id`、`elements_init_source=custom_checkout`、`referrer_host` 和 `stripe_js_id`。

到了最核心的 `POST https://api.stripe.com/v1/payment_pages/{cs_live}/confirm`，请求体里必须原原本本塞进整组 `elements_session_client` 8 字段块和客户端选项块，缺一个子项都可能报参数不匹配：

```text
elements_session_client[client_betas][0]=custom_checkout_server_updates_1
elements_session_client[client_betas][1]=custom_checkout_manual_approval_1
elements_session_client[elements_init_source]=custom_checkout
elements_session_client[referrer_host]=platform.example.com
elements_session_client[session_id]=elements_session_xxx
elements_session_client[stripe_js_id]=<UUID>
elements_session_client[locale]=zh
elements_session_client[is_aggregation_expected]=false
elements_options_client[saved_payment_method][enable_save]=auto
elements_options_client[saved_payment_method][enable_redisplay]=auto
init_checksum=<来自 init 响应>
js_checksum=<来自 deploy_status_henson.json>
rv_timestamp=<来自 deploy_status_henson.json>
expected_amount=98214
expected_payment_method_type=card
```

这里最容易把新手坑死的时序陷阱，是 `confirm` 返回 `status: "open"`（`requires_approval`）之后的动作。千万别一看见 `requires_approval` 就手欠立刻去调业务平台的 `/payments/checkout/approve`！从真实 HAR 时序看，标准路径是 `fall-through`：Stripe 内部预检通过后会主动回调通知业务平台自动完成审批，客户端只需要每隔 2 到 3 秒轮询一次 `POST https://api.stripe.com/v1/payment_pages/{cs_live}/poll`（最多等 60 秒），盯着里面的 `payment_object_status` 变成 `succeeded` 即可；只有当平台回调超时未触发时，才轮得到带平台一次性挑战头（同一会话严禁重复调用）的手动 `approve` 兜底登场。

同时在 `requires_action` 状态下，一定要分清两种名字很像、本质完全不同的挑战。

一种是 `next_action.type` 为 `verify_with_challenge` 的风控挑战：它跟银行卡组织的 3DS 无关，纯粹是 Stripe Radar 觉得当前请求特征可疑，拉起了企业级人机挑战（参数挂在 `elements/sessions` 返回的 `passive_captcha` 下，验证端点为 `/v1/payment_intents/{pi_id}/verify_challenge`）。这里有个从成功 HAR 里扒出来的关键状态机优化（Fast-Path）：有时候 `confirm` 接口表面刚吐出 `requires_action`，底下的 `PaymentIntent` 其实已经扣款成功变成 `succeeded` 了！所以在收到 `requires_action` 时，第一步先调 `GET /v1/payment_intents/{pi_id}` 看一眼真实的 `pi["status"]`，如果已经是 `"succeeded"` 直接收工返回成功，省得画蛇添足把已经成功的单子搞报错。

另一种则是真正的发卡行 3D Secure 强身份验证（EMV 3DS / Visa Secure），需要持卡人跳转发卡行页面输短信 OTP 或在手机银行 App 里按指纹。不管是撞上发卡行 3DS 还是撞上人机验证门禁，合规稳妥的工程设计都应该直接回退拉起真实浏览器窗口交给用户本人完成确认（比如后文参考实现里的 `checkout-server` 降级模式），绝不要去搞什么第三方打码黑盒或硬绕验证机制，既违反安全准则又极易触发封号拒付。

## 0x03 TLS 握手自洽、出口 IP 钉死与安全测试护栏

最后收尾交代四条在网络层和工程安全上绝不能省的铁律。

第一条是 TLS 握手指纹（JA3 / JA4）、HTTP 协议版本（`confirmation_tokens` 与 `payment_pages/confirm` 走 HTTP/2，`payment_intents/confirm` 兼容 HTTP/1.1）跟 HTTP 请求头必须严格成套匹配。比如在 Python 里用 `curl_cffi` 或在 Node.js 里用 `CycleTLS` 选了 `chrome131` 的 TLS 握手画像，你的 `User-Agent` 和 `Sec-CH-UA` 就必须原原本本写 `131`；要是切到 `safari18` 画像，就必须把 Safari 压根不会发送的 `Sec-CH-UA*` 系列头全部摘干净。用 Chrome 131 的 TLS 握手却顶着 Chrome 124 的 UA 头，在 Cloudflare 和 Stripe 边缘网关眼里就是一眼假的劣质脚本，直接回敬 `403` 或 `429`。

第二条是整笔结账会话从头到尾必须钉死同一个住宅出口 IP。从向业务平台发第一个请求建 Checkout Session 开始，一直到最终 `confirm` 与 `poll` 结束，中间所有发往平台和 Stripe 的包必须走同一个固定代理节点（拿机房数据中心 IP 直连在 Radar 里天然高危；而中途一旦代理轮换变了出口 IP，Stripe 比对前后源 IP 不一致会当场按会话劫持拒单）。

第三条是留好请求节奏与并发信号量。真人从打开收银台到填完卡点确认通常要花十几到三十秒，在建会话、算税、建令牌和确认这几个关键节点之间插上 `0.8` 到 `3.0` 秒的 `random.uniform` 间隔，并用 `asyncio.Semaphore(3)` 把单出口并发严格压住，别一秒钟狂轰几十个包把接口打进限流。

第四条是联调阶段永远默认打开 Dry-Run 干跑开关（`commit_payments = False`），只跑通前面的会话、算税与令牌拼装，跳过最后一步真实扣款的 `confirm`；真实卡号只留在当前请求内存里用完即清，绝不落盘，日志里一律把会话令牌和卡要素脱敏成 `***`。

---

## 0x04 五套多语言架构参考源码下载

为了方便对照理解双客户端 Cookie 隔离、状态机流转以及 `deploy_status_henson.json` 动态版本同步的工程写法，这里整理了 5 套已彻底剥离具体业务域名与密钥配置的参考骨架源码（运行测试前需自行按合规沙盒环境配置 `.env`）：

| 参考项目 | 技术栈 | 支持流模式 | 核心架构特点与下载 |
|---|---|---|---|
| `saas-pay-sdk` | Python / CLI | Custom | 精简命令行骨架，含成套 TLS 画像与异常退避 · [下载源码包](/downloads/saas-pay-sdk.zip) |
| `subscription-manager` | Python Flask / Web UI | Custom & Hosted | 带绑卡、查账单与升降级状态管理面板 · [下载源码包](/downloads/subscription-manager.zip) |
| `payment-gateway` | Python Flask / Web UI | Custom & Hosted | 队列信号量并发控制与状态聚合看板 · [下载源码包](/downloads/payment-gateway.zip) |
| `checkout-server` | Python / Local HTTP | Custom & Hosted | 本地编排服务 + SQLite 持久化 + 真实浏览器窗口回退 · [下载源码包](/downloads/checkout-server.zip) |
| `protocol-engine` | Node.js / Modules | Custom & Hosted | 模块化分层引擎，基于 CycleTLS 与动态构建哈希同步 · [下载源码包](/downloads/protocol-engine.zip) |

---

### 附：海外 SaaS 订阅常用虚拟卡工具参考

平时正经订阅海外开发者工具（ChatGPT、Claude、Cursor 等）如果手头缺一张支持国际 Stripe 结算的卡片，可以看看 ZovoCard（支持 Visa / Mastercard，多卡独立限额管理，即开即用）：

<a href="https://zovocard.com/register?invite=7777777" target="_blank" rel="noopener" style="display:inline-block;padding:8px 20px;font-size:14px;color:#fff;background:#6366f1;border-radius:6px;text-decoration:none;font-weight:600;">了解 ZovoCard →</a>
