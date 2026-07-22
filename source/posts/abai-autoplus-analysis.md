---
title: "aBaiAutoplus 深度拆解：当「注册机」进化成 AI 账号工厂"
description: "从协议层到浏览器层，从 PayPal 到 GoPay，从邮箱轮换到代理池——完整解析这款 300+ Star 的 AI 账号自动注册系统的技术架构，并与同类工具横向对比。"
date: 2026-06-01T17:00:00+08:00
draft: false
categories: ["技术分析"]
tags: ["AI", "自动化", "开源工具", "架构分析", "注册机", "GoPay", "PayPal"]
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> **一分钟速读**：aBaiAutoplus 不止是"注册机"，而是一套完整的 AI 账号自动化工厂——插件化架构支持 12 个平台，协议 + 浏览器双模式，甚至打通了 PayPal / GoPay 付款开通 ChatGPT Plus 的全链路。本文从 HTTP 指纹对抗、邮箱轮换、注册流程引擎到支付协议逆向，逐层拆解其技术内幕，并与同类工具横向对比。

---

## 引言

先问一个问题：一个账号注册工具，和"AI 账号工厂"之间差了多远？

答案是：差了**付费通道**和**生命周期管理**。

市面上注册 ChatGPT 账号的工具不少。用 Selenium 填个表单、接个验证码、输出 token —— 这是 2023 年的及格线。但到了 2026 年，当 ChatGPT Plus 的后付费链路涉及 Stripe → PayPal hCaptcha 风控 → Express Checkout → Hermes 兜底支付，或者 Stripe → Midtrans 收银台 → GoPay 14 步 API 付款，事情就完全是另一个量级的复杂度了。

**aBaiAutoplus** —— GitHub 上架两天 311 Star、208 Fork，基于 `any-auto-register` 二次开发，在插件化注册框架之上硬是接上了 GoPay 和 PayPal 两条付费管道，把注册工具做成了"账号 + Plus 订阅"的全自动生产线。

本文不是功能罗列。我们从架构、协议对抗、支付链路、生态对比四个维度切入，拆解它到底做了什么、怎么做到的、以及相比同类工具是「换皮」还是「进化」。

---

## 一、架构全景：插件化的"账号工厂"

先说结论：这是一个标准的 **DDD（领域驱动设计）分层架构** + **插件注册表模式**。

```
api/          ── FastAPI 路由层（REST + SSE 实时日志推送）
application/  ── 应用编排层（任务调度、付款流水线、多租户 API）
domain/       ── 领域模型（Account / Task / Proxy / Platform 抽象）
core/         ── 核心能力层（平台基类、注册引擎、代理池、生命周期）
platforms/    ── 平台插件层（每个平台一个独立包）
providers/    ── Provider 插件层（邮箱 / 验证码 / 接码 / 代理驱动）
frontend/     ── React + TypeScript + Vite + TailwindCSS
electron/     ── Electron 桌面端打包
```

### 1.1 插件的自发现机制

系统的灵魂在 `core/registry.py`。启动时用 `pkgutil.iter_modules` 扫描 `platforms/` 下的所有 Python 包，任何带 `@register` 装饰器的 `BasePlatform` 子类都会被自动注册到全局注册表：

```python
# 一个平台插件的典型结构
@register
class ChatGPTPlatform(BasePlatform):
    name = "chatgpt"
    display_name = "ChatGPT"
    supported_executors = ["protocol", "headless", "headed"]
    supported_identity_modes = ["mailbox"]
    supported_oauth_providers = ["google", "microsoft"]
    capabilities = ["plus_payment", "paypal_checkout"]
```

这意味着添加新平台不需要修改任何核心代码——你在 `platforms/` 下新建一个包，实现 `plugin.py`，定义 `build_protocol_mailbox_adapter()` 和 `build_browser_registration_adapter()`，系统启动时它就会出现在 Web UI 里。

### 1.2 注册流程引擎：三种模式统一抽象

