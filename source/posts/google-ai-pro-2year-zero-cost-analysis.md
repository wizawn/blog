---
title: "扒开一份 Google AI Pro 两年零成本自动化脚本：Ngbm 改包、叠加逻辑与形同虚设的防扣费检查"
date: 2026-11-04T22:00:00+08:00
lastmod: 2026-11-04T23:51:15+08:00
draft: false
categories: ["安全研究", "技术分析"]
tags: ["Google One", "Google Play", "Playwright", "源码审计", "支付安全", "Offer Token"]
description: "审计公开仓库 Google_AI_Pro_2Year_ZeroCost_Auto 的 1794 行核心引擎：梳理 batchexecute Ngbm 请求改写、eacquire 结账弹窗轮询、本地代理桥接，以及源码里一抓一大把的状态误判、SOCKS5 协议乌龙与本地安全漏洞。"
weight: 10
---

前阵子拿到了一份打包好的开源工具 [`Google_AI_Pro_2Year_ZeroCost_Auto`](https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto)。名字起得相当唬人，号称全自动给账号叠出两年的 Google AI Pro"零成本"订阅。

把压缩包解开看，外围结构倒是很直白：一个监听本机 `127.0.0.1:8765` 的 FastAPI 小后台 `app.py`，配一张纯原生 JS 写的暗色单页控制台 `templates/index.html`（每隔 1.5 秒轮询一次 `GET /api/state` 刷队列表格和日志，左边填卡号和代理，右边粘账号），再加两个挂清华镜像源装包启动的 Windows `.bat` 批处理。`app.py` 里一共就摆了 8 个接口：`POST /api/config` 存卡与代理配置、`/api/accounts/import` 批量导号、`/api/run/single` 与 `/api/run/batch` 跑单号或排队批处理、`/api/stop` 停任务、`/api/open_browser` 手动拉起独立 Chrome 窗口、`/api/proxy/test` 测代理，外加那个高频轮询的 `/api/state`。

真正干活的逻辑全塞在 1794 行的 `automation_engine.py` 里。它的如意算盘是用 Playwright 走 CDP 接管系统 Chrome，趁网页发包时注入一段 JS 改写 Google One 的订阅参数，分三轮把作者攒下来的 12 个月、6 个月、6 个月三组促销 `Offer Token` 硬塞进去凑够 24 个月，最后自动点掉续订。好玩的是，通篇真正碰协议改包的 JS 满打满算也就 150 行，剩下的一千六百多行全在跟登录挑战、绑卡输入框和结账弹窗死磕；而且越往下细读源码越让人捏把汗，里面到处是子串硬匹配、静默放行和协议张冠李戴。顺手把它的实现细节和暗坑挨个记一笔。

## 0x00 `HOOK_JS`：半路改写 `Ngbm` 请求与 `eacquire` 结账弹窗

引擎拉起浏览器上下文后，第一件事是用 `context.add_init_script` 往 Google 相关域名里注入一段约 150 行的 `HOOK_JS`。这段脚本一共干了四件事：拦 XHR 发送、拦结账 iframe 的地址赋值、顺手抓下当前订阅 ID 存进 `window.__capturedSubId`，再挂出一个 `window.__setDirectTest(config)` 方法让外面的 Python 在三轮叠加之间随时切换要塞进去的 Token，不用每步重装整段脚本。

第一路拦截瞄准的是 `XMLHttpRequest.prototype.send`。Google One 网页端走的是谷歌自家前端常见的 `batchexecute` RPC 通道（`/_/SubscriptionsFrontendUi/data/batchexecute`），其中管订阅变更的 RPC ID 叫 `Ngbm`。表单里的 `f.req` 解开 URL 编码之后是一层套一层的嵌套 JSON 数组，里面装着目标商品 ID 和对应的 `Offer Token`：

```javascript
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function (body) {
    if (typeof body === "string" && body.includes("Ngbm")) {
        body = rewriteFreq(body);
    }
    return origSend.call(this, body);
};
```

