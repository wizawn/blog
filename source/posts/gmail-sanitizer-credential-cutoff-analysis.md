---
title: "Gmail Sanitizer 深度拆解：8 步全链路凭据切断的自动化实现"
description: "从 DrissionPage 浏览器自动化到 AES-256-GCM 加密冷库，从 Sudo Gate 循环挑战到 Cloudflare Email Worker 极速接码——完整解析一款 Google 账号全链路凭据切断系统的技术内幕。"
date: 2026-08-04T14:00:00+08:00
draft: false
weight: 1
categories: ["技术分析"]
tags: ["Google", "自动化", "安全", "DrissionPage", "浏览器自动化", "凭据管理", "账号安全"]
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK  ⚠️ **博主微信暂时被封，请优先加入上方 QQ 群（46333839）**

进微信群请联系博主，各位觉得文章对你有帮助的话可否打赏一些呀~

---

> 一分钟速读：Gmail Sanitizer 是一套 8 步全链路凭据切断系统，覆盖恢复邮箱、恢复手机、Passkey、2FA 密钥、OAuth 授权等所有后门，逐一切断后用新凭据重新登录验证。底层用 DrissionPage 驱动真实 Chrome 绕过 Google 反自动化检测，配合 Cloudflare Email Worker 实现验证码秒级推送，AES-256-GCM 加密冷库保护敏感数据，asyncio 任务队列 + 死信队列实现批量并发 + 失败自愈。本文从攻防对抗、引擎架构、接码管道三个维度展开。

---

## 引言

你从卡网买了一个 Google 账号，改了密码，是不是就安全了？

不是。

改密码只切断了 6 条"绳子"中的 1 条。卖家仍然可以通过以下方式盗回你的账号：

| 后门 | 盗回方式 |
|------|----------|
| 恢复邮箱 | 通过"忘记密码"流程，Google 会把重置链接发到卖家的恢复邮箱 |
| 恢复手机号 | 同上，短信验证码直接发到卖家手机 |
| Passkey | 卖家的设备上注册了 Passkey，无需密码即可登录 |
| TOTP 2FA 密钥 | 卖家手里有 Base32 密钥，能随时生成你的 2FA 验证码 |
| 旧会话 / Cookie | 卖家的浏览器可能还保持着登录状态 |
| OAuth 授权 | 授权过的第三方应用可以读取邮件、通讯录等数据 |

你只改了密码？卖家用恢复邮箱就能把密码改回来。你改了密码又关了 2FA？Passkey 还在。你把 Passkey 也删了？OAuth 授权的第三方应用还在偷偷读你的数据。

Gmail Sanitizer 的目标就是一口气把这 6 条绳子全部切断。

---

## 一、核心功能：8 步全链路凭据切断

这个系统的核心是一条 8 步流水线，每一步精确对应一个后门：

| 步骤 | 操作 | 切断的后门 | 关键难点 |
|------|------|-----------|---------|
| Step 1 | 登录验证 | 验证旧凭据有效性 | 2FA 挑战、Account Chooser、中间提示页 |
| Step 2 | 替换恢复邮箱 | 卖家的恢复邮箱 → 买家自建接码邮箱 | Google 可能要求邮箱验证码 |
| Step 3 | 移除恢复手机 | 卖家绑定的手机号 | 可能需要 Sudo 二次验证 |
| Step 4 | 删除所有 Passkey | 卖家设备的无密码登录凭据 | 循环删除，最多 20 个 |
| Step 5 | 重置 2FA | 旧 TOTP 密钥 → 新 Base32 密钥 | 需要提取页面上的 Base32 密钥文本 |
| Step 6 | 修改密码 + 全设备登出 | 旧密码 + 旧会话 | 密码强度校验、设备登出确认 |
| Step 7 | 撤销 OAuth 授权 | 所有第三方应用权限 | 循环撤销，最多 30 个 |
| Step 8 | 新凭据验证 | 确认所有切断生效 | 用新密码 + 新 2FA 重新登录 |

实际执行顺序是 1-2-5-4-3-6-7-8，Step 5（重置 2FA）被提前到 Step 4（删除 Passkey）之前。原因是 Step 5 需要在 Sudo Gate 中输入旧 TOTP 码验证身份，如果先删了 Passkey，Google 可能挑选 Passkey 作为 Sudo 验证方式却找不到，导致验证失败。

### 1.1 Sudo Gate：Google 的二次验证拦截

Google 在修改安全设置时会弹出 Sudo Gate（二次身份验证页面）。Sudo Gate 的挑战方式不固定，Google 根据账号状态动态选择：

```python
def handle_google_sudo_gate(self, page, password, totp_secret=None, 
                            gmail=None, recovery_email=None):
    for cycle in range(6):  # 最多循环 6 次
        current_url = page.url
        
        # 1. Account Chooser（会话过期）
        if "accountchooser" in current_url:
            # 点击账号重新选择
            
        # 2. 2FA 方式选择页
        if "challenge/selection" in current_url:
            # 智能选择：优先 recovery email > TOTP
            
        # 3. 恢复邮箱验证 (challenge/kpe)
        if is_rec_email_challenge and recovery_email:
            # 输入恢复邮箱地址
            
        # 4. 密码重输 (challenge/pwd)
        if is_pwd_challenge:
            # 重新输入当前密码
            
        # 5. TOTP 二次验证 (challenge/totp)
        if is_totp_challenge and totp_secret:
            # 生成并输入 TOTP 验证码
```

