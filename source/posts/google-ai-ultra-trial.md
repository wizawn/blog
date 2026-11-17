---
title: "用 Frida 借 Google One 进程调 BillingClient，开出 AI Ultra 的 $0 试用"
date: 2026-11-17
description: "在 MuMu 模拟器里用 Frida 挂进 Google One 进程，动态加载 BillingClient 查出 Ultra 5x（12 个月）和 20x（1 个月）的隐藏免费试用，顺便记一下找商品 ID 和调脚本时踩的坑。"
categories: ["安全研究", "技术分析"]
tags: ["Google One", "Google Play", "BillingClient", "Frida", "Offer Token"]
draft: false
weight: 1
image: "/blog-cover-default.jpg"
---

## 0x00 页面上不给看，BillingClient 里倒是都有

Google AI Ultra 现在分两档：5x 是 20TB，月费 $99.99；20x 是 30TB，月费 $199.99。

正常在 Google One 网页或者 App 里点来点去，你是看不到任何试用入口的，页面上就孤零零一个"升级"按钮，点进去直接弹出 $199.99 的确认框。但实际上，这两档的 $0 试用 offer 一直就躺在 Play 结算库（`BillingClient`）的返回值里，只是客户端前端压根没打算展示出来。

最后两档我都拉出了 $0 试用，5x 开了 12 个月，20x 开了 1 个月。顺手把整个摸索过程和踩的坑记一笔，免得过阵子自己都忘了当初怎么绕出来的。

## 0x01 模拟器、3 美元的卡，还有装不上的 Magisk

动手前先把防翻车措施做好：全程只在 macOS 上的 MuMu 模拟器里折腾，不碰真机；账号上绑的那张卡里也只放了 3 美元。毕竟 20x 一个月要 $199.99，真要哪步脚本写歪了或者手滑点错，让银行直接给拒掉，比啥心理安慰都管用。

思路其实很直白：Google One 本身就是接了 Play 订阅的客户端，既然它自己能弹出 Google Play 的支付框，不如直接借它的进程去调 `BillingClient`，问问 Google Play 这边这个商品到底有哪些 offer。

环境用 MuMu 自带的 `adb` 连上 `127.0.0.1:16384`，再把 `frida-server` 的端口转发出来：

```bash
ADB="/Applications/MuMuPlayer.app/Contents/MacOS/MuMuEmulator.app/Contents/MacOS/tools/adb"
"$ADB" connect 127.0.0.1:16384
"$ADB" -s 127.0.0.1:16384 forward tcp:27042 tcp:27042
```

最开始其实想过走 Magisk 模块那套，但试了下发现 MuMu 里的 `su` 是定制过的，Magisk 装不上，这条路直接堵死了。好在需求本来也不复杂，干脆上 Frida（17.26.4）直接 attach 到正在跑的 Google One 进程（`com.google.android.apps.subscriptions.red`）里。

## 0x02 把 BillingClient 塞进进程里

刚准备开写就碰上第一个麻烦：Google One 的 APK 里压根没有打包 `BillingClient` 这套库，运行的时候才从 Play 相关的模块里加载。要在 Frida 里直接调它的 API，只好自己提前备好一个带着 Billing 库的 `module.apk` 推到 `/data/local/tmp/module.apk`，挂进进程后再用 `DexClassLoader` 动态加载进来，父加载器沿用 App 自己的：

```javascript
var DexClassLoader = Java.use("dalvik.system.DexClassLoader");
var dexLoader = DexClassLoader.$new(
    "/data/local/tmp/module.apk",
    context.getCodeCacheDir().getAbsolutePath(),
    null,
    context.getClassLoader()
);

Java.classFactory.loader = dexLoader;
```

核心调用链倒是很标准：`startConnection()` 连上结算服务，拿商品 ID 调 `queryProductDetailsAsync` 把详情查回来，遍历 `getSubscriptionOfferDetails()` 挑出试用周期最长的那个 offer token，最后丢给 `launchBillingFlow()` 拉起支付弹窗。

但真正把这几步串起来跑通，中间踩的细碎坑一点不少。

## 0x03 把脚本跑通前踩的坑

第一个低级坑是命令行习惯。我用的 Frida 17.26.4 早把 `--no-pause` 参数砍掉了，结果凭肌肉记忆顺手加上去，一回车就报错，删掉才正常 attach 进去。