`rewriteFreq` 解开嵌套数组后交给 `patchTargetNode`（兼容了两种数组形状）替换里面的商品列表和订阅参数。但它的异常处理写得极其心大：`try...catch` 一旦解析报错，不弹窗也不阻断，直接把没改成功的原始 `body` 原封不动发给谷歌服务器。

第二路拦截盯着 Google Play 的结账弹窗。点下升级按钮后，页面会通过 iframe 加载 `tokenized.play.google.com/eacquire/multiline`，URL 查询串里的 `ear` 参数同样是一大串 JSON 数组，而且在 `ear[4][0]` 里面还套了一层 Base64 编码的内层商品结构。为了防漏，作者一口气改写了 `HTMLIFrameElement.prototype.src` 的属性描述符、`Element.prototype.setAttribute`，甚至还去包了一层 `TrustedTypePolicy.prototype.createScriptURL`：

```javascript
function rewriteUrl(val) {
    const s = String(val || "");
    if (!s.includes("/eacquire/multiline") || !currentTest) return val;
    // 解开外层 ear 数组与 ear[4][0] 里的 Base64，同步替换商品列表与模式参数
    ear[24] = null;
    u.searchParams.set("ear", JSON.stringify(ear));
    return u.toString();
}
```

这里有个挺外行的细节：按浏览器的 Trusted Types 规范，`createScriptURL` 管的是 `<script src>` 和 Worker 脚本地址，`<iframe src>` 压根不走 `TrustedScriptURL`，那处钩子纯属作者看页面开了安全策略就闭着眼睛乱糊上去的。另外代码里顺手把 `ear[24]` 清成了 `null`，整份仓库也没留半句注释交代第 24 号位到底是什么字段。

## 0x01 写死的五串 Token、混乱的命名与五步叠加流水线

回到 Python 源码开头，迎面就是五串写死的促销 Token（这里隐去原始长串，只保留脚本里的变量名和日志备注）：

```python
PREFIX = "subs:com.google.android.apps.subscriptions.red:"

TOK_PRO5TB_12M   = "<已略>"  # 步骤日志标作 12 个月优惠
TOK_PRO5TB_6M_SS = "<已略>"  # 步骤日志标作 S25 6 个月优惠
TOK_PRO5TB_6M    = "<已略>"  # 步骤日志标作 Pixel 6 个月优惠
TOK_PRO5TB_6M_2  = "<已略>"  # 第三层失败时的备用值
YT_FREE_TOK      = "<已略>"  # YouTube Premium 试用附加项
```

光看这几行命名就能看出这工程拼得有多急：主类名叫 `GoogleUltraAutomator`，常量名叫 `PRO5TB`，结果用 `PREFIX` 拼出来的真实商品 ID 却是 `g1.2tb.ai.subs_variant`（每次还强行捆绑一个 `g1.youtube_premium_individual_add_on`），而构造函数里收进来的 `target_plan` 参数往下翻遍全文压根没地方用过。

单号任务跑起来一共按顺序走五个异步方法，号与号之间硬等两秒。

第一步 `step1_login` 负责登录过验证。这里面唯一写得比较规矩的是它自己手搓的 `get_totp` 函数：没引第三方库，老老实实按 RFC 6238 做 Base32 解码、时间戳整除 30 秒算计数器、跑 `HMAC-SHA1` 动态截断取 6 位模，填入前要是看当前 30 秒周期只剩不到 3 秒还会主动等跳下一个新码再填。但外围跑 16 轮循环的 `pass_reauth_on_page` 就糙得没边了：碰上辅助邮箱 `challenge/kpe`、TOTP 框或 `gds.google.com` 提示页还能点两下，一旦撞见图片 reCAPTCHA 只写了点复选框，碰见 `signin/rejected` 直接 `return`，可最外层连个布尔返回值都没接，照样乐呵呵打出一行"登录完成"接着往下冲。

第二步 `step2_layer1_12m` 先去读 Play 订阅管理页。只要整张网页文本里出现 `2028` 或者写死的 `2027年10月`、`Oct 2027` 字样（压根没定位这串日期是不是挂在 Google One 那一行底下），就当成已经开过了直接跳过。否则先调 `get_current_sub_id` 用三层正则从 HTML 或 `AF_initDataCallback` 脚本块里抠出形如 `[a-z]{24}\.AO-J1O` 的 24 位当前订阅 ID（好笑的是如果页面里有好几条订阅抠出了多个候选值，部分分支居然先丢进无序的 Python `set` 去重再随便抓第一个出来），然后把第一层配置推进 `HOOK_JS`：

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