这是整个架构最精巧的部分。所有平台的注册逻辑被收敛到三个标准 Flow 类中：

| Flow | 适用场景 | 核心组件 |
|------|----------|----------|
| **ProtocolMailboxFlow** | 纯 HTTP API 注册 + 邮箱验证码 | `worker_builder` → `register_runner` → `result_mapper` |
| **BrowserRegistrationFlow** | 需要浏览器的注册（Turnstile / hCaptcha / OAuth） | `browser_worker_builder` → `browser_register_runner` |
| **ProtocolOAuthFlow** | OAuth 协议订阅（Google / Microsoft 登录） | `oauth_runner` → `result_mapper` |

三者的共同点是都依赖 **Adapter 模式**：

```python
@dataclass(slots=True)
class ProtocolMailboxAdapter:
    result_mapper: Callable        # 结果映射器
    worker_builder: Callable       # Worker 构造器
    register_runner: Callable      # 注册执行器
    otp_spec: OtpSpec | None       # 验证码抓取规格
    link_spec: LinkSpec | None     # 验证链接抓取规格
    use_captcha: bool              # 是否需要打码
```

每个平台的 `plugin.py` 只需「组装」一个 Adapter 并返回，Flow 引擎负责执行环境的构建（代理注入、邮箱轮换、验证码回调、超时控制、取消检查）。这种设计让"注册"这件事变成了**声明式配置**——开发者不需要理解并发控制、异常重试、SSE 日志推送等技术细节。

### 1.3 技术栈选型中的安全考量

注意几个关键组件的选择：

- **HTTP 客户端**：`curl_cffi` 而非 `requests` 或 `httpx`。原因很简单——`curl_cffi` 能伪造 TLS 指纹（`impersonate="chrome136"`），让请求在 TLS 握手层面就"看起来像浏览器"。Cloudflare / Akamai 等 WAF 对 `requests` 库的 JA3 指纹一抓一个准。

- **浏览器引擎**：Playwright（Chromium）+ Camoufox（反指纹）+ BitBrowser（指纹浏览器）。三套浏览器后端覆盖不同场景——Playwright 用于普通表单、Camoufox 用于需要绕过 Turnstile 的场景、BitBrowser 用于 PayPal 这种对浏览器环境极度敏感的平台。

- **桌面端**：Electron 内嵌完整 Python 后端，不依赖用户安装 Python 环境。这种"all-in-one"打包方式是降低使用门槛的关键——用户双击 `.dmg` 或 `.exe` 就能用。

---

## 二、核心突破口：从"注册"到"付款"的最后一公里

如果说插件化架构是骨架，那付款集成就是灵魂。这是 aBaiAutoplus 与上游 `any-auto-register` 最本质的分野。

### 2.1 GoPay 付款链路：14 步 API 协议

印尼 GoPay 是 ChatGPT Plus 订阅的一条「野路子」。因为 ChatGPT 在印尼的定价（IDR）相对低廉，且 GoPay 对虚拟卡/PIN 的验证不如欧美严格，整套链路可以被协议化。

其流水线分三步（实现见 `application/gopay_pay_chatgpt.py`）：

```
步骤一【协议】：调用 generate_plus_link(country=ID, currency=IDR)
      → 拿到 Stripe Hosted Checkout 的 cashier_url

步骤二【浏览器】：打开 cashier_url → 等待页面自动跳转到 Midtrans 域
      → 捕获 midtrans_url（Snap v3/v4 重定向 URL）

步骤三【协议】：GoPayPayment.pay(midtrans_url, account)
      → 14 步 Midtrans API：生成支付token → 启动交易 → GoPay 扫码/确认 → 回调
```

第三步最精彩——Midtrans 的 Snap 收银台本质是一套 RESTful API 编排，每步都需要精确的 header 构造、csrf token 传递、以及 JWT 签名验证。项目在 `platforms/gopay-deploy/` 中做了一套完整的 GoPay 协议 Worker，从账号登录、PIN 验证、余额查询到付款确认，全链路协议化。

