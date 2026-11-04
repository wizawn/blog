---
title: "Google AI Pro (5 TB) 零成本两年全自动化深度拆解 — 从 Offer Token 注入到三层 Mode 5 叠加的完整技术链路"
date: 2026-11-04T22:00:00+08:00
draft: false
weight: 1
categories: ["安全研究", "漏洞分析"]
tags: ["Google One", "Google Play", "Playwright", "深度分析", "支付安全", "Offer Token", "订阅漏洞"]
description: "完整拆解一套基于 Playwright CDP + Google Play Ngbm 拦截器的全自动化脚本，通过 XHR/iframe 请求劫持将 Google One 结账弹窗的 Offer Token 替换为三层免费试用 Token（12M + 6M + 6M），配合 Mode 5 顺延叠加机制，实现单账号 24 个月 Google AI Pro (5 TB) 零成本订阅。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

## 0x00 这东西是什么

前几天拿到一份打包好的工具，名字很直白：`Google_AI_Pro_2Year_ZeroCost_Auto`。

说人话就是：用一张外币信用卡（Visa / Mastercard），通过脚本自动化操作 Google One 的结账流程，把 Google AI Pro (5 TB) 的订阅时长叠到两年，全程不花一分钱。叠完之后自动去 Google Play 取消续订，锁死到期日，卡上不会产生任何扣款。

听起来像是天方夜谭，但把代码逐行读完之后，发现它的实现逻辑其实非常清晰——本质上就是利用 Google Play 结账弹窗对客户端提交的 Offer Token 缺乏服务端校验这一点，通过 JavaScript 注入把正常的付费订阅请求篡改成免费试用订阅请求。然后重复三次，12 + 6 + 6 = 24 个月。

这篇文章会把这套工具从头到尾拆干净。不是使用教程，是技术分析。

## 0x01 整体架构：一个本地 Web 控制台

先看文件结构：

```
├── app.py                  # FastAPI 后端，提供 Web API 和控制台页面
├── automation_engine.py    # 核心自动化引擎，Playwright + Chrome CDP
├── config.json             # 配置文件：卡信息、账号列表、代理模板
├── requirements.txt        # 依赖：fastapi, uvicorn, playwright, pydantic
├── templates/
│   └── index.html          # 控制台前端，暗色主题的单页应用
├── 1_首次运行_安装依赖并启动.bat
└── 2_启动控制台.bat
```

两个 bat 文件很简单，一个装依赖一个启动服务。依赖用的清华镜像源，说明面向的是国内用户。服务跑在 `127.0.0.1:8765`，本地访问。

`app.py` 是一个标准的 FastAPI 应用，提供了这些 API：

- `POST /api/config` — 保存全局配置（地区、卡信息、代理模板）
- `POST /api/accounts/import` — 批量导入 Google 账号
- `POST /api/run/single` — 单账号执行
- `POST /api/run/batch` — 批量队列执行
- `POST /api/stop` — 停止任务
- `POST /api/open_browser` — 为指定账号手动打开独立 Chrome 窗口
- `POST /api/proxy/test` — 测试代理连通性
- `GET /api/state` — 轮询当前状态（前端每 1.5 秒调一次）

前端是一个纯静态的单页应用，没用任何框架，原生 JS + CSS 变量做的暗色主题。左边填卡信息和代理，右边批量粘贴账号，下面是账号队列表格和实时日志终端。每 1.5 秒 fetch 一次 `/api/state` 刷新界面。

这部分没什么特别的，标准的前后端分离控制台。真正有意思的全在 `automation_engine.py` 里。

## 0x02 核心武器：HOOK_JS — Ngbm 请求拦截器

整个工具的灵魂是一段大约 190 行的 JavaScript，代码里叫 `HOOK_JS`。这段 JS 会在页面加载时注入到 `one.google.com`，作用是拦截并篡改 Google One 结账流程中的所有关键请求。

它做了四件事：

### 第一件：劫持 XMLHttpRequest.send

Google One 的结账弹窗在提交订阅请求时，会通过 XHR 发送一个 POST 请求，body 里有一个 `f.req` 参数，这个参数是一个嵌套的 JSON 数组。数组里有一个叫 `Ngbm` 的 RPC 调用，它携带了当前订阅的具体内容——包括要订阅哪个套餐、用哪个 Offer Token、以什么模式（Mode）执行。