这里的 `21` 和 `ear8` 第二个槽位里的 `5` 全是硬编码黑盒数字，作者拿 `5` 当已有订阅叠加模式使，但没留任何与 Android Billing 枚举对应的协议说明。

第三步和第四步分别换上 `TOK_PRO5TB_6M_SS` 与 `TOK_PRO5TB_6M`（失败再试 `TOK_PRO5TB_6M_2`），三层之间分别硬睡 45 秒、45 秒、40 秒，跳过判断照样是一堆写死的 2028 年中英文月份，从来没按真实起始日算过偏移。

第五步 `step5_cancel_and_verify` 去退订防续费。只要全页没搜到"已取消"三个字，它就直接点页面上第一个可见的"管理"按钮进去点取消。要是你这号上刚好还订着别的排在第一行的 Google 服务，退错谁全凭运气；退完也不复查状态到底变没变，截张图再用正则捞个日期，捞不着就填一句 `"已激活 (详见截图)"`，把任务大笔一挥标成 `completed`。

## 0x02 弹窗轮询与形同虚设的"`0.00` 零消费保护"

整份源码里最惊险的地方，全集中在 `_poll_eacquire_modal` 和 `open_and_click_subscribe` 这两段结账点击逻辑里。

先看弹窗轮询。点完升级按钮后，脚本遍历所有 frame 找带 `eacquire` 的弹窗，一旦在里面扫到至少四个可见 `input` 输入框，连表单归属都不核对就开始按顺序调 `press_sequentially` 逐字敲卡号，邮编默认硬填免税州波特兰的 `97201`（界面上吹成"免税绑卡"，代码里其实连税额都没看一眼）。保存完等 `instrumentmanager` 消失，要是循环等满次数还没消失，它居然也照样把 `inline_card_saved` 设成 `True` 往下走。唯有按钮可见性检查写得还算细致，挨个看了 `display`、`opacity`、`aria-hidden`、`pointerEvents` 并用 `elementFromPoint` 测了遮挡。

等真正到了要点下最终"订阅"按钮的前一秒，作者写了一道号称保命用的"零消费保护"：

```python
if "ultra" not in step_tag.lower() and "0.00" not in clean_txt and "免费" not in clean_txt and "Free" not in clean_txt:
    self.last_subscribe_error = f"零消费保护拦截：弹窗未显示 0.00 免费试用 ({clean_txt[:180]})"
    return False
```

盯住这行 `if` 看三秒钟，后背汗毛都能立起来：`clean_txt` 是把整个结账弹窗拼出来的一整坨纯文本！

万一前面的 `HOOK_JS` 解析失败原样放行了全价请求，弹窗上明晃晃印着本月立即扣款 `$10.00`、`$20.00` 或者 `$200.00`，因为字符串 `"10.00"` 和 `"200.00"` 肚子里本来就包含子串 `"0.00"`，`"0.00" not in clean_txt` 当场判定有零元字样，脚本眼皮都不眨就会替你把真金白银的扣款按钮点下去！退一步讲，哪怕主套餐价格是 `$19.99` 不含 `.00`，只要底下捆绑的那个 YouTube 附加项旁边写着"免费"或"Free"，或者步骤标签里带了 `"ultra"`，这道所谓的保护锁照样原地失灵。

点完订阅进 35 轮结果等待循环（中途自动补填 CVC、重输密码或 TOTP）之后，结果判断同样让人哭笑不得。作者把 `"Google Play 积分"`、`"备用付款方式"`、`"以后再说"`、`"知道了"`、`"Got it"` 全塞进了成功词列表，而且排在错误词检查的前面（弹窗关掉后的另一处分支甚至连见到 `"Welcome"` 都算成功）。只要弹出一张"您不符合免费试用条件 -> [知道了]"的拒单框，脚本一瞅见"知道了"三个字，立马喜滋滋当成订阅成功返回 `True`。反过来，"订单仍在处理中"却被它塞进了错误词列表，外层收到失败歇三秒直接重刷一遍，极易搞出重复下单；要是前三步半路抛了异常退出，第五步的自动取消续订更是压根不会跑。

