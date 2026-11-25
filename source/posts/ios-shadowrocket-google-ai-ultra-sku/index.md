---
title: "iOS 端用小火箭改写 SKU 拿到 Google AI Ultra 的一折价和免费试用"
date: 2026-11-24T22:00:00+08:00
lastmod: 2026-11-25T11:30:00+08:00
description: "在 iPhone 上用小火箭（Shadowrocket）开启 HTTPS 解密与响应体改写，把 one.google.com/ai 返回的 iOS 原价 SKU 替换成隐藏的 .acq 促销 SKU，拉出 Google AI Ultra 30TB 前三个月 $19.99 一折价或首月 $0 免费试用。"
categories: ["安全研究", "技术分析"]
tags: ["Google AI Ultra", "Google One", "Shadowrocket", "小火箭", "SKU 改写", "iOS", "MITM"]
draft: false
weight: 10
---

## 0x00 上回塞 Frida 太重，这回在 iPhone 上半路换个商品名

[上一篇](/posts/google-ai-ultra-trial/)折腾的是 Android 那边的路子：在电脑上装 MuMu 模拟器、推 `frida-server`、自己备一个带结算库的 `module.apk`，再用 `DexClassLoader` 塞进 Google One 进程里调 `BillingClient`，把藏在底下的 `$0` 试用翻出来。整套流程虽然稳稳跑通了，但对没碰过逆向的朋友实在不太友好，光是配 ADB 转发和来回切类加载器就能劝退一大半人。

后来顺手看了一眼 iOS 这边的请求链路，发现压根不用搞进程注入那么重。iPhone 上虽然没法随便往 App 内存里塞钩子，但 Google One 的 iOS 客户端在加载 AI 订阅方案页时，底层会走 HTTPS 请求 `one.google.com/ai`，由服务端把当前允许展示的套餐编号（也就是 SKU）塞在响应体里发回手机渲染。

说白了，只要让小火箭（Shadowrocket）在手机本地当个中间传话的：趁谷歌把价目表发回来的半路上，把里面写死的 iOS 原价 SKU 偷偷替换成带折扣或试用的隐藏 SKU，客户端拿到的就是换过的商品 ID，点订阅自然拉起对应的促销价收银台。平时用 Surge、Quantumult X（圈 X）、Loon、Stash 或者 Clash 系的客户端也是一模一样的道理，核心都是开一条针对 `one.google.com` 的 HTTPS 解密（MITM）规则，再配一段响应体字符串替换。下面直接拿大家手里最常见的小火箭把完整步骤和踩过的坑捋一遍，照着点几下就能上手。

## 0x01 动手前先备好干净号、限额卡，认清两套 SKU 命名

开搞之前先把防扣费护栏和账号条件交底，免得规则配半天最后卡在资格弹窗上。

最重要的一件事先说在前面：换上跨端促销 SKU 之后，最终结账扣的是你在谷歌 `payments.google.com` 里绑定的银行卡，跟苹果 App Store 账户余额或 Apple Pay 半毛钱关系没有。苹果原生的 `StoreKit` 内购只认 App Store Connect 后台写死的那几款 iOS 商品名，而这套 `.acq` 促销编号走的是谷歌自家的结算通道，所以在苹果商店里绑卡是使不上劲的，动手前得先把卡绑进谷歌付款资料里。

拿来操作的谷歌账号必须同时满足两条硬门槛：一是账号目前没有任何现存的 Google One 订阅（哪怕订着最便宜的 100GB 基础版都不行），二是已经提前在 `payments.google.com` 绑好了一张可用的海外 Visa 或 Mastercard 卡。如果是冲首月 `$0` 免费试用去的，跟上回一样，往虚拟卡里只放 3 美元最保险；如果是冲 Ultra 30TB 前三个月一折（`$19.99`/月）去的，首月当场就要扣第一笔钱，卡里塞个 22 美元左右刚够付首月加预授权就行。万一哪步手滑没命中改写、弹出了 `$199.99` 的原价框也不至于被一刀扣穿。