HOOK_JS 重写了 `XMLHttpRequest.prototype.send`，在每次发送时检查 body 是否包含 `Ngbm`。如果包含，就调用 `rewriteFreq` 函数，解析出 `f.req` 的 JSON 结构，找到 `Ngbm` 调用的 payload，然后调用 `patchTargetNode` 把里面的 `node[12]`（商品列表）和 `node[7]`（订阅模式参数，即 ear8）替换成脚本预设的值。

```javascript
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(body) {
    if (typeof body === 'string' && body.includes('Ngbm')) {
        body = rewriteFreq(body);
    }
    return origSend.call(this, body);
};
```

这就是核心中的核心。Google 的前端把要买什么东西、用什么优惠券、以什么模式升级这些信息全部放在客户端构建的请求参数里发给后端，而后端——至少在 Offer Token 校验这个环节上——并没有做严格的来源验证。

### 第二件：劫持 iframe src 设置

Google One 的结账弹窗是通过 iframe 加载 `eacquire/multiline` 这个 URL 实现的。这个 URL 的 query string 里有一个 `ear` 参数，也是一个 JSON 数组，结构和 Ngbm payload 类似，包含了商品列表和订阅模式。

HOOK_JS 同时拦截了三个设置 iframe src 的入口：

1. `HTMLIFrameElement.prototype.src` 的 setter — 通过 `Object.defineProperty` 重写
2. `Element.prototype.setAttribute` — 拦截对 iframe src 属性的设置
3. `TrustedTypePolicy.prototype.createScriptURL` — 拦截 Trusted Types 策略下的 URL 创建

每当有 URL 包含 `/eacquire/multiline` 时，`rewriteUrl` 函数会解析 URL 中的 `ear` 参数，把 `ear[13]`（商品列表）、`ear[4]`（base64 编码的内层参数，解码后替换 `inner4[8]`）和 `ear[8]`（订阅模式参数）全部替换成脚本预设的值。同时清空 `ear[24]`（疑似防重放或签名字段）。

```javascript
function rewriteUrl(val) {
    const s = String(val || '');
    if (!s.includes('/eacquire/multiline') || !currentTest) return val;
    // ... 解析 ear 参数，替换商品列表和模式
    ear[24] = null;  // 清空签名/防重放字段
    u.searchParams.set('ear', JSON.stringify(ear));
    return u.toString();
}
```

### 第三件：捕获当前订阅 ID

在替换过程中，HOOK_JS 会从原始请求中提取 `node[7][5][0]` 或 `ear[8][5][0]`——这是当前账号已有订阅的 24 位订阅 ID。这个 ID 很重要，因为叠加操作（Mode 5）需要知道是在哪个已有订阅上叠加新的免费时长。脚本把它存在 `window.__capturedSubId` 里，后续构建 ear8 参数时会用到。

### 第四件：通过 window.__setDirectTest 动态切换注入配置

HOOK_JS 不是写死要注入什么内容的。它暴露了一个 `window.__setDirectTest(config)` 方法，Python 端在每一步执行前都会调用这个方法，传入当前步骤要使用的 Offer Token 和模式参数。这样同一段 JS 就能在五个步骤中注入不同的内容。

## 0x03 Offer Token：免费试用的钥匙

代码开头定义了一组硬编码的 Token 常量：

```python
TOK_PRO5TB_12M   = "AVbCH/cspB8VdqKJ+ax/uPxUFAVu..."   # 12 个月免费 Pro 5TB
TOK_PRO5TB_6M    = "AVbCH/fUON3w8hpfeutprA3BMQwr..."   # 6 个月免费 (Pixel 活动)
TOK_PRO5TB_6M_2  = "AVbCH/cJ5SeHgkVRt+bdcrapx/aL..."   # 6 个月免费 (备用 Token)
TOK_PRO5TB_6M_SS = "AVbCH/cgl4zvPT2Lqw95Gn+RYAJI..."   # 6 个月免费 (S25 活动)
YT_FREE_TOK      = "AVbCH/eW4Nfp8KBl0zlm7x9PhaiC..."   # YouTube Premium 1 个月试用
```

这些 Token 是什么？它们是 Google One / Google Play 促销活动的 Offer Token，通常绑定在特定的设备购买（比如买了 Pixel 手机送 6 个月 Google One）或特定的促销活动（比如三星 S25 购机活动）上。

