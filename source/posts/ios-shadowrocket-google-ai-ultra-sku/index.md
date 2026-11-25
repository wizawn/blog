---
title: "iOS 免越狱改写 SKU 拿 Google AI Ultra 免费试用与一折价：小火箭、Clash、Stash、Surge、圈 X、Loon 全客户端实录"
date: 2026-11-24T22:00:00+08:00
lastmod: 2026-11-25T13:55:00+08:00
description: "在 iPhone 上免越狱拦截宿主 App 内嵌网页与原生 Protobuf 双通道，把默认下发的 iOS 原价 SKU 替换成隐藏促销编号，通过苹果 StoreKit 拉出 Google AI Ultra 首月 $0 免费试用或 $9.99 / $19.99 一折价，附美区 Apple ID 绑卡避坑与全客户端配置。"
categories: ["安全研究", "技术分析"]
tags: ["Google AI Ultra", "Google One", "Shadowrocket", "小火箭", "Clash", "Stash", "Surge", "Quantumult X", "Loon", "SKU 改写", "iOS"]
draft: false
weight: 10
---

## 0x00 上回塞 Frida 太重，这回把 iOS 全家桶代理工具一次配齐

[上一篇](/posts/google-ai-ultra-trial/)折腾 Google AI Ultra 的 `$0` 试用时，走的是 Android 模拟器那条重路子：在电脑上装 MuMu、推 `frida-server`、备一个带结算库的 `module.apk`，再用 `DexClassLoader` 动态塞进 Google One 进程里调 `BillingClient`。整套流程跑得挺稳，但对没碰过逆向的朋友实在不太友好，光是配 ADB 端口转发和来回切类加载器就能劝退一大半人。

后来顺手抓了一下 iPhone 上的请求链路，发现 iOS 端免越狱压根不用搞进程注入那么重。谷歌旗下的 iOS 客户端在渲染 AI 订阅升级页时，当前允许展示哪些套餐编号（也就是 SKU），全靠服务端通过两条通道下发给手机：一条是宿主 App 内嵌 `WKWebView` 请求的 `https://one.google.com/ai`（多账号路径长成 `/u/0/ai`），返回明文 HTML 与内嵌配置块。

另一条则是原生套餐展台接口 `https://subscriptionsmobile-pa.googleapis.com/$rpc/google.internal.one.v1.StorefrontService/GetDynamicStorefrontInfo`，走的是带 5 字节帧头的二进制 gRPC / Protobuf 数据流。只要让手机上的代理软件在本地当个中间传话的，趁这两路响应落回客户端之前把里面写死的 `g1.ios.*` 日常正价编号偷偷替换成隐藏促销编号，App 点订阅时就会乖乖拿着换过的商品 ID 去拉苹果收银台。

不管你主力用的是小火箭（`Shadowrocket`）、`Surge`、`Clash` 全系（包括 iOS 端的 `Stash`，以及跑纯 `Mihomo` 内核的 `Clash Mi`、`FlClash`、`Clash Verge`、`Karing`），还是 `Loon`、`Quantumult X`（圈 X）、`Egern`，底子都是同一套拦截逻辑，只是各家配置文件的写法和内核能力有一点差别。动手前先看一眼下面这张表，对号入座挑自己手头正在用的工具往下翻就行：

| 你手里正在用的客户端 | 本地 HTTPS 改包能力 | 推荐挂载格式 | 是否需要电脑配合 |
|---|---|---|---|
| `Shadowrocket`（小火箭）/ `Surge` | 原生支持请求头、正文正则与二进制脚本 | 在原有配置上叠加 `.sgmodule` 模块 | 不需要，纯手机独立完成 |
| `Stash`（iOS 版 Clash 生态） | 原生内置 `http.mitm` 与 `binary-mode` 脚本 | 在现有机场配置上叠加 `.stoverride` 覆写 | 不需要，内联脚本单文件生效 |
| `Clash Mi` / `FlClash` / `Clash Verge` / `Karing` | 纯 `Mihomo` 内核无本地改响应体引擎 | `+proxies` / `+rules` 或 `main(config)` 覆写 | 需要同一 Wi-Fi 下电脑开改写网关 |
| `Loon` / `Quantumult X`（圈 X）/ `Egern` | 原生支持 MITM 与二进制响应体脚本 | `.plugin` / `.snippet` / `Egern.yaml` + `.js` | 不需要，纯手机独立完成 |

## 0x01 两条实测路线、StoreKit 结算边界，还有三个入口 App 的差异

最开始我也犯过一个想当然的经验主义错误：以为 `.acq` 这类跨端拉新编号只认谷歌网页端的 `payments.google.com` 结算，甚至还去试过拿手机 Safari 直接开 `one.google.com/ai` 能不能照猫画虎。结果真机挂上 `storekitd` 日志跟抓包一对才彻底摸清底牌：`g1.ios.30tb.ai.pro.m`、`g1.ios.20tb.m.v2`、`g1.ios.2tb.*` 全是苹果 App Store Connect 后台注册的 `SKProduct` 内购商品编号，只有在 iOS 原生宿主应用（彩色 G 图标的 `Google` 搜索 App、`Gemini` App、`Google One` App）的内嵌 `WKWebView` 与原生 `GetDynamicStorefrontInfo` 通道里才会下发，点按钮后直接桥接苹果本地 `StoreKit`。你要是拿普通手机 Safari 浏览器去开 `one.google.com/ai`，服务端压根不会吐出 `g1.ios.*` 编号，谷歌纯网页结算走的也是服务端签名的加密令牌而非客户端明文 SKU。

这就把整套方案的结算边界彻底框死了。iOS 免越狱改写 SKU 全程走苹果 App Store（`StoreKit` 应用内购买）收银台，扣款与验资只看当前 iPhone 在 `设置 -> Apple 账户 -> 媒体与购买项目` 里登录的那个美区 Apple ID 及其绑定的支付方式，跟谷歌账号底下 `payments.google.com` 绑没绑卡、付款资料锁在哪个国家没有半毛钱关系。谷歌账号那边唯一需要提前确认的干净前提，是当前号上不能挂着任何现存的 Google One 订阅（哪怕顶着一个 100GB 基础版，后台算资格时也会直接把新客 `.acq` 优惠剥掉）。另外，彩色 G 图标的 `Google` 搜索 App、`Gemini` App 和 `Google One` App 虽然升级页底层都走这套链路，但三者在 App Store Connect 后台登记的内购商品子集与本地缓存并不一样，在某一个 App 里点开如果只弹原价，换另外两个官方 App 重试往往就能拉出折扣。

按手里账号的新老情况，实测下来一共分两条路走，原价编号、目标促销编号与优先推荐的入口 App 对照如下：