再看一眼我们要替换的字符串。上一篇在 Android 侧摸出来带试用的商品 ID 往往嵌着 `play`（比如 `g1.play.ai.pro`、`g1.play.20tb`），而在 iPhone 上抓 `one.google.com/ai` 返回给客户端的数据时，默认下发的原价 SKU 统一换成了 `g1.ios.*` 前缀：

| 客户端默认收到的 iOS 原价 SKU | 对应订阅档位 | 默认月费 |
|---|---|---|
| `g1.ios.30tb.ai.pro.m` | Google AI Ultra 30TB（20x） | $199.99 |
| `g1.ios.20tb.m.v2` | Google AI Ultra 20TB（5x） | $99.99 |
| `g1.ios.2tb.*` 系列 | Google AI Pro（2TB / 5TB） | $19.99 |

虽说默认展示的商品名带了 `ios` 前缀，但谷歌结算后台真正管拉新促销的那批 `.acq` 商品编号是跨平台共用的，后缀规律也跟 Android 侧完全一致：`.acq` 代表纯新客获客（Acquisition），`_ip_90p` 代表 Introductory Price 90% off（前三个月打一折），`_eft` 代表免费试用（Extended Free Trial）。常用的四组替换关系直接对照下面这张表挑一组用就行：

| 原响应里的源 SKU | 替换成的目标促销 SKU | 实际拉出的收银台效果 |
|---|---|---|
| `g1.ios.30tb.ai.pro.m` | `g1.ai.ultra.3months_ip_90p.acq` | Ultra 30TB 前 3 个月一折（$19.99/月） |
| `g1.ios.30tb.ai.pro.m` | `g1.ai.ultra.1month_eft.acq` | Ultra 30TB 首月 $0 免费试用 |
| `g1.ios.20tb.m.v2` | `g1.20tb.3months_ip_90p.acq` | Ultra 20TB 前 3 个月一折（$9.99/月） |
| `g1.ios.20tb.m.v2` | `g1.20tb.1month_eft.acq` | Ultra 20TB 首月 $0 免费试用 |

再叮嘱一句 `.acq` 的脾气：它只认白板新客。只要当前谷歌号名下挂着任何一档现存订阅，哪怕改写规则把字符串换过去了，谷歌后台在算价时也会直接把 `introprice` 优惠阶段吞掉，只吐回光秃秃的 `base` 原价，甚至直接返回空列表。

## 0x02 小火箭三步实操：开证书信任、挂改写模块、杀后台拉账单

很多人第一次拿小火箭改响应体，照着网上的半截配置抄完死活不生效，十有八九是栽在"证书只装没信任"或者"写了裸脚本名手机根本读不到文件"这两个地方。下面按手机屏幕上的真实点击顺序拆成三步，不用自己买域名搭服务器，两分钟就能配好。

第一步是开启 HTTPS 解密并打开系统的根证书信任（只需做一次，以前配过抓包的直接核对一眼即可）。打开小火箭切到底部的"配置"页，点当前正在用的那条配置右边的蓝色 `(i)` 图标，往下滑找到"HTTPS 解密"，把开关打开。如果底下提示还没生成过证书，点"生成新的 CA 证书"，接着点"安装证书"，顺着弹窗允许下载描述文件。下载完去 iPhone 系统的 `设置` 顶部点"已下载描述文件"（或者进 `设置 -> 通用 -> VPN 与设备管理`，部分系统区域叫"描述文件与设备管理"），把 `Shadowrocket` 描述文件装上。注意这还没完，iOS 16 以后把真正的总开关藏得很深：继续进系统 `设置 -> 通用 -> 关于本机`，拉到最底下点进 `证书信任设置`，把刚才那个 `Shadowrocket` 根证书右侧的开关手动掰绿。漏掉最后这一下，后面解出来的流量全是证书报错，什么改写规则都跑不到。做完回小火箭点右上角"完成"保存。

