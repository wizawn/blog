---
title: "iOS ChatGPT Pro 20x 强开订阅全解析 — 从越狱抓包到 Apple buyProduct API 的完整技术链路"
date: 2026-09-17T22:00:00+08:00
draft: false
weight: 1
categories: ["安全研究", "支付安全", "技术科普"]
tags: ["ChatGPT", "Pro 20x", "iOS", "Apple", "IAP", "越狱", "App Store", "buyProduct", "MITM", "订阅", "支付安全", "逆向工程"]
description: "OpenAI 关闭了 Pro 20x 新订阅入口，但 App Store 的 IAP 商品仍然存在。本文深度拆解通过越狱 iOS 设备抓取 Apple ID 鉴权数据，直接调用 Apple buyProduct API 强制开通 Pro 20x 的完整技术链路。附三大支付平台（Stripe / Google Play / Apple IAP）的跨平台攻击面对比。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK  ⚠️ **博主微信暂时被封，请优先加入上方 QQ 群（46333839）**

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> 免责声明：本文基于一份已公开的教程和我们自己的协议分析写成，只讨论 Apple IAP 与订阅系统的工作原理，供安全研究和防御参考。请勿用于任何未授权操作，后果自负。

---

## 前言

OpenAI 在 2026 年下半年停掉了 Pro 20x（每月 200 美元）的新订阅入口。网页端撤了按钮，App 里去掉了选项，checkout 接口也开始拒绝新的 Pro 20x 请求。

但入口关掉不等于商品下架。前一阵有人把一套绕过办法开源了出来，思路很直接：不碰 OpenAI 的界面，直接对 Apple 的购买接口下单。OpenAI 关的是自家前端，App Store 后台那个 IAP 商品还挂着——只要能凑出一个合法的购买请求，Apple 照样扣款出收据，OpenAI 收到回执照样得开。

我拿到了那份教程的完整版，六章，从前置条件、网络配置、越狱设置一路讲到拦截原理和字段含义。下面在它的基础上补上我们自己的分析，顺带跟之前拆过的 [Stripe 协议支付](../stripe-protocol-payment-automation-deep-dive-2026)、[Google Play 订阅转移](../gpt-plus-google-play-subscription-transfer) 摆在一起对照，把这条链讲透。

---

## 一、核心原理：为什么 App Store 能绕过 OpenAI 的限制

### 1.1 OpenAI 关了什么

关的其实是几个面向用户的入口：网页端的订阅按钮和定价页没了，iOS/Android app 里不再列出 Pro 20x 这个选项，`/payments/checkout` 接口也开始拒绝 `plan_type=chatgptpro` 的新建请求。三条路都是"用户点得到的地方"，全被掐掉了。

### 1.2 OpenAI 没关什么

**App Store Connect 里的 IAP 商品没有下架。**

在 Apple 的体系里，一个 IAP 商品有自己独立的生命周期，跟 app 界面上展不展示是两码事。app 可以决定不把某个商品摆出来，但只要它在 App Store Connect 后台还挂着 "Approved"，Apple 的购买 API 就照单全收。

类比一下：超市把某个货撤下了货架，可收银系统里那个条码还在。你拿条码去自助机一扫，照样结账走人。

### 1.3 Apple 的购买 API 不管 App UI 的事

Apple 的内部购买端点是：

```
POST https://p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct
```

它收到请求后做三件事：先看鉴权字段（buyParams、guid、ams、cookie、afdsv2）合不合法，再看 salableAdamId 指向的商品在不在、能不能买，最后扣款、生成 receipt，通过 App Store Server Notifications 把交易推给开发者。

它唯独不看一件事：app 当前有没有在界面上展示这个商品。Apple 的支付系统跟 app 的 UI 是两套东西，互不干涉。

### 1.4 OpenAI 为什么一般会认这张收据

根据 Apple 的 App Store Review Guidelines（特别是 3.1.1 In-App Purchase 条款），通过 App 内购买解锁的功能必须由 Apple 的 IAP 体系交付，开发者不能在收到合法交易后拒不发放对应权益（否则可能被 Apple 判定违规、影响上架）。因此在正常设计下，OpenAI 收到一张合法且能对应到某个账号的 Pro 20x App Store 交易通知，**预期会**为该账号开通 Pro 20x。

不过要说明：这不代表 OpenAI 毫无裁量权——它仍可以基于自身风控（异常购买、退款、账号信誉等）拒绝或事后撤销开通，也可以要求交易能正确关联到一个 OpenAI 账号（见后文"交付"一节）才发放权益。"必开"是理想模型，不是绝对保证。

**所以整条链路是：**

```
构造 buyProduct 请求
    ↓
Apple 验证鉴权 + 商品存在
    ↓
Apple 扣款 $200
    ↓
Apple 生成 receipt
    ↓
App Store Server Notification → OpenAI
    ↓
OpenAI 验证 receipt → 合法 → 开通 Pro 20x
```

UI 层的限制，在协议层面毫无意义。

---

## 二、前置条件