正常情况下，这些 Token 只有在满足特定条件（比如设备型号验证、首次激活验证）时才会出现在结账流程中。但 HOOK_JS 做的事情就是：不管你有没有资格，直接把这些 Token 塞进结账请求里。而 Google Play 的后端在处理这些 Token 时，似乎并没有严格校验请求来源是否真的是一台 Pixel 手机或一台 S25。

代码里还有一个前缀常量：

```python
PREFIX = "subs:com.google.android.apps.subscriptions.red:"
```

这是 Google One 订阅商品的完整包名前缀，用来构建商品 ID。比如 `PREFIX + "g1.2tb.ai.subs_variant"` 就是 Google AI Pro (5 TB) 的订阅商品标识，`PREFIX + "g1.youtube_premium_individual_add_on"` 就是 YouTube Premium 附加订阅。

每层叠加时，脚本都会同时塞入一个 YouTube Premium 1 个月试用的 Token。这不是为了白嫖 YouTube——而是因为 Google Play 的结账流程似乎更容易接受「套餐 + 附加项」这种组合下单的形式来触发免费试用处理逻辑。

## 0x04 五步流水线：从登录到锁死

整个自动化流程分五步，每一步都是 `GoogleUltraAutomator` 类里的一个 async 方法。

### Step 1: 登录 Google 账号

`step1_login` 做的事情说起来很简单：打开 Google 登录页，输入邮箱密码，过验证。但实际实现相当复杂，因为 Google 的登录流程有无数种中间状态需要处理。

`pass_reauth_on_page` 这个方法处理了以下所有情况：

- 账号选择器（多账号登录时选择正确的账号）
- 邮箱输入框 + 下一步
- 密码输入框 + 下一步
- 辅助邮箱验证（`challenge/kpe` 页面，自动填入预设的辅助邮箱）
- 2FA TOTP 验证（自动生成并填入 6 位动态码）
- Google Authenticator 选择页（从多种验证方式中选择身份验证器）
- 其他验证方式切换（遇到二维码/推送验证时，点击「试试其他方式」切换到 TOTP）
- reCAPTCHA 人机验证（自动点击复选框）
- 新设备安全拦截（`signin/rejected`）
- gds.google.com 辅助信息提示页（取消/跳过）
- 各种弹窗对话框（以后再说、跳过、取消、不用了）

这个方法内部是一个最多跑 16 轮的循环，每轮检查当前页面的 URL 和 body 文本，匹配到哪种状态就执行对应的操作。写法很暴力但很有效——把 Google 登录流程的所有可能分支都穷举了一遍。

2FA 动态码生成是脚本自己实现的，没有依赖任何第三方库。`get_totp` 函数手写了标准的 TOTP 算法：base32 解码密钥 → 当前时间戳除以 30 得到计数器 → HMAC-SHA1 → 动态截断 → 取模得到 6 位数字。在填入前还会检查当前 TOTP 周期剩余时间，如果不到 3 秒就等下一个周期，避免填进去的码过期。

### Step 2: 首层 12 个月免费叠加

`step2_layer1_12m` 是第一层叠加。在执行之前，脚本会先去 Google Play 订阅页检查当前账号的状态——如果已经有 2028 年的到期日，说明之前跑过了，直接跳过。如果当前订阅处于「已取消」状态，先调 `ensure_subscription_active` 点击「重新订阅」恢复活跃状态。

然后构建注入配置：

```python
cfg_l1 = {
    "name": "Step2_Layer1_12M_YTFree_ZeroCost",
    "full_items": [
        [[PREFIX + "g1.2tb.ai.subs_variant", 21], None, None, None, 1, [TOK_PRO5TB_12M]],
        [[PREFIX + "g1.youtube_premium_individual_add_on", 21], None, None, None, 1, [YT_FREE_TOK]],
    ],
    "ear8": [None, 5, None, None, None, [sub_id]] if sub_id else None,
}
```

这个 `full_items` 数组就是要塞进结账请求的商品列表。每个商品是一个嵌套数组，第一个元素是 `[商品ID, 21]`（21 看起来是某种商品类型标识），最后一个元素是 Offer Token 数组。

`ear8` 里的 `5` 是关键——这就是 **Mode 5**。在 Google Play Billing 的语境里，Mode 5 对应 `CHARGE_FULL_PRICE`，但在 Google One 的内部实现中，Mode 5 搭配免费试用 Token 使用时的行为是：**在当前订阅的到期日之后顺延叠加新的免费时长**，而不是从当天开始计算。

