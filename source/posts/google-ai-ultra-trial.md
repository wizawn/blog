---
title: "Google AI Ultra 的 $0 试用：页面不给看，接口里一直有"
date: 2026-11-17
description: "在 MuMu 里用 Frida 借 Google One 的进程调 BillingClient，开出 Ultra 5x 和 20x 的免费试用，顺便记下找商品 ID 时走的弯路。"
categories: ["安全研究", "技术分析"]
tags: ["Google One", "Google Play", "BillingClient", "Frida", "Offer Token"]
draft: false
weight: 1
image: "/blog-cover-default.jpg"
---

## 0x00 先说结果

Google AI Ultra 有两档。5x 是 20TB，$99.99 一个月。20x 是 30TB，$199.99 一个月。

两档我都开出了 $0 试用。5x 开的是 12 个月，20x 开的是 1 个月。

这个试用在 Google One 的任何页面上都看不到。网页没有，App 里也没有。你能看到的只有"升级"，点进去是一个写着 $199.99 的确认框。它藏在 Play 结算库（BillingClient）的返回值里，页面根本没打算展示。

这篇记一下过程。成功的部分很短，大半篇幅是我走错的路。

## 0x01 动手之前

先定两条规矩。

第一，只在 MuMu 模拟器里弄，不碰真机。

第二，绑的那张卡里只放了 3 美元。20x 一个月 $199.99，万一哪一步点歪了，银行会替我拒绝。说起来有点丢人，但整件事里我最踏实的就是这个设计。

## 0x02 Magisk 装不上，换 Frida

思路很朴素。Google One 本来就是 Play 订阅的客户端，它能弹出支付框，那我借它的进程去问 Google Play："这个商品现在有哪些 offer？"

MuMu 里的 `su` 是定制的，Magisk 装不上，靠 Magisk 的那一套路子就断了。最后用 Frida，直接挂到正在跑的 Google One 进程上。

另一个麻烦：Google One 的 APK 里没有打包 BillingClient。我自己准备了一个 `module.apk`，里面带着这个库，用 `DexClassLoader` 加载进去，父加载器用 App 自己的。

## 0x03 几个坑

下面这几个，每一个都白白耗掉我不少时间。

**Java 的 0 不是 JS 的 0。** `getPriceAmountMicros()` 返回 Java 的 `long`，到了 Frida 里 `typeof` 是 `object`。所以 `micros === 0` 永远是假。我的脚本一个试用都没找到，可日志里价格那一栏明明写着"免费"。盯着屏幕看了很久才反应过来，改成这样：

```javascript
if (micros == 0 || String(micros) === "0") {
    // 这才是免费阶段
}
```

**支付框必须在主线程弹。** `launchBillingFlow()` 我最开始是在回调线程里直接调的，结果黑屏。那一下我以为把模拟器搞坏了。改成 `Handler(Looper.getMainLooper()).post(...)`，就好了。

**类加载器要来回切。** `Handler`、`Looper` 是系统类，`BillingClient` 是 `module.apk` 里的类。不切换就是一串 ClassNotFound。我的做法是用谁切谁，用完切回去。

**点坐标。** 后面要点"升级"按钮。我连试三次，其中一次点到了"包年"标签，页面还跳了过去。最后用 `uiautomator dump` 拿到按钮的真实边界才点准。眼睛估坐标这件事，我以后不干了。

## 0x04 Ultra 5x：一次就通

商品 ID 是 `g1.play.20tb`。查回来 5 个 offer：

- 4 个带试用，`eft-1month`、`eft-3month`、`eft-6month`、`eft-12month`，都是先 $0，再 $99.99 一个月
- 1 个普通 offer，没有试用

选了 12 个月那个，拿它的 offer token 去拉支付框，确认，成了。这一档没出任何意外。

## 0x05 Ultra 20x：找 ID 比开通难

20x 的问题是我不知道它的商品 ID。

先去翻 jadx 反编译出来的代码，什么都没有。后来才明白，商品 ID 不写死在 APK 里，是 Google 通过 Phenotype 下发的。又去翻 Google One 本地的 `StoragePlansDataCache.db`，里面只有低档位的 ID，Ultra 的不在，大概因为这个号已经订着 5x 了。

最后用了个笨办法：挂上 hook，监听 `JSONObject.put` 和 `Bundle.putString`，然后在 App 里亲手点"升级"。点下去，日志里蹦出来一个名字：`g1.ai.pro`。

拿它去查 BillingClient，结果只有一个 offer，$199.99，没有试用。

我当时想的是：不对。别人能开出来，说明入口一定在，只是我手里这个 ID 不是那个。

于是换了一台全新的模拟器、全新的账号，把能想到的命名规律排列组合了二十来个，一起丢进去批量查。回来三个：

- `g1.ai.pro`：$199.99，无试用。就是 App 里"升级"按钮用的那个
- `g1.30tb`：$149.99，无试用
- `g1.play.ai.pro`：$199.99，**有 4 个试用 offer**

最后这个才是要找的。它的 offer 标签是 `eft, genaipro, play, promotional`，试用有 1、3、6、12 个月四档。

我的理解是，App 的"升级"按钮走的是 `g1.ai.pro`，所以页面永远不会给你看试用。带 `play` 的那个才有。目前手里的两个例子（`g1.play.20tb` 和 `g1.play.ai.pro`）都带 `play`，不知道算不算规律，只有两个样本。

## 0x06 "您不符合免费试用条件"

在第一个新账号上，我选了 12 个月那档，弹出来说不符合试用条件。换成 1 个月，提示变成：

> 您不符合免费试用条件，尽管如此，您仍能订阅

后面接的是一个"知道了"按钮。我没点订阅，价格是 $199.99，卡里只有 3 美元，我也不想知道会发生什么。

后来换了一个号，用同一个脚本、同样的 `eft-1mo`，这次弹出了正常的试用确认框，点确认，成功了。

这两个号到底差在哪，我没查实。我的猜测是第一个号没有付款方式，Google 要用卡来托底试用结束后的扣款。但这只是猜测。20x 的 12 个月在第二个号上也没来得及试，所以到底 12 个月能不能开，我现在不知道。

我还写了个脚本想回查订阅状态，没读出结果，最后只能以 Play 的弹窗和手动确认为准。

## 0x07 开完之后

一个月后它会按 $199.99 续费。我的卡里放着 3 美元，能不能扣成功我不想赌。到期之前要记得去取消。

下次有新号再试 12 个月那档，试完回来补这篇。

---

*脚本里涉及的账号、卡号和令牌都没放进文章。*
