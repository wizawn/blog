---
title: "iOS 免越狱改写 SKU 拿 Google AI Ultra 免费试用与一折价：小火箭、Clash、Stash、Surge、圈 X、Loon 全客户端实录"
date: 2026-11-24T22:00:00+08:00
lastmod: 2026-11-25T12:20:00+08:00
description: "在 iPhone 上免越狱拦截网页与原生 Protobuf 双通道，把默认下发的 iOS 原价 SKU 替换成隐藏促销编号，拉出 Google AI Ultra 首月 $0 免费试用或 $9.99 / $19.99 一折价，附 Shadowrocket、Clash 全系（Stash / Clash Mi / FlClash / Clash Verge / Karing）、Surge、Loon、Quantumult X、Egern 完整配置。"
categories: ["安全研究", "技术分析"]
tags: ["Google AI Ultra", "Google One", "Shadowrocket", "小火箭", "Clash", "Stash", "Surge", "Quantumult X", "Loon", "SKU 改写", "iOS"]
draft: false
weight: 10
---

## 0x00 上回塞 Frida 太重，这回把 iOS 全家桶代理工具一次配齐

[上一篇](/posts/google-ai-ultra-trial/)折腾的是 Android 模拟器那条路子：在电脑上装 MuMu、推 `frida-server`、备一个带结算库的 `module.apk`，再用 `DexClassLoader` 动态塞进 Google One 进程里调 `BillingClient`，把藏在底下的 `$0` 试用翻出来。整套流程跑得挺稳，但对没碰过逆向的朋友实在不太友好，光是配 ADB 端口转发和来回切类加载器就能劝退一大半人。

后来顺手抓了一下 iPhone 上的请求链路，发现 iOS 端压根不用搞进程注入那么重。谷歌旗下的 iOS 客户端在渲染 AI 订阅升级页时，当前允许展示哪些套餐编号（也就是 SKU），全靠服务端通过两条通道下发给手机：一条是内嵌网页容器请求的 `https://one.google.com/ai`（多账号路径长成 `/u/0/ai`），返回明文 HTML 与内嵌配置块。

另一条则是原生套餐展台接口 `https://subscriptionsmobile-pa.googleapis.com/$rpc/google.internal.one.v1.StorefrontService/GetDynamicStorefrontInfo`，走的是带 5 字节帧头的二进制 gRPC / Protobuf 数据流。只要让手机上的代理软件在本地当个中间传话的，趁这两路响应落回客户端之前把里面写死的 `g1.ios.*` 日常正价编号偷偷替换成隐藏促销编号，App 点订阅时就会乖乖拿着换过的商品 ID 去拉收银台。

不管你主力用的是小火箭（`Shadowrocket`）、`Surge`、`Clash` 全系（包括 iOS 端的 `Stash`，以及跑纯 `Mihomo` 内核的 `Clash Mi`、`FlClash`、`Clash Verge`、`Karing`），还是 `Loon`、`Quantumult X`（圈 X）、`Egern`，底子都是同一套拦截逻辑，只是各家配置文件的写法和内核能力有一点差别。动手前先看一眼下面这张表，对号入座挑自己手头正在用的工具往下翻就行：

| 你手里正在用的客户端 | 本地 HTTPS 改包能力 | 推荐挂载格式 | 是否需要电脑配合 |
|---|---|---|---|
| `Shadowrocket`（小火箭）/ `Surge` | 原生支持请求头、正文正则与二进制脚本 | 在原有配置上叠加 `.sgmodule` 模块 | 不需要，纯手机独立完成 |
| `Stash`（iOS 版 Clash 生态） | 原生内置 `http.mitm` 与 `binary-mode` 脚本 | 在现有机场配置上叠加 `.stoverride` 覆写 | 不需要，内联脚本单文件生效 |
| `Clash Mi` / `FlClash` / `Clash Verge` / `Karing` | 纯 `Mihomo` 内核无本地改响应体引擎 | `+proxies` / `+rules` 或 `main(config)` 覆写 | 需要同一 Wi-Fi 下电脑开改写网关 |
| `Loon` / `Quantumult X`（圈 X）/ `Egern` | 原生支持 MITM 与二进制响应体脚本 | `.plugin` / `.snippet` / `Egern.yaml` + `.js` | 不需要，纯手机独立完成 |