这意味着如果你当前订阅到 2026 年 10 月，叠一个 12 个月免费，到期日就变成 2027 年 10 月。再叠 6 个月，变成 2028 年 4 月。再叠 6 个月，2028 年 10 月。三层叠完，两年。

### Step 3 & Step 4: 二层和三层叠加

`step3_layer2_6mss` 和 `step4_layer3_6m` 的逻辑和 Step 2 完全一样，区别只是使用不同的 Offer Token：

- Step 3 用 `TOK_PRO5TB_6M_SS`（S25 活动的 6 个月免费 Token）
- Step 4 用 `TOK_PRO5TB_6M`（Pixel 活动的 6 个月免费 Token），如果失败会退而使用备用 Token `TOK_PRO5TB_6M_2`

每层叠加完成后都会等待 40-45 秒，让 Google Play 后台完成结算同步。Step 4 完成后还会额外去 Play 订阅页验证到期日是否确实推进到了 2028 年。

### Step 5: 取消续订，锁死到期日

`step5_cancel_and_verify` 最后收尾。打开 Google Play 订阅管理页，点击「管理」→「取消订阅」→ 选择取消原因（选最后一个「拒绝回答」）→ 点击「继续」→ 点击最终的「取消订阅」确认按钮。

取消之后，订阅状态变成「已取消，到期日 2028 年 10 月 xx 日」。到期日不会因为取消而提前，两年内可以正常使用 Google AI Pro 的所有功能，到期后自然失效，卡上不会有任何后续扣款。

最后截一张 Play 订阅页的截图作为凭证，从截图里解析到期日更新到状态面板。

## 0x05 eacquire 弹窗轮询：最复杂的 60 秒

整个自动化流程中最难写的部分不是 HOOK_JS，而是 `_poll_eacquire_modal`——等待并处理 Google Play 结账弹窗的轮询方法。

这个方法要处理的情况之多令人发指：

**首先是弹窗出现前的等待。** Google One 页面上点击「开始使用」或「获取优惠」按钮后，Google Play 的 eacquire iframe 弹窗不是马上出现的。脚本每秒检查一次所有 frame，看有没有 URL 包含 `eacquire` 的 iframe。最多等 60 次。

**然后是内联绑卡。** 如果弹窗出来了但内容是「添加付款方式」或「首先添加付款方式」，说明这个 Google 账号还没绑过支付方式。脚本会自动点击「添加信用卡或借记卡」，等待 Google 的 instrumentmanager iframe 加载出来，然后找到里面的输入框，依次用 `press_sequentially`（模拟逐字输入，带 35ms 延迟）填入卡号、有效期、CVC、持卡人姓名、邮编，最后点击「保存卡」。

这里有个细节：邮编默认填 `97201`，这是美国俄勒冈州波特兰的邮编。俄勒冈是美国的免税州，没有销售税。这就是为什么工具名称里有「免税」两个字——通过使用免税州的账单地址，确保即使 Google 试图收费，也不会有额外的税费。当然，因为全程都是 $0.00 的免费试用，税不税的其实无所谓，但万一中间哪步出了问题，这也算一层保护。

**接着是各种中间确认按钮。** 在弹窗加载过程中，Google 可能会弹出「运作方式」说明页（需要点击「继续订阅」）、「换用此方案」确认按钮、「前往结账」按钮等等。脚本在 `_poll_eacquire_modal` 的每次循环中都会用一个巨大的 `page.evaluate` 扫描页面上所有可见按钮，如果文本匹配预设的关键字列表就自动点击。

这段 JavaScript 还做了很认真的可见性检查——不只是检查 `display: none`，还检查了 `opacity`、`aria-hidden`、`pointerEvents`、以及用 `elementFromPoint` 确认按钮确实是在最上层没有被遮挡。这种细节说明作者在实际调试中踩过不少坑。

## 0x06 点击「订阅」之后：CVC、密码、2FA 全自动

`open_and_click_subscribe` 方法在弹窗加载完成后，先做一系列检查：

1. **零消费保护** — 如果弹窗文本里不包含 `0.00`、`免费`、`Free` 中的任何一个，直接拒绝点击，中断流程。这是一个硬保护，防止因为 Token 失效或注入失败导致实际扣款。
2. **卡号校验** — 如果弹窗里显示的支付卡不是配置中卡号的后四位，自动点击切换到正确的卡。
3. **点击「订阅」按钮** — 先尝试 Playwright 的标准 click，如果失败（被遮挡、不可交互等）就退回到 JS 原生事件触发（依次 dispatch mousedown → mouseup → click 三个事件加一个 `.click()` 调用）。

