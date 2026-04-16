---
title: "CLI Proxy API 配置详解 - 从入门到精通的完整指南（2026 最新版）"
date: 2026-04-16T11:38:00Z
draft: false
categories: ["技术教程", "AI 工具"]
tags: ["CLI Proxy API", "Codex", "Claude", "配置教程", "API 中转"]
description: "超详细！手把手教你配置 CLI Proxy API，搞定 Codex/Claude/Gemini 多账号管理，轻松实现 API 中转和负载均衡"
image: "/blog-cover-default.jpg"
weight: -998
---

> **💬 ChatGPT Plus 充值服务**
> 
> | 套餐 | 价格 | 说明 |
> |------|------|------|
> | Plus 一个月 (无质保) | ¥15 | 掉了不补 |
> | Plus 一个月 (有质保) | ¥35 | 掉了包补 |
> | Pro 200 刀 (一个月无质保) | ¥350 | - |
> | Pro 200 刀 (一个月质保) | ¥550 | - |
> | Pro 100 刀 (一个月无质保) | ¥200 | - |
> 
> **微信联系购买，秒发货！**

---

## 前言

嘿，朋友们！今天咱们来聊一个超级实用的东西——**CLI Proxy API 配置文件**。

说实话，刚开始我看到这密密麻麻的配置项时，整个人都是懵逼的。啥是 `round-robin`？`quota-exceeded` 又是啥？别急，看完这篇教程，我保证你也能成为配置高手！

咱们就拿着真实的配置文件，一项一项来拆解，保证通俗易懂，连我这个小白都能看懂（好吧，其实我已经研究了好几天了😅）。

---

## 一、基础配置：先把服务跑起来

### 1.1 监听地址和端口

```yaml
host: ""
port: 8317
```

**通俗解释**：
- `host: ""` 意思是监听所有网络接口，简单说就是**谁都能访问**
- `port: 8317` 就是服务运行的端口号

**⚠️ 安全提示**：
如果你想让服务只在本机运行（不让外人访问），改成：
```yaml
host: "127.0.0.1"  # 或 "localhost"
```

### 1.2 HTTPS 配置（可选）

```yaml
tls:
  enable: false
  cert: ""
  key: ""
```

这个不用多说，想启用 HTTPS 就填上你的证书和私钥。不过说实话，本地测试的话 HTTP 就够了，毕竟咱们是在内网用嘛~

---

## 二、管理 API：控制面板的配置

### 2.1 远程管理权限

```yaml
remote-management:
  allow-remote: true
  secret-key: "$2a$10$Q6P9MnBjFuqO1wOuq2QRP.NUZLeCr2vLJX.5DPtsma/izTljxoVaO"
  disable-control-panel: false
```

**解读**：
- `allow-remote: true` 允许远程访问管理面板
- `secret-key` 是管理密码（已经加密过了）
- `disable-control-panel: false` 表示启用控制面板

**💡 小贴士**：
如果你不想让别人访问你的管理面板，把 `allow-remote` 改成 `false` 就行，这样只有本机才能访问。

### 2.2 管理面板来源

```yaml
panel-github-repository: "https://github.com/router-for-me/Cli-Proxy-API-Management-Center"
```

这个就是管理面板的 GitHub 仓库地址，系统会自动从这里下载面板。

---

## 三、认证配置：谁能访问你的服务

### 3.1 认证目录

```yaml
auth-dir: "~/.cli-proxy-api"
```

这个目录用来存储认证信息（比如 OAuth token 之类的）。`~` 代表你的用户主目录。

### 3.2 API 密钥

```yaml
api-keys:
  - yanling6,hate
```

**重点来了！** 这里就是你的**访问密码**。客户端连接时需要提供这个密钥。

**⚠️ 安全警告**：
- 千万别把这个密钥泄露给别人！
- 建议改成更复杂的密码，比如 `MySuperSecretKey2026!`
- 可以配置多个密钥，给不同的人用

---

## 四、核心功能配置

### 4.1 请求重试

```yaml
request-retry: 3
```

这个很实用！如果请求失败（比如遇到 502、503 错误），系统会自动重试 3 次。

**重试的场景**：
- 403 Forbidden
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

说白了，就是遇到这些错误别急着报错，多试几次说不定就好了~

### 4.2 配额管理