> 有个前提得先说清楚：ChatGPT 官方 app 现在要求 iOS 18。
>
> 这个 app 的最低系统版本一直在往上抬，早前还是 iOS 17，最近一次更新提到了 iOS 18。低于 18 的系统在 App Store 里要么只能装到某个不再更新的旧版本，要么直接装不上。别小看这一条，它把整件事切成了两个对设备要求完全不同的阶段。
>
> 抓鉴权那一步，一台能越狱、能跑 MITM 的机器就够了。buyParams、guid、afdsv2、ams、cookie 这些都是 Apple ID 层面的凭证，跟你拿哪个 app 触发无关，随便走一个内购流程就能抓到，根本用不上 ChatGPT app。所以它可以是台便宜好越狱的老机器，iOS 15、16 都行。
>
> 交付那一步不一样。要把买到的订阅落到目标 OpenAI 账号上，通常得在登录了那个账号的 ChatGPT app 里点一下「恢复购买」，而新版 app 要 iOS 18 才装得上。
>
> 矛盾就在这里：主流越狱（palera1n、Dopamine）主要覆盖 iOS 15-16，往上到 17 已经零散，iOS 18 的公开越狱基本没有。想凑一台"既是 iOS 18、又越了狱"的机器很难。所以实操里一般是两台分工——一台老越狱机抓鉴权，一台正常的 iOS 18 设备（不用越狱）登录目标账号做交付。下面的设备配置都按这个思路来。

### 2.1 硬件

| 角色 | 设备 | 要求 | 说明 |
|------|------|------|------|
| **抓鉴权** | 越狱 iOS 设备 | 已越狱（iOS 版本取决于当前可用的越狱工具，通常 15-16） | 装 MITM 证书、绕过 SSL Pinning、抓 Apple ID 鉴权数据 |
| **交付** | 能跑新版 ChatGPT app 的 iOS 设备 | **iOS 18 及以上**（无需越狱） | 登录目标 OpenAI 账号，做「恢复购买」绑定订阅 |
| **代理主机** | 电脑 | macOS / Windows / Linux | 运行 MITM 代理工具 |
| **网络** | 稳定的美国代理 | — | 与 Apple ID 区域匹配 |

> 如果目标 Apple ID 就是你自己日常在用的（订阅会落到你自己账号），且 OpenAI 交付路径走的是 Apple 服务端通知（App Store Server Notifications），交付阶段理论上不一定要手动 Restore；但绝大多数实操场景仍以「iOS 18+ 设备 + ChatGPT app 手动恢复购买」为准，因此这里按需要两台设备来规划。

### 2.2 软件

| 工具 | 用途 |
|------|------|
| **越狱工具** | palera1n（A11 及以下，checkm8 漏洞，覆盖 iOS 15-16）/ Dopamine（A12-A15，覆盖 iOS 15.0-16.6.1）；iOS 17-18 公开越狱有限，按设备实际情况选择 |
| **SSL Kill Switch 2** | 绕过 App Store 的 SSL Certificate Pinning |
| **MITM 代理** | Charles Proxy / mitmproxy / Reqable（推荐 Charles，iOS 生态支持最好） |
| **ChatGPT App** | 交付设备（iOS 18+）上安装的官方版本 |

### 2.3 账号

| 账号 | 要求 |
|------|------|
| **Apple ID** | 美区，已绑定支付方式（信用卡/借记卡/Apple 礼品卡余额），且卡内/余额足够支付一个月 Pro 20x |
| **OpenAI 账号** | 目标 ChatGPT 账号（交付阶段需要在 iOS 18+ 设备上登录） |

### 2.4 为什么必须越狱

简单说：**Apple 的 App Store 和 iTunes Store 有 SSL Certificate Pinning（证书锁定）。**

正常情况下，即使你在 iOS 系统里安装并信任了 MITM 代理的 CA 证书，App Store 的流量仍然无法被代理拦截——因为 App Store 只信任 Apple 自己的证书，不走系统信任链。

越狱后装 SSL Kill Switch 2（或类似 tweak），可以在 runtime hook 掉证书校验函数，让 App Store 的流量走系统信任链 → 被 MITM 代理截获。

这和我们在 Android 上做的事一样——Android 的 ChatGPT App 也有证书锁定，需要 Frida/Xposed 来绕过。**平台不同，原理一模一样。**

---

## 三、网络环境配置

### 3.1 代理配置

Apple 的购买 API 会检查请求的源 IP 是否与 Apple ID 的注册区域匹配。美区 Apple ID 必须用美国 IP。

```
iOS 设备 → HTTP 代理（MITM） → 上游 SOCKS5 代理（美国住宅 IP） → Apple 服务器
```

推荐架构：

```
iPhone ──WiFi──▶ 电脑（Charles / mitmproxy）
                        │
                        ▼
               上游代理（US 住宅 IP）
                        │
                        ▼
             p70-buy.itunes.apple.com
```

Charles 配置上游代理：`Proxy → External Proxy Settings → SOCKS Proxy → 填入美国代理地址`

### 3.2 MITM 证书安装

