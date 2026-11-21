---
title: "前端撤了按钮，收银台条码还在：复盘 iOS 端借 buyProduct 强开 ChatGPT Pro 20x 的链路"
date: 2026-09-17T22:00:00+08:00
draft: false
categories: ["安全研究", "支付安全"]
tags: ["ChatGPT", "Pro 20x", "iOS", "Apple IAP", "buyProduct", "越狱", "StoreKit", "逆向工程"]
description: "复盘 2026 年下半年流出的 iOS ChatGPT Pro 20x 强开方案：当网页与客户端撤掉订阅入口但 App Store Connect 后台未下架商品时，如何通过越狱 MITM 抓取 Apple ID 五项鉴权参数直调 MZBuy.woa/wa/buyProduct，并横向对比三大移动与网页支付渠道的信任边界。"
weight: 10
---

2026 年下半年，OpenAI 把月费 $200 的 Pro 20x 新建订阅入口全线撤掉了：网页端定价页没了按钮，iOS 和 Android 客户端隐藏了档位，连自家的 `/payments/checkout` 接口看到 `plan_type=chatgptpro` 的新建请求也直接拒单。

结果没过多久，圈子里就流出了一套硬开的野路子，思路直白得让人一拍大腿：既然 OpenAI 关的是自家的前端界面和网页结账口，那就压根别碰 OpenAI 的页面，直接拿着商品条码去找苹果的 App Store 收银台下单。

只要开发者为了保住存量老订户的每月自动续费、没在 App Store Connect 后台把对应的应用内购买（IAP）商品彻底下架（状态还挂着 `Approved`），苹果底层的购买接口就照单全收。借着当时公开流出的六章实操记录和协议样本，把这条链路的底层机制、双机分工门槛，以及它跟站内聊过的 [Stripe 协议支付](/posts/stripe-protocol-payment-automation-deep-dive-2026/)、[Google Play 凭证转移](/posts/gpt-plus-google-play-subscription-transfer/) 的异同摆在一块儿顺一遍。

## 0x00 货架撤了，三十年前的 `MZBuy.woa` 收银台照样认条码

在苹果的生态里，"App 界面上展不展示某个购买按钮"和"这个内购商品在不在售"完全是两套互不统属的系统。

当你在 iPhone 上按下面容或指纹确认任何一笔内购时，iOS 系统底层真正去敲的购买端点长这样：

```text
POST https://p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct
```

顺嘴提个挺有年代感的冷知识：上面这串 URL 里的 `WebObjects` 和 `MZBuy.woa`（MZ 即 MobileZone，`wa` 是 WebObjects Direct Action），源自 1996 年乔布斯还在 NeXT 时推出的那套老牌服务端框架（早年用 Objective-C 写，2000 年 WebObjects 5 转向了 Java），后来跟着 NeXT 一块儿进了苹果。整整三十年过去了，如今撑起全球几千亿美金流水 App Store 交易核心的依然是这套老架构，看到 `.woa` 后缀基本就能断定是苹果自家的老底子（域名前头的 `p70` 只是苹果分配的 CDN 服务器池编号，不同账号和地区可能落在 `p25`、`p47` 等不同分片上）。

`buyProduct` 收到请求后只核对三件事：Apple ID 的五组设备与会话鉴权合不合法、`salableAdamId` 指向的内购商品在不在架上、绑定的付款方式能不能扣下这 $200。至于此刻手机屏幕上的 ChatGPT App 里有没有画这个档位，苹果收银台一眼都不看。

等苹果扣完 $200 生成交易凭证，开通信号会顺着两条独立通道往 OpenAI 后端送：一条是服务端对服务端的 App Store Server Notifications V2（苹果把带 JWS 签名的交易通知主动推给开发者回调地址）；另一条是客户端侧的恢复购买同步（新版 App 调 StoreKit 2 的 `AppStore.sync()` 与 `Transaction.currentEntitlements` 验签，兼容层对应早年 StoreKit 1 的 `restoreCompletedTransactions`）。受苹果审核指南 `3.1.1` 内购条款的约束，只要这笔钱真真实实从 App Store 扣成了且能关联到具体账号，除非撞上异常风控或事后退款撤销，业务后端按规矩都会给对应账号放行权益。