第二步是新建一个本地改写模块。这里千万别去网上随便导别人挂着远程 `https://.../xxx.js` 外链的模块：你既然已经对 `one.google.com` 开了 HTTPS 解密，一旦引了来路不明的外部脚本，人家顺手读走请求头里的谷歌登录 Cookie 简直易如反掌。

最省事也最安全的起手方案，是直接用小火箭兼容的 `[Body Rewrite]` 正文正则替换语法，不用额外建 `.js` 文件，把屏蔽 QUIC、指定解密域名和替换 SKU 捏进同一个纯文本本地模块里。下面这段默认把 Ultra 30TB 原价换成前三个月 `$19.99` 一折价，顺带把 20TB 原价换成首月免费试用（如果想把 30TB 也换成首月免费试用，把第 9 行末尾的 `g1.ai.ultra.3months_ip_90p.acq` 改成 `g1.ai.ultra.1month_eft.acq` 即可）：

```ini
#!name=Google One Ultra SKU 本地改写
#!desc=屏蔽 UDP 443 强制回落 TCP，并将 one.google.com/ai 响应中的 iOS 原价 SKU 替换为促销 SKU

[Rule]
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

[Body Rewrite]
http-response ^https://one\.google\.com/(?:u/\d+/)?ai(?:[/?#].*)?$ g1\.ios\.30tb\.ai\.pro\.m g1.ai.ultra.3months_ip_90p.acq
http-response ^https://one\.google\.com/(?:u/\d+/)?ai(?:[/?#].*)?$ g1\.ios\.20tb\.m\.v2 g1.20tb.1month_eft.acq

[MITM]
hostname = %APPEND% one.google.com
```

把上面整段代码块复制下来，打开小火箭点底部"配置"，切到上方的"模块"栏，点右上角的 `+` 号新建本地模块，整段粘贴进去点右上角保存，确认模块列表里这一项前面打上了蓝勾。

有一个小概率边界情况得提前打个预防针：`[Body Rewrite]` 走的是代理引擎内置的固定响应体缓冲上限（通常在 1MB 左右），没法手动调大；万一 `one.google.com/ai` 某次返回的页面体积偏大超了内置阈值，引擎会静默跳过不替换。要是碰到日志里看请求过了代理却死活没改掉，或者你平时主力用的是 Surge、Quantumult X（圈 X）、Loon、Stash 以及 Clash 系客户端（Clash 用 `rewrite` 或 `script` 配合 MITM 白名单，圈 X 用 `url script-response-body`），可以切到下面这套标准的 `[Script]` 脚本方案，用 `max-size=2097152` 手动把响应体上限撑到 2MB，同时 URL 正则用 `(?:[/?#].*)?$` 兼容不带参数的裸 `/ai`、带参数的 `/ai?...` 以及多账号路径 `/u/0/ai`：

```ini
#!name=Google One Ultra 脚本版改写
#!desc=使用自定义 JS 改写 one.google.com/ai 响应体中的 SKU（放宽响应体至 2MB）

[Rule]
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

[Script]
google-one-sku = type=http-response, pattern=^https://one\.google\.com/(?:u/\d+/)?ai(?:[/?#].*)?$, requires-body=1, max-size=2097152, script-path=http://192.168.1.100:8080/sku-rewrite.js

[MITM]
hostname = %APPEND% one.google.com
```

配套的 `sku-rewrite.js` 加上判空保护，防止遇到 `304` 空响应时抛异常：

```javascript
let body = $response && $response.body;
if (body) {
    // Ultra 30TB：iOS 原价替换为前 3 个月 $19.99 一折
    body = body.replace(/g1\.ios\.30tb\.ai\.pro\.m/g, "g1.ai.ultra.3months_ip_90p.acq");
    // Ultra 20TB：iOS 原价替换为首月 $0 免费试用
    body = body.replace(/g1\.ios\.20tb\.m\.v2/g, "g1.20tb.1month_eft.acq");
    $done({ body });
} else {
    $done({});
}
```