| 目标方案与参考扣款价 | 原响应里的默认 SKU | 替换后的目标促销 SKU | 手机端优先推荐的入口 App |
|---|---|---|---|
| Ultra 20x（30TB）首月 $0 免费试用 | `g1.ios.30tb.ai.pro.m`（或连 `g1.ios.20tb.m.v2` 跨档映射） | `g1.ai.ultra.1month_eft.acq` | 优先 `Google` 搜索 App，清干净缓存的 `Google One` 或 `Gemini` 也可测 |
| Ultra 5x（20TB）首月 $0 免费试用 | `g1.ios.20tb.m.v2` | `g1.20tb.1month_eft.acq` | 优先 `Gemini` 或 `Google` 搜索 App，清干净缓存的 `Google One` 也可测 |
| Ultra 5x（20TB）前 3 个月 $9.99/月 | `g1.ios.20tb.m.v2` | `g1.20tb.3months_ip_90p.acq` | 优先 `Gemini` 或 `Google` 搜索 App（点头像 -> 升级 -> 选 20TB） |
| Ultra 20x（30TB）前 3 个月 $19.99/月 | `g1.ios.30tb.ai.pro.m` | `g1.ai.ultra.3months_ip_90p.acq` | 优先 `Google` 搜索 App 彩色 G 图标（选 30TB），清干净缓存的 `Google One` 也可测 |
| AI Pro（2TB）连续 12 个月一折测试候选 | `g1.ios.2tb.*` 系列 | `g1.2tb.ai.12months_ip_90p` | 优先 `Google` 搜索 App 或 `Gemini`（能否拉出 $1.99/月以收银台实显为准） |

先说白板新号首选的 `$0` 免费试用路线。只要你的谷歌号和美区 Apple ID 之前没用过同组首购优惠，把 `g1.ios.30tb.ai.pro.m` 换成 `g1.ai.ultra.1month_eft.acq` 就能拉起满血 `20x`（30TB）的首月 `$0` 苹果内购确认单；实测直接把 `20TB` 按钮对应的 `g1.ios.20tb.m.v2` 映射到 `g1.ai.ultra.1month_eft.acq`，点 `20TB` 卡片还能跨档拉起满血 `20x` 的首月 `$0` 试用。如果手里某个号拉不出 `20x` 的免费试用，也可以单独拿 `g1.20tb.1month_eft.acq` 测一下 `5x`（20TB）档的试用池，最终能不能免单同样看苹果收银台弹窗显示。

这里必须专门排一颗网上以讹传讹的大雷：千万别信什么"开完一个月试用再去系统订阅里点查看所有方案，能翻出隐藏的一年免费档顺延一年"的传言。真机实测下来根本没这回事：苹果 `StoreKit` 订阅组一旦激活了任一档位，哪怕你刚开出来的是 `1month_eft.acq` 首月 `$0` 试用，当前 Apple ID 在这个订阅组的首购入门优惠资格（`Introductory Offer`）当场就算用掉了。此时点进 iPhone 系统 `设置 -> Apple 账户 -> 订阅 -> 查看所有方案`（`See All Plans`），列表里根本看不见任何 `$0` 免费试用或者 `$9.99`、`$19.99` 的低价优惠，展示出来的清一色都是 `$99.99`/月、`$199.99`/月这类日常全价，盲目点切换只会按全价排期扣款！同样因为同一个订阅组只给一次新客优惠机会，准备冲 `$0` 试用的白板号千万别先挂付费一折模块（`3months_ip_90p.acq`）去试水，否则会把原本能弹出来的 `$0` 首购试用直接顶成付费一折。

再说拿不到免费资格的老号，退一步改开付费一折的选型经验。彩色 G 图标的 `Google` 搜索 App、`Gemini` App 和 `Google One` App 三个官方入口底层走的都是同一套双通道，但各自在 App Store Connect 登记的内购商品子集与本地缓存机制不同，没清干净缓存的 `Google One` 更容易回退弹出 `$199.99`/月原价。实测点 `5x`（20TB）前三个月 `$9.99`/月时，优先用 `Gemini` 或 `Google` 搜索 App（点右上角头像进升级页选卡片）；点满血 `20x`（30TB）前三个月 `$19.99`/月时，优先用彩色 G 图标的 `Google` 搜索 App，把缓存清干净的 `Google One` 也能测。要是在某一个 App 里点升级只弹原价，彻底杀掉进程换另外两个官方 App 重试，往往就能顺利刷出折扣价。至于尾巴上不带 `.acq` 后缀的 `g1.2tb.ai.12months_ip_90p`，它是社区测出的 `AI Pro` 2TB 连续 12 个月一折测试候选，不同账号能不能拉出 `$1.99`/月一律以弹出的 App Store 收银台实际显示为准。

## 0x02 动手前先把美区 Apple ID 支付方式整利索

既然扣款全走苹果美区 `StoreKit`，在配代理软件之前，最好先花五分钟把手头美区 Apple ID 的付款方式和账单地址收拾利索。很多人后面脚本一发就中，偏偏在双击侧边键那一下吃瘪，十有八九都是栽在绑卡细节上。

先把绑卡时的网络环境说死。不管是往 Apple ID 里绑卡、连 PayPal、充礼品卡还是双击侧边键结账，苹果自家的域名一律得走本地网络直连。还没挂本文代理模块之前，干脆先把手机上的 VPN 彻底关掉，裸连进 `设置 -> Apple 账户 -> 付款与配送` 把支付方式绑好；等后面开起代理刷价格时，各客户端规则里写的 `apple.com`、`itunes.apple.com`、`apps.apple.com` 强制 `DIRECT` 也会替你兜底。千万别挂着几百人共用的机房代理节点去改 Apple ID 付款资料，苹果对异地机房 IP 改卡极度敏感，点保存那一下就容易触发盗刷风控。

接着是账单寄送地址（`Billing Address`）里的消费税暗坑。美区账号的账单地址优先填在美国免税州：最顺手的是俄勒冈州 `Oregon`（比如城市填 `Portland`，邮编填 `97201`）或者特拉华州 `Delaware`（邮编 `19801`），另外蒙大拿 `Montana`、新罕布什尔 `New Hampshire` 以及阿拉斯加安克雷奇（`Alaska` `Anchorage`，邮编 `99501`，注意阿拉斯加部分市镇收地方税）也没有消费税。要是随手填到了加州、纽约这类有税州，买 `$19.99` 一折套餐时苹果收银台会按当地税率额外叠上 6% 到 10% 左右的消费税，结账金额直接跳成 `$21.xx`；你卡里或余额里要是刚好只留了 `$20`，当场就会因为差一两美元被拒付。但这里有个外币卡的例外细节得留神：如果你直绑的海外实体卡或虚拟卡发卡行开了严格的 `AVS`（地址与邮编核验），Apple ID 里填的街道和 `ZIP` 邮编就必须跟发卡行后台登记的账单地址保持一致；用支持自定义账单地址的合规虚拟卡时，直接把发卡后台和 Apple ID 两边的邮编统一设成免税州的 `97201` 或 `19801` 最省心。

至于美区 Apple ID 具体绑哪种付款方式，实测下来就三条路子，各自的脾气和门槛差别不小。

最主流也最省心的是绑美区 PayPal，既能拉出 `$0` 免费试用，也能正常扣付费一折。国内银行发行的普通双币或全币种 Visa、Mastercard 信用卡，直接往美区 App Store 硬塞基本都会因为发卡国不是美国被秒拒；常规绕法是先去注册一个美区 PayPal 账号，把自己的国内 Visa 或 Mastercard 外币卡绑进美区 PayPal 里，再回 iPhone 的 `付款与配送` 选择绑定这个美区 PayPal。用这条路子只要记住苹果美区 PayPal 默认走小额合并账单（`Batch Billing`）：双击侧边键显示订阅成功、Google 云端空间也到账之后，PayPal 账单往往要隔 1 到 72 小时才会真正把钱划走。这三天里千万别看着没扣款就手痒去解绑 PayPal 或锁卡，一旦苹果后台跑合并结算时扣了个空，这号立刻就会背上一笔历史欠费单。