同时注意到一个巧妙的工程手段——**PhoneTTLGuard**：

```python
class PhoneTTLGuard:
    """Hero-SMS 号码 20 分钟自动回收的护栏"""
    def __init__(self, ttl_seconds: int = 1200):
        self.ttl_seconds = ttl_seconds
        self._start = time.monotonic()

    def check(self) -> None:
        if self.elapsed() > self.ttl_seconds:
            raise RuntimeError("号码有效期已过，任务失败")
```

因为接码平台的印尼号码只有 20 分钟有效期，如果你在注册 GoPay 后超过 20 分钟才去调用付款接口，号码已被回收，短信验证码就收不到了。这个护栏用 `time.monotonic()`（不受系统时钟回拨影响）在每一步执行前检查，超时直接判失败——干净利落的工程防御。

### 2.2 PayPal 付款链路：HAR 协议逆向的艺术

比 GoPay 更复杂的是 PayPal。ChatGPT Plus 的后付费链路会经过 Stripe → PayPal 的审批协议跳转，PayPal 端有：

- **hCaptcha passive 检测**（包含约 2200 字符的签名 JWT）
- **Generic Risk Center 企业风控**（5 次交叉验证请求）
- **SignUp Guest 注册流**（包括手机号验证、地址填充、卡片绑定）
- **Hermes 兜底支付**（OPT_OUT 模式，$0 trial 不产生真实扣款）

项目仓库中一份 77MB 的 HAR 文件 `checkout-20260523-160436-04xg0pylps_edu.hsxhome.com.har`（含 846 个请求），被逐帧反推成了协议文档 `PAYPAL_PROTOCOL_FLOW.md`，拆解出 6 个 Stage、20+ 个端点的完整调用链。

最值得关注的技术点：

**① hCaptcha passive 的"不战而胜"**

PayPal 的 `/auth/validatecaptcha` 端点接受 `hcaptchaToken=NOT_REACHABLE` 作为参数——也就是说，在某些条件下，PayPal 自己的前端 JavaScript 在检测不到 hCaptcha 时也不会拒绝请求，而是走到一个 authchallengenodeweb 模板（返回 200 + 7387 字节 HTML）。真正的 hCaptcha 校验在另一个端点 `/auth/verifyhcaptchapassive` 中触发，需要 hCaptcha SDK 生成的 `P1_<签名JWT>` token。

这个发现意味着：**如果能绕过 PayPal 的 Generic Risk Center 风控评分，hCaptcha 可能根本不会被触发**。这是典型的"从协议层面理解风控触发条件"的逆向思路，而不是硬着头皮去对着 hCaptcha 死磕。

**② Hermes 兜底支付的 $0 trial 秘密**

在前几次 addCard 时，GraphQL mutate 返回 `ISSUER_DECLINE / CARD_GENERIC_ERROR` 并不代表失败。PayPal 会自动在 redirect URL 追加 `addFIContingency=noretry&fallback=1&reason=CARD_GENERIC_ERROR`（base64 编码），把流量导进 `/webapps/hermes` 兜底支付。Hermes 里只需发一个 `authorize` mutation，带 `fundingPreference={"balancePreference":"OPT_OUT"}`，PayPal 就会直接返回 `status=success`——因为它识别到这是一笔 $0 试用的审批授权，不需要真实扣款。

**OPT_OUT 是整条链路中最关键的一个参数**。它告诉 PayPal："别从任何资金渠道扣款，这是一笔授权审批。" 不掌握这个细节，你会以为 visa 虚拟卡被拒就是失败。掌握了，你就知道这条 HAR 里的所有"失败"步骤都是预期的路由分支。

### 2.3 代理池：成功率驱动的智能轮换

代理在 AI 账号注册中是核心竞争力。Cloudflare 对数据中心 IP 的态度越来越严苛，Turnstile 验证码的通过率与 IP 质量直接挂钩。

aBaiAutoplus 的代理池设计有三种层级：