1. 打开 Charles → `Help → SSL Proxying → Install Charles Root Certificate on a Mobile Device`
2. iPhone 浏览器访问 `chls.pro/ssl` 下载证书
3. `设置 → 通用 → VPN 与设备管理 → 安装描述文件`
4. `设置 → 通用 → 关于本机 → 证书信任设置 → 启用完全信任`

**关键步骤**：第 4 步很多人漏掉。iOS 安装证书和信任证书是两个独立操作，只安装不信任 = 白装。

### 3.3 SSL Proxying 规则

在 Charles 中配置 SSL Proxying：

```
Proxy → SSL Proxying Settings → Enable SSL Proxying
Add:
  Host: *.itunes.apple.com
  Port: 443
Add:
  Host: *.apple.com
  Port: 443
```

如果用 mitmproxy：

```bash
mitmproxy --mode regular --set upstream_cert=false -p 8888
```

配置完成后，访问 App Store 应该能在代理工具中看到明文 HTTPS 请求。如果还是显示 `CONNECT` 隧道而不是解密内容，说明 SSL Kill Switch 没生效——检查越狱工具和 tweak 的兼容性。

---

## 四、iOS 越狱设备配置

### 4.1 越狱工具选择

这一台只用来**抓鉴权**，不需要跑 ChatGPT app，所以选一个越狱成熟、稳定的老系统即可：

| iOS 版本 | 处理器 | 推荐工具 | 类型 |
|----------|--------|---------|------|
| 15.0-16.6.1 | A12-A15 | Dopamine | semi-untethered（rootless） |
| 15.0-16.7.x | A8-A11 | palera1n | semi-tethered（checkm8，需重插） |
| 17.x / 18.x | A12+ | 公开越狱有限，视设备而定 | — |

> **提示**：抓鉴权的设备不用追新。用一台老款 iPhone（如 A11 的 iPhone 8/X，配 palera1n）专门做这件事就够了，闲鱼几百块一台。**注意区分角色**：这台老机器负责抓鉴权，真正登录目标账号、做「恢复购买」的是另一台 iOS 18+ 设备（见 §2）——别指望在一台 iOS 15 的老机器上装新版 ChatGPT app。

### 4.2 安装必要 Tweak

越狱完成后，通过 Cydia/Sileo 安装：

```
SSL Kill Switch 2    — 绕过证书锁定
PreferenceLoader     — Tweak 设置面板
AppList              — 应用列表（SSL Kill Switch 依赖）
```

SSL Kill Switch 2 设置：

```
Settings → SSL Kill Switch 2
  ├── Disable Certificate Validation: ON
  └── 选择目标 App → 勾选 App Store / iTunes Store
```

**注意**：不要全局开启证书绕过——那样会影响所有 App 的安全性。只针对 App Store / iTunes Store 开启就够了。

### 4.3 验证 MITM 生效

打开 App Store → 随便搜个 App → 查看代理工具：

- **成功**：看到 `GET https://p70-buy.itunes.apple.com/...` 的解密请求
- **失败**：只看到 `CONNECT p70-buy.itunes.apple.com:443` 且无解密内容

如果失败，排查：
1. SSL Kill Switch 是否选中了正确的进程（`com.apple.AppStore`）
2. 越狱环境是否完整（`uicache` / `ldrestart` 后重试）
3. 代理证书是否已经被**完全信任**（不只是安装）

---

## 五、订阅拦截与转移原理

这一节是整个方法的核心。

### 5.1 Apple 购买请求的鉴权体系

在 App Store 里点一下"购买"，iOS 会往 Apple 的购买服务器发一个 HTTP POST 请求，里头带着五个关键的鉴权字段：

| 字段 | 全称 | 说明 | 类比 |
|------|------|------|------|
| `buyParams` | Buy Parameters | Apple 生成的购买上下文参数包，包含加密的会话数据 | 类似 Stripe 的 `client_secret` |
| `guid` | Global Unique Identifier | 设备唯一标识符，由硬件信息计算得出 | 类似 Stripe 指纹的 `muid` |
| `afdsv2` | Apple Fraud Detection Service v2 | Apple 的反欺诈指纹 token，采集设备行为数据 | 类似 Stripe Radar 的设备指纹 |
| `ams` | Apple Media Services | 媒体服务鉴权 token | 类似 RevenueCat 的 API Key |
| `cookie` | Session Cookies | Apple ID 会话 cookie（含 `myacinfo`、`itctx` 等） | 类似 OpenAI 的 `__Secure-next-auth` |

这五个字段凑齐，等于拿到了你 Apple ID 的完整付款授权——谁手里有它们，谁就能以你的身份向 Apple 下单。

### 5.2 各字段深度解析

#### buyParams

这是一个 Base64 编码的二进制数据包，由 App Store 客户端在发起购买时生成。内部包含：
- 当前 Apple ID 的 session 信息
- 购买请求的签名数据
- 设备上下文信息

**重要特性**：根据原始教程的描述和实际操作验证，buyParams 与**当前购买会话**绑定，但据称不与**特定商品 ID** 绑定——这意味着触发任意 IAP 时抓到的 buyParams，可以配合不同的商品参数（如 salableAdamId）使用。这是整个方法成立的关键前提。

#### guid