第二条路是直绑支持美区的海外银行卡或合规虚拟 Visa、Mastercard，好处是能像上一篇那样靠卡内余额做物理防扣穿护栏。但很多新手会在 `$0` 试用上踩一个隐蔽的坑：往 Apple ID 绑卡的瞬间，苹果通常会发一笔 `$0` 到 `$1` 左右的临时预授权（验完卡自动撤销），所以哪怕你只是冲着首月 `$0` 免费试用去的，卡里也别留 `0.00` 空余额去碰运气，至少放 `$2` 到 `$3` 应付验卡预授权。要是准备开 Ultra 30TB 前三个月 `$19.99`/月的一折档（免税州地址下），往卡里放 `$22` 左右刚刚好：既够付首月加验卡，万一哪一步手滑没命中改写弹了 `$199.99` 原价，或者三个月后忙忘了退订，银行直接因余额不足拒付，比定十个闹钟都踏实。

实在既没有外币卡也搞不定美区 PayPal 的话，第三条路是去苹果美国官网（`apple.com`）买正规电子版 `Apple Gift Card` 发到自己邮箱充值账户余额，千万别去二手平台贪便宜买来路不明的低价黑卡，一旦沾上黑卡极易直接封禁商店权限。如果是开 `$9.99` 或 `$19.99` 的付费一折，在免税州地址下充够对应美元直接扣账户余额非常稳。但必须把丑话说在前面：纯礼品卡余额去碰 `$0` 免费试用很容易吃闭门羹。只要你的 Apple ID 名下只有礼品卡余额、完全没绑任何有效的辅助银行卡或 PayPal（或者余额根本不够覆盖试用期结束后的首个原价续费周期 `$99.99` / `$199.99`），点 `$0` 自动续期免费试用时，苹果几乎都会拦下来强制要求先补充付款方式，或者直接弹出购买审核框。所以奔着 `$0` 免费试用去的朋友，优先还是把美区 PayPal 或留了两三美元的外币卡绑上。

## 0x03 小火箭（Shadowrocket）与 Surge 配置：在现有配置上叠加 .sgmodule

支付环境垫好底，接下来配代理。新手拿小火箭配改写最容易踩的一个大坑，就是去导入别人给的"独立空白 `.conf` 配置文件"。在小火箭里，你平时生成并信任好的根证书私钥（`ca-p12` / `ca-passphrase`）连同所有机场节点，全都保存在当前正在用的 `default.conf` 肚子里。一旦导入并切到一个新建的空白 `.conf`，里面既没有外部节点，也没有刚才信任过的那把 CA 私钥，`one.google.com` 根本解不开密。稳妥的做法是始终保持选中你原有的 `default.conf`，在上面直接挂载 `.sgmodule` 叠加模块。

第一步先把 `default.conf` 的 HTTPS 解密证书开好（以前抓过包、信任过证书的朋友直接跳到下一步）。先把小火箭首页顶部的连接总开关关掉，切到底部"配置"页，点 `default.conf` 右侧的蓝色 `(i)` 图标，往下找到"HTTPS 解密"点进去，打开顶部的"HTTPS 解密"开关，依次点"证书 -> 生成新的 CA 证书 -> 安装证书 -> 允许"把描述文件下到手机里。接着打开 iPhone 系统 `设置`，点顶部的"已下载描述文件"（或者进 `设置 -> 通用 -> VPN 与设备管理`），输入锁屏密码把 `Shadowrocket` 描述文件装上。装完描述文件只走了一半，继续进系统 `设置 -> 通用 -> 关于本机`，一路滑到最底下点进"证书信任设置"，找到 `Shadowrocket` 根证书把右侧开关掰绿（要是点进来发现列表是空的，说明漏了前一步安装描述文件）。全部弄完切回小火箭，千万记得连续点两次右上角的保存对勾退回列表，别顺手往右滑屏幕返回，左滑返回不会保存刚才打开的 HTTPS 解密开关！

第二步挂改写模块。如果你只想用纯手机花一分钟跑通、不想单独放任何 `.js` 脚本文件，直接复制下面这段纯文本模块（文末压缩包 `Shadowrocket叠加模块(.sgmodule基于default.conf)/` 目录里也备好了现成的 `GAI-PureText-FreeTrial-免JS纯文本版.sgmodule` 与 `GAI-PureText-90Off-免JS纯文本版.sgmodule`）。它同时干了四件事：拦掉 `UDP 443` 逼流量退回常规 TCP、让苹果内购域名走直连、强迫原生接口返回未压缩数据、用内置的 `[Body Rewrite]` 把内嵌网页容器里的三档 SKU 一次换齐（下面演示付费一折的 `3months_ip_90p.acq`；白板新号冲 `$0` 免费试用时把两处 `3months_ip_90p.acq` 换成 `1month_eft.acq` 即可）：

```ini
#!name=Google AI Ultra SKU 免脚本叠加模块
#!desc=叠加于已有 default.conf，覆盖苹果内购直连、QUIC 阻断与三档 SKU 替换
#!system=ios

[Rule]
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP
DOMAIN-SUFFIX,itunes.apple.com,DIRECT
DOMAIN-SUFFIX,apps.apple.com,DIRECT
DOMAIN-SUFFIX,mzstatic.com,DIRECT
DOMAIN-SUFFIX,xp.apple.com,DIRECT
DOMAIN-SUFFIX,apple.com,DIRECT
DOMAIN-SUFFIX,icloud.com,DIRECT
DOMAIN-SUFFIX,one.google.com,PROXY
DOMAIN,subscriptionsmobile-pa.googleapis.com,PROXY

[Header Rewrite]
http-request ^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo header-replace Accept-Encoding identity
http-request ^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo header-replace grpc-accept-encoding identity

[Body Rewrite]
http-response ^https://one\.google\.com/(?:u/\d+/)?ai.*$ g1\.ios\.20tb\.m\.v2 g1.20tb.3months_ip_90p.acq
http-response ^https://one\.google\.com/(?:u/\d+/)?ai.*$ g1\.ios\.30tb\.ai\.pro\.m g1.ai.ultra.3months_ip_90p.acq
http-response ^https://one\.google\.com/(?:u/\d+/)?ai.*$ g1\.ios\.2tb\.[A-Za-z0-9._-]+ g1.2tb.ai.12months_ip_90p

[MITM]
enable = true
hostname = %APPEND% one.google.com, subscriptionsmobile-pa.googleapis.com
```

打开小火箭底部的"配置"，切到顶栏的"模块"，点右上角 `+` 号新建本地模块，把整段代码贴进去保存并确认前面打上了勾。要是遇到页面体积偏大超了 `[Body Rewrite]` 的默认缓冲上限，或者客户端某次升级页完全不走网页容器、只读原生 `GetDynamicStorefrontInfo` 的二进制 Protobuf 响应，就把文末提供的 [gai-sku-dual-channel.js](gai-sku-dual-channel.js) 存进系统"文件" App 的 `我的 iPhone -> Shadowrocket -> Scripts/` 目录（如果 `Shadowrocket` 根目录下还没有复数的 `Scripts` 文件夹，手动新建一个再放进去；也可以在自己电脑同目录起一行 `python3 -m http.server 8080` 填局域网地址，切勿乱引网上来路不明的第三方外链脚本，免得暴露 `one.google.com` 的登录 Cookie），再往上面的模块里补上这段 `[Script]` 声明，注意 `script-path=` 后面必须带上相对根目录的 `Scripts/` 前缀（文末压缩包里的标准 `.sgmodule` 已默认配好）：

