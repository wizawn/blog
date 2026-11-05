---
title: "Google AI Pro 两年“零成本”脚本分析"
date: 2026-11-04T22:00:00+08:00
draft: false
weight: 1
categories: ["安全研究", "技术分析"]
tags: ["Google One", "Google Play", "Playwright", "源码分析", "支付安全", "Offer Token"]
description: "Ngbm 请求改写、Google Play 结账弹窗、代理桥接，以及源码中几处影响订阅结果判断的细节。"
image: "/blog-cover-default.jpg"
lastmod: 2026-11-04T23:51:15+08:00
---

{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

## 0x00 这东西是什么

拿到一份打包好的工具：`Google_AI_Pro_2Year_ZeroCost_Auto`。

工具用 Playwright 操作 Google One 的结账流程，分三次换入作者标作 12、6、6 个月的优惠，最后取消续订。名字里的“两年”就是这么来的。

我主要看了 `automation_engine.py`。1794 行，前面是一段注入页面的 JavaScript，后面负责登录、找弹窗、绑卡、点击订阅和读取结果。改请求的地方不算长，处理页面状态占了大半。

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

两个 bat 文件，一个装依赖并启动，一个直接启动。依赖用的清华镜像源，README 写的是 Windows 10/11、Python 3.10 以上和系统 Chrome。服务跑在 `127.0.0.1:8765`，本地访问。

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

批量任务是排队执行的，一个账号结束，等两秒，再跑下一个。实际浏览器操作在 `automation_engine.py` 里。

## 0x02 HOOK_JS：Ngbm 请求拦截器

`HOOK_JS` 大约 150 行，通过 `context.add_init_script` 注入。它先检查页面主机名，再接管 XHR 发送和几处 iframe URL 设置。

它做了四件事：

### 第一件：劫持 XMLHttpRequest.send

脚本针对的是带有 `Ngbm` 调用的 XHR 请求。body 中的 `f.req` 解码后是一层套一层的 JSON，里面放着商品、Offer Token 和订阅参数。

HOOK_JS 重写了 `XMLHttpRequest.prototype.send`，先检查 body 是不是包含 `Ngbm` 的字符串，再交给 `rewriteFreq` 解析。`patchTargetNode` 负责替换里面的商品列表和订阅参数，代码兼容了两种数组形状。

```javascript
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(body) {
    if (typeof body === 'string' && body.includes('Ngbm')) {
        body = rewriteFreq(body);
    }
    return origSend.call(this, body);
};
```

`rewriteFreq` 的异常处理很短，解析失败就返回原 body，继续发请求。Hook 没改成功时，浏览器也不会因此停下来。

### 第二件：劫持 iframe src 设置

Google One 的结账弹窗是通过 iframe 加载 `eacquire/multiline` 这个 URL 实现的。这个 URL 的 query string 里有一个 `ear` 参数，也是一个 JSON 数组，结构和 Ngbm payload 类似，包含了商品列表和订阅模式。

这里一共挂了三处钩子，Trusted Types 那一处只在接口存在时安装：

1. `HTMLIFrameElement.prototype.src` 的 setter — 通过 `Object.defineProperty` 重写
2. `Element.prototype.setAttribute` — 拦截对 iframe src 属性的设置
3. `TrustedTypePolicy.prototype.createScriptURL` — 拦截 Trusted Types 策略下的 URL 创建

`rewriteUrl` 解析 URL 中的 `ear`，修改商品信息和订阅参数。除了外层的商品项，它还会解开 `ear[4][0]` 里的 base64，把内层那份商品信息一起改掉。`ear[24]` 被清空了，字段含义在这份代码里没有说明。

```javascript
function rewriteUrl(val) {
    const s = String(val || '');
    if (!s.includes('/eacquire/multiline') || !currentTest) return val;
    // 中间省略 ear 的解析及参数替换
    ear[24] = null;
    u.searchParams.set('ear', JSON.stringify(ear));
    return u.toString();
}
```

### 第三件：捕获当前订阅 ID

替换过程中，Hook 会把原始请求中的订阅值存进 `window.__capturedSubId`。Python 端没有提前找到 ID 时，后续参数有机会沿用这里捕获的值。

### 第四件：通过 window.__setDirectTest 动态切换注入配置

HOOK_JS 暴露了一个 `window.__setDirectTest(config)` 方法。Python 在几次订阅操作之间传入不同的 Token 和模式参数，不用每次重装整段 Hook。

## 0x03 写死的 Offer Token

代码开头是一组固定 Token，下面只保留变量名。注释按作者的命名和步骤日志标注：

```python
TOK_PRO5TB_12M   = "<省略>"  # 12 个月
TOK_PRO5TB_6M    = "<省略>"  # 日志中标作 Pixel 6 个月
TOK_PRO5TB_6M_2  = "<省略>"  # 备用值
TOK_PRO5TB_6M_SS = "<省略>"  # 日志中标作 S25 6 个月
YT_FREE_TOK     = "<省略>"  # YouTube Premium 试用
```

这些值直接跟着程序发走，包里没有附活动规则或获取记录。Pixel、S25 和时长目前只能按作者的标注理解。

代码里还有一个前缀常量：

```python
PREFIX = "subs:com.google.android.apps.subscriptions.red:"
```

这是 Google One 订阅商品的前缀。程序用它拼出 `g1.2tb.ai.subs_variant` 和 `g1.youtube_premium_individual_add_on` 两个商品。前者的名字含 `2tb`，常量却叫 `PRO5TB`，类名又叫 `GoogleUltraAutomator`，命名混在了一起。`target_plan` 虽然传进构造函数，后面的套餐选择并没用到它。

每次配置都附带 YouTube Premium 那一项，作者没解释这样搭配的原因。

## 0x04 五步流水线

整个自动化流程分五步，每一步都是 `GoogleUltraAutomator` 类里的一个 async 方法。

### Step 1: 登录 Google 账号

`step1_login` 打开登录页，处理账号选择，再进入邮箱、密码和后续验证。

账号选择器在 `step1_login` 里，其余不少中间页交给 `pass_reauth_on_page`：

- 邮箱、密码输入页
- 辅助邮箱验证（`challenge/kpe`）
- Google Authenticator 选择页及 TOTP 输入框
- “试试其他方式”一类验证方式切换
- gds.google.com 辅助信息提示页
- “以后再说”“跳过”“不用了”等弹窗

这个方法最多跑 16 轮，每轮看 URL 和 body 文本，再执行对应操作。reCAPTCHA 只写了点击复选框，图片题没有处理；遇到 `signin/rejected` 会直接返回。外层最后仍会打“登录完成”的日志，这里没有一个明确的登录成功结果传回来。

2FA 动态码生成是脚本自己实现的，没有依赖任何第三方库。`get_totp` 函数手写了标准的 TOTP 算法：base32 解码密钥 → 当前时间戳除以 30 得到计数器 → HMAC-SHA1 → 动态截断 → 取模得到 6 位数字。在填入前还会检查当前 TOTP 周期剩余时间，如果不超过 3 秒就等下一个周期，避免填进去的码过期。

### Step 2: 第一组订阅配置

`step2_layer1_12m` 先读取 Play 订阅页。整页出现 `2028`，或者命中写死的 `2027年10月`、`Oct 2027` 等日期文字，就跳过这一步。页面上出现“重新订阅”时，还会尝试把订阅恢复。它没有先把文字定位到某个套餐。

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

`full_items` 是商品列表，里面放了主套餐和 YouTube 附加项，每项最后带一个 Token 数组。这里保留了源码中的数组结构，`21` 的具体协议含义没有定义。

`ear8` 的第二项设成了 `5`，有订阅 ID 时一起传入。作者把它用于后续叠加，但源码没有提供这组内部字段的协议定义，也没有与 Android Billing 枚举的对应关系。

### Step 3 & Step 4: 二层和三层叠加

`step3_layer2_6mss` 和 `step4_layer3_6m` 继续调用同一个订阅函数，换用另外两组 Token：

- Step 3 用 `TOK_PRO5TB_6M_SS`
- Step 4 先用 `TOK_PRO5TB_6M`，失败后换 `TOK_PRO5TB_6M_2`

跳过条件也跟着换成了几组 2028 年的月份。这里没有根据开始日期计算十二个月、十八个月或两年，用的都是固定日期。三层分别停 45、45、40 秒再继续；第三层最后只检查整页有没有 `2028`，没有比较目标订阅前后的日期。

### Step 5: 取消续订

`step5_cancel_and_verify` 先看自动取消开关。开启后，如果整页没有“已取消”“重新订阅”“取消日期”，就点第一个可见的“管理”，再尝试取消、选择原因和确认。

这几处都是全页查找，没有按 Google AI 的那条订阅定位。最后也没有再检查它是否真的变成了已取消。

截图之后，日期是从页面文字里读的，没有用 OCR：

```python
exp_str = m_date.group(1) if m_date else "已激活 (详见截图)"
```

日期正则同时接受“取消日期”和“续订日期”。没找到匹配，就填上面这句“已激活”，随后把任务标成 `completed`。

## 0x05 eacquire 弹窗轮询

`_poll_eacquire_modal` 这一段很长，主要是在等结账弹窗，以及处理它加载过程里的各种中间页面。

**先等弹窗。** 点击 Google One 的按钮后，脚本遍历 frame，查找 URL 里含 `eacquire` 的那一个。循环从 60 次起步，但点过某些过渡按钮还会补回次数，内部又有等待，所以总耗时并不是 60 秒。

**碰到绑卡页就填卡。** 这段按输入框位置填写，使用 `press_sequentially` 逐字输入。它会扫描 frame，找到至少四个可见 input 就开始处理，没先确认这些字段属于哪张表单。持卡人为空时才填，邮编也有输入框数量条件。保存后会等 `instrumentmanager` 消失，但等满次数仍没消失，也会设 `inline_card_saved = True`。

邮编默认值是 `97201`。代码没有计算税额，前端把这里叫“免税绑卡”只是界面文案。

**再处理过渡按钮。** “继续订阅”“换用此方案”“前往结账”这些文字都在匹配列表里。找到可见按钮后，程序直接点击。

可见性判断不只看 `display`，还看了 `opacity`、`aria-hidden`、`pointerEvents`，并用 `elementFromPoint` 检查遮挡。

## 0x06 点击“订阅”之后

`open_and_click_subscribe` 方法在弹窗加载完成后，先做一系列检查：

1. 按银行卡尾号尝试切换付款方式；找不到、切换失败时仍可能继续。
2. 在弹窗文字里找 `0.00`、`免费` 或 `Free`，没有就返回失败。这处判断后面单独看。
3. 点击“订阅”。先用普通 click，再尝试强制点击，最后才走 JS 事件。

点击之后进入最多 35 轮的等待循环，处理可能出现的各种验证：

- **CVC 安全码验证** — 有时 Google Play 会要求重新输入 CVC，脚本自动从配置中取出 CVC 填入
- **Google 账号密码二次验证** — 结账时可能触发身份验证，脚本自动填入密码
- **2FA TOTP 验证** — 同上，自动生成并填入动态码
- **「验证是您本人」按钮** — 没有输入框的情况下，直接点击验证按钮

循环主要读取当前页面的 frame，也会对最后一个弹出的页面调用认证处理。成功词列表里除了“已订阅”，还有这些：

```python
"Google Play 积分",
"备用付款方式",
"以后再说",
"知道了",
"Got it",
```

命中一个就可能返回 `True`。而错误词的检查排在后面，同一段文字同时命中两边时，会先走成功分支。弹窗关闭后的另一处判断还接受 `Welcome`。这些普通提示很容易被算成订阅成功。

## 0x07 代理隧道桥接

`LocalHttpProxyAuthBridge` 是一个本地 HTTP 代理桥。Chrome 连接本机端口，它再向上游转发请求或建立 CONNECT 隧道，并加上 `Proxy-Authorization: Basic ...`，省去 Chrome 里的代理认证弹窗。

本机端口按调试端口加 200 算，默认情况下是 `9520`。这里实现的是 HTTP 代理转发，没有 SOCKS5 握手，也没有到 HTTPS 上游的 TLS 连接。解析器虽然接受 `socks5://`，带用户名时却同样送进这个 HTTP 桥。

这个桥接器还做了几件事：

1. 屏蔽 `_BLOCKED_PROXY_HOSTS` 中的域名，里面既有 Chrome 后台连接，也有 Safe Browsing 相关地址。
2. 检查 CONNECT 返回状态，不是 200 时进入重试。
3. 失败后尝试轮换用户名里的会话标识。用户名里要有 `-session-` 才会实际改值，换不换 IP 由上游决定。

代理模板支持 `{country}` / `{COUNTRY}` / `{session}` / `{SESSION}` 四个占位符。另有一个 FloppyData 分支：proxy 字符串长度至少 24、又不含 `:` 和 `@` 时，就按 API Key 请求代理资料。

## 0x08 账号导入与格式兼容

`import_accounts` 支持 `----`、`—`、`|`、`/`、制表符、逗号和空格。它按优先级选一种分隔符，再按固定位置取邮箱、密码，其余字段才做识别。

辅助字段大致按下面的顺序判断：

- 排除带协议头的代理后，含 `@` 的当作辅助邮箱
- URL 或匹配 IP、端口格式的当作代理
- 符合 Base32 形状的当作 TOTP 密钥

密码里带分隔符会被拆开，空字段被过滤后也会改变位置。斜杠分隔没有避开 `socks5://`；带 `@` 的部分代理写法还会先被认成邮箱。去重则把整个邮箱的点都删掉了，连域名也一起处理，并不限于 Gmail 用户名。自动编号取当前列表长度加一，删过账号后可能撞号。

## 0x09 Windows 下手动打开浏览器

`_launch_on_interactive_desktop` 用 `ctypes` 调用 `CreateProcessW`，把 `STARTUPINFOW.lpDesktop` 设为 `winsta0\default`。

这是手动“打开浏览器”按钮用的入口。它指定当前会话里的桌面，没有切换 Windows 用户会话。自动流水线仍用 `subprocess.Popen` 启动 Chrome。

`wShowWindow = 3` 对应 `SW_MAXIMIZE`，请求最大化窗口。

## 0x0A Chrome 独立目录

每个账号按邮箱生成 Chrome 用户数据目录，形式是 `profiles/profile_...`，特殊字符会替换成下划线。Cookie、localStorage 等浏览器数据因此分开保存，后续能继续使用已有 profile。

目录名没有额外的重名检查，登录状态是否还有效也要看 Google。

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
--webrtc-ip-handling-policy=disable_non_proxied_udp  # 限制非代理 UDP
--enforce-webrtc-ip-permission-check               # 配套的 WebRTC 权限检查
```

末尾两项是 WebRTC 的代理相关设置，脚本没有接着检查它们在当前 Chrome 上的实际效果。

然后通过 `--remote-debugging-port` 暴露 Chrome DevTools Protocol 端口，Playwright 通过 `connect_over_cdp` 连接上去操控。

## 0x0B 订阅 ID 动态提取

`get_current_sub_id` 从 Google One 页面的 HTML 里找 24 位小写字符串，填进订阅参数。

提取逻辑有三层 fallback：

1. 正则匹配 `[a-z]{24}\.AO-` 格式
2. 正则匹配 `[a-z]{24}\.AO-J1O` 格式
3. 从 `AF_initDataCallback` 的 script block 中提取含 `subscriptions.red` 或 `g1.` 的数据块里的 24 位字符串

找到多个候选时，部分分支先转成 `set`，再拿第一个，没有按套餐核对。找不到就返回 `None`，之后依靠 Hook 在符合结构的请求中保留原订阅值。

## 0x0C 零消费检查

这里最需要仔细看的就是这个条件：

```python
if "ultra" not in step_tag.lower() and "0.00" not in clean_txt and "免费" not in clean_txt and "Free" not in clean_txt:
    self.last_subscribe_error = f"零消费保护拦截：弹窗未显示 0.00 免费试用 ({clean_txt[:180]})"
    return False
```

`clean_txt` 是整段弹窗文字。`10.00` 里也有 `0.00`；订单中某个附加项写着免费，也能让这条判断放行。这里并没读取应付总额或币种。函数另有预期关键词参数，不过三层订阅都没传。前面检查卡号、有效期和 CVC 是否填写，也只是在检查表单完整性。

## 0x0D 配置文件和日志

`config.json` 直接存卡信息、账号密码、辅助邮箱和 TOTP 密钥，`/api/state` 又把这些字段发回控制台。程序只监听本机，但没有自己的登录鉴权。

认证过程中还有几条日志直接写出了 CVC 和动态验证码。

前端的日志显示做了 HTML 转义，账号表格却直接把邮箱、密码、编号等拼进 `innerHTML`，部分字段还进入内联 `onclick`。引号可能把按钮的 `onclick` 拼坏，HTML 标签也会被浏览器解析。

## 0x0E IP 环境检测

`verify_ip_environment` 先访问 `ipinfo.io/json`，失败再试 `ipwho.is`，把 IP、国家、城市和运营商显示出来。

查询出错时，有代理桥就尝试轮换会话。两个站都查不到结果，也会继续执行。

这里没有将查询到的国家和 `target_region` 对比，也没有判断出口是不是住宅 IP。日志中的“检测通过”是在取到查询结果后写的。

## 0x0F 重试和停止

重试分散在几个地方：

- `safe_goto` 总共尝试四次；还有下一次尝试且使用了代理桥时，会轮换会话
- 第一、二层订阅失败后，等三秒再试一次
- 第三层换用备用 Token
- 登录流程最多跑三轮

需要留意的是，“订单仍在处理中”也在错误词列表里，外层收到失败后仍可能再次操作订阅。前面的步骤如果抛错，则直接退出，不会补做最后的取消续订。停止按钮也只是设置标志，要等执行器下次检查才能停；点单号停止还会一起停掉后续批量队列。

单号与批量入口之间没有统一排除重复任务，运行记录可能互相覆盖。启动前还会按调试端口找 PID 并强制结束，没有核对进程归属。

---

原版工具开源仓库：[https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto](https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto)