注意小火箭不像桌面版 Surge 那样有独立的本地脚本目录，模块里要是只写裸文件名 `script-path=sku-rewrite.js` 大概率会报找不到文件。真要跑脚本版，在自己电脑上存好 `sku-rewrite.js` 起一行 `python3 -m http.server 8080` 填局域网地址，或者丢到自己的私密 GitHub Gist 拿 Raw 直链填进去最稳；纯手机操作的新手直接用前面那段免 `.js` 的 `[Body Rewrite]` 模块就够了。

第三步是连上代理触发改写。回到小火箭首页先确认两件事：一是"全局路由"一定要选默认的`配置`模式（千万别选成`直连`，选直连就不走规则和重写引擎了），二是代理节点选美国等明确支持 Google AI Ultra 的地区，确认无误再打开顶部的连接开关。接着把手机后台原本开着的 Google One App 彻底往上划掉杀干净进程，重新打开 Google One App 切到那个绑好卡的干净谷歌号，点进 AI 订阅页面（如果 App 本地缓存太死怎么刷都不变，也可以打开 Safari 无痕窗口访问 `https://one.google.com/ai` 对照测试）。想确认改写到底吃上没有，切回小火箭底部的"数据"（或"日志"）页搜一下 `one.google.com`，能看到请求走过 MITM 解密并带上重写标记，再点升级按钮就能拉出折扣收银台了。

## 0x03 为什么改个响应字符串就能过：展示层与结算层的信任脱节

可能有人会纳闷：价格难道不应该是谷歌服务器自己说了算吗，怎么在手机里改几个字母就能按一折结算？

其实谷歌后台并没有蠢到让客户端随便编造价格数字，你就算把页面上的 `$199.99` 文本改成 `$0.01`，真正扣款时服务器理都不会理你。这里真正被绕过去的，是"当前前端界面允许用户发起哪一个商品编号的购买"这道展示过滤。

正常的业务流程分两截走：前半截客户端请求 `one.google.com/ai` 拉可用方案列表，前端服务看一眼你的环境是 iOS，就按默认策略只往响应里塞 `g1.ios.30tb.ai.pro.m` 这类日常正价 SKU，压根不把 `.acq` 拉新促销编号发给你；后半截等你按下订阅按钮时，客户端拿着刚才响应里的 SKU 编号去向谷歌结算后端发起购买请求。

问题就出在前后两截各管一摊。后面的结算服务收到 `g1.ai.ultra.3months_ip_90p.acq` 时，只管校验三件事：库里有没有这个合法的促销 SKU、促销活动还在不在有效期内、当前谷歌账号符不符合无历史订阅加已绑卡的新客资格。它默认假设"只要客户端能把这个 SKU 传上来，肯定就是前面展示层刚刚下发给它的"，中间没有做任何一次服务端签名绑定或会话回查。口子就在这里。趁响应落回客户端之前把原价编号换成真实存在的隐藏促销编号，两头校验就全都顺顺当当放行了。

## 0x04 实测踩过的四个细碎坑

真正在真机上调通之前，我也连着撞了好几回软钉子，这里按排查顺序记一下，万一你点开还是 `$199.99` 原价，直接挨个对照查就行。

头一个拦路虎就是前面模块里顺手加进去的那条 `UDP 443` 拦截规则。`one.google.com` 默认优先走 HTTP/3（也就是基于 UDP 443 端口的 QUIC 协议），而小火箭的 MITM 解密只能拆 TCP 上的常规 TLS 流量，碰上走 UDP 的 QUIC 直接解不了，流量从旁边溜走了，后面的重写规则一行都不会触发。加上 `AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP` 之后，系统发现 UDP 443 不通就会自动回落到常规 TCP 连接，解密和替换瞬间就活过来了。唯一要注意的是这条规则在模块开启期间会把手机上所有 App 的 QUIC 一并拦掉，平时刷网页可能会慢一丢丢，订阅办完记得关掉模块。

第二个坑是响应体体积与本地缓存。Google One 的 `/ai` 页面经常一口气塞回来大几百 KB 的数据，如果走脚本改写没配 `max-size` 很容易因为超默认体积上限导致脚本超时失效；另外要是开代理之前已经进过一次 Google One 的升级页，客户端会把上一次拉回来的原价方案列表缓存在内存里，不杀后台重进的话点多少次都是旧数据。同时记得看一眼小火箭规则列表，确认 `one.google.com` 没有被别的分流规则提前判成 `DIRECT` 直连跳过代理。