```yaml
quota-exceeded:
  switch-project: true
  switch-preview-model: true
  antigravity-credits: true
```

**这是啥意思？**

假设你有个账号的配额用完了，系统会自动：
1. `switch-project: true` → 切换到另一个项目
2. `switch-preview-model: true` → 切换到预览版模型
3. `antigravity-credits: true` → 尝试用 Google One AI 信用

**通俗点说**：就是**自动备胎**！一个账号用完了，自动换下一个，不用你手动操作。

### 4.3 路由策略

```yaml
routing:
  strategy: "round-robin"
```

**round-robin** 是啥？就是**轮询**！

举个例子：你有 3 个账号，第一个请求用账号 A，第二个用账号 B，第三个用账号 C，第四个又回到账号 A... 如此循环。

**好处**：负载均衡，不会把某个账号用废了~

---

## 五、API 密钥配置（重点！）

### 5.1 Codex API 配置

```yaml
# codex-api-key:
#   - api-key: "sk-atSM..."
#     prefix: "test"
#     base-url: "https://www.example.com"
#     models:
#       - name: "gpt-5-codex"
#         alias: "codex-latest"
```

**解读**：
- `api-key`：你的 Codex API 密钥
- `base-url`：API 端点地址（如果是 CPA 中转，这里填 CPA 的地址）
- `models`：支持的模型列表
- `alias`：你给模型起的别名

**💡 实用技巧**：
如果你有多个 CPA 服务商，可以这样配置：

```yaml
codex-api-key:
  - api-key: "sk-packycode-xxx"
    base-url: "https://codex-api.packycode.com/v1"
    weight: 70  # 70% 的流量走这里
  - api-key: "sk-88code-xxx"
    base-url: "https://www.88code.org/openai/v1"
    weight: 30  # 30% 的流量走这里
```

这样就实现了**负载均衡**！

### 5.2 Claude API 配置

```yaml
# claude-api-key:
#   - api-key: "sk-atSM..."
#     base-url: "https://www.example.com"
#     models:
#       - name: "claude-3-5-sonnet-20241022"
#         alias: "claude-sonnet-latest"
```

和 Codex 配置类似，不过 Claude 有个特殊功能——**cloaking（伪装）**：

```yaml
cloak:
  mode: "auto"  # 自动伪装
  sensitive-words:
    - "API"
    - "proxy"
```

**这是干啥的？**

简单说，就是**隐藏你的代理身份**。有些上游服务会检测你是不是在用代理，这个功能可以帮你绕过检测。

**⚠️ 注意**：
- `mode: "auto"` 只在非 Claude Code 客户端时伪装
- `mode: "always"` 总是伪装
- `mode: "never"` 从不伪装

### 5.3 Gemini API 配置

```yaml
# gemini-api-key:
#   - api-key: "AIzaSy...01"
#     base-url: "https://generativelanguage.googleapis.com"
#     models:
#       - name: "gemini-2.5-flash"
#         alias: "gemini-flash"
```

Gemini 的配置也差不多，不过有个特殊功能——**模型排除**：

```yaml
excluded-models:
  - "gemini-2.5-pro"
  - "gemini-2.5-*"
  - "*-preview"
```

**这是啥意思？**

就是**不想显示某些模型**。比如你觉得 `gemini-2.5-pro` 太贵不想用，就把它排除掉。

**通配符用法**：
- `gemini-2.5-*` 排除所有 `gemini-2.5-` 开头的模型
- `*-preview` 排除所有 `-preview` 结尾的模型
- `*flash*` 排除所有包含 `flash` 的模型

---

## 六、OpenAI 兼容配置

```yaml
# openai-compatibility:
#   - name: "openrouter"
#     base-url: "https://openrouter.ai/api/v1"
#     api-key-entries:
#       - api-key: "sk-or-v1-...b780"
#     models:
#       - name: "moonshotai/kimi-k2:free"
#         alias: "kimi-k2"
```

这个功能超实用！**可以把任何兼容 OpenAI 接口的服务接进来**。

**举个例子**：
你想用 Kimi、通义千问、文心一言等模型，但它们不是原生支持怎么办？用这个配置！

```yaml
openai-compatibility:
  - name: "your-provider"
    base-url: "https://your-provider.com/v1"
    api-key-entries:
      - api-key: "sk-your-key"
    models:
      - name: "qwen-2.5-72b"
        alias: "qwen-max"
      - name: "kimi-k2"
        alias: "kimi"
```