```ini
[Script]
GAI_Web_StoreKit = type=http-response,requires-body=1,max-size=0,pattern=^https://one\.google\.com/(?:u/\d+/)?ai.*$,script-path=Scripts/gai-sku-dual-channel.js
GAI_Native_Storefront = type=http-response,requires-body=1,binary-body-mode=1,max-size=524288,pattern=^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo,script-path=Scripts/gai-sku-dual-channel.js
```

如果你主力用的是 `Surge`（无论是 iOS 版还是 macOS 桌面版），配置起来更省心，因为 `.sgmodule` 本来就是 Surge 的原生模块格式。iOS 版打开 Surge 点右上角进 `MitM`，点"生成新的 CA 证书"装好描述文件，再去系统 `设置 -> 通用 -> 关于本机 -> 证书信任设置` 掰绿根证书，回到 Surge 把 `MitM`、`Rewrite` 和 `Scripting` 三个总开关全打开（macOS 版直接在 `偏好设置 -> MitM` 里点生成并信任证书写入系统钥匙串就行）。接着在 `iCloud Drive`（或 `我的 iPhone`）底下的 `Surge/` 根目录里确认有复数的 `Scripts` 文件夹（没有就新建一个），把 `gai-sku-dual-channel.js` 放进 `Surge/Scripts/gai-sku-dual-channel.js`，进"模块 -> 安装新模块"导入上面这份带 `script-path=Scripts/gai-sku-dual-channel.js` 的 `.sgmodule` 勾选启用。出发前瞄一眼首页的出站模式，确认选在"规则判定"（小火箭那边叫全局路由选 `配置`），千万别停在"直接连接"上，选好美国节点打开开关就能去杀后台刷价格了。

## 0x04 Clash 全生态配置：分清 Stash 单机覆写与纯 Mihomo 局域网网关

群里问得最多的就是"我手机和电脑上只有 Clash，到底怎么配"。先把最容易翻车的两条铁律摊开讲清楚：第一，千万别去点网上那种裸 `clash://install-config?url=...` 的一键导入链接，那玩意儿导入的是一整份空白节点库，点下去直接把你正在用的机场订阅覆盖没了，连网都出不去；正经做法永远是在你现有的机场配置上挂载"覆写（`Override`）"，原有机场节点和策略组一根汗毛都不动。第二，看清你手里的客户端底子：`App Store` 上的 `Stash` 虽然兼容 Clash 配置文件，但它自己内置了完整的 `http.mitm` 和 `http.script` 引擎，光靠一台 iPhone 就能独立改完双通道；而 `Clash Mi`、`FlClash`、`Clash Verge`、`Karing` 底层跑的是纯 `Mihomo`（原 `Clash.Meta`）路由内核，它只管三四层流量分发，压根没有拆开 HTTPS 改响应体的本地脚本引擎，必须把那两个谷歌域名分流给同一 Wi-Fi 下电脑跑的改写网关。

### 1. iOS Stash（免电脑，单文件 .stoverride 内联脚本独立生效）

手里有 `Stash` 的朋友不需要开电脑。先在 Stash 底部点"工具 -> HTTPS 解密"，生成根证书、安装描述文件，照例去系统 `设置 -> 通用 -> 关于本机 -> 证书信任设置` 把 Stash 根证书掰绿，再回 Stash 确认"HTTPS 解密"和"脚本"开关都已开启。

Stash 官方的 `.stoverride` 覆写规范有个特别舒服的设计：顶层的 `rules:` 会自动置顶插入你当前正在用的机场配置里，不会冲掉任何节点；同时底下的 `script-providers:` 支持直接用 `payload: |` 把整段 JavaScript 代码内联写进同一个文件里，连外部 `.js` 都不用单独拷。你可以直接从文末压缩包 `Clash与Stash规则库(叠加至当前配置保留原节点)/` 里选好对应档位的 `.stoverride` AirDrop 到手机导入，也可以直接复制下面这段自带完整双通道解析逻辑的 `.stoverride` 保存启用（把内联脚本第一行的 `MODE` 从 `"eft"` 改成 `"90off"` 即可切到老号付费一折）：

