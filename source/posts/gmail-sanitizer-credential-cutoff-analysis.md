---
title: "只改密码拦不住找回：看 Gmail Sanitizer 的 8 步凭据流转与 Google 7 天窗口盲区"
description: "梳理自动化安全工具 Gmail Sanitizer 的工程实现：从 1-2-5-4-3-6-7-8 乱序过 Sudo Gate、AES-256-GCM 凭据加密冷库到 Cloudflare Email Worker 接码，并补齐它漏掉的 7 天旧恢复凭据宽限期与邮件转发后门。"
date: 2026-08-04T14:00:00+08:00
draft: false
categories: ["安全研究", "技术分析"]
tags: ["Google", "账号安全", "DrissionPage", "凭据管理", "AES-GCM", "自动化"]
weight: 10
---

做过团队测试账号交接或者企业安全巡检的人都很清楚，接手一个现成的 Google 账号时，光把登录密码改掉基本等于没锁门。

只要前任持有人手里还留着其他任意一条恢复通道或持久化凭据，随时都能把账号反手申诉拿回去，或者一声不吭继续读里面的数据：原恢复邮箱和原恢复手机号可以直接收重置验证码；旧设备上注册过的 Passkey（通行密钥）按一下指纹就能免密直登；以前扫过的 Authenticator 二步验证（Base32）种子随时能算出有效的 6 位动态码；没踢下线的浏览器 Cookie 和以前点过允许的第三方 OAuth 应用，更是连登录页都不用过就能接着调接口。

开源项目 `Gmail Sanitizer` 当初想解决的就是这件繁琐事：把手工挨个翻安全设置清后门的活儿，做成一条带断点续跑和加密存储的 8 步自动化流水线。先把丑话挑明：在卡网买卖个人 Google 账号本身直接违反 Google 服务条款，而且极易触发异地风控秒封，这篇笔记纯粹从账号交接安全审计和浏览器自动化工程设计的角度，看看它做对了哪些细节，又漏掉了哪几个连脚本都挡不住的致命真后门。

## 0x00 为什么要按 `1-2-5-4-3-6-7-8` 的乱序去跑

在账面定义上，这套工具列了整整齐齐 8 个步骤：登录验活旧凭据（Step 1）、换绑恢复邮箱（Step 2）、删掉旧恢复手机号（Step 3）、循环删光最多 20 个已绑定的 Passkey（Step 4）、重置 Authenticator TOTP 密钥（Step 5）、用标准库 `secrets` 生成 18 位带大小写数字符号的强密码改密并踢掉其他设备会话（Step 6）、循环吊销最多 30 个第三方 OAuth 应用授权（Step 7），最后拿全套新密码加新 2FA 重新登录做最终核验（Step 8）。

但去翻它的核心调度代码就会发现，真正落地的执行顺序被故意改成了 `1 -> 2 -> 5 -> 4 -> 3 -> 6 -> 7 -> 8`，把原本排在后面的重置 2FA（Step 5）硬生生提到了删 Passkey（Step 4）和删手机号（Step 3）前面。

这个看似别扭的顺序，完全是被 Google 的 Sudo Gate（敏感操作二次验身拦截）逼出来的。每当你去改安全设置里的关键项，Google 都会根据当前账号绑定状态动态挑一种验证方式拦你一下，而且经常在同一次操作里连环出招（比如刚输完密码，下一页立马又要你验 TOTP）。如果你按顺序先把 Passkey 全删光了再去重置 2FA，Google 的会话状态偶尔没来得及同步刷新，偏偏在 Sudo Gate 里点名让你用刚删掉的 Passkey 验身，整条流水线当场就死锁在那儿了。反过来先把新的 TOTP Base32 种子换好攥在自己手里，后面再去删 Passkey、删手机、改密码（Step 6 改完密码立刻在内存里热更新 `cred.password = new_password`），再撞上拦截就能一路拿新凭据丝滑过关。

为了应付连环跳出来的不同挑战页，Sudo Gate 处理器写了一个最多转 6 轮的 URL 匹配循环：

```python
def handle_google_sudo_gate(self, page, password, totp_secret=None,
                            gmail=None, recovery_email=None):
    for _ in range(6):
        current_url = page.url
        if "accountchooser" in current_url:
            # 会话掉线跳回选号页，重新点选当前账号
            ...
        elif "challenge/selection" in current_url:
            # 多种验身方式选择页：优先挑当前手里握有凭据的恢复邮箱或 TOTP
            ...
        elif "challenge/kpe" in current_url and recovery_email:
            # 要求补全完整恢复邮箱地址确认身份
            ...
        elif "challenge/pwd" in current_url:
            # 重新输入当前生效密码
            ...
        elif "challenge/totp" in current_url and totp_secret:
            # 调 pyotp 算出当前 30 秒窗口的动态码填进去
            ...
```