点击之后进入最多 35 轮的等待循环，处理可能出现的各种验证：

- **CVC 安全码验证** — 有时 Google Play 会要求重新输入 CVC，脚本自动从配置中取出 CVC 填入
- **Google 账号密码二次验证** — 结账时可能触发身份验证，脚本自动填入密码
- **2FA TOTP 验证** — 同上，自动生成并填入动态码
- **「验证是您本人」按钮** — 没有输入框的情况下，直接点击验证按钮

每轮循环都会检查所有 frame（包括弹出的新页面和嵌套 iframe）的文本内容，寻找成功标志（「已订阅」「感谢您订阅」「Google Play 积分」）或失败标志（「购买失败」「付款遭拒」`[OR-xxx]` 错误码等）。

## 0x07 住宅代理隧道桥接

`LocalHttpProxyAuthBridge` 是一个轻量级的本地 HTTP/HTTPS CONNECT 代理桥接器。为什么需要它？因为 Chrome 的 `--proxy-server` 启动参数不支持带用户名密码的代理认证。如果你的代理需要 Basic Auth，Chrome 会弹一个认证对话框，自动化脚本没法处理。

所以脚本在本地起了一个代理桥接服务。Chrome 连接到 `127.0.0.1:9520`（不需要认证），桥接服务再转发到真正的上游代理（带上认证头）。

这个桥接器还做了几件事：

1. **过滤 Chrome 后台噪音流量** — `_BLOCKED_PROXY_HOSTS` 列表里有 `mtalk.google.com`、`safebrowsing.googleapis.com` 等 Chrome 的后台服务域名，直接返回 502，减少对代理流量的浪费。
2. **验证上游 CONNECT 响应** — 检查上游代理返回的 CONNECT 响应是否真的是 200，不是的话走重试。
3. **自动轮换住宅代理会话** — 如果连续 3 次连接失败，自动修改 session ID（在 username 里追加 `rN` 后缀）触发住宅代理提供商分配新的出口 IP。

代理模板支持 `{country}` / `{COUNTRY}` / `{session}` / `{SESSION}` 四个占位符，用于动态替换国家代码和会话标识。还有个特殊逻辑：如果 proxy 字段填的是一个 24+ 字符的纯字母数字字符串（没有 `:` 和 `@`），脚本会把它当作 FloppyData 的 API Key，自动调 FloppyData API 获取子用户凭证并构建代理 URL。

## 0x08 账号导入与格式兼容

`import_accounts` 是一个写得相当鲁棒的账号解析器。它支持的分隔符包括：`----`、`—`（中文破折号）、`|`、`/`（排除含 `http://` 的情况）、`\t`（制表符）、`,`（逗号）、空格。

对于每行解析出来的字段，脚本用以下规则识别各部分：

- 包含 `@` 的 → 邮箱（第二个含 `@` 的视为辅助邮箱）
- 以 `http://`、`https://`、`socks5://` 开头或匹配 `IP:端口` 格式的 → 代理地址
- 16+ 字符的 Base32 字符串（`[A-Za-z2-7]+=*`） → 2FA TOTP 密钥
- 其余按位置推断为密码

重复邮箱会更新已有记录而非新增。邮箱比较时忽略了 `.`（Gmail 的点号等价特性）。

## 0x09 Windows 桌面会话穿透

`_launch_on_interactive_desktop` 这个函数有点意思。它用 `ctypes` 直接调用 Windows API 的 `CreateProcessW`，把 `STARTUPINFOW.lpDesktop` 设为 `winsta0\default`。

这是为了解决一个特定场景：如果这个脚本运行在某些远程桌面或沙箱环境（比如 exebox）中的后台 session 里，直接 `subprocess.Popen` 启动的 Chrome 可能会跑在一个不可见的桌面上。通过显式指定 `winsta0\default`，确保 Chrome 窗口出现在用户实际看到的交互桌面上。

`wShowWindow = 3` 是 `SW_MAXIMIZE`，让 Chrome 一启动就最大化。

这个细节说明作者考虑到了批量跑号场景下的远程管理需求。

## 0x0A Chrome 独立环境隔离