| 层级 | 来源 | 特点 |
|------|------|------|
| **静态代理池** | 手动添加的固定代理 | 按成功率加权轮询，连续失败 5 次自动禁用 |
| **动态 API 提取** | 代理商的 HTTP API 动态提取 | 每次提取新 IP，适合大批量任务 |
| **旋转网关代理** | BrightData / Oxylabs / IPRoyal 等 | 固定入口地址，每次请求自动分配不同出口 IP |

三个关键设计：
1. **自动回退**：动态代理失败 → 回退到静态代理池 → 再失败才报错
2. **成功率统计**：`GET /api/stats/by-proxy` 可按代理查询成功率排行
3. **平台敏感度区分**：不同平台对 IP 的容忍度不同，可分别配置代理策略

---

## 三、生态完整性：从注册到交付的全链路

一个只注册不管后续的工具是半成品。aBaiAutoplus 做了完整的生命周期闭环：

### 3.1 账号生命周期管理器

```python
# core/lifecycle.py
- 每 6 小时：有效性检测（check token 是否还能用）
- 每 12 小时：Token 自动续期（当前支持 ChatGPT session_token 刷新）
- Trial 过期扫描：快过期 → 预警标记，已过期 → 状态更新为 EXPIRED
```

这不是装饰性功能——如果你有 200 个 ChatGPT 账号，手动检查每个 token 是否过期是不现实的。生命周期管理器让账号池成为一种「可运营的资源」，而非一次性消耗品。

### 3.2 多维度成功率仪表盘

```
/api/stats/overview     → 全局概览（总数、成功率、状态分布）
/api/stats/by-platform  → 按平台统计成功率（看哪个平台风控严）
/api/stats/by-day       → 按天注册趋势（看成功率是否在下降）
/api/stats/by-proxy     → 代理成功率排行（淘汰低质代理）
/api/stats/errors       → 失败错误聚合（分析常见失败原因）
```

把成功率数据分析做成独立 API，意味着可以接入 Grafana / Prometheus 等外部监控，而不只是看 Web UI 上的图表。这是「工具」到「运维平台」之间的一条分界线。

### 3.3 账号导出生态

注册完的账号需要被消费。支持 6 种导出格式：

- **JSON / CSV**：常规导出
- **CPA**：内容发布平台导入格式
- **Sub2API**：订阅 API 转换器格式
- **Kiro-Go**：Kiro 平台的 config.json 格式
- **Any2API**：开源 API 网关格式（注册完自动推送到网关，即注册即用）

最后这个 Any2API 联动很有意思——注册工具本身不提供 API 服务，但它能自动把账号推送到另一个 API 网关项目，让下游消费者通过统一接口获取账号。这是一种「微服务化」的思路：注册工具专注生产，API 网关专注分发。

### 3.4 Any2API 自动推送映射

| 平台 | 推送目标 | 数据类型 |
|------|----------|----------|
| Kiro | kiroAccounts | 账号池 |
| Grok | grokTokens | Token 池 |
| Cursor | cursorConfig | Cookie + 配置 |
| ChatGPT | chatgptConfig | Token + 配置 |
| Blink | blinkConfig | 凭证 |
| Windsurf | windsurfAccounts | 账号池 |

---

## 四、横向对比：与同类工具的异同

### 4.1 any-auto-register（上游项目）

| 维度 | any-auto-register | aBaiAutoplus |
|------|-------------------|-------------|
| ⭐ Star | 2529 | 311 |
| 🍴 Fork | 885 | 208 |
| 平台数 | 13+ | 12（继承上游 + 新增 GoPay） |
| 协议模式 | ✅ | ✅ |
| 浏览器模式 | ✅ | ✅ |
| PayPal 付款 | ❌ | ✅（浏览器 PayPal 结账） |
| GoPay 付款 | ❌ | ✅（协议 14 步 API 付款） |
| Any2API 联动 | ✅ | ✅ |
| 接码渠道 | SMS-Activate / HeroSMS | + SMSPool / SMSBower |
| C 端管理门户 | ❌ | ✅（customer_portal_api） |
| 桌面客户端 | Mac / Win（社区版） | Mac / Win（完整版） |