在 Step 5 重置二步验证时，脚本得从网页弹窗里把形如 `ABCD EFGH IJKL MNOP` 的 4 字符分组 Base32 密钥文本抠出来。顺手提个原仓库代码里的小 Bug：它写的两层正则漏斗在第二层兜底遍历 DOM 元素时，忘了把 `m.group(1).upper()` 重新赋给局部变量，一旦第一层没命中就会直接抛 `NameError`（或者读到第一层筛剩下的脏值）。把这处变量赋值修干净之后，两层提取逻辑就很稳了：

```python
# 第一层：优先匹配标准的 4 字符空格分组 Base32 文本
m_groups = re.search(r"\b(?:[a-zA-Z2-7]{4}\s+){3,7}[a-zA-Z2-7]{4}\b", dialog_text)
new_secret = None
if m_groups:
    cand = m_groups.group(0).replace(" ", "").upper()
    if len(cand) in (16, 24, 32):
        new_secret = cand

# 第二层兜底：去空格后扫弹窗内所有 16~32 位合法 Base32 串，排除标题英文词
if not new_secret:
    for elem in page.eles("xpath://div[@role='dialog']//*"):
        m = re.search(r"\b([a-zA-Z2-7]{16,32})\b", elem.text.replace(" ", ""))
        if m:
            cand = m.group(1).upper()
            if cand not in ("AUTHENTICATOR", "VERIFICATION"):
                new_secret = cand
                break
```

抠出 `new_secret` 当场调 `pyotp.TOTP(new_secret).now()` 算出 6 位码填回确认框，新 2FA 就正式生效了。而且每跑完一小步，`StepProgress` 都会立刻把 10 个细分布尔位之一落盘保存（比如 `account.mark_step("step2_email_changed")`）；万一跑到第 5 步正好赶上代理抖动超时，下一轮重试会直接跳过已经打勾的前几步接着往下跑，不会傻乎乎从头再来一遍。

## 0x01 独立 Chrome 进程、异步线程池、接码 Worker 与 `AES-256-GCM`

往下看它的底座，有四块工程细节值得挑出来细看。

第一块是双引擎隔离。代码里同时写了 `DrissionPage` 和 `Playwright` 两套驱动，真正干活默认走直接拉起真实 Chrome 进程的 `DrissionPage`：每次领任务找一个空闲调试端口（高并发下找空闲端口记得加锁或直接让内核分配，防瞬间端口抢占竞态），并单独配一个 `data/chrome_profiles/profile_{port}` 目录，这样既不会撞上 Chrome 的 `SingletonLock` 文件死锁，也不会在多账号之间串了 Cookie。至于它给 Playwright 备的那份 `stealth_browser.py`，里面用普通 JS 数组去覆盖 `navigator.plugins`（一测 `instanceof PluginArray` 就露馅），还把 5 组 User-Agent、分辨率、语言（`en-US` / `zh-CN`）和时区（`America/New_York` / `Asia/Shanghai`）做成独立随机抽签。实战里千万别学这种乱炖法：顶着美国出口 IP 和纽约时区，语言却报 `zh-CN`，或者手改的旧版 UA 跟 Chromium 内核发出去的 `Sec-CH-UA` 请求头对不上号，在 Google 的反自动化风控眼里简直就是黑夜里的萤火虫，老老实实让时区和语言跟着出口 IP 归属地走才合逻辑。

第二块是 `asyncio.Queue` 配死信队列（Dead-Letter Queue）和抖动节流。Worker 领任务前先睡一个 `1.5` 到 `5.0` 秒的随机抖动，每步页面点击之间插 `random.uniform(0.8, 2.0)` 秒停顿。碰到 `WRONG_PASSWORD`、`ACCOUNT_DISABLED` 这类硬伤直接踢进人工复核，不再白费力气；碰到 `STEP_TIMEOUT`、`PROXY_ERROR` 则按 `2^n` 秒指数退避最多重排 3 次；要是失败原因里带着 `passkeyenrollment` 或 `speedbump`，说明只是被 Google 推销通行密钥的中间引导页绊住了脚，自动跳过弹窗拉回重试队列。这里有个写 Python 混编时极容易踩的坑：`DrissionPage` 底层是同步阻塞 I/O，在 20 个并发 `asyncio` 协程 Worker 里调 `DrissionEngine.run_sync(task)` 时，必须包进 `await asyncio.to_thread(engine.run_sync, task)`（或独立进程池）里跑，如果直接在协程里裸调同步方法，一个浏览器等网页加载就会把整个事件循环彻底冻死。