## 0x01 两条实测路线、双结算通道，还有绝对不能进错的入口 App

最开始我也犯过一个想当然的经验主义错误：以为 `.acq` 这类跨端拉新编号只认谷歌网页端的 `payments.google.com` 结算，跟苹果原生的 `StoreKit` 内购尿不到一个壶里。结果拿真机挂上 `storekitd` 日志点了几轮才看明白，谷歌其实早把这批隐藏促销编号同步注册进了苹果 App Store Connect 后台，只是苹果商店里每一个 iOS App 各自维护着一张互不相通的内购商品表（`SKProduct`）。选错点击升级的入口 App，改写规则哪怕百分之百命中了，弹出来的照样是 `$199.99` 原价。

按手里账号的新老情况，实测下来一共分两条路走，原价编号、目标隐藏编号和必须打开的入口 App 对照如下：

| 目标方案与实测扣款价 | 原响应里的默认 SKU | 替换后的目标促销 SKU | 手机端必须打开的入口 App |
|---|---|---|---|
| Ultra 20x（30TB）首月 $0 免费试用 | `g1.ios.30tb.ai.pro.m` | `g1.ai.ultra.1month_eft.acq` | `Google` 搜索 App、`Gemini`（仅 $0 试用可用 `Google One`） |
| Ultra 5x（20TB）首月 $0 免费试用 | `g1.ios.20tb.m.v2` | `g1.20tb.1month_eft.acq` | `Google` 搜索 App、`Gemini`（仅 $0 试用可用 `Google One`） |
| Ultra 5x（20TB）前 3 个月 $9.99/月 | `g1.ios.20tb.m.v2` | `g1.20tb.3months_ip_90p.acq` | 仅限 `Gemini` App（点头像 -> 升级 -> 20TB） |
| Ultra 20x（30TB）前 3 个月 $19.99/月 | `g1.ios.30tb.ai.pro.m` | `g1.ai.ultra.3months_ip_90p.acq` | 仅限 `Google` 搜索 App 彩色 G 图标（选 30TB） |
| AI Pro（2TB / 5TB）前 12 个月 $1.99/月 | `g1.ios.2tb.*` 系列 | `g1.2tb.ai.12months_ip_90p` | `Google` 搜索 App（彩色 G 图标）或 `Gemini` |

先说白板新号首选的 `$0` 免费试用路线。只要你的谷歌号和美区 Apple ID 之前没开过同组试用，把 `30TB` 换成 `g1.ai.ultra.1month_eft.acq`（或者干脆把 `20TB` 和 `30TB` 两个按钮全指到 `g1.ai.ultra.1month_eft.acq`），进 `Google` 搜索 App、`Gemini` 或 `Google One` 点升级就能直接拉出首月 `$0` 的苹果内购确认单。而且 `g1.20tb.1month_eft.acq`（5x）和 `g1.ai.ultra.1month_eft.acq`（20x）在商店里算两件独立商品，领过 20x 试用的号回头还能单独测一把 5x。

这里顺手记一个很容易漏掉的进阶彩蛋。首月 `$0` 试用刚激活那一下，别急着退出来，立刻进 iPhone 系统 `设置 -> Apple 账户 -> 订阅`，点进刚生效的 `Google`（或 `Google One`）订阅项，再点里面的"查看所有方案"（`See All Plans`，也可以直接用浏览器开 `https://apps.apple.com/account/subscriptions`）。苹果系统会把同一个订阅组底下所有上架过的隐藏档位全列出来，不少账号能在这里直接翻出前端页面根本没画出来的 `Google AI Ultra (1 year free trial)` 一年免费档，点切换就能顺延整整一年。另外千万留个神：准备冲 `$0` 试用的号，一上来别挂付费一折模块（`3months_ip_90p.acq`）去试水。苹果 `StoreKit` 同一个订阅组只给一次新客优惠机会，强行塞付费 `.acq` 会把原本能弹出来的免费试用直接顶成付费一折。