## 0x01 为什么实操非得备"一老一新"两台 iPhone

把原理搬到真机环境上，迎面就会撞上一个很现实的系统版本错位：新版 ChatGPT 官方 iOS 客户端把最低系统门槛抬到了 iOS 18，偏偏主流成熟的公开越狱全停在 iOS 15 到 16。

为什么抓个包非越狱不可？因为苹果的 App Store 和 iTunes Store 进程做了死板的 TLS 证书锁定（SSL Certificate Pinning），压根不走系统的普通用户信任链。哪怕你在没越狱的手机上装好了 Charles 或 mitmproxy 根证书、也乖乖开了完全信任，打开 App Store 抓到的依然只有黑漆漆的 `CONNECT` 隧道，半个明文字节都解不开。

好在整条链路刚好能劈成对系统要求截然不同的两半，一老一新两台机器各司其职：

| 分工角色 | 设备与系统要求 | 干什么活 |
|---|---|---|
| 抓鉴权专用机 | 老款越狱 iPhone（iOS 15 - 16） | 挂 rootless 反证书锁定插件 + MITM 代理，随便触发一次内购弹窗截获 Apple ID 通用购买凭据 |
| 恢复购买交付机 | 日常未越狱 iPhone（iOS 18+） | 装最新版官方 ChatGPT App，挂同一个美区 Apple ID 登录目标 OpenAI 账号点"恢复购买" |

这里有几个老教程经常写劈叉的越狱细节得纠正一下。抓鉴权这台老机器压根不需要装 ChatGPT App（我们要抓的 `buyParams`、`guid`、`afdsv2`、`ams` 和 Cookie 全是 Apple ID 账户层面的通用令牌，随便找个带内购的免费小软件触发支付框就能抓出来），收一台几百块钱的 A11 老机型（iPhone 8 / X，checkm8 硬件洞跑 `palera1n`；注意更早的 A8 机型系统最高只到 iOS 12，别照着错误表格去买）或者 iOS 15.0 到 16.6.1 的 A12 - A15 机型跑 `Dopamine` 最省心。

同时注意，`Dopamine` 和如今的 `palera1n` 默认都是 rootless（无根越狱，目录挂在 `/var/jb` 下），十年前 Cydia 时代那套写系统根分区的 `AppList` 和老版 `SSL Kill Switch 2` 根本装不进去，得在 Sileo 或 Zebra 里装适配了 rootless 与 `ElleKit` 注入器的 SSL Kill Switch 3（搭配 `AltList` 选进程）。装好进设置打开 `Disable Certificate Validation` 时，切记只勾选 `App Store` / `iTunes Store`（`com.apple.AppStore`），千万别图省事全局关掉整台手机所有应用的证书校验，更别在这台越狱测试机上登自己的主力 Apple ID 或手机银行。

网络转发链也必须严格锁死出口 IP：`越狱 iPhone --WiFi--> 电脑 Charles / mitmproxy --> 上游美国住宅 SOCKS5 代理 --> 苹果服务器`。在电脑上装证书时很多人会漏掉第四步：iPhone 浏览器打开 `chls.pro/ssl` 下完描述文件，去"设置 -> 通用 -> VPN 与设备管理"装完还不算完，必须再去"设置 -> 通用 -> 关于本机 -> 证书信任设置"里把根证书的完全信任开关手动拨开。Charles 里在 `External Proxy Settings` 填好美国家宽 SOCKS5，再往 `SSL Proxying Settings` 里加上 `*.itunes.apple.com:443` 和 `*.apple.com:443`（用 `mitmproxy` 则跑 `mitmproxy --mode regular --set upstream_cert=false -p 8888`）。这时候打开 App Store 随便搜个软件，代理面板里能看到解密后的 `GET https://p70-buy.itunes.apple.com/...` 明文请求才算成了；要是还卡在 `CONNECT`，先查插件有没有勾对进程，或者跑一遍 `uicache` / `ldrestart` 重载注入环境。