第三块是 Step 2 换绑恢复邮箱时的验证码管道。它用自己域名的 Cloudflare Email Routing 配了一条 Catch-All 转发给边缘侧的 Email Worker，收到信当场用一组正则把 6 位验证码抠出来回调给主程序；万一 30 秒没等来邮件，如果在交互终端下（`sys.stdin.isatty()`）就自动退化成 `input()` 让人工敲进去：

```javascript
const codePatterns = [
  /\b([0-9]{6})\b(?=\s*(?:is your|是您的|verification|验证|code))/i,
  /(?:verification code|验证码)[^\d]*([0-9]{6})/i,
  /G-([0-9]{6})/i,
  /\b([0-9]{6})\b/, // 兜底规则：切记只在剥掉标签的纯文本正文上跑！
];
```

写这种邮件解析 Worker 时有两个小坑千万留意：一是最后那条裸匹配 6 位数字的兜底正则，只准喂纯文本正文（`text/plain`），绝不能直接扫原始 HTML 邮件源码，否则分分钟把 CSS 样式里的 `#123456` 颜色十六进制码当成验证码塞回来；二是 Worker 往主程序发 HTTP POST 回调时一定要带 `Bearer` 共享密钥或 HMAC 签名，别开成谁都能往里灌假码的裸接口。

第四块是落库加密。新改出来的强密码、TOTP Base32 种子和会话 Cookie 在进数据库前，统一用 32 字节主密钥跑一遍 `AES-256-GCM` 认证加密。每次加密用 `os.urandom(12)` 现摇一个 96-bit 随机 Nonce，确保语义安全且绝不踩 GCM 最忌讳的 Nonce 复用大忌；更讲究一点的写法是把当前行的 `account_id` 编码成关联认证数据（AAD）一块儿喂进去，这样就算有人拿到了数据库读写权限，也没法把 A 账号的密文偷梁换柱贴到 B 账号头上：

```python
class CredentialCipher:
    def __init__(self, master_key: bytes):
        self._aesgcm = AESGCM(master_key)  # 32 字节主密钥

    def encrypt(self, plaintext: str, account_id: str) -> str:
        nonce = os.urandom(12)
        aad = account_id.encode("utf-8")
        ct = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return (nonce + ct).hex()
```

## 0x02 泼盆冷水：跑完这 8 步依然挡不住的四个真后门

看完了上面挺严整的自动化设计，最后得把原项目宣传里说的"覆盖全部后门、洗完即绝对安全"这个牛皮戳破。站在真实的 Google 账号安全体系面前，光跑完这 8 步，至少还漏着四道大口子。

头号大雷是 Google 官方专门为防盗号设计的"7 天旧恢复凭据保护窗口"。当一个账号在陌生设备或新 IP 上改掉了恢复手机号和恢复邮箱之后，在随后的整整 7 天之内，Google 的申诉与高危校验页面依然允许往修改之前的旧手机号或旧恢复邮箱发送验证码，一键把你改过的所有密码和二步验证全盘推翻！这是刻在 Google 服务端风控状态机里的硬规则，客户端脚本写得再花哨也绕不过这 7 天观察期。

第二处漏网之鱼是 8 位一次性备用验证码（Backup Codes）与 16 位应用专用密码（App Passwords）。Step 5 只重置了 Authenticator 的动态码种子，如果原持有人事先生成并存下了那 10 组 8 位备用码，脚本没去主动点销毁重生成，旧备用码照样能过二步验证；应用专用密码虽然在改主密码时通常会被顺带吊销，但交接审计时同样得亲眼核对一遍列表为空才放心。

第三处最阴险，因为它压根不在 `myaccount.google.com` 的安全设置页里，而是藏在 Gmail 邮箱自己的后台（`mail.google.com/#settings/fwdandpop` 与账号导入页）：事先配好一条自动转发地址外加"收到验证码邮件自动归档跳过收件箱"的静默过滤器，或者在"授予对您账号的访问权限"里挂一个邮件委托（Mail Delegation）账号。哪怕你把外层的 Google 密码、Passkey、TOTP、OAuth 全换了一百遍，往后发进这个邮箱的所有敏感邮件还是会一封不落地抄送出去。

第四处则是物理硬件安全密钥（WebAuthn Security Keys）与绑在旧安卓手机系统层的 Google Prompt 设备推送，它们的权限权重和移除门槛都比普通网页 Passkey 棘手得多。所以真在正规业务交接里接管高价值 Google 账号，跑完凭据轮换只是走了万里长征第一步，老老实实进 Gmail 把转发规则、过滤器和委托列表翻个底朝天，再盯紧 7 天保护期届满后的安全检查清单，才算真正把门锁死。