再说拿不到免费资格的老号，退一步改开付费一折的规矩。这一路最大的坑就在入口 App 上：付费一折绝对不能在 `Google One` App 里点！`Google One` 的内购白名单里只录了 `g1.ios.*` 和免费试用编号，压根不认识非 `ios` 前缀的一折编号，在里面点升级只会被回退成 `$199.99`/月。想开 5x（20TB）前三个月 `$9.99`/月，必须进 `Gemini` App 点右上角头像选升级；想开满血 20x（30TB）前三个月 `$19.99`/月，或者 AI Pro 连续 12 个月 `$1.99`/月（注意 Pro 这个编号 `g1.2tb.ai.12months_ip_90p` 尾巴上不带 `.acq`，如果个别老号连 `90p` 一折都吃不到，把 `90p` 改成 `75p` 还能退一步测二五折），必须去下那个彩色 G 图标的 `Google` 搜索 App，点右上角头像进升级页选卡片。

扣款方式和防翻车护栏也顺手拎清。在上面这几个 iOS 原生 App 里点订阅，拉起的是苹果美区 `StoreKit` 付款单（双击侧边键确认，扣美区 Apple ID 绑定的卡或美区 PayPal），所以后面所有客户端的分流规则都必须把 `itunes.apple.com`、`apps.apple.com`、`apple.com` 这些苹果结算域名强制设为 `DIRECT` 直连，免得挂代理调收银台撞上苹果异地风控。

反过来，如果你不开原生 App，直接在手机 Safari 无痕窗口打开 `https://one.google.com/ai` 网页版点订阅，走的则是谷歌自家的 `payments.google.com` 网页收银台，扣谷歌付款资料里的海外 Visa 或 Mastercard 卡。走网页通道的话跟上一篇一样，冲 `$0` 试用往虚拟卡里只放 3 美元，冲 `$19.99` 一折只放 22 美元，靠卡内余额做物理限额永远最踏实；同时确认当前谷歌号名下没有任何现存的 Google One 订阅（哪怕挂着 100GB 基础版，后台算价时也会直接剥掉 `.acq` 的优惠阶段）。

## 0x02 小火箭（Shadowrocket）与 Surge 配置：在现有配置上叠加 .sgmodule

先从小火箭讲起。新手拿小火箭配改写最容易踩的一个大坑，就是去导入别人给的"独立空白 `.conf` 配置文件"。在小火箭里，你平时生成并信任好的根证书私钥（`ca-p12` / `ca-passphrase`）连同所有机场节点，全都保存在当前正在用的 `default.conf` 肚子里。一旦导入并切到一个新建的空白 `.conf`，里面既没有外部节点，也没有刚才信任过的那把 CA 私钥，`one.google.com` 根本解不开密。稳妥的做法是始终保持选中你原有的 `default.conf`，在上面直接挂载 `.sgmodule` 叠加模块。

第一步先把 `default.conf` 的 HTTPS 解密证书开好（以前抓过包、信任过证书的朋友直接跳到下一步）。先把小火箭首页顶部的连接总开关关掉，切到底部"配置"页，点 `default.conf` 右侧的蓝色 `(i)` 图标，往下找到"HTTPS 解密"点进去，打开顶部的"HTTPS 解密"开关，依次点"证书 -> 生成新的 CA 证书 -> 安装证书 -> 允许"把描述文件下到手机里。接着打开 iPhone 系统 `设置`，点顶部的"已下载描述文件"（或者进 `设置 -> 通用 -> VPN 与设备管理`），输入锁屏密码把 `Shadowrocket` 描述文件装上。装完描述文件只走了一半，继续进系统 `设置 -> 通用 -> 关于本机`，一路滑到最底下点进"证书信任设置"，找到 `Shadowrocket` 根证书把右侧开关掰绿（要是点进来发现列表是空的，说明漏了前一步安装描述文件）。全部弄完切回小火箭，千万记得连续点两次右上角的保存对勾退回列表，别顺手往右滑屏幕返回，左滑返回不会保存刚才打开的 HTTPS 解密开关！

第二步挂改写模块。如果你只想用纯手机花一分钟跑通、不想单独放任何 `.js` 脚本文件，直接复制下面这段纯文本模块（文末压缩包 `Shadowrocket叠加模块/` 目录里也备好了现成的 `GAI-PureText-FreeTrial-免JS纯文本版.sgmodule` 与 `GAI-PureText-90Off-免JS纯文本版.sgmodule`）。它同时干了四件事：拦掉 `UDP 443` 逼流量退回常规 TCP、让苹果内购域名走直连、强迫原生接口返回未压缩数据、用内置的 `[Body Rewrite]` 把网页容器里的三档 SKU 一次换齐（下面演示付费一折的 `3months_ip_90p.acq`；白板新号冲 `$0` 免费试用时把两处 `3months_ip_90p.acq` 换成 `1month_eft.acq` 即可）：

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