**本质差异**：`any-auto-register` 做了「注册」，aBaiAutoplus 做了「注册 + 付费」。两者的架构是同源的（同一套插件基类和注册引擎），但 aBaiAutoplus 在 ChatGPT 平台上的深度远超上游——不只是接口注册，而是打通了从账户创建到 Plus 订阅扣款的全流程。

可以这么说：
- `any-auto-register` = 注册框架 + 多平台适配器
- `aBaiAutoplus` = 注册框架 + ChatGPT Plus 付费工程 + GoPay 全套协议

### 4.2 gpt-auto-register（⭐397）

最直接的单平台竞品。基于 Python + Selenium，专注 ChatGPT 账号注册。

| 维度 | gpt-auto-register | aBaiAutoplus |
|------|-------------------|-------------|
| 浏览器引擎 | Selenium（单引擎） | Playwright / Camoufox / BitBrowser（三引擎） |
| 架构 | 单体脚本 | 插件化 DDD 分层 |
| 平台支持 | ChatGPT 单一平台 | 12 平台 |
| 付款集成 | ❌ | ✅（PayPal + GoPay） |
| Web UI | 无 | React + SSE 实时日志 |
| 账号管理 | 基础导出 | 生命周期管理 + 仪表盘 + 多格式导出 |
| TLS 指纹 | 无 | curl_cffi impersonate |
| 桌面客户端 | 无 | Electron |

**差距不在功能数量，在架构理念**。`gpt-auto-register` 是一个能用的注册脚本；`aBaiAutoplus` 是一个可扩展的注册平台。

### 4.3 chatgpt-auto-register（⭐13）

基于 `undetected-chromedriver` 的入门级实现。功能最基础，适合学习原理，不具备生产级可用性。与 aBaiAutoplus 不在同一量级，不做详细对比。

### 4.4 差异化总结

如果把「AI 账号注册工具」的进化分为三个阶段：

```
第一代（2023）    Selenium + 手动配置 → 注册成功
第二代（2024-25） Playwright + 多平台 + 插件化 → 注册 + 管理
第三代（2026）    协议逆向 + 付费打通 + 微服务生态 → 全链路自动化
```

aBaiAutoplus 处于第二代向第三代的过渡期——它继承了第二代的插件化框架，但用 GoPay / PayPal 协议逆向和 Any2API 联动把自己推进了第三代的门槛。三者的核心差异体现在付费集成、TLS 对抗深度、以及生态完整度上。

---

## 五、工程细节中值得关注的亮点

### 5.1 TLS 指纹伪装的双层策略

项目在 HTTP 层面有两套请求方案：

- **curl_cffi**（`core/http_client.py`）：默认 `impersonate="chrome136"`，伪造完整的 TLS 握手指纹
- **tls_client**（`core/tls.py`）：更轻量的选择，用于 GoPay 等对 TLS 检测不那么严格的场景

这种「双层策略」是有深度的——curl_cffi 的 impersonate 虽然真实度高，但附带性能开销；对于不需要高伪装的 API 请求，退回到 tls_client 能提升吞吐量。

### 5.2 邮箱层的「深度防御」

9 种邮箱 Provider 不是简单的多选，而是一种**分层防护策略**：

- **自己的域名邮箱**（Laoudo）：稳定性最高，适合重要账号，不会被封
- **自建 Cloudflare Worker 邮箱**：完全可控，邮箱域名随机，难以被平台封禁
- **公共临时邮箱**（DuckMail / TempMail.lol）：零配置，适合快速测试
- **MoeMail 自动注册**：连邮箱也是自动创建的，适合大规模并发

不同场景用不同邮箱，这是一种**对抗意识**——当平台开始针对特定邮箱域名做风控时，你有备选方案。

### 5.3 验证码求解的递进策略