```yaml
name: "Google AI Ultra SKU 双通道内联覆写"
desc: "叠加于当前机场配置生效，保留全部原节点，内联脚本免电脑独立运行"
category: GoogleAI

rules:
  - AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN-SUFFIX,one.google.com)),REJECT
  - AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN,subscriptionsmobile-pa.googleapis.com)),REJECT
  - DOMAIN-SUFFIX,itunes.apple.com,DIRECT
  - DOMAIN-SUFFIX,apps.apple.com,DIRECT
  - DOMAIN-SUFFIX,mzstatic.com,DIRECT
  - DOMAIN-SUFFIX,xp.apple.com,DIRECT
  - DOMAIN-SUFFIX,apple.com,DIRECT
  - DOMAIN-SUFFIX,icloud.com,DIRECT

http:
  mitm:
    - "one.google.com"
    - "*.one.google.com"
    - "subscriptionsmobile-pa.googleapis.com"
  header-rewrite:
    - ^https:\/\/subscriptionsmobile\-pa\.googleapis\.com\/\$rpc\/.*GetDynamicStorefrontInfo request-replace Accept-Encoding identity
    - ^https:\/\/subscriptionsmobile\-pa\.googleapis\.com\/\$rpc\/.*GetDynamicStorefrontInfo request-replace grpc-accept-encoding identity
  script:
    - match: ^https:\/\/subscriptionsmobile\-pa\.googleapis\.com\/\$rpc\/.*GetDynamicStorefrontInfo
      name: gai_sku_req
      type: request
      timeout: 10
    - match: ^https:\/\/one\.google\.com\/(?:u\/\d+\/)?ai.*$
      name: gai_sku_resp
      type: response
      require-body: true
      max-size: 1048576
      timeout: 15
    - match: ^https:\/\/subscriptionsmobile\-pa\.googleapis\.com\/\$rpc\/.*GetDynamicStorefrontInfo
      name: gai_sku_resp
      type: response
      require-body: true
      binary-mode: true
      max-size: 524288
      timeout: 15

script-providers:
  gai_sku_req:
    interval: 86400
    payload: |
      (function() {
        const h = Object.assign({}, ($request && $request.headers) || {});
        for (const k of Object.keys(h)) {
          const low = k.toLowerCase();
          if (low === "accept-encoding" || low === "grpc-accept-encoding") delete h[k];
        }
        h["Accept-Encoding"] = "identity";
        h["grpc-accept-encoding"] = "identity";
        $done({ headers: h });
      })();
  gai_sku_resp:
    interval: 86400
    payload: |
      (function() {
        const MODE = "eft"; // "eft": 首月$0免费试用 | "90off": 老号付费一折
        const PAIRS = MODE === "90off"
          ? [["g1.ios.20tb.m.v2", "g1.20tb.3months_ip_90p.acq"], ["g1.ios.30tb.ai.pro.m", "g1.ai.ultra.3months_ip_90p.acq"]]
          : [["g1.ios.20tb.m.v2", "g1.20tb.1month_eft.acq"], ["g1.ios.30tb.ai.pro.m", "g1.ai.ultra.1month_eft.acq"]];
        const toB = s => Uint8Array.from(s, c => c.charCodeAt(0) & 0xff);
        const encV = v => { const o = []; while (true) { const b = v & 0x7f; v >>>= 7; if (v) o.push(b | 0x80); else { o.push(b); return new Uint8Array(o); } } };
        const eqB = (b, o, l, p) => { if (l !== p.length) return false; for (let i = 0; i < l; i++) if (b[o + i] !== p[i]) return false; return true; };
        const hasB = (b, o, l, p) => { if (l < p.length) return false; for (let i = o; i <= o + l - p.length; i++) { let ok = true; for (let j = 0; j < p.length; j++) if (b[i + j] !== p[j]) { ok = false; break; } if (ok) return true; } return false; };
        function skipGroup(b, p, e, ef, d) {
          if (d <= 0) return -1;
          while (p < e) {
            let tg = 0, sh = 0;
            while (p < e) { const c = b[p++]; tg |= (c & 0x7f) << sh; if (!(c & 0x80)) break; sh += 7; if (sh > 35) return -1; }
            const fn = tg >>> 3, wt = tg & 7;
            if (fn <= 0) return -1;
            if (wt === 4) return fn === ef ? p : -1;
            if (wt === 0) { while (p < e && (b[p++] & 0x80)) {} }
            else if (wt === 1) { if (p + 8 > e) return -1; p += 8; }
            else if (wt === 5) { if (p + 4 > e) return -1; p += 4; }
            else if (wt === 2) {
              let ln = 0, ls = 0;
              while (p < e) { const c = b[p++]; ln |= (c & 0x7f) << ls; if (!(c & 0x80)) break; ls += 7; if (ls > 28) return -1; }
              if (ln < 0 || p + ln > e) return -1;
              p += ln;
            } else if (wt === 3) {
              p = skipGroup(b, p, e, fn, d - 1);
              if (p < 0) return -1;
            } else return -1;
          }
          return -1;
        }
        function rwPb(b, s, e, sb, db, d) {
          if (d <= 0 || !hasB(b, s, e - s, sb)) return null;
          const cs = []; let p = s, h = 0;
          while (p < e) {
            const ts = p; let tg = 0, sh = 0;
            while (p < e) { const c = b[p++]; tg |= (c & 0x7f) << sh; if (!(c & 0x80)) break; sh += 7; if (sh > 35) return null; }
            const fn = tg >>> 3, wt = tg & 7;
            if (fn <= 0) return null;
            if (wt === 3) {
              const ge = skipGroup(b, p, e, fn, d - 1);
              if (ge < 0) return null;
              cs.push(b.subarray(ts, ge));
              p = ge;
              continue;
            }
            cs.push(b.subarray(ts, p));
            if (wt === 0) { const vs = p; while (p < e && (b[p++] & 0x80)) {} cs.push(b.subarray(vs, p)); }
            else if (wt === 1) { if (p + 8 > e) return null; cs.push(b.subarray(p, p + 8)); p += 8; }
            else if (wt === 5) { if (p + 4 > e) return null; cs.push(b.subarray(p, p + 4)); p += 4; }
            else if (wt === 2) {
              let ln = 0, ls = 0;
              while (p < e) { const c = b[p++]; ln |= (c & 0x7f) << ls; if (!(c & 0x80)) break; ls += 7; if (ls > 28) return null; }
              if (ln < 0 || p + ln > e) return null;
              const ss = p; p += ln; let rep = null;
              if (eqB(b, ss, ln, sb)) { rep = db; h++; }
              else if (d > 1 && hasB(b, ss, ln, sb)) { const n = rwPb(b, ss, ss + ln, sb, db, d - 1); if (n) { rep = n.bytes; h += n.hits; } }
              const pl = rep || b.subarray(ss, ss + ln);
              cs.push(encV(pl.length), pl);
            } else return null;
          }
          if (p !== e || !h) return null;
          const out = new Uint8Array(cs.reduce((a, c) => a + c.length, 0));
          let o = 0; for (const c of cs) { out.set(c, o); o += c.length; }
          return { bytes: out, hits: h };
        }
        function rwFrame(b, sb, db) {
          if (b.length >= 5) {
            let fp = 0, ok = true, fh = 0; const fc = [];
            while (fp < b.length) {
              if (fp + 5 > b.length) { ok = false; break; }
              const flg = b[fp];
              if (flg !== 0x00 && flg !== 0x01 && flg !== 0x80 && flg !== 0x81) { ok = false; break; }
              const flen = ((b[fp + 1] << 24) >>> 0) + (b[fp + 2] << 16) + (b[fp + 3] << 8) + b[fp + 4];
              if (flen > 16777216 || fp + 5 + flen > b.length) { ok = false; break; }
              let pl = b.subarray(fp + 5, fp + 5 + flen);
              if (flg === 0x00 && hasB(b, fp + 5, flen, sb)) { const r = rwPb(b, fp + 5, fp + 5 + flen, sb, db, 20); if (r) { pl = r.bytes; fh += r.hits; } }
              const nl = pl.length;
              const hd = new Uint8Array([flg, (nl >>> 24) & 0xff, (nl >>> 16) & 0xff, (nl >>> 8) & 0xff, nl & 0xff]);
              fc.push(hd, pl); fp += 5 + flen;
            }
            if (ok && fp === b.length && fh > 0) {
              const out = new Uint8Array(fc.reduce((a, c) => a + c.length, 0));
              let o = 0; for (const c of fc) { out.set(c, o); o += c.length; }
              return { bytes: out, hits: fh };
            }
          }
          return rwPb(b, 0, b.length, sb, db, 20);
        }
        let raw = $response && $response.body;
        if (raw instanceof ArrayBuffer) raw = new Uint8Array(raw);
        if (raw instanceof Uint8Array) {
          let cur = raw, hit = false;
          for (const [s, d] of PAIRS) { const r = rwFrame(cur, toB(s), toB(d)); if (r && r.hits) { cur = r.bytes; hit = true; } }
          $done(hit ? { body: cur } : {});
        } else if (typeof raw === "string" && raw.length > 0) {
          const obs = raw.match(/g1\.[a-z0-9._]{2,60}acq/g) || [];
          const sm = Object.fromEntries(PAIRS);
          const fb = MODE === "90off"
            ? {}
            : { "g1.20tb.1month_eft.acq": "g1.20tb.3months_ip_90p.acq", "g1.ai.ultra.1month_eft.acq": "g1.ai.ultra.3months_ip_90p.acq" };
          let hits = 0;
          const txt = raw.replace(/(^|[^A-Za-z0-9._@%-])(g1\.[A-Za-z0-9._-]+)(?=$|[^A-Za-z0-9._-])/g, (m, pre, id) => {
            if (id.indexOf("g1.ios.2tb.") === 0 && id.length > 11) { hits++; return pre + "g1.2tb.ai.12months_ip_90p"; }
            if (Object.prototype.hasOwnProperty.call(sm, id)) {
              let t = sm[id];
              if (obs.indexOf(t) === -1 && fb[t] && obs.indexOf(fb[t]) !== -1) t = fb[t];
              hits++; return pre + t;
            }
            return m;
          });
          $done(hits ? { body: txt } : {});
        } else $done({});
      })();
```

### 2. Clash Mi / FlClash / Clash Verge / Karing（覆写叠加电脑局域网网关）

用纯 `Mihomo` 系客户端的朋友，思路是"各司其职"：你手机上成千上万个日常连接照旧走你自己的机场节点，唯独把 `one.google.com` 和 `subscriptionsmobile-pa.googleapis.com` 这两个域名拐个弯递给同一 Wi-Fi 下电脑跑的本地改写网关，改完包再由电脑的美国代理出口发出去。