第三个坑在第一个老测试号上折腾了我十来分钟。当时抓包确认响应里的 `g1.ios.30tb.ai.pro.m` 明明已经一字不差换成了 `g1.ai.ultra.3months_ip_90p.acq`，可点进结账框一看，上面照样冷冰冰印着 `US$199.99/month`。回头一查历史账单才拍大腿：这个号已经订着一档最低配的 Google One Basic 100GB。对挂着现存订阅的账号，谷歌服务端下发数据时压根不给 `.acq` 促销编号配 `introprice` 折扣字段，客户端拿到的就是个光秃秃的 `base` 原价，换了商品名价格也不会变。换上第二个干干净净的无订阅新号，同样的规则，收银台立马吐出了 `US$19.99/month`。

第四个容易踩空的地方是谷歌付款资料（Payment Profile）串区。有些朋友平时折腾海外服务，同一个谷歌号底下的 `payments.google.com` 里同时残留了多个不同国家的付款资料，比如一个香港 HKD、一个美国 USD。结账时系统如果把订阅挂在了不支持区的旧资料名下，就算钱扣成功了，回头进 Antigravity 调 Claude 高阶模型时配额也会卡在 Starter 动不了，纯属白花钱。稳妥的做法是付钱前先进 `payments.google.com/gp/w/home/settings` 检查一眼，把多余的非支持区付款资料关掉，只留一个干净的支持区资料。

## 0x05 收银台核对价格与善后提醒

永远以点击最终确认按钮前弹出来的那张收银台明细作为唯一准绳，没看到折扣数字之前千万别闭着眼睛往下点。

改写生效后打开 Google One App 进到 AI 页面，点升级弹出的 Ultra 30TB 一折收银台长这样：

```text
Google AI Ultra (30 TB)
  开始日期：今天          US$19.99/month
  开始日期：2027年2月     US$199.99/month
  Mastercard ····6872
  [订阅]
```

账面算得很清楚：前三个月每月扣 `$19.99`，第四个月（2027 年 2 月对应账单日）起恢复原价 `$199.99`/月。三个月合计 `$59.97`，按正常原价订三个月得 `$599.97`，省下整整 `$540`。

如果是换成 `1month_eft.acq` 走首月免费试用的路子，收银台更直接：

```text
Google AI Ultra (30 TB)
  今天          US$0.00
  1个月后       US$199.99/month
  [开始免费试用]
```

顺便多嘴提醒一句风控问题：网上流传的那些 `tokenized.play.google.com/eacquire/multiline?ear=...` 超长免抓包直链，主力号千万别图省事乱点。把链接里的 `ear` 参数剥出来做一次 Base64 解码就能看见（上一篇末尾那条参考样本里也能直观看到），里面原封不动封存着最初抓包者的 BotGuard 设备指纹、UA 字符串和时区信息。成百上千个不同设备的用户去点同一条死链接，在谷歌风控那边看起来就是一群提交了相同假指纹的关联账号集群。2026 年 11 月中旬刚刚有一波开发者因为乱叠异常试用被批量清退降级，连原有的正价订阅都被一并撤掉，直接打回了免费 15GB。在自己手机上用本地代理实时改写 SKU 的好处，就是每次结账会话都由你自己的真机当场生成，没有静态指纹污染这个问题。

订阅激活之后记得顺手干完两件收尾小事：第一，回小火箭切到底部"配置"再点上方"模块"，把刚才勾选的那个改写模块点掉取消勾选，恢复手机正常的 QUIC 网络；第二，一折的第 90 天、免费试用的第 30 天一过就会按 `$199.99`/月自动续费，记得到期前手动去取消订阅，平时卡里也别留太多余额，万一忙忘了取消也扣不动。

---

*文里略去了具体账号和卡信息。*