打开小火箭底部的"配置"，切到顶栏的"模块"，点右上角 `+` 号新建本地模块，把整段代码贴进去保存并确认前面打上了勾。要是遇到页面体积偏大超了 `[Body Rewrite]` 的默认缓冲上限，或者客户端某次升级页完全不走网页容器、只读原生 `GetDynamicStorefrontInfo` 的二进制 Protobuf 响应，就把文末提供的 [gai-sku-dual-channel.js](gai-sku-dual-channel.js) 存进系统"文件" App 的 `我的 iPhone -> Shadowrocket -> Scripts/` 目录（也可以在自己电脑同目录起一行 `python3 -m http.server 8080` 填局域网地址，切勿乱引网上来路不明的第三方外链脚本，免得暴露 `one.google.com` 的登录 Cookie），再往上面的模块里补上这段 `[Script]` 声明（文末压缩包里的标准 `.sgmodule` 已默认写好）：

```ini
[Script]
GAI_Web_StoreKit = type=http-response,requires-body=1,max-size=0,pattern=^https://one\.google\.com/(?:u/\d+/)?ai.*$,script-path=gai-sku-dual-channel.js
GAI_Native_Storefront = type=http-response,requires-body=1,binary-body-mode=1,max-size=524288,pattern=^https://subscriptionsmobile\-pa\.googleapis\.com/\$rpc/.*GetDynamicStorefrontInfo,script-path=gai-sku-dual-channel.js
```

如果你主力用的是 `Surge`（无论是 iOS 版还是 macOS 桌面版），配置起来更省心，因为 `.sgmodule` 本来就是 Surge 的原生模块格式。iOS 版打开 Surge 点右上角进 `MitM`，点"生成新的 CA 证书"装好描述文件，再去系统 `设置 -> 通用 -> 关于本机 -> 证书信任设置` 掰绿根证书，回到 Surge 把 `MitM`、`Rewrite` 和 `Scripting` 三个总开关全打开（macOS 版直接在 `偏好设置 -> MitM` 里点生成并信任证书写入系统钥匙串就行）。接着把 `gai-sku-dual-channel.js` 丢进 `iCloud Drive`（或 `我的 iPhone`）底下的 `Surge/Scripts/` 文件夹，进"模块 -> 安装新模块"导入上面这份带 `[Script]` 的 `.sgmodule` 勾选启用。出发前瞄一眼首页的出站模式，确认选在"规则判定"（小火箭那边叫全局路由选`配置`），千万别停在"直接连接"上，选好美国节点打开开关就能去杀后台刷价格了。

## 0x03 Clash 全生态配置：分清 Stash 单机覆写与纯 Mihomo 局域网网关

群里问得最多的就是"我手机和电脑上只有 Clash，到底怎么配"。先把最容易翻车的两条铁律摊开讲清楚：第一，千万别去点网上那种裸 `clash://install-config?url=...` 的一键导入链接，那玩意儿导入的是一整份空白节点库，点下去直接把你正在用的机场订阅覆盖没了，连网都出不去；正经做法永远是在你现有的机场配置上挂载"覆写（`Override`）"，原有机场节点和策略组一根汗毛都不动。第二，看清你手里的客户端底子：`App Store` 上的 `Stash` 虽然兼容 Clash 配置文件，但它自己内置了完整的 `http.mitm` 和 `http.script` 引擎，光靠一台 iPhone 就能独立改完双通道；而 `Clash Mi`、`FlClash`、`Clash Verge`、`Karing` 底层跑的是纯 `Mihomo`（原 `Clash.Meta`）路由内核，它只管三四层流量分发，压根没有拆开 HTTPS 改响应体的本地脚本引擎，必须把那两个谷歌域名分流给同一 Wi-Fi 下电脑跑的改写网关。

### 1. iOS Stash（免电脑，单文件 .stoverride 内联脚本独立生效）

手里有 `Stash` 的朋友不需要开电脑。先在 Stash 底部点"工具 -> HTTPS 解密"，生成根证书、安装描述文件，照例去系统 `设置 -> 通用 -> 关于本机 -> 证书信任设置` 把 Stash 根证书掰绿，再回 Stash 确认"HTTPS 解密"和"脚本"开关都已开启。