先在连着同一个路由器的电脑上把网关跑起来。如果你电脑上已经在跑配套桌面控制台的"iOS 免越狱"页，直接拿手机扫界面上的二维码，在 Safari 里点下载"域限定 CA 根证书"（证书绑了 Name Constraints，只对这两个谷歌域名有效），装完描述文件去系统 `关于本机 -> 证书信任设置` 掰绿即可。要是手头没装桌面端，直接下载文末的 [gai_mitm_gateway.py](gai_mitm_gateway.py)（压缩包的 `Clash本地网关脚本(纯Mihomo内核专用)/` 目录里也有一份），用开源的 `mitmproxy` 在电脑终端绑死局域网 IP 起一个临时网关（下面假设你电脑局域网 IP 是 `192.168.1.100`，电脑本机 Clash 美国代理端口是 `7897`，需要开老号付费一折时在命令最前面加个 `GAI_MODE=tri_smart`）：

```bash
pip install mitmproxy
mitmdump --listen-host 192.168.1.100 -p 18910 \
  --proxyauth gtool:change-me-token \
  --mode upstream:http://127.0.0.1:7897 \
  -s gai_mitm_gateway.py
```

首次用 `mitmdump` 的话，先在手机系统 Wi-Fi 里临时配一下手动代理连过去访问 `http://mitm.it` 把根证书装上并进 `证书信任设置` 掰绿，装完就把系统 Wi-Fi 手动代理关回自动。接着打开手机上的 `Clash Mi`、`FlClash`（或桌面端的 `Clash Verge`），进入 `配置 (Profiles) -> 覆写 (Override)` 新建一条 YAML 覆写规则，把里面的 `192.168.1.100` 和 `change-me-token` 换成你刚才设的电脑局域网 IP 与口令（若直接导入压缩包里的覆写模板，则是替换 `<YOUR_COMPUTER_LAN_IP>` 与 `<YOUR_STUDIO_LAN_TOKEN>`）：

```yaml
+proxies:
  - name: "GTool-iOS-Rewrite"
    type: http
    server: 192.168.1.100
    port: 18910
    username: "gtool"
    password: "change-me-token"

+rules:
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN-SUFFIX,one.google.com)),REJECT
  - AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN,subscriptionsmobile-pa.googleapis.com)),REJECT
  - DOMAIN-SUFFIX,one.google.com,GTool-iOS-Rewrite
  - DOMAIN,subscriptionsmobile-pa.googleapis.com,GTool-iOS-Rewrite
  - DOMAIN-SUFFIX,itunes.apple.com,DIRECT
  - DOMAIN-SUFFIX,apps.apple.com,DIRECT
  - DOMAIN-SUFFIX,mzstatic.com,DIRECT
  - DOMAIN-SUFFIX,xp.apple.com,DIRECT
  - DOMAIN-SUFFIX,apple.com,DIRECT
  - DOMAIN-SUFFIX,icloud.com,DIRECT
```

盯一眼上面最顶头那三条 `IP-CIDR,...,DIRECT,no-resolve`，千万别嫌啰嗦手欠删掉：手机开着 TUN 虚拟网卡模式时，如果不把内网段置顶直连，发往 `192.168.1.100:18910` 的包会被 TUN 自己抓回来塞进代理隧道打死循环，最后全卡超时。另外有些版本的客户端覆写面板更习惯填 JavaScript 扩展脚本，直接在"覆写 -> JavaScript 脚本"里贴下面这段 `main(config)` 函数，效果一模一样，还会顺手帮你把嗅探域名覆写打开：

```javascript
function main(config) {
  if (!config || typeof config !== "object") return config;
  if (config.sniffer && typeof config.sniffer === "object") {
    config.sniffer["override-destination"] = true;
  }
  const gwProxy = {
    name: "GTool-iOS-Rewrite",
    type: "http",
    server: "192.168.1.100",
    port: 18910,
    username: "gtool",
    password: "change-me-token"
  };
  const headRules = [
    "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
    "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
    "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
    "AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN-SUFFIX,one.google.com)),REJECT",
    "AND,((NETWORK,UDP),(DST-PORT,443),(DOMAIN,subscriptionsmobile-pa.googleapis.com)),REJECT",
    "DOMAIN-SUFFIX,one.google.com,GTool-iOS-Rewrite",
    "DOMAIN,subscriptionsmobile-pa.googleapis.com,GTool-iOS-Rewrite",
    "DOMAIN-SUFFIX,itunes.apple.com,DIRECT",
    "DOMAIN-SUFFIX,apps.apple.com,DIRECT",
    "DOMAIN-SUFFIX,mzstatic.com,DIRECT",
    "DOMAIN-SUFFIX,xp.apple.com,DIRECT",
    "DOMAIN-SUFFIX,apple.com,DIRECT",
    "DOMAIN-SUFFIX,icloud.com,DIRECT"
  ];
  const oldProxies = Array.isArray(config.proxies)
    ? config.proxies.filter(p => p && p.name !== "GTool-iOS-Rewrite")
    : [];
  config.proxies = [gwProxy, ...oldProxies];
  const headSet = new Set(headRules);
  const oldRules = Array.isArray(config.rules)
    ? config.rules.filter(r => !headSet.has(r))
    : [];
  config.rules = [...headRules, ...oldRules];
  return config;
}
```

至于用 `Karing` 的朋友，除了直接导入合入节点的配置，也可以在自定义分流组里直接挂载文末压缩包 `Clash与Stash规则库(叠加至当前配置保留原节点)/RuleSet远程与本地分流规则库/` 底下的 `gai_rewrite.json`（指给局域网 HTTP 网关节点）和 `apple_direct.json`（指给 `DIRECT`）。连上 VPN 后第一次触发局域网通信时，iOS 系统会弹一个"是否允许查找并连接到本地网络上的设备"权限框，记得点"允许"。接着教你一个三秒钟验通不通的办法：不用先去刷谷歌 App，直接打开手机 Safari 访问 `https://one.google.com/g1-sku-report`（这条是 `gai_mitm_gateway.py` 本地拦截生成的自检探针路由），只要页面干净利落地吐出一段包含 `"ok": true` 和命中计数的 JSON，就说明分流、局域网网关和证书信任三条线全齐活了。

## 0x05 Loon、Quantumult X（圈 X）与 Egern 配置，以及 Protobuf 为什么不能硬替

剩下三款 iOS 进阶玩家常用的工具全都自带完整的本地脚本引擎，只要把文末的 [gai-sku-dual-channel.js](gai-sku-dual-channel.js) 下载放进各家对应的本地脚本位置（打开脚本第 6 行的 `MODE_KIND` 常量就能在默认的免费试用模式 `"tri_eft_smart"`、老号付费一折模式 `"tri_smart"` 和全按钮直通 20x 免费模式 `"eft_20x_direct"` 之间切换），再把对应的规则片段挂上去就行。注意这三家的本地脚本目录命名各有讲究，别放串了。

用 `Loon` 的话，先在 `配置 -> MITM` 里生成并安装根证书，去系统 `关于本机 -> 证书信任设置` 掰绿，把 MITM、复写和脚本总开关都打开。重点看准文件夹名字：Loon 本地脚本目录是单数的 `Loon/Script/`（尾巴没有 `s`，跟小火箭和 Surge 的 `Scripts` 不一样！），把 `gai-sku-dual-channel.js` 放进系统"文件" App 的 `我的 iPhone`（或 `iCloud Drive`）底下的 `Loon/Script/` 目录后，新建或导入下面这份 `.plugin` 插件即可直接用裸文件名 `script-path=gai-sku-dual-channel.js` 引用。另外 Loon 拦 QUIC 的原生规则写法是 `PROTOCOL,QUIC,REJECT`（开启期间会全局拦掉 QUIC 强制走 TCP，办完订阅关掉插件就能恢复），原生接口那一行脚本也必须带上 `binary-body-mode=true`：