每个账号有自己独立的 Chrome 用户数据目录：`profiles/profile_{email}`。这意味着：

- 不同账号之间的 Cookie、localStorage、IndexedDB 完全隔离
- 登录一次之后，下次跑可以跳过 Step 1 直接从 Step 2 开始
- 不会出现多账号串 session 的问题

启动 Chrome 时带了一堆参数：

```
--no-first-run               # 跳过首次运行向导
--no-default-browser-check    # 跳过默认浏览器检查
--disable-popup-blocking      # 禁用弹窗拦截（结账弹窗需要）
--disable-background-networking  # 减少后台网络请求
--disable-sync                # 禁用 Chrome 同步
--disable-component-update    # 禁用组件更新
--disable-domain-reliability  # 禁用域名可靠性追踪
--no-pings                    # 禁用 ping 追踪
--webrtc-ip-handling-policy=disable_non_proxied_udp  # 防止 WebRTC 泄露真实 IP
--enforce-webrtc-ip-permission-check               # 同上
```

`--webrtc-ip-handling-policy` 和 `--enforce-webrtc-ip-permission-check` 这两个参数是为了防止 WebRTC STUN 泄露真实 IP——即使走了代理，WebRTC 默认还是会通过 UDP 直接连接 STUN 服务器暴露真实出口 IP。

然后通过 `--remote-debugging-port` 暴露 Chrome DevTools Protocol 端口，Playwright 通过 `connect_over_cdp` 连接上去操控。

## 0x0B 订阅 ID 动态提取

`get_current_sub_id` 方法从 Google One 页面的 HTML 中提取当前账号的 24 位订阅 ID。这个 ID 在 Mode 5 叠加时是必须的——你得告诉 Google「我要在哪个已有订阅上面叠加」。

提取逻辑有三层 fallback：

1. 正则匹配 `[a-z]{24}\.AO-` 格式
2. 正则匹配 `[a-z]{24}\.AO-J1O` 格式
3. 从 `AF_initDataCallback` 的 script block 中提取含 `subscriptions.red` 或 `g1.` 的数据块里的 24 位字符串

如果三层都没匹配到，脚本不会中断——日志里会打一行「将由 Ngbm 拦截器动态保留原订阅 ID」。这是因为 HOOK_JS 在拦截请求时也会从原始请求中捕获订阅 ID 并存到 `window.__capturedSubId`，即使 Python 端没有提前拿到也没关系。

## 0x0C 零消费保护机制

整个工具有多层零消费保护：

1. **前端校验** — 执行前检查卡号、有效期、CVC 是否填写完整
2. **弹窗文本校验** — 点击「订阅」之前检查弹窗文本是否包含 `0.00` / `免费` / `Free`
3. **Step 跳过逻辑** — 每一步开始前都会检查 Google Play 订阅页的到期日，如果已经达到目标就自动跳过
4. **订阅状态恢复** — 如果发现订阅处于「已取消」状态，先恢复再叠加
5. **错误关键字检测** — 订阅后检查 `购买失败`、`付款遭拒`、`[OR-xxx]`、`insufficient funds` 等错误标志

第二层是最关键的。如果 HOOK_JS 注入失败（比如页面在注入之前就加载完了、或者 Google 更新了前端结构），弹窗里显示的会是正常的付费价格而不是 $0.00，这时脚本会直接中断，不会去点那个「订阅」按钮。

## 0x0D 卡付路线 vs PSC 路线

上面分析的这套工具走的是**卡付路线**（Credit Card 路线）。要说清楚的是，在 Google One 白嫖圈子里还有另一条路线叫 **PSC 路线**（Paysafecard 路线），这套工具里没有涉及，但有必要区别说明。

### 卡付路线（本工具）

- **支付工具**：Visa / Mastercard 外币信用卡（虚拟卡、实体卡均可）
- **核心原理**：通过 HOOK_JS 拦截 Google Play 结账弹窗的请求，注入免费试用 Offer Token + Mode 5 叠加
- **绑卡行为**：需要在 Google Play 中绑定一张银行卡（脚本自动内联绑卡），但全程不产生实际扣款
- **成本**：理论上 $0.00，卡不会被扣款。但需要一张有效的国际信用卡通过 Google 的卡片验证
- **风险**：如果 Token 失效或注入失败，有零消费保护兜底不会扣款；但绑卡这个行为本身会被 Google 记录，理论上存在账号关联风险
- **适用场景**：批量跑号，一张卡可以绑多个账号，全程自动化
- **技术门槛**：需要会跑 Python 脚本和处理代理环境