进到脚本里之后，最折腾人的是免费价格的判断。`getPriceAmountMicros()` 返回的是 Java 的 `long`，到了 Frida 的 JS 环境里 `typeof` 一看竟然是个 `object`，导致 `micros === 0` 永远不成立。我跑完脚本一条试用也没筛出来，可打印出来的日志里价格明明清清楚楚写着"免费"，盯着屏幕看了半天才反应过来是类型问题，老老实实改成宽松比较才过：

```javascript
if (micros == 0 || String(micros) === "0") {
    // 这样才能匹配到 $0 试用阶段
}
```

然后是 `Java.classFactory.loader` 必须跟着来回切。像 `Handler`、`Looper` 这些都是 Android 系统类，而 `BillingClient` 在我加载进来的 `module.apk` 里，如果不切换类加载器，一 `Java.use()` 就是一连串 `ClassNotFoundException`。最后只能在脚本里用谁之前切到谁，用完赶紧切回来：

```javascript
Java.classFactory.loader = null;
var launchHandler = Handler.$new(Looper.getMainLooper());
Java.classFactory.loader = dexLoader;
```

说起来为什么非得用 `Handler`？因为 `launchBillingFlow()` 必须跑在主线程上。我一开始图省事直接在查询结果的回调线程里调它，结果模拟器直接黑屏，当时真以为把环境搞坏了。把构建参数和调用那段塞进 `Runnable`，再通过 `launchHandler.post(...)` 扔回主线程才算稳住。另外传给 `launchBillingFlow()` 的 `Activity` 引用也不能偷懒在脚本刚挂上时就缓存死，得在回调执行的时候去 `ActivityThread.currentActivityThread().mActivities` 里重新捞一个既没 finish 也没 destroy 的当前 Activity 出来，不然调支付框一样容易出问题。

还有一个界面操作上的小插曲：调试过程中有需要脚本自动点"升级"按钮的地方，我一开始偷懒靠肉眼估屏幕坐标连试了三次，其中一次还直接点偏到"包年"标签上把页面切走了。后来乖乖用 `uiautomator dump` 把布局导出来拿到按钮的真实 bounds，再没点歪过。

## 0x04 Ultra 5x 一遍过，20x 却卡在商品 ID

先把 5x 拿来试水，这一档出奇地顺。商品 ID 是 `g1.play.20tb`，调 `queryProductDetailsAsync` 一次拉回来 5 个 offer：

- 4 个带免费试用：`eft-1month`、`eft-3month`、`eft-6month`、`eft-12month`，全都是第一周期 $0，之后按 $99.99/月续费
- 1 个常规无试用 offer

挑了个最长的 `eft-12month`，拿着它的 offer token 拉起支付弹窗，确认一下 `Phase[0]` 写着 $0 之后直接点确认，1 年期的 Ultra 5x 就这么开了出来。

本来以为 20x 照葫芦画瓢改个 ID 就完事了，结果刚起步就卡死：我压根不知道 20x 的商品 ID 叫什么。

我先按常规路子去翻 Google One 本地的缓存库 `StoragePlansDataCache.db`，把库拖出来用 `sqlite3` 和 `strings` 过了一遍：

```bash
"$ADB" shell "su -c 'cat /data/data/com.google.android.apps.subscriptions.red/databases/StoragePlansDataCache.db'" > /tmp/plans.db
sqlite3 /tmp/plans.db ".dump" | strings | grep "g1\."
```

库里确实能翻出低档位那一整排熟悉的命名：`g1.100gb`（100GB）、`g1.200gb`（200GB）、`g1.helium`（400GB）、`g1.2tb`（2TB）、`g1.2tb.ai`（5TB），外加一些区域促销后缀（比如 `g1.100gb.3months_ip_85p.acq` 这种），但就是看不见 Ultra 20x 的踪影。

转头又去拿 jadx 反编译 APK，想看看代码里有没有写死高档位的 ID。翻了一圈只在 Phenotype flag 的默认值里看到 `g1.100gb` 这种基础档（比如 `yfd.java` 的 flag `45684818`），真正用到的商品 ID 全是通过 Phenotype 从服务端下发的，DEX 里根本不留底。顺便吐槽一句，jadx 反编译混淆类的时候会自动给顶层类加个 `p000.` 前缀（比如 `p000.wso`），Frida 运行时 hook 要是直接照抄也会报 `ClassNotFoundException`，去掉前缀用裸名 `wso` 才行。

## 0x05 摸出 20x 隐藏 ID：g1.play.ai.pro