## 0x02 断点截获五项鉴权与千分位价格细节

环境通了之后，在 Charles 里给 `p70-buy.itunes.apple.com` 的 `*/buyProduct*` 路径挂一个只拦 Request 的断点（Breakpoint）。回越狱手机随便点个内购项，按完面容或密码确认的那一瞬间，请求就会在飞出电脑之前被 Charles 稳稳摁住。

这时候把请求体和请求头里下面这几样命根子完整拷下来，然后果断点 `Abort` 把这次请求掐死（没发到苹果服务器，自然一分钱都不会扣）：

1. `buyParams`：200 到 500 字节左右的 Base64 加密上下文，由 StoreKit 在拉起支付框时现场生成，有效期就几分钟。这套打法能跑通全靠一个关键前提：实测 `buyParams` 虽然绑死了当前 Apple ID 会话和设备，但并没有跟触发弹窗时的那个具体商品 ID 死绑，换掉外面的商品参数照样能过校验。
2. `guid`：根据网卡硬件信息算出来的十六进制设备唯一标识。同一台机器不管重装多少次它都不变，要是拿同一台越狱机一天刷几十单，风控顺着这串 `guid` 一抓一个准。
3. `afdsv2`：长达一两千到四千字符的 Apple Fraud Detection Service v2 反欺诈令牌。跟网页端靠浏览器 JS（`m.stripe.com/6`）采 Canvas 指纹的 Stripe Radar 不同，`afdsv2` 直接调 iOS 系统私有接口采集陀螺仪、加速度计、电池状态、屏幕触控和运行时环境。只要你不去篡改它的生成过程，越狱真机正常产出的 `afdsv2` 一般能过检，但想脱离真机在纯 Python 脚本里凭空捏造一个合法的 `afdsv2` 几乎不可能。
4. `ams` 与会话凭据集合：包括媒体服务令牌 `ams`、核心会话 Cookie（`myacinfo` 与 `itctx`），以及请求头里必须原样带上的三个苹果特征头：`X-Dsid`（Apple ID 数字目录标识）、`X-Apple-I-MD`（Machine Data 设备数据）和 `X-Apple-I-MD-M`（设备元数据）。

抓齐之后趁几分钟内令牌还没过期，走和刚才抓包完全一致的那个美国住宅代理出口 IP（两边源 IP 一旦变了立马会被苹果拒单），把表单里的商品字段换成 Pro 20x 的真实登记参数发往刚才抓到的那个 `pXX-buy.itunes.apple.com` 节点：

```http
POST https://p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct HTTP/1.1
Host: p70-buy.itunes.apple.com
Content-Type: application/x-www-form-urlencoded
Cookie: <原样保留抓到的 myacinfo 与 itctx 等完整 Cookie>
X-Dsid: <原样保留>
X-Apple-I-MD: <原样保留>
X-Apple-I-MD-M: <原样保留>

productType=A&price=200000&salableAdamId=6657954405&pricingParameters=STDQ&pg=default&offerName=oai_chatgpt_pro_20000_1m&appAdamId=6448311069&guid=<...>&buyParams=<...>&afdsv2=<...>&ams=<...>
```

这串表单里的七个商品键值每个都有来头：`appAdamId=6448311069` 就是公开的 ChatGPT 官方 iOS 应用编号（打开 `apps.apple.com/app/id6448311069` 就能核对）；`salableAdamId=6657954405` 是 Pro 20x 这个内购项在苹果后台的唯一商品 ID；`productType=A` 代表自动续期订阅（Auto-Renewable Subscription）；`pricingParameters=STDQ` 是普通 App Store 标准计价常量（像 Apple Arcade 游戏内项则会用 `GAME`），`pg=default` 是默认支付组。