设备的唯一标识。在 iTunes/App Store 这套协议里，guid 通常由设备网络接口的 MAC 地址等硬件标识生成，表现为一串十六进制字符（桌面客户端上常见是 12 位，真机上的取值方式可能不同）。

它跟设备硬件绑定，不会随便变。同一台机器反复操作，guid 一直是那一个——风控要盯的话，这是个很明显的锚点。

#### afdsv2

Apple Fraud Detection Service v2。这是 Apple 自研的反欺诈系统，类似于 Stripe 的 Radar。根据已知的设备指纹技术和逆向分析，它在设备端可能采集的信号包括（不限于）：

- 传感器数据（加速度计 / 陀螺仪等）
- 设备状态（电池、屏幕亮度等）
- 触控行为模式
- 网络环境信息
- 系统运行时信息

生成的 token 是一个很长的字符串（通常 1000+ 字符），每次购买请求都会重新生成。

**越狱对 afdsv2 的影响**：Apple 的 FDS 理论上可以检测到越狱状态。但根据社区反馈，只要不修改 afdsv2 的生成过程（即让系统正常收集并生成），越狱设备的 afdsv2 通常仍会被接受。风险是长期频繁操作可能积累风控分数被标记。

#### ams

Apple Media Services token，用于标识当前登录的 Apple ID 在 Apple 媒体服务体系中的身份。这个 token 通常在 Apple ID 登录时颁发，有效期较长。

#### cookie

Apple ID 的会话凭据集合。这里的"cookie"是一个泛称，实际包含 HTTP Cookie 和自定义请求头两类：

**Cookie：**

| Cookie 名 | 说明 |
|-----------|------|
| `myacinfo` | Apple ID 主会话 token |
| `itctx` | iTunes 上下文 token |

**自定义请求头（随 cookie 一起抓取）：**

| Header 名 | 说明 |
|-----------|------|
| `X-Dsid` | Directory Services ID（Apple ID 数字标识） |
| `X-Apple-I-MD` | Machine Data（设备标识数据） |
| `X-Apple-I-MD-M` | Machine Data Metadata（设备标识元数据） |

### 5.3 与 Stripe / Google Play 的鉴权对比

我们做了三个平台的支付协议逆向，正好可以做个对比：

| 维度 | Stripe 协议支付 | Google Play (RevenueCat) | Apple IAP (buyProduct) |
|------|----------------|-------------------------|----------------------|
| **绕过层** | Web UI → 直调 Stripe API | App UI → Xposed 拦截 BillingClient | App UI → 直调 Apple Purchase API |
| **鉴权抓取方式** | HAR 抓包（浏览器 DevTools） | MITM + Xposed Hook | MITM（越狱 + SSL Kill Switch） |
| **核心鉴权字段** | pk_live / ctoken / client_secret / guid+muid+sid | fetch_token + app_user_id + RC API Key | buyParams / guid / afdsv2 / ams / cookie |
| **反欺诈系统** | Stripe Radar + hCaptcha Enterprise | Google Play Protect + SafetyNet | Apple FDS (afdsv2) |
| **TLS 指纹检测** | 有（Cloudflare + Stripe 自检） | 无（RC 不检查 TLS 指纹） | 有（Apple 自有 CDN 检测） |
| **证书锁定** | 无（浏览器不锁定） | 有（需 Frida/Xposed 绕过） | 有（需 SSL Kill Switch 绕过） |
| **token 有效期** | Session 级（分钟到小时） | 72 小时（未 Acknowledge） | Session 级 |
| **复用性** | 每次需要新 ctoken | 一 token 一账号 | 需看具体实现 |

三个平台的共同点：**都是在协议层绕过 UI 层的限制，核心逻辑完全相同。**

差异在于"如何获取鉴权凭据"和"反欺诈系统有多强"。Stripe 最容易（浏览器 DevTools 导出 HAR 即可），Google Play 居中（需要 Root/Xposed 但不需要越狱），Apple 最难（必须越狱 + MITM）。

### 5.4 "订阅转移"的原理

文档标题里还有个关键词：**订阅转移**。

这和我们之前写过的 [Google Play 订阅转移](../gpt-plus-google-play-subscription-transfer) 是一个思路：

1. **Apple ID A** 在越狱设备上完成购买 → Pro 20x 订阅绑定到 Apple ID A
2. ChatGPT App 收到 App Store 的购买回执，准备把权益绑定到当前登录的 OpenAI 账号
3. **在 App 处理回执之前**，切换 ChatGPT 的登录账号到目标账号 B
4. App 把 Pro 20x 权益绑到了账号 B

> **注意**：上面这条路径描述的是"通过 App 的 StoreKit 正常发起购买"的场景。而本文的核心方法是用**原始 buyProduct API** 完成购买——此时 App 并不会自动收到一个待提交的回执。因此在 API 购买的场景下，真正可靠的绑定方式是下面 §9.2 的 **Restore Purchases**：设备登录购买用的 Apple ID A，在登录了目标 OpenAI 账号 B 的 ChatGPT app 里点「恢复购买」，StoreKit 会向 Apple 查到 A 名下的 Pro 20x 订阅并同步给账号 B。