这样你就能像调用原生模型一样调用这些第三方模型了~

---

## 七、高级配置（可选）

### 7.1 代理配置

```yaml
proxy-url: "socks5://user:pass@192.168.1.1:1080/"
```

如果你需要翻墙访问某些服务，这里填你的代理地址。

**支持的协议**：
- `socks5://`
- `http://`
- `https://`

### 7.2 调试配置

```yaml
debug: false
pprof:
  enable: false
  addr: "127.0.0.1:8316"
```

**debug: true** 会输出详细日志，方便排查问题。

**pprof** 是性能分析工具，一般用不到，开启后可以访问 `http://127.0.0.1:8316/debug/pprof` 查看性能数据。

### 7.3 日志配置

```yaml
logging-to-file: false
logs-max-total-size-mb: 0
error-logs-max-files: 10
```

- `logging-to-file: true` 把日志写到文件（而不是控制台）
- `logs-max-total-size-mb: 100` 日志文件最大 100MB，超了自动删除旧的
- `error-logs-max-files: 10` 最多保留 10 个错误日志文件

---

## 八、实战：完整配置示例

好了，说了这么多，来个完整的配置示例：

```yaml
# 基础配置
host: ""
port: 8317

# 管理配置
remote-management:
  allow-remote: true
  secret-key: "你的管理密码"

# 认证配置
auth-dir: "~/.cli-proxy-api"
api-keys:
  - "你的客户端访问密钥"

# Codex 配置（多 CPA 负载均衡）
codex-api-key:
  - api-key: "sk-packycode-xxx"
    base-url: "https://codex-api.packycode.com/v1"
    weight: 70
  - api-key: "sk-88code-xxx"
    base-url: "https://www.88code.org/openai/v1"
    weight: 30

# Claude 配置
claude-api-key:
  - api-key: "sk-claude-xxx"
    base-url: "https://api.claude-provider.com"
    models:
      - name: "claude-sonnet-4-20250514"
        alias: "claude-sonnet"

# 配额管理
quota-exceeded:
  switch-project: true
  switch-preview-model: true

# 路由策略
routing:
  strategy: "round-robin"

# 重试配置
request-retry: 3
```

---

## 九、常见问题

### Q1: 配置后无法启动？
**检查**：
- YAML 格式是否正确（缩进是否对齐）
- 端口是否被占用（`netstat -tlnp | grep 8317`）
- 密钥格式是否正确

### Q2: 请求失败怎么办？
**排查步骤**：
1. 打开 `debug: true` 查看详细错误
2. 检查 API Key 是否有效
3. 检查 Base URL 是否正确
4. 检查网络连接（是否需要代理）

### Q3: 如何实现多个账号轮流使用？
**配置**：
```yaml
codex-api-key:
  - api-key: "sk-key1"
    base-url: "https://cpa1.com/v1"
  - api-key: "sk-key2"
    base-url: "https://cpa2.com/v1"
routing:
  strategy: "round-robin"
```

### Q4: 如何限制某些模型的访问？
**配置**：
```yaml
excluded-models:
  - "gpt-5-codex-mini"
  - "claude-opus-*"
```

---

## 十、总结

好了，今天的教程就到这里！

**重点回顾**：
1. **基础配置**：host、port、tls
2. **管理配置**：remote-management、secret-key
3. **认证配置**：api-keys（别泄露！）
4. **API 配置**：codex-api-key、claude-api-key、gemini-api-key
5. **高级功能**：负载均衡、模型排除、自动重试

**最后提醒**：
- 配置前**备份原文件**
- 修改后**重启服务**
- 密钥**千万别泄露**
- 遇到问题**开 debug 模式**

如果还有不懂的，欢迎在评论区留言，我看到会回复的~

---

## 参考资料

- CLI Proxy API GitHub: https://github.com/router-for-me/cli-proxy-api
- 管理面板：https://github.com/router-for-me/Cli-Proxy-API-Management-Center
- 配置示例：查看官方文档

---

*本文基于真实配置文件编写，配置项可能随版本更新而变化，请以官方文档为准。*

*觉得有用？别忘了分享给更多需要的朋友！👍*