### PSC 路线（本工具未涉及）

- **支付工具**：Paysafecard（预付费充值卡），通过 Google Play 充值余额
- **核心原理**：同样利用 Offer Token 或促销活动，但支付方式走 Google Play 余额而非银行卡直付
- **绑卡行为**：不需要绑定银行卡，而是先用 Paysafecard PIN 码给 Google Play 账户充值余额
- **成本**：需要购买 Paysafecard 充值卡，面额通常是最小的 10 欧 / 10 美元。但如果操作得当，余额会因为 $0.00 试用而不被消耗，充值的余额可以留着或用于其他购买
- **风险**：不涉及真实银行卡信息，匿名性更强。Paysafecard 是一次性 PIN 码，不存在后续扣款风险
- **适用场景**：对隐私要求较高、不愿暴露银行卡信息的场景
- **技术门槛**：需要获取对应地区的 Paysafecard PIN 码（部分地区有购买限制）

两条路线的**底层漏洞是同一个**——Google Play 对客户端提交的 Offer Token 和订阅模式参数缺乏严格的服务端校验。区别只是用什么方式通过 Google 的支付方式验证环节。

卡付路线的优势是全程自动化、成本为零；劣势是需要暴露银行卡信息。PSC 路线的优势是匿名性强；劣势是需要花钱买 Paysafecard 且操作流程不那么容易全自动化。

## 0x0E IP 环境检测与网络指纹

`verify_ip_environment` 在正式操作 Google 之前会先访问 `ipinfo.io/json` 或 `ipwho.is/` 检测当前浏览器的出口 IP。这不只是为了给控制台显示一个 IP 标识——更重要的是确认代理确实生效了，出口 IP 确实在目标国家。

如果 IP 检测失败（代理不通），脚本会触发住宅代理会话轮换再试一次。连续失败则跳过检测继续执行，日志里打一条警告。

Google 对订阅操作有地区限制和风控。如果出口 IP 不在美区，或者 IP 质量太差（数据中心 IP、被标记的 IP），可能导致 Google Play 结账弹窗不出现、出现地区错误提示、或者触发额外的安全验证。这也是为什么代理模板支持住宅代理——住宅 IP 的质量通常比数据中心 IP 好得多。

## 0x0F 重试、容错与自愈

整个自动化引擎的容错设计贯穿始终：

- `safe_goto` — 页面导航最多重试 4 次，每次失败自动轮换住宅代理会话
- `open_and_click_subscribe` — 每层叠加如果第一次失败，等 3 秒后重试一次
- Step 4 有两个 Token 备选，第一个失败换第二个
- 弹窗轮询超时后如果检测到内联绑卡完成，会重新发起整个弹窗触发流程
- 每次操作前都检查 `stop_requested` 标志，用户随时可以中断
- 登录流程最多跑 3 轮完整的 login_round
- 所有 Playwright 操作都有 timeout，不会无限挂起

这些重试逻辑加上零消费保护，使得整个工具即使在网络不稳定或 Google 页面结构微调的情况下，也有相当高的成功率。

## 0x10 结语

把这套工具拆完，其实核心漏洞就一句话：**Google Play 结账流程中，客户端可以自由替换 Offer Token 和订阅模式参数，服务端没有做充分校验**。

脚本作者在此基础上做了大量的工程化工作：自动登录、自动过验证、自动绑卡、自动处理各种弹窗和中间状态、住宅代理隧道桥接、多账号队列管理、零消费保护……这些加起来才构成了一个「开箱即用」的全自动化工具。

从技术角度看，HOOK_JS 的 iframe src 拦截和 XHR body 篡改思路很干净，处理了 Trusted Types 策略下的 URL 创建这种边缘情况。eacquire 弹窗的轮询处理虽然代码量大，但考虑到 Google 结账流程的复杂性和不确定性，这种穷举式的状态机写法是合理的。

从防御角度看，Google 需要做的改进也很明确：Offer Token 应该绑定设备指纹或用户资格做服务端校验，而不是信任客户端提交的任意 Token；Mode 5 叠加应该检查叠加来源是否合法而不是无条件接受。

但截至本文写作时，这些 Token 似乎仍然有效。至于还能有效多久，就不好说了。

---

原版工具开源仓库：[https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto](https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto)