最容易让人看迷糊的是 `offerName=oai_chatgpt_pro_20000_1m` 和 `price=200000` 里差了整整十倍的两个数字：OpenAI 自己起的 `offerName` 内部名是按美分记的（`20000` 美分即 $200.00，`1m` 代表 1 个月），而苹果 `MZBuy` 老协议里的 `price` 字段用的是千分之一货币单位（milli-units，$1.00 等于 `1000`），所以 $200.00 传进去正好是 `200000`。

请求返回扣款成功之后，拿起那台没越狱的 iOS 18+ 手机，App Store 登着刚付完钱的这个美区 Apple ID，打开官方 ChatGPT App 登录目标 OpenAI 账号，进设置点一下"恢复购买（Restore Purchases）"，StoreKit 查到该 Apple ID 名下刚生效的 Pro 20x 订阅就会同步过去。这里顺带把概念分清：2026 年 7 月之后 OpenAI 早就修掉了早年的 [iOS 收据一票多刷漏洞](/posts/gpt-plus-receipt-vulnerability-2026/)，同一个 `original_transaction_id` 只能绑死一个 OpenAI 账号；但因为这里真金白银付了 $200 产生了一笔全新的 `original_transaction_id`，首次绑定给目标账号并不会撞上旧收据复用拦截（当然，如果后续这个 Apple ID 向苹果申请恶意退款，苹果同样会发撤销通知把关联的订阅直接收回）。

## 0x03 三大支付渠道摆在一起看：少关一层门就是敞口

把网页端 Stripe、Android 端 Google Play（配 RevenueCat）和 iOS 端 Apple IAP 横向拉张表对照一下，就能看清移动与 Web 支付攻防里各自的软肋在哪：

| 对比维度 | Stripe 网页协议流 | Google Play + RevenueCat | Apple IAP (`buyProduct`) |
|---|---|---|---|
| 凭据提取门槛 | 低（浏览器 DevTools 导 HAR） | 中（Root 挂系统证书 + 反 Pinning Hook） | 高（需备专门的老款越狱真机 + rootless 插件） |
| 平台反欺诈底座 | Stripe Radar + 企业级人机验证 | Google Play Integrity API（早年 SafetyNet 已彻底关停） | 系统底层硬件传感器指纹 `afdsv2` |
| 核心问题出在哪 | 纯 API 复刻网页结账；后端关掉创建会话入口即彻底封死 | 中间聚合层早期未核对付款凭据与目标 `app_user_id` 归属 | 前端和自有 API 撤了入口，但商店后台商品未下架，协议层直通收银台 |

归根结底，跨多端售卖订阅的业务系统想要停售某个高价档位，从来都不是让前端把按钮隐藏掉、自家 `/checkout` 接口加一行拦截就算收工的。

如果顾忌在 App Store Connect 后台一刀切下架商品会误伤存量老订户的自动续费，业务服务端在处理 [App Store Server Notifications V2](https://developer.apple.com/documentation/appstoreservernotifications) 的 JWS 通知和客户端 [StoreKit 2](https://developer.apple.com/storekit/) 恢复购买请求时，就必须显式检查交易的首次购买时间（`originalPurchaseDate`）与订阅族历史：凡是在停售截止时间点之后才新诞生的 `original_transaction_id` 首购单，一律在业务侧拒绝开权并提示走商店退款；同时在所有正常客户端发起购买时塞入 `appAccountToken` 把付款上下文跟当前登录账号焊死。前端、业务网关、第三方应用商店后台这三道门，哪一道偷懒留了条缝，协议请求就能顺着哪条缝钻进去。

---

*文中所涉协议样本与抓包字段均已隐去真实会话身份信息。*