关键设计在于循环处理。Google 可能在一次操作中连续弹出多种挑战（先要密码，再要 TOTP），所以 Sudo Gate 处理器用 `for cycle in range(6)` 最多循环 6 次，每次检测当前 URL 和页面元素，动态匹配处理策略。

### 1.2 TOTP 密钥提取：从页面 HTML 中挖掘 Base32

Step 5 重置 2FA 时，需要从 Google 的 Authenticator 设置页面提取新的 Base32 密钥。这个密钥显示在页面上的格式是 4 字符一组、空格分隔的文本（如 `ABCD EFGH IJKL MNOP`）。

提取策略是两层漏斗：

```python
# 第一层：正则匹配 4-8 组 Base32 字符块
m_groups = re.search(
    r"\b(?:[a-zA-Z2-7]{4}\s+){3,7}[a-zA-Z2-7]{4}\b", 
    dialog_text
)
if m_groups:
    candidate = m_groups.group(0).replace(" ", "").upper()
    if len(candidate) in (16, 24, 32):
        new_secret = candidate

# 第二层：暴力遍历所有元素文本
if not new_secret:
    for e in page.eles("xpath://div[@role='dialog']//..."):
        m = re.search(r"\b([a-zA-Z2-7]{16,32})\b", txt.replace(" ", ""))
        if m and candidate not in ("AUTHENTICATOR", "VERIFICATION", ...):
            new_secret = candidate
```

提取到密钥后，立即用 `pyotp.TOTP(new_secret).now()` 生成验证码填入确认框，完成 2FA 重置闭环。

### 1.3 断点续跑：任意步骤中断后恢复

每完成一个步骤，引擎立即将进度持久化：

```python
account.mark_step("step2_email_changed")
self._save_sync(account)
```

`StepProgress` 用 10 个布尔字段精确记录每一步的完成状态。重试时，引擎检查哪些步骤已完成，直接跳过：

```python
if not account.step_progress.step2_email_changed:
    ok = self._step2_recovery_email(page, cred, account)
    # ...
```

这意味着如果 Step 5 因为网络超时失败，重试时会跳过 Step 1-4 直接从 Step 5 开始。

---

## 二、技术架构

### 2.1 双引擎设计

系统提供两套浏览器引擎，适配不同场景：

| | DrissionPage 引擎 | Playwright 引擎 |
|---|---|---|
| Chrome 类型 | 真实 Chrome 进程 | Chromium 内核 |
| 反检测能力 | 天然通过，就是真 Chrome | 需要 JS 注入伪装 |
| 并发模式 | 每个任务独立端口 + Profile | 每个任务独立 BrowserContext |
| 适用场景 | 生产环境（高通过率） | 开发调试（API 更友好） |
| 进程隔离 | 每个账号独立 Chrome 进程 | 同一 Browser 下的 Context 隔离 |

DrissionPage 引擎是生产首选。它直接控制真实 Chrome 浏览器，Google 的反自动化检测基本无效，因为从 Google 视角看这就是普通用户在操作浏览器。

进程隔离的实现方式：

```python
def _make_options() -> ChromiumOptions:
    port = _find_free_port()  # 每个任务随机端口
    opt.set_local_port(port)
    # 独立 Profile 目录，防止 Chrome SingletonLock 死锁
    profile_dir = f"data/chrome_profiles/profile_{port}"
    opt.set_user_data_path(profile_dir)
```

每个账号对应一个独立的 Chrome 实例（独立端口 + 独立 Profile），彻底避免了并发时的 Cookie 串扰和 SingletonLock 死锁。

### 2.2 反检测体系

Playwright 引擎需要额外的反检测处理。`stealth_browser.py` 实现了完整的指纹随机化：

```javascript
// 隐藏 webdriver 属性
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// 伪造 plugins（无头浏览器默认为空）
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
        // ...
    ]
});
```

配合随机 User-Agent、随机分辨率、随机时区和随机语言：

```python
_USER_AGENTS = ["Chrome/125.0", "Chrome/124.0", ...]  # 5 种
_VIEWPORTS   = [1920x1080, 1440x900, ...]             # 5 种
_LOCALES     = ["en-US", "zh-CN", ...]                 # 5 种
_TIMEZONES   = ["America/New_York", "Asia/Shanghai", ...] # 5 种
```

每个 BrowserContext 从这些池子中随机组合，确保指纹不重复。

### 2.3 任务队列 + 死信队列

并发调度用经典的 asyncio 生产者-消费者模型：

```
┌──────────────┐     ┌──────────────┐
│   任务入队    │────▶│ asyncio.Queue │
└──────────────┘     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Worker 0 │ │ Worker 1 │ │ Worker N │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             ▼             ▼             ▼
        ┌──────────────────────────────────┐
        │  DrissionEngine.run_sync(task)   │
        └──────────┬───────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
    ┌──────────┐     ┌──────────┐
    │ VERIFIED │     │  FAILED  │──▶ 死信队列
    └──────────┘     └──────────┘     (指数退避重试)
```