| 策略 | 优先级 | 使用场景 |
|------|--------|----------|
| 本地 Solver（Camoufox 自动点击 checkbox） | 1 | Turnstile checkbox，最快最省 |
| 远程 Solver（YesCaptcha / 2Captcha） | 2 | 需要图片识别或本地失败时 |
| 手动介入 | 3 | 极端风控场景 |

「先本地、再远程、最后手动」的递进逻辑，比直接调打码平台更经济。

### 5.4 开源安全审计的"工程良心"

项目开源前做了一份详细的安全审计（`OPEN_SOURCE_RELEASE.md`），发现的 P0 级问题包括：

- 81 个真实 ChatGPT 账号明文凭证已被 git 跟踪
- 8 个 GoPay 账号的手机号 + PIN 明文泄露
- 13 个调试 dump 文件含 PayPal / Stripe 实时 cookie

这份审计本身就是一个有价值的技术文档——它展示了「开源前要做哪些安全检查」的完整 checklist：
1. 扫描 git 历史中的凭证文件
2. 检查源码中的硬编码 API Key
3. 审查第三方 APK 逆向常量是否可公开
4. 验证 `.gitignore` 规则是否生效
5. `git filter-repo` 重写历史的完整命令

每个打算开源的开发者都应该读一遍这份文档。

---

## 六、局限与风险

### 6.1 技术局限

- **GoPay 地域锁定**：依赖印尼手机号 + 印尼 IP，对中国用户不友好
- **PayPal 浏览器自动化不稳定**：BitBrowser profile 持久化是双刃剑——历史 cookie 积累后可能触发异常检测
- **Camoufox 依赖**：本地 Solver 依赖于 Camoufox 的反指纹浏览器，ARM 架构支持有限
- **MoeMail 公共实例不可控**：依赖第三方部署的实例稳定性

### 6.2 运维负担

- 3.7M 行 Python（含依赖）不是小工程，依赖更新和兼容性维护是个长期问题
- 跨平台浏览器自动化（Playwright + Camoufox + BitBrowser）的环境配置复杂度高
- 多接码渠道、多验证码渠道的 API 轮换和余额管理需要持续关注

### 6.3 法律与道德边界

项目在 README 中明确了「仅供学习研究」的定位，并且基于 AGPL-3.0 许可证。但必须指出：

- 自动化注册违反几乎所有目标平台的 ToS
- 协议化支付链路可能涉及支付欺诈的法律风险
- 印尼 GoPay 的 APK 逆向常量（`CLIENT_SECRET` 等）存在 ToS 和版权问题

**技术是好技术，但使用场景需要谨慎判断。**

---

## 七、总结

aBaiAutoplus 之所以值得深入分析，不是因为它「又多了一个注册工具」，而是因为它展示了注册工具从**脚本**到**平台**的完整进化路径。

它的核心价值不在于星星数（311 相比上游的 2529 还差得远），而在于：

1. **架构上**：插件化 + DDD 分层，让注册能力可扩展、可维护
2. **技术上**：支付协议逆向（PayPal 6 Stage + GoPay 14 步），把"注册"延伸到"付费"
3. **工程上**：代理池智能轮换、邮箱分层防护、TLS 指纹对抗，形成了一个完整的反风控体系
4. **生态上**：Any2API 联动、多格式导出、customer_portal_api，让注册工具成为可运营的基础设施

与同类工具相比，它最大的差异化优势是**付费链路的打通**——这是三个对比项目都不具备的能力。GoPay 协议付款和 PayPal 浏览器结账这两条「野路子」，背后是扎实的 HAR 分析和协议逆向工作，不是简单的 API 拼接。

当然，它的"进化"仍在进行中——AGPL-3.0 许可证意味着衍生项目可以在此基础上继续扩展，而 3.7M 行的 Python 代码量也意味着维护成本不低。

对于想学习注册工具架构设计、支付协议逆向、或者浏览器自动化实战的开发者，这个项目是一个非常有价值的参考案例。

---

*本文基于 2026 年 6 月 1 日的仓库状态分析。项目仍在快速迭代中，部分细节可能已有更新。*