```ini
#!name = Google AI Ultra SKU 双通道改写插件
#!desc = 覆盖苹果内购直连、QUIC 拦截与网页/Protobuf 双通道 SKU 替换
#!system = ios

[Rule]
PROTOCOL,QUIC,REJECT
DOMAIN-SUFFIX,itunes.apple.com,DIRECT
DOMAIN-SUFFIX,apps.apple.com,DIRECT
DOMAIN-SUFFIX,mzstatic.com,DIRECT
DOMAIN-SUFFIX,xp.apple.com,DIRECT
DOMAIN-SUFFIX,apple.com,DIRECT
DOMAIN-SUFFIX,icloud.com,DIRECT
DOMAIN-SUFFIX,one.google.com,PROXY
DOMAIN,subscriptionsmobile-pa.googleapis.com,PROXY

[Rewrite]
^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo header-replace Accept-Encoding identity
^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo header-replace grpc-accept-encoding identity

[Script]
http-response ^https://one\.google\.com/(?:u/\d+/)?ai.*$ script-path=gai-sku-dual-channel.js, requires-body=true, tag=GAI_Web_StoreKit
http-response ^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo script-path=gai-sku-dual-channel.js, requires-body=true, binary-body-mode=true, tag=GAI_Native_Storefront

[MITM]
hostname = one.google.com, subscriptionsmobile-pa.googleapis.com
```

用 `Quantumult X`（圈 X）的朋友有两个专属细节千万留神。第一，圈 X 的 `[filter_local]` 分流段不支持按传输层端口拦 `UDP 443`，要防 HTTP/3 溜号得编辑主配置文件的 `[general]` 段落，往里面加一行 `udp_drop_list = 443`；第二，Surge、Loon、Stash 在二进制模式下都是把 `Uint8Array` 塞进 `$response.body` 里传给脚本，唯独圈 X 是把 `ArrayBuffer` 放在 `$response.bodyBytes` 字段里，改完还得原样包成 `$done({ bodyBytes: ... })` 交回去（好在 `gai-sku-dual-channel.js` 已经专门写了 `isQxBytes` 分支兼容好了）。点圈 X 右下角小风车生成配置好根证书并去系统信任后，把 `gai-sku-dual-channel.js` 放进 `Quantumult X/` 根目录或 `Quantumult X/Scripts/` 子目录（存文件时盯一眼后缀，别被系统或文本编辑器偷偷补成 `.js.txt`），挂载下面这段 `.snippet` 片段即可：

```ini
; 别忘了在主配置 [general] 段加上 udp_drop_list = 443 阻断 QUIC
[filter_local]
host-suffix, itunes.apple.com, direct
host-suffix, apps.apple.com, direct
host-suffix, mzstatic.com, direct
host-suffix, xp.apple.com, direct
host-suffix, apple.com, direct
host-suffix, icloud.com, direct
host-suffix, one.google.com, proxy
host, subscriptionsmobile-pa.googleapis.com, proxy

[rewrite_local]
^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo url request-header (\r\n)(?i)Accept-Encoding:\s*[^\r\n]+(\r\n) request-header $1Accept-Encoding: identity$2
^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo url request-header (\r\n)(?i)grpc-accept-encoding:\s*[^\r\n]+(\r\n) request-header $1grpc-accept-encoding: identity$2
^https://one\.google\.com/(?:u/\d+/)?ai.*$ url script-response-body gai-sku-dual-channel.js
^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo url script-response-body gai-sku-dual-channel.js

[mitm]
hostname = one.google.com, subscriptionsmobile-pa.googleapis.com
```

如果你用的是这两年挺火的模块化客户端 `Egern`，同样先在设置里开好 MITM 证书并完成系统完全信任，在主配置里确认开了 `block_quic: true`。放脚本有个很省事的办法：直接打开 Egern 点底部 `工具 -> 脚本 -> +`，选本地位置新建一个名叫 `gai-sku-dual-channel.js` 的脚本把代码贴进去保存，之后在模块里写 `script_url: gai-sku-dual-channel.js` 就能直接调到。新建 YAML 模块时，核心是在原生接口那条 `http_response` 底下把 `body_required: true` 和 `binary_body: true` 一块儿加上：

```yaml
# 使用前请确认已在 Egern 主配置开启 block_quic: true
name: "Google AI Ultra SKU 双通道模块"
description: "覆盖苹果内购直连与网页/Protobuf 双通道 SKU 替换"
domain_suffix_set:
  - match: itunes.apple.com
    policy: DIRECT
  - match: apps.apple.com
    policy: DIRECT
  - match: mzstatic.com
    policy: DIRECT
  - match: xp.apple.com
    policy: DIRECT
  - match: apple.com
    policy: DIRECT
  - match: icloud.com
    policy: DIRECT
header_rewrites:
  - http_request:
      match: "^https://subscriptionsmobile\\-pa\\.googleapis\\.com/\\$rpc/.*GetDynamicStorefrontInfo"
      name: Accept-Encoding
      value: identity
      type: replace
  - http_request:
      match: "^https://subscriptionsmobile\\-pa\\.googleapis\\.com/\\$rpc/.*GetDynamicStorefrontInfo"
      name: grpc-accept-encoding
      value: identity
      type: replace
scriptings:
  - http_response:
      name: "GAI-Web-StoreKit"
      match: "^https://one\\.google\\.com/(?:u/\\d+/)?ai.*$"
      script_url: gai-sku-dual-channel.js
      body_required: true
  - http_response:
      name: "GAI-PB-Storefront"
      match: "^https://subscriptionsmobile\\-pa\\.googleapis\\.com/\\$rpc/.*GetDynamicStorefrontInfo"
      script_url: gai-sku-dual-channel.js
      body_required: true
      binary_body: true
mitm:
  hostnames:
    - one.google.com
    - subscriptionsmobile-pa.googleapis.com
```

顺嘴聊两句为什么第二条通道非得写二进制解析代码不可。`GetDynamicStorefrontInfo` 吐回来的是标准的 gRPC 数据帧：最外层顶着 5 个字节的帧头（1 字节帧标志位加上 4 字节大端序负载长度），里面套着好几层 Protobuf 的 `wire type 2` 变长消息，每一个字符串和外层父消息前面都顶着一个 `varint` 字节长度前缀。你把 16 字节的 `g1.ios.20tb.m.v2` 换成 26 字节的 `g1.20tb.3months_ip_90p.acq`，平白多出来 10 个字节；要是直接拿二进制查找替换硬塞进去，从最里层的字符串字段到外层所有嵌套子消息的 `varint` 长度、再到最外头那 4 字节大端帧长全都会错位，客户端反序列化当场崩掉，升级页直接刷出一片空白。所以先在请求头里强塞 `identity` 把 gzip 压缩剥掉，再由脚本兼容跳过 `wire type 3` 分组并递归遍历每一层 Protobuf 标签，由内向外逐层重算 `varint` 长度、更新 5 字节帧头，客户端吃进去才跟原生下发的一模一样。

## 0x06 实测排坑、撞上 24 到 72 小时购买审核怎么破，以及模块包下载