死信队列的分类逻辑：

- 不可重试类型自动隔离：`WRONG_PASSWORD`（密码错误）、`ACCOUNT_DISABLED`（封号）、`CAPTCHA_BLOCKED`（风控拦截），这些重试也没用，直接进人工审核
- 可重试类型指数退避：`STEP_TIMEOUT`（超时）、`PROXY_ERROR`（代理挂了），等 2^n 秒后重试，最多 3 次
- Passkey 误判恢复：如果失败详情包含 `passkeyenrollment` 或 `speedbump`，说明并非真正失败，实际是卡在中间提示页，强制纳入可重试队列

### 2.4 AES-256-GCM 加密冷库

所有敏感字段（新密码、TOTP 密钥、Cookie）在存入数据库前经过 AES-256-GCM 加密：

```python
class _Cipher:
    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)  # 96-bit 随机 nonce
        ct = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return (nonce + ct).hex()  # nonce 和密文拼接后存储
```

GCM 模式提供认证加密，既保密也防篡改。即使数据库被拖库，没有 32 字节主密钥也无法解密。而且每次加密使用随机 nonce，相同明文产生不同密文，抵抗已知明文攻击。

---

## 三、验证码邮件管道

Step 2（替换恢复邮箱）可能触发 Google 的邮箱验证码。系统通过 Cloudflare Email Worker 实现秒级接码：

```
Google 发送验证码邮件
    ↓
Cloudflare Email Routing（Catch-All 规则）
    ↓
Email Worker（正则提取 6 位验证码）
    ↓
HTTP POST → 主程序回调接口
    ↓
主程序轮询取码 → 填入浏览器
```

Email Worker 的正则提取覆盖了 Google 验证码邮件的多种模板：

```javascript
const codePatterns = [
  /\b([0-9]{6})\b(?=\s*(?:is your|是您的|verification|验证|code))/i,
  /(?:verification code|验证码)[^\d]*([0-9]{6})/i,
  /G-([0-9]{6})/i,          // Google 特定格式 "G-123456"
  /\b([0-9]{6})\b/,         // 兜底：提取第一个 6 位数字
];
```

如果邮件通道超时（30 秒），系统会降级到手动模式，在终端提示操作者输入验证码：

```python
if sys.stdin.isatty():
    user_code = input("6-digit code (or Enter to skip): ").strip()
```

---

## 四、安全设计亮点

| 设计 | 实现 | 目的 |
|------|------|------|
| 进程隔离 | 每账号独立 Chrome 进程 + 独立端口 + 独立 Profile | 防 Cookie 串扰、防 SingletonLock |
| 加密存储 | AES-256-GCM + 随机 Nonce | 数据库脱库也无法解密 |
| 人类行为模拟 | `random.uniform(0.8, 2.0)` 秒操作间隔 + Worker 领任务前 1.5-5.0 秒抖动 | 降低 Google 风控触发率 |
| 中间提示页自动跳过 | 识别 Passkey 引导、恢复邮箱确认等弹窗 | 防止流程卡死 |
| 密码强度保证 | 18 位、大小写 + 数字 + 符号、`secrets` 模块生成 | 通过 Google 密码强度校验 |
| 密码热切换 | Step 6 修改密码后立即 `cred.password = new_password` | 后续步骤用新密码通过 Sudo Gate |

---

## 五、与同类方案对比

| 维度 | 手动操作 | 简单脚本 | Gmail Sanitizer |
|------|---------|---------|----------------|
| 覆盖后门数 | 取决于经验（通常漏 2-3 个） | 1-2 个（通常只改密码） | 全部 6 类后门 |
| 单号耗时 | 15-30 分钟 | 3-5 分钟 | 1-3 分钟 |
| 并发能力 | 1 | 1-3 | 20+（可配置） |
| 断点续跑 | 不支持 | 不支持 | 支持（10 步粒度） |
| 失败自愈 | 手动重试 | 无 | 死信队列 + 指数退避 |
| 凭据保护 | 明文 | 明文 | AES-256-GCM |
| 反检测 | 不需要 | Selenium（易被检测） | 真实 Chrome / 指纹随机化 |
| Sudo Gate 处理 | 人工判断 | 通常卡住 | 6 种挑战类型自动适配 |

---

## 写在最后

Gmail Sanitizer 的技术含量不在"自动化"本身，Selenium 填表单谁都会。它的价值在于对 Google 安全机制的深度理解：知道 Google 有哪些后门、知道 Sudo Gate 有哪些挑战类型、知道 Base32 密钥在页面上以什么格式显示、知道修改密码后旧 TOTP 密钥还能用多久。

从工程角度看，断点续跑 + 死信队列 + 加密冷库的组合让它从"一次性脚本"变成了可运维的生产系统，这是大多数同类工具缺失的维度。

大体量的 Google 账号采购场景，先批量跑一遍 8 步清洗再投入使用，是成本最低的安全保障。