或者更直接的方式——类似我们之前分析过的 [iOS 收据复用漏洞](../gpt-plus-receipt-vulnerability-2026)：

1. 在设备上完成购买，拦截 App 发给 OpenAI 的回执提交请求
2. 修改请求中的 auth token（换成目标账号的 token）
3. 重放请求 → 目标账号获得 Pro 20x

说到底，Apple 只负责收钱出票，OpenAI 只负责验票开权。中间这张票落到谁头上，取决于你怎么操作。

---

## 六、订阅流程详解

### 6.1 完整操作流程

```
┌─────────────────────────────────────────────────────────┐
│               Phase 1: 鉴权数据捕获                      │
│                                                         │
│  越狱 iOS 设备 + MITM 代理 + SSL Kill Switch            │
│  打开 App Store → 触发任意 IAP 购买（如 Plus）           │
│  代理中拦截 POST .../buyProduct 请求                     │
│  提取: buyParams, guid, afdsv2, ams, cookie             │
│  阻断请求（不让它真正完成支付）                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               Phase 2: 构造 Pro 20x 购买请求              │
│                                                         │
│  保留 Phase 1 的鉴权字段                                 │
│  替换商品参数为 Pro 20x 的值:                             │
│    productType = A                                      │
│    salableAdamId = 6657954405                            │
│    offerName = oai_chatgpt_pro_20000_1m                 │
│    price = 200000                                       │
│    appAdamId = 6448311069                               │
│  发送到: p70-buy.itunes.apple.com/.../buyProduct        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               Phase 3: Apple 处理 + OpenAI 开通           │
│                                                         │
│  Apple 验证鉴权 → 扣款 $200 → 生成 transaction           │
│  App Store Server Notification → OpenAI 后端             │
│  OpenAI 验证 receipt → 合法 → 开通 Pro 20x              │
│  或: 在 ChatGPT App 中 "Restore Purchases" 触发同步     │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Phase 1 详细步骤

**Step 1**：越狱设备连接 MITM 代理，确认代理工作正常。

**Step 2**：在 Charles 中设置 Breakpoint（断点拦截）：

```
Proxy → Breakpoints → Add:
  Protocol: HTTPS
  Host: p70-buy.itunes.apple.com
  Path: */buyProduct*
  方向: Request（拦截请求，不拦截响应）
```

**Step 3**：在越狱设备上打开 ChatGPT App → 进入订阅页面 → 触发任意一个 IAP 购买流程。

这一步你可以随便选哪个套餐——Plus、Pro Lite、随便一个。目的不是真的购买，而是触发 App Store 的支付流程，让系统生成鉴权数据。

**Step 4**：当 App Store 弹出支付确认面板时，确认支付（Face ID / Touch ID / 密码）。

**Step 5**：确认后，Charles 会在断点处拦截到 `POST .../buyProduct` 请求。此时请求**还没有发送到 Apple 服务器**。

**Step 6**：从请求体中提取 5 个关键字段并保存：

```
buyParams = <Base64 长字符串>
guid = <十六进制字符串，长度视设备而定>
afdsv2 = <1000+ 字符的长字符串>
ams = <Apple Media Services token>
cookie = <完整的 Cookie 字符串>
```

**Step 7**：在 Charles 中选择 **Abort**（中止请求），不让它到达 Apple 服务器。这样不会产生真实扣款。

### 6.3 Phase 2 详细步骤

拿到鉴权数据后，用脚本或者 HTTP 工具（如 Postman / curl / Python requests）构造 Pro 20x 的购买请求：

```http
POST https://p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct
Content-Type: application/x-www-form-urlencoded
Cookie: <Phase 1 保存的完整 cookie>
X-Apple-I-MD: <Machine Data>
X-Apple-I-MD-M: <Machine Data Metadata>
X-Dsid: <Directory Services ID>