规则挂好连上美国节点之后，第一件必做的动作是把手机后台开着的 `Google`、`Gemini`、`Google One` 彻底往上划掉杀干净进程再重进。客户端会把上一次拉回来的原价方案列表缓存在内存里，不杀后台重进的话点多少次都是旧数据。永远以双击侧边键前弹出来的那张苹果 `StoreKit` 收银台明细作为唯一准绳，看到 `1 month free trial`（`$0.00`）或者前三个月 `$9.99/month`、`$19.99/month` 的字样再按下去。

真机实测时有两类苹果侧弹窗最容易让人误以为"改写失效了"，其实跟代理脚本半毛钱关系没有。

第一类也是最多人撞上的拦路虎，是双击侧边键扫完面容之后，屏幕正中间蹦出一句 `"Your Purchase Could Not Be Completed"`（常带着 `"Submit a request to Apple Support for review"` 按钮，中文提示"购买未完成，提交申请至 Apple 支持以供审核"）。能走到双击侧边键这一步，说明前面的 SKU 改写和 `StoreKit` 商店查价早就跑通了，卡住你的纯粹是苹果的自动交易风控：一个刚注册没多久、刚绑完卡或者刚切过网络环境的美区 Apple ID，冷不丁发起一笔原价标签高达 `$99.99` 或 `$199.99`/月的订阅，很容易被苹果风控模型先拦下来审一道。

碰到这个弹窗，先点弹窗上的提交审核按钮，或者用浏览器打开 `https://getsupport.apple.com/`，依次选 `Billing & Subscriptions -> Unable to purchase -> Chat` 找在线客服，把下面这段英文发过去请对方帮忙登记内购复核：

```text
Hi, I tried to purchase a Google One subscription via In-App Purchase on my iPhone, and received "Your Purchase Could Not Be Completed - Submit a request to Apple Support for review". Could you please help review and unblock In-App Purchases on my Apple Account? Thank you.
```

但这里一定要把预期摆正，千万别信网上说的"找客服点一下就能百分百秒过"。除了极少数非常轻微的首单拦截在登记后能较快放行，绝大多数情况下，苹果自动风控系统都会直接给这个账号挂上 `24` 到 `48` 小时、常见甚至长达 `72` 小时的安全审核与冷却等待期；哪怕你当场要求转接苹果高级顾问（`Senior Advisor`），对方后台也没有强行跳过自动冷却计时器的秒解按钮，最多只能帮你提一张加速审核工单（`Expedite Case`）。

一旦客服或系统提示需要等待 24 到 72 小时审核，接下来这三条实操规矩直接决定你是顺利解封还是越陷越深。第一条铁律是严守静默期：这三天里绝对不要手痒去重复连点购买，也不要反复解绑重绑卡或者挂着不同代理 IP 来回退出登录这个 Apple ID。苹果风控的冷却计时器是重置累加机制，中途每失败重试一次，倒计时就会重新拉满回 72 小时。

第二条是急着用模型、不想干等三天时的双轨绕法。要是你手里恰好有以前注册过一阵子、平时正常下过几个免费 App 的老美区 Apple ID，完全可以"只换商店号、不动主账号"破局：iOS 的系统主 `iCloud` 账号和管内购的商店账号本来就是分家管理的，直接进 `设置 -> Apple 账户 -> 媒体与购买项目 -> 退出登录`，只把商店登录换成那个老美区 Apple ID（手机主 `iCloud` 别动，`Google` 或 `Gemini` App 里登录的目标谷歌号也别动），上划杀掉谷歌 App 后台重新点进升级页，通常当场就能顺利付通；至于前面那个卡在审核期的新 Apple ID，老老实实静置满 72 小时等邮件解封后留作备用就行。

第三条是满 72 小时后的兜底边界。万一真的一动不动静置超过了 72 小时还是买不了，再去 `getsupport.apple.com` 找在线客服明确说明已经等满 72 小时（`I have waited more than 72 hours after submitting the review request`），这时请对方转接 `Senior Advisor` 人工介入跟进才真正管用。但要是因为误充了来路不明的低价礼品卡直接跳出 `"Your Apple ID has been disabled in the App Store and iTunes"`（商店账户被禁用），就别拿跨区资料去硬刚人工申诉了，果断止损换干净新号。

第二类常见报错是弹窗提示 `"Your payment method was declined"`。碰到这个先去 iPhone 系统 `设置 -> Apple 账户 -> 媒体与购买项目 -> 查看账户 -> 购买记录` 里翻一圈，看看是不是以前某个订阅续费扣款失败（比如前面提过的美区 PayPal `Batch Billing` 延迟结算时卡里没钱）留下了一笔标红的未结清历史欠单，有的话先把旧账结清才能开新单；要是购买记录干干净净，回头核对一眼 `0x02` 讲过的两件事：账单地址是不是忘改免税州导致税后跳到了 `$21.xx` 超出卡内限额，或者冲 `$0` 试用时卡里是不是留了 `0.00` 空余额没扛住苹果那 `$1` 预授权验卡。

顺便再提一嘴外部直链的风控雷区：网上流传的那些 `tokenized.play.google.com/eacquire/multiline?ear=...` 免抓包网页直链，主力号千万别图省事乱点。把里面的 `ear` 参数做一次 Base64 解码就能看见，里面原封不动封存着最初抓包那台电脑的 BotGuard 设备指纹、浏览器 UA 和时区。几百个人拿不同账号去点同一条死链接，在谷歌风控眼里就是共用同一份静态环境快照的异常关联请求，一旦碰上风控复核很容易被收回试用资格打回免费 15GB。在自己手机上用代理模块实时替换 SKU，每次 `StoreKit` 结账会话都由你自己的真机当场生成，干净得多。

订阅顺利到账之后记得收好两个尾巴。第一，回各自的代理软件把改写规则关掉，恢复日常刷网页的 HTTP/3 QUIC 速度：小火箭进"配置 -> 模块"取消勾选，`Surge` 进"模块"取消启用，`Stash` 在当前配置下取消勾选对应的 `.stoverride`，`Clash Mi` / `FlClash` / `Clash Verge` 进"配置 -> 覆写"关掉条目并按 `Ctrl+C` 停掉电脑终端上的 `mitmdump`，`Loon` 进"插件"关掉开关，圈 X 取消勾选重写片段并把 `[general]` 里的 `udp_drop_list = 443` 删掉，`Egern` 进模块页关闭模块并还原 `block_quic`。第二，免费试用的第 30 天、一折特惠的第 90 天一到就会按 `$99.99` 或 `$199.99`/月原价自动续费，记得到期前去 iPhone 系统 `设置 -> Apple 账户 -> 订阅` 手动点掉续订。

上面提到的所有客户端现成配置文件（含小火箭与 Surge 的双通道及免 `.js` 纯文本 `.sgmodule`、已内联完整脚本的 Stash `.stoverride`、纯 Mihomo 的 YAML / JS 覆写与 `mitmdump` 网关脚本、Karing `.json` 规则集、Loon `.plugin`、圈 X `.snippet`、Egern 模块，分免费试用版与老号付费一折版）已经全部打包脱敏好放在这里，按需自取：

- 全客户端一键模块压缩包：[下载 Google AI iOS 全客户端免越狱模块包（ZIP）](google-ai-ios-modules.zip)
- 独立双通道改写脚本（供手动放进 `Scripts` 或 `Script` 目录参考）：[下载通用双通道 Protobuf 脚本（gai-sku-dual-channel.js）](gai-sku-dual-channel.js)
- 纯 Mihomo 客户端配套电脑端网关脚本：[下载 mitmdump 双通道网关脚本（gai_mitm_gateway.py）](gai_mitm_gateway.py)

---

*文里略去了具体账号和卡信息。*