静态翻不到，只好回 App 里抓运行时。我写了个简单的 hook 专门盯住 `JSONObject.put` 和 `Bundle.putString`，只要传进来的 key 是 `productId`、`skuId` 或 `product_id` 就打一条日志，然后回 App 界面亲手点了一下"升级"按钮。

点下去的那一刻，日志里果然吐出一个名字：`g1.ai.pro`。

结果拿 `g1.ai.pro` 兴冲冲去查 `BillingClient`，返回的却只有孤零零一个 $199.99 的无试用 offer。

这就有点不对劲了。既然别人手里能开出 20x 的试用，说明入口肯定存在，多半是 App 里"升级"按钮绑定的这个 ID 本身就没配试用。对照一下前面查出来的 `g1.play.20tb` 和 `g1.2tb.ai`、`g1.ai.pro` 这些命名规律，我干脆新起了一台模拟器、换了个全新账号，把能拼出来的二十来个候选 ID 排成一串，全塞进 `queryProductDetailsAsync` 里批量撞一遍（无效的 ID 接口会自动忽略，有效的才会返回详情）。

最后还真撞出来三个有效的 30TB 档商品 ID：

| 商品 ID | 月费 | 试用情况 | 备注 |
|---|---|---|---|
| `g1.ai.pro` | $199.99 | 无 | App 里"升级"按钮实际调用的就是这个 |
| `g1.30tb` | $149.99 | 无 | 另一个不同定价的 30TB 档位 |
| `g1.play.ai.pro` | $199.99 | **4 个试用 offer** | 正主，tag 带 `eft,genaipro,play,promotional` |

原来同一个 30TB 档位底下 Google 居然配了三个不同的商品 ID，而且只有名字里带着 `play` 的 `g1.play.ai.pro` 才带试用。更有意思的是它的 offerId 命名也跟 5x 对不上，5x 那边叫 `eft-1month` 到 `eft-12month`，20x 这边变成了 `eft-1mo`、`eft-3mo`、`eft-6mo`、`eft-12mo`，连自家命名规范都没统一。

至于为什么 App 界面上永远看不到试用，原因也挺清楚了：客户端按钮点过去走的是不带试用的 `g1.ai.pro`，页面根本没去拉 `g1.play.ai.pro`。目前我手里见过的两个带试用的 Ultra 档（`g1.play.20tb` 和 `g1.play.ai.pro`）名字里都嵌了 `play`，虽然只有两个样本还不敢打包票说这是死规律，但以后再找新档位的话，往这个方向猜基本八九不离十。

另外提一嘴，前面那个老号在本地缓存里没翻出 Ultra 20x，其实就算拿对了 ID 也开不出来，因为这个号已经订着 5x 了，已有订阅会把试用资格直接过滤掉。

## 0x06 换新号实测："您不符合免费试用条件"

拿到 `g1.play.ai.pro` 之后本以为直接收工，结果在第一个全新账号上还是吃了瘪。选 `eft-12mo` 直接提示不符合试用条件，退一步换成 1 个月的 `eft-1mo`，Pay 弹窗给了一句提示：

> 您不符合免费试用条件，尽管如此，您仍能订阅

下面孤零零一个"知道了"按钮，价格写着 $199.99。卡里虽然只有 3 美元，我也不想点下去测试 Google 的风控和扣款容错，直接关掉了。

后来换了第二个号，同样的脚本、同样的 `eft-1mo`，这次没有任何阻碍，正常弹出了 $0 试用的 Play 确认框，确认后顺利激活。

折腾下来，Ultra 20x 触发试用资格的两条硬条件也算彻底摸清了：账号里必须先有付款方式，而且不能已有订阅。缺付款方式会像第一个新号那样直接吃拒绝弹窗，已有订阅则会把试用资格直接过滤掉，这两条踩中哪一个都弹不出 $0 试用。

另外，我还写了个小脚本想通过 `BillingClient` 回查一下当前账号的订阅状态，结果在日志打出 `Connected` 之后就再没输出，一直没把结果读出来，最后还是全凭 Play 弹出来的那张 $0 确认框和手动点击来确认的。

## 0x07 记得去取消，别赌那 3 美元

一个月之后这个 20x 就会按 $199.99 尝试自动续费了，哪怕卡里就放着 3 美元，我也不打算去赌扣款失败后账号会变成什么状态，到期前记得手动把订阅退了。

---

*文里略去了脚本中涉及的具体账号、卡信息以及完整代码和 token。*