productType=A
&price=200000
&salableAdamId=6657954405
&pricingParameters=STDQ
&pg=default
&offerName=oai_chatgpt_pro_20000_1m
&appAdamId=6448311069
&guid=<Phase 1 的 guid>
&buyParams=<Phase 1 的 buyParams>
&afdsv2=<Phase 1 的 afdsv2>
&ams=<Phase 1 的 ams>
```

**注意事项**：

1. **代理 IP 一致性**：这个请求必须走和 Phase 1 相同的出口 IP。Apple 会比对购买请求的源 IP，如果和鉴权生成时的 IP 不同，可能被拒。这与 [Stripe 协议支付](../stripe-protocol-payment-automation-deep-dive-2026)中的"出口 IP 一致性"规则完全相同。

2. **时效性**：鉴权数据（特别是 buyParams 和 afdsv2）有时效性。抓到后应尽快使用，拖太久 token 会过期。

3. **请求头**：除了 Cookie 外，还需要带上 Apple 的特征请求头（`X-Apple-I-MD` 等）。这些也在 MITM 抓包中一并获取。

### 6.4 Phase 3：交付

Apple 处理购买后有两种通知机制：

**机制一：App Store Server Notifications V2（服务端到服务端）**

Apple 向 OpenAI 配置的 notification endpoint 发送 JSON Web Signature (JWS) 格式的通知，包含完整的交易信息。OpenAI 的后端验证 JWS 签名 → 确认交易合法 → 开通对应的订阅。

这是最可靠的通知路径，不需要客户端参与。

**机制二：App 端 Restore Purchases**

在 ChatGPT App 中执行"恢复购买"操作（StoreKit 的 `restoreCompletedTransactions`），App 会向 Apple 服务器查询当前 Apple ID 的所有有效订阅，然后把新的 Pro 20x 订阅同步到当前登录的 OpenAI 账号。

换句话说，Apple 扣完钱，把"这个用户买了 Pro 20x"的通知发给 OpenAI，OpenAI 就得开权益；用户自己在 app 里点一下"恢复购买"，走的是另一条路，结果一样。

---

## 七、关键请求与字段说明

### 7.1 商品参数逐字段拆解

```
productType=A&price=200000&salableAdamId=6657954405&pricingParameters=STDQ&pg=default&offerName=oai_chatgpt_pro_20000_1m&appAdamId=6448311069
```

| 字段 | 值 | 含义 | 怎么确定的 |
|------|-----|------|-----------|
| `productType` | `A` | Auto-Renewable Subscription（自动续期订阅） | Apple IAP 的订阅商品类型标识 |
| `price` | `200000` | 对应 Pro 20x 月费 $200.00 | Apple 内部价格编码（具体单位以实际抓包为准） |
| `salableAdamId` | `6657954405` | Pro 20x 这个 IAP 商品的 Apple 内部 ID | 每个 IAP 商品在 Apple 系统里都有唯一的 Adam ID |
| `pricingParameters` | `STDQ` | 标准 App Store 商品的定价参数 | 逆向工具（如 ipatool）里已知的常量：普通 App Store 商品用 `STDQ`，Apple Arcade 用 `GAME` |
| `pg` | `default` | 支付组 | 默认支付组 |
| `offerName` | `oai_chatgpt_pro_20000_1m` | 商品名称标识 | `oai`=OpenAI, `chatgpt`=ChatGPT, `pro`=Pro 档, `20000`=2 万美分即 $200, `1m`=1 个月 |
| `appAdamId` | `6448311069` | ChatGPT App 的 App Store ID | 在 `apps.apple.com/app/id6448311069` 可验证 |

### 7.2 ChatGPT 的 IAP 商品体系（推测）

基于 offerName 的命名规则推导——仅 Pro 20x 的值来自已公开的教程，其余为合理推测：

| 订阅档位 | 月费 | 推测的 offerName | salableAdamId |
|---------|------|-----------------|---------------|
| Plus | $20 | `oai_chatgpt_plus_2000_1m`（推测） | 未知 |
| Pro Lite (5x) | $100 | `oai_chatgpt_pro_10000_1m`（推测） | 未知 |
| **Pro (20x)** | **$200** | **`oai_chatgpt_pro_20000_1m`**（已确认） | **6657954405** |

### 7.3 端点地址解析

```
https://p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct
```

| 部分 | 含义 |
|------|------|
| `p70` | Apple CDN 服务器池编号。Apple 使用多个服务器池（p25, p47, p70 等），不同设备/区域可能被路由到不同的池 |
| `buy.itunes.apple.com` | iTunes Store 购买服务域名 |
| `WebObjects` | Apple 的 WebObjects 框架标识（Apple 自研的 Java Web 框架，iTunes Store 后端至今仍在使用） |
| `MZBuy.woa` | "MZ" = MobileZone，Buy 应用的 WebObjects Application |
| `wa/buyProduct` | WebObjects Direct Action，执行购买操作 |

**题外话**：WebObjects 最初由 NeXT 公司在 1996 年推出（起初基于 Objective-C，2000 年 WebObjects 5 转向 Java），后随 NeXT 被 Apple 收购。Apple 的 iTunes Store / App Store 后端至今仍在使用这个已有 30 年历史的框架。`MZBuy.woa` 这种 URL 结构在互联网上几乎只有 Apple 在用——看到 `.woa` 后缀就知道是 Apple 的后端。

### 7.4 buyParams 的结构特征

虽然 buyParams 的内部格式是加密的（Apple 的私有协议），但从外部特征可以观察到：

- **编码格式**：Base64
- **解码后大小**：通常 200-500 字节
- **包含信息**：经过加密的购买会话上下文
- **生成时机**：在设备端触发购买流程时由 StoreKit 框架生成
- **有效期**：通常几分钟内有效
- **绑定关系**：与当前 Apple ID session + 设备绑定，但不与特定商品绑定

### 7.5 afdsv2 的结构特征

Apple Fraud Detection Service v2 token：

- **长度**：通常 1000-4000 字符
- **编码**：Base64 或自定义编码
- **采集数据**：加速度计、陀螺仪、电池状态、屏幕信息、网络环境、应用列表等
- **生成频率**：每次购买请求都重新生成
- **对应平台**：类似 Stripe Radar 的 `device_data`，或 Google 的 SafetyNet attestation

与 Stripe 的对比：

| | Stripe Radar | Apple FDS (afdsv2) |
|---|---|---|
| **信号来源** | 浏览器 JS（m.stripe.com/6） | iOS 系统级 API |
| **采集深度** | 浏览器指纹、Canvas、WebGL | 硬件传感器 + 系统状态 |
| **检测越狱/Root** | 不直接检测 | 可能检测（但不一定阻断） |
| **可伪造性** | 较容易（curl_cffi 等） | 困难（硬件数据难以伪造） |

这也是为什么 Apple IAP 路径的安全级别比 Stripe 协议支付更高——**你很难在没有真实 iOS 设备的情况下伪造 afdsv2。** 必须在真机上操作。

---

## 八、跨平台攻击面全景对比

做了三个支付平台的协议逆向之后，我们可以画一张完整的攻击面全景图：

### 8.1 三条路径

```
┌──────────────────────────────────────────────────────────────────┐
│                    ChatGPT Pro 20x 开通                          │
│                                                                  │
│  路径 1: Stripe 协议支付                                          │
│  ┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐  │
│  │ HAR 抓包 │→ │ 构造 ctoken │→ │ PI confirm  │→ │ Stripe   │  │
│  │ (浏览器) │   │ + 税务优化  │   │ + 3DS 处理  │   │ webhook  │  │
│  └─────────┘   └────────────┘   └────────────┘   └──────────┘  │
│                                                                  │
│  路径 2: Google Play 订阅转移                                     │
│  ┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐  │
│  │ MITM 或  │→ │ 提取 fetch │→ │ RC /receipts│→ │ RC 通知  │  │
│  │ ADB 提取 │   │ _token     │   │ + account  │   │ OpenAI   │  │
│  └─────────┘   └────────────┘   └────────────┘   └──────────┘  │
│                                                                  │
│  路径 3: Apple IAP 强开（本文）                                    │
│  ┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐  │
│  │ 越狱    │→ │ 抓取 5 个   │→ │ buyProduct  │→ │ ASSN V2  │  │
│  │ + MITM  │   │ 鉴权字段   │   │ API 调用    │   │ 通知     │  │
│  └─────────┘   └────────────┘   └────────────┘   └──────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 全维度对比