## 0x03 `socks5://` 协议乌龙、进程强杀与本地控制台漏洞

除了结账逻辑，周边几个工程模块里也埋着不少一眼能看穿的硬伤。

先看本地代理桥 `LocalHttpProxyAuthBridge`。为了让 Chrome 走带账号密码的上游代理时不弹认证框，脚本在本地（调试端口加 200，默认 `9520`）起了一个本地转发桥，自动帮请求加上 `Proxy-Authorization: Basic ...`，支持 `{country}`、`{session}` 等模板占位符（遇到失败还会尝试改写带 `-session-` 的用户名换出口 IP，另外留了个长度满 24 且不含 `:` 与 `@` 时去调 FloppyData 接口拉代理的分支，同时用 `_BLOCKED_PROXY_HOSTS` 拦掉了 Chrome Safe Browsing 等后台域名）。但这个桥从头到尾只实现了纯明文 HTTP 转发和 `CONNECT` 隧道，压根没写半行 SOCKS5 二进制握手代码；偏偏外面的配置解析器看见 `socks5://user:pass@host:port` 也照收不误塞进这个 HTTP 桥里，发出去的是 ASCII 文本 `CONNECT`，对面等着收 `0x05` 字节的 SOCKS5 服务端当场就得挂断。

再看账号导入和环境巡检。`import_accounts` 支持 `----`、`|`、`/`、逗号和空格分隔，但没避开 `socks5://` 里的斜杠，密码里一旦带了分隔符字段位置就全乱了；做邮箱去重时更莽，直接把整串邮箱里所有的 `.` 全删掉，连 `@` 后面域名里的点都一锅端了。而号称做前置把关的 `verify_ip_environment` 依次去调 `ipinfo.io/json` 和 `ipwho.is`，查出国家城市往日志里一打就算"检测通过"，既没跟目标地区做比对，连两个接口全挂了都照样放行往下跑。

至于浏览器管理，每个号按邮箱建一个 `profiles/profile_...` 独立目录，启动时挂上一串 `--disable-popup-blocking`、`--webrtc-ip-handling-policy=disable_non_proxied_udp`、`--enforce-webrtc-ip-permission-check` 和 `--remote-debugging-port` 参数（Windows 下点手动打开浏览器按钮则会调 `_launch_on_interactive_desktop`，用 `ctypes` 调 `CreateProcessW` 把 `STARTUPINFOW.lpDesktop` 指到 `winsta0\default` 并设 `wShowWindow = 3` 最大化窗口）。但它在拉起 Chrome 前清理残留端口时，居然只按调试端口号查出 PID 就直接强杀，连那个进程到底是不是 Chrome 都不核对一眼。

最后一眼看回 `127.0.0.1:8765` 的本地 Web 控制台：后端不设任何口令鉴权，银行卡号、有效期、CVC 安全码、账号密码和 TOTP 种子全明文存在 `config.json` 里，验证中途有几条日志甚至直接把明文 CVC 打在了屏幕上，`/api/state` 每 1.5 秒把全套敏感凭据明文往外吐一次。更要命的是前端 `index.html` 虽然给日志框做了转义，渲染账号队列表格时却直接拿未转义的邮箱和密码去拼 `innerHTML` 与内联 `onclick` 属性：密码里带个单引号就能把界面按钮废掉，掺一段脚本标签就是现成的本地 DOM XSS，要是在同一个浏览器里打开了恶意网页跨站探一下本地 `8765` 端口，整包账号和卡信息就全交出去了。

通篇审下来，这就是一份把界面和自动化动作堆得很满、但在金额核验和安全边界上全靠碰运气的典型快餐脚本。真要拿自己的环境去试这类来路不明的自动化工具，像前文折腾 Ultra 20x 时那样只给虚拟卡留 3 美元限额，永远是保住钱包的最后一道硬保险。