Stash 官方的 `.stoverride` 覆写规范有个特别舒服的设计：顶层的 `rules:` 会自动置顶插入你当前正在用的机场配置里，不会冲掉任何节点；同时底下的 `script-providers:` 支持直接用 `payload: |` 把整段 JavaScript 代码内联写进同一个文件里，连外部 `.js` 都不用单独拷。你可以直接从文末压缩包 `Clash与Stash规则库/` 里选好对应档位的 `.stoverride` AirDrop 到手机导入，也可以直接复制下面这段自带内联双通道脚本的 `.stoverride` 保存启用（把内联脚本第一行的 `MODE` 从 `"eft"` 改成 `"90off"` 即可切到老号付费一折）：

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
        const hasB = (b, o, l, p) => { for (let i = o; i <= o + l - p.length; i++) { let ok = true; for (let j = 0; j < p.length; j++) if (b[i + j] !== p[j]) { ok = false; break; } if (ok) return true; } return false; };
        function rwPb(b, s, e, sb, db, d) {
          if (d <= 0 || !hasB(b, s, e - s, sb)) return null;
          const cs = []; let p = s, h = 0;
          while (p < e) {
            const ts = p; let tg = 0, sh = 0;
            while (p < e) { const c = b[p++]; tg |= (c & 0x7f) << sh; if (!(c & 0x80)) break; sh += 7; if (sh > 35) return null; }
            const wt = tg & 7; if ((tg >>> 3) <= 0) return null;
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
          if (b.length >= 5 && (b[0] === 0 || b[0] === 0x80)) {
            let fp = 0, ok = true, fh = 0; const fc = [];
            while (fp < b.length) {
              if (fp + 5 > b.length) { ok = false; break; }
              const flg = b[fp], fl = ((b[fp + 1] << 24) >>> 0) + (b[fp + 2] << 16) + (b[fp + 3] << 8) + b[fp + 4];
              if (fp + 5 + fl > b.length) { ok = false; break; }
              let pl = b.subarray(fp + 5, fp + 5 + fl);
              if (flg === 0 && hasB(b, fp + 5, fl, sb)) { const r = rwPb(b, fp + 5, fp + 5 + fl, sb, db, 20); if (r) { pl = r.bytes; fh += r.hits; } }
              const hd = new Uint8Array([flg, (pl.length >>> 24) & 0xff, (pl.length >>> 16) & 0xff, (pl.length >>> 8) & 0xff, pl.length & 0xff]);
              fc.push(hd, pl); fp += 5 + fl;
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
          let txt = raw;
          for (const [s, d] of PAIRS) txt = txt.split(s).join(d);
          txt = txt.replace(/g1\.ios\.2tb\.[A-Za-z0-9._-]+/g, "g1.2tb.ai.12months_ip_90p");
          $done(txt !== raw ? { body: txt } : {});
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

至于用 `Karing` 的朋友，除了直接导入合入节点的配置，也可以在自定义分流组里直接挂载文末压缩包 `RuleSet远程与本地分流规则库/` 底下的 `gai_rewrite.json`（指给局域网 HTTP 网关节点）和 `apple_direct.json`（指给 `DIRECT`）。连上 VPN 后第一次触发局域网通信时，iOS 系统会弹一个"是否允许查找并连接到本地网络上的设备"权限框，记得点"允许"。接着教你一个三秒钟验通不通的办法：不用先去刷谷歌 App，直接打开手机 Safari 访问 `https://one.google.com/g1-sku-report`，只要网页干净利落地吐出一段包含 `"ok": true` 和命中计数的 JSON，就说明分流、局域网网关和证书信任三条线全齐活了。

## 0x04 Loon、Quantumult X（圈 X）与 Egern 配置，以及 Protobuf 为什么不能硬替

剩下三款 iOS 进阶玩家常用的工具全都自带完整的本地脚本引擎，只要先把文末的 [gai-sku-dual-channel.js](gai-sku-dual-channel.js) 下载存进各自客户端的本地 `Scripts` 目录（打开脚本最顶部的 `MODE_KIND` 常量就能在默认的免费试用模式 `"tri_eft_smart"` 和老号付费一折模式 `"tri_smart"` 之间切换），再把对应的规则片段挂上去即可。

用 `Loon` 的话，先在 `配置 -> MITM` 里生成并安装根证书，去系统 `关于本机 -> 证书信任设置` 掰绿，把 MITM、复写和脚本总开关都打开。把 `gai-sku-dual-channel.js` 放进 `我的 iPhone`（或 `iCloud Drive`）下的 `Loon/Scripts/` 目录，接着新建或导入下面这份 `.plugin` 插件。注意 Loon 拦 QUIC 的原生规则写法是 `PROTOCOL,QUIC,REJECT`（开启期间会全局拦掉 QUIC 强制走 TCP，办完订阅关掉插件就能恢复），而且原生接口那一行脚本必须带上 `binary-body-mode=true`：

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

用 `Quantumult X`（圈 X）的朋友有两个专属细节千万留神。第一，圈 X 的 `[filter_local]` 分流段不支持按传输层端口拦 `UDP 443`，要防 HTTP/3 溜号得编辑主配置文件的 `[general]` 段落，往里面加一行 `udp_drop_list = 443`；第二，Surge、Loon、Stash 在二进制模式下都是把 `Uint8Array` 塞进 `$response.body` 里传给脚本，唯独圈 X 是把 `ArrayBuffer` 放在 `$response.bodyBytes` 字段里，改完还得原样包成 `$done({ bodyBytes: ... })` 交回去（好在 `gai-sku-dual-channel.js` 已经专门写了 `isQxBytes` 分支兼容好了）。点圈 X 右下角小风车生成配置好根证书并去系统信任后，把 `gai-sku-dual-channel.js` 丢进 `Quantumult X/Scripts/` 目录，挂载下面这段 `.snippet` 片段即可：

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

如果你用的是这两年挺火的模块化客户端 `Egern`，同样先在设置里开好 MITM 证书并完成系统完全信任，在主配置里确认开了 `block_quic: true`，把 `gai-sku-dual-channel.js` 放进本地脚本目录后新建一个 YAML 模块，核心是在原生接口那条 `http_response` 底下把 `body_required: true` 和 `binary_body: true` 一块儿加上：

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

顺嘴聊两句为什么第二条通道非得写二进制解析代码不可。`GetDynamicStorefrontInfo` 吐回来的是标准的 gRPC 数据帧：最外层顶着 5 个字节的帧头（1 字节压缩标志位 `0x00` 加上 4 字节大端序负载长度），里面套着好几层 Protobuf 的 `wire type 2` 变长消息，每一个字符串和外层父消息前面都顶着一个 `varint` 字节长度前缀。你把 16 字节的 `g1.ios.20tb.m.v2` 换成 26 字节的 `g1.20tb.3months_ip_90p.acq`，平白多出来 10 个字节；要是直接拿二进制查找替换硬塞进去，从最里层的字符串字段到外层所有嵌套子消息的 `varint` 长度、再到最外头那 4 字节大端帧长全都会错位，客户端反序列化当场崩掉，升级页直接刷出一片空白。所以先在请求头里强塞 `identity` 把 gzip 压缩剥掉，再由脚本递归遍历每一层 Protobuf 标签，由内向外逐层重算 `varint` 长度并更新 5 字节帧头，客户端吃进去才跟原生下发的一模一样。

## 0x05 实测排坑、Apple 内购风控解锁话术与模块包下载

规则挂好连上美国节点之后，第一件必做的动作是把手机后台开着的 `Google`、`Gemini`、`Google One` 彻底往上划掉杀干净进程再重进。客户端会把上一次拉回来的原价方案列表缓存在内存里，不杀后台重进的话点多少次都是旧数据。永远以双击侧边键前弹出来的那张收银台明细作为唯一准绳，看到 `1 month free trial`（`$0.00`）或者前三个月 `$9.99/month`、`$19.99/month` 的字样再按下去。

真机实测时还有两类苹果侧的弹窗最容易让人误以为"改写失效了"，其实跟脚本半毛钱关系没有。第一种是双击侧边键输完面容之后，屏幕正中间蹦出一句 `"Your Purchase Could Not Be Completed - Submit a request to Apple Support for review"`（中文提示"购买未完成，提交申请至 Apple 支持以供审核"）。能走到双击侧边键这一步，说明 SKU 改写和商店查价早就成功了，纯粹是你这个新注册的美区 Apple ID 第一次发起内购撞上了苹果的账号风控。别反复狂点，直接用浏览器打开 `https://getsupport.apple.com/`，依次选 `Billing & Subscriptions -> Unable to purchase -> Chat` 找在线客服，把下面这段英文发过去，人工客服后台点一下放行，回头再订就能秒过：

```text
Hi, I tried to purchase a Google One subscription ($19.99) via In-App Purchase on my iPhone, and received "Your Purchase Could Not Be Completed - Submit a request to Apple Support for review". Could you please help review and unblock In-App Purchases on my Apple Account? Thank you.
```

第二种常见报错是弹窗提示 `"Your payment method was declined"`。碰到这个先去 iPhone 系统 `设置 -> Apple 账户 -> 媒体与购买项目 -> 查看账户 -> 购买记录` 里翻一圈，十有八九是以前某个订阅续费扣款失败留下了一笔红色的未结清欠费单，先把旧欠单结清才能买新订阅。另外如果你绑的是美区 PayPal，苹果内购默认走小额合并账单（`Batch Billing`），页面弹出订阅成功且容量到账后，PayPal 账单往往要过 1 到 72 小时才会实际扣走那笔钱；千万别看着没扣款就手痒去解绑 PayPal，不然等苹果后台真正发起合并结算时扣空，号立刻就变欠费风控态了。要是你走的是 Safari 网页端 `payments.google.com` 结算，付款前记得先进 `payments.google.com/gp/w/home/settings` 看一眼，把香港等非支持区的旧付款资料关掉，免得订阅挂错区导致回头进 Antigravity 调高阶模型时配额死活卡在 Starter。

顺便再提一嘴外部直链的风控雷区：网上流传的那些 `tokenized.play.google.com/eacquire/multiline?ear=...` 免抓包直链，主力号千万别图省事乱点。把里面的 `ear` 参数做一次 Base64 解码就能看见，里面原封不动封存着最初抓包那台电脑的 BotGuard 设备指纹、浏览器 UA 和时区。几百个人拿不同账号去点同一条死链接，在谷歌风控眼里就是一窝共用假指纹的关联集群，2026 年 11 月中旬刚有一大批乱叠异常试用的账号被集中清退打回免费 15GB。在自己手机上用代理模块实时替换 SKU，每次结账会话都由你自己的真机当场生成，干净得多。

订阅顺利到账之后记得收好两个尾巴。第一，回各自的代理软件把改写规则关掉，恢复日常刷网页的 HTTP/3 QUIC 速度：小火箭进"配置 -> 模块"取消勾选，`Surge` 进"模块"取消启用，`Stash` 在当前配置下取消勾选对应的 `.stoverride`，`Clash Mi` / `FlClash` / `Clash Verge` 进"配置 -> 覆写"关掉条目并按 `Ctrl+C` 停掉电脑终端上的 `mitmdump`，`Loon` 进"插件"关掉开关，圈 X 取消勾选重写片段并把 `[general]` 里的 `udp_drop_list = 443` 删掉，`Egern` 进模块页关闭模块并还原 `block_quic`。第二，免费试用的第 30 天、一折特惠的第 90 天一到就会按 `$99.99` 或 `$199.99`/月原价自动续费，记得到期前去系统 `设置 -> Apple 账户 -> 订阅`（网页开通的去 Google One 管理页）手动点掉续订。

上面提到的所有客户端现成配置文件（含小火箭与 Surge 的双通道及免 `.js` 纯文本 `.sgmodule`、已内联完整脚本且去掉冗余顶层键的 Stash `.stoverride`、纯 Mihomo 的 YAML / JS 覆写与 `mitmdump` 网关脚本、Karing `.json` 规则集、Loon `.plugin`、圈 X `.snippet`、Egern 模块，分免费试用版与老号付费一折版）已经全部打包脱敏好放在这里，按需自取：

- 全客户端一键模块压缩包：[下载 Google AI iOS 全客户端免越狱模块包（ZIP）](google-ai-ios-modules.zip)
- 独立双通道改写脚本（供手动放进 `Scripts` 目录参考）：[下载通用双通道 Protobuf 脚本（gai-sku-dual-channel.js）](gai-sku-dual-channel.js)
- 纯 Mihomo 客户端配套电脑端网关脚本：[下载 mitmdump 双通道网关脚本（gai_mitm_gateway.py）](gai_mitm_gateway.py)

---

*文里略去了具体账号和卡信息。*