| 维度 | Stripe 协议支付 | Google Play 转移 | Apple IAP 强开 |
|------|----------------|-----------------|---------------|
| **设备要求** | 无（纯 HTTP） | Android（Root 或 MITM） | iOS（必须越狱） |
| **入门难度** | 低 | 中 | 高 |
| **单次成本** | 信用卡扣款金额 | 信用卡扣款金额 | Apple ID 支付方式扣款 |
| **自动化程度** | 极高（纯 API） | 高（ADB + API） | 中（依赖越狱设备） |
| **反检测难度** | TLS 指纹 + hCaptcha | 较低 | afdsv2 设备指纹 |
| **OpenAI 验证** | Stripe webhook | RevenueCat 通知 | App Store Server Notification |
| **可规模化** | 完全可脚本化 | 可脚本化 | 受限于越狱设备数量 |
| **OpenAI 能修吗** | 能（加强 session 校验） | 能（RC 侧加 user 校验） | 难（需要在 ASC 下架商品） |

### 8.3 从攻击面看防御优先级

**最容易修的是 Google Play 路径**：RevenueCat 只要在 `/v1/receipts` 接口加上 `app_user_id` 与付款人的校验，就能堵住转移漏洞。

**Stripe 路径本质上不是漏洞**——它只是用 API 替代了浏览器操作，属于自动化而非绕过。OpenAI 关闭 checkout 入口就堵死了这条路（但目前 Stripe 路径仅用于已开放的订阅档位）。

**Apple IAP 路径最难修**。要堵这个洞，OpenAI 有两个选择：

1. **在 App Store Connect 下架 Pro 20x 商品** → 但这会影响现有 iOS Pro 用户的续费
2. **在收据验证时拒绝新的 Pro 20x 购买** → 可行，但需要区分"新购买"和"续费"

Apple 自己也很难帮忙——因为从 Apple 的角度看，这是一笔完全合法的交易。用户有 Apple ID、有支付方式、有真实设备、商品也是 approved 状态。Apple 的系统设计初衷就是让开发者可以灵活管理 IAP 商品，而不是让 Apple 来决定哪些商品能卖。

---

## 九、关于"订阅转移"的额外分析

### 9.1 收据转移（Receipt Transfer）

这个方法和我们之前写的 [iOS 收据复用漏洞](../gpt-plus-receipt-vulnerability-2026) 是可以结合使用的。

流程：
1. 通过 buyProduct API 完成购买，Apple 向 ChatGPT App 推送 receipt
2. 拦截 ChatGPT App 提交给 OpenAI 的 receipt 请求
3. 将 receipt 绑定到不同的 OpenAI 账号

但需要注意：2026 年 7 月后 OpenAI 已经**部分修复**了 iOS 收据复用漏洞。具体表现为收据的 `original_transaction_id` 会被检查——同一个 `original_transaction_id` 不能同时绑定多个 OpenAI 账号。

**但如果每次都是新购买（新的 transaction），收据都是新的**，转移不受此限制。

### 9.2 Restore Purchases 路径

更简单的转移方式：

1. 在越狱设备上用 **Apple ID A** 完成 Pro 20x 购买
2. 在 ChatGPT App 中登录 **OpenAI 账号 B**
3. 在 App 内执行 "Restore Purchases"（恢复购买）
4. StoreKit 查询 Apple ID A 的有效订阅 → 找到 Pro 20x
5. ChatGPT App 将 Pro 20x 绑定到 OpenAI 账号 B

**这要求**：在步骤 3 时，设备登录的 Apple ID 必须是 A（即购买 Pro 20x 的那个 Apple ID）。这样 StoreKit 才能查到对应的订阅。

---

## 十、风险与注意事项

### 10.1 Apple 账号风险

| 风险 | 等级 | 说明 |
|------|------|------|
| Apple ID 封禁 | **中** | 频繁异常购买可能触发 Apple 的账号风控 |
| 支付方式封禁 | **中** | 信用卡频繁大额 IAP 可能被银行标记 |
| 设备封禁 | **低** | Apple 目前不会因为 IAP 行为封禁设备，但 guid 会被记录 |
| 退款追溯 | **高** | Apple 的退款政策可以追溯，OpenAI 收到退款通知会撤销订阅 |

### 10.2 越狱设备安全

越狱 = 放弃 iOS 的安全模型。需要注意：

1. **不要在越狱设备上存储敏感信息**（主力 Apple ID、银行 App 等）
2. **专机专用**：用一台专门的老设备做这件事
3. **及时清理**：操作完成后关闭 SSL Kill Switch，避免日常使用时被中间人攻击

### 10.3 合法性

不同司法管辖区对这类操作的定性不同。一些可能的法律风险：

- **绕过技术保护措施**：越狱本身在某些国家/地区属于灰色地带
- **违反 TOS**：OpenAI 和 Apple 的服务条款都禁止此类操作
- **计算机欺诈**：通过技术手段获取未被授权的服务访问权

**本文仅供技术研究与学习。** 实际操作的法律后果由读者自行承担。

---

## 十一、技术总结

### 完整攻击链路

```
越狱 iOS + MITM → 抓取 buyParams/guid/afdsv2/ams/cookie
                    ↓
            构造 Pro 20x buyProduct 请求
                    ↓
  p70-buy.itunes.apple.com/WebObjects/MZBuy.woa/wa/buyProduct
                    ↓
         Apple 验证鉴权 → 扣款 $200 → 生成 receipt
                    ↓
    App Store Server Notification V2 → OpenAI 后端
                    ↓
        OpenAI 验证 receipt → 合法 → 开通 Pro 20x
```

### 漏洞本质

**平台方（OpenAI）在 UI 层关闭了入口，但在支付平台（Apple）层面没有关闭商品。** 只要 App Store Connect 里的 IAP 商品还处于 "Approved" 状态，Apple 的购买 API 就接受任何合法的购买请求，不管 App 的 UI 有没有展示这个商品。

这和我们之前发现的每一个支付漏洞的本质是一样的：

- [0 PHP 跨区混淆](../chatgpt-plus-0php-cross-region-pricing-exploit-2026)：**Stripe 创建 session 时的区域信号不一致**
- [prorationMode Hook](../google-play-ccmax-proration-vulnerability-2026)：**Google Play Billing 的 proration 参数可被客户端修改**
- [RevenueCat 凭证转移](../gpt-plus-google-play-subscription-transfer)：**RevenueCat 不校验付款人与开通人的对应关系**
- [₱982 Pro 20x TOCTOU](../chatgpt-pro20x-982php-toctou-race-condition-2026)：**Stripe PI 金额锁定与订阅计划变更不互斥**
- [iOS 收据复用](../gpt-plus-receipt-vulnerability-2026)：**OpenAI 不校验收据与 Apple ID 的绑定关系**
- **iOS IAP 强开（本文）**：**App Store 商品未下架，API 层可绕过 UI 层限制**

说白了就一句话：几层状态得对齐。UI 关了，API 也得关；API 关了，支付平台后台的商品也得跟着下架。中间任何一层没关严，那层就是留给别人的入口。

---

## 参考资料

- [Apple In-App Purchase 文档](https://developer.apple.com/in-app-purchase/)
- [App Store Server Notifications V2](https://developer.apple.com/documentation/appstoreservernotifications)
- [StoreKit 2 文档](https://developer.apple.com/storekit/)
- [SSL Kill Switch 2](https://github.com/nabla-c0d3/ssl-kill-switch2)
- [mitmproxy 官方文档](https://docs.mitmproxy.org/)
- [Stripe 协议支付深度拆解（本站）](../stripe-protocol-payment-automation-deep-dive-2026)
- [GPT Plus 订阅转移全解析（本站）](../gpt-plus-google-play-subscription-transfer)
- [iOS 收据复用漏洞（本站）](../gpt-plus-receipt-vulnerability-2026)

---

**标签**: #ChatGPT #Pro20x #iOS #Apple #IAP #越狱 #AppStore #支付安全 #订阅 #逆向工程 #Stripe #GooglePlay
