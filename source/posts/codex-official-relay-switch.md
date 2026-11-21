---
title: "Codex 官方订阅和中转怎么切换？手改配置与 CC-Switch 说明"
slug: "codex-official-relay-switch"
date: 2026-09-18T12:30:00+08:00
draft: false
categories: ["Codex常见问题"]
tags: ["Codex", "官方订阅", "中转", "CC-Switch", "配置"]
description: "把 ChatGPT 订阅登录、OpenAI 官方 API 和第三方中转的账单与配置边界捋清楚，用 profile 文件干净切换。"
weight: 10
---

很多人刚开始混用官方订阅和第三方中转的时候，最爱干的一件事就是反复去涂改 `~/.codex/config.toml`，改来改去不是把原配置弄丢了，就是环境变量没对上，报出一堆莫名其妙的鉴权错。

动手之前先把这三条通道的账本分清楚。平时走浏览器 OAuth 登录的叫 ChatGPT 官方订阅模式，吃的是 Plus、Pro 或 Business 账号自带的周期窗口额度，登录态对不对直接敲 `codex login status` 就能看（顺手提一句，`codex logout` 会把本机保存的 ChatGPT 登录态和 API Key 凭据一块儿清掉，没事别乱敲）。用 `printenv OPENAI_API_KEY | codex login --with-api-key` 绑 API Key 的是 OpenAI 官方按量 API，按 Token 扣 `platform.openai.com` 的预付美元余额，受组织 Tier 速率和项目预算限制。至于第三方中转，完全走服务商自己发的 Key、自己的转发地址和限流日志，跟前两条通道互不相通。

三者的会话历史、权限和计费彼此独立，千万别为了切个中转就把本地存着官方登录态的 `~/.codex/auth.json` 删掉，更别把这个文件发给任何人。

## 0x00 用独立 profile 文件切换最省心

新版 Codex CLI 原生支持在 `~/.codex/` 目录下并排放多个 `<名称>.config.toml` 方案文件，启动时传个 `--profile` 参数就能指定跑哪套。

动手前先把主配置文件备份一份留底：

```bash
cp ~/.codex/config.toml ~/.codex/config.toml.bak-$(date +%Y%m%d-%H%M%S)
```

假设平时主力跑官方订阅，主配置 `~/.codex/config.toml`（或者单独建个 `~/.codex/official.config.toml` 放个人偏好）留给官方不动；另外新建一个 `~/.codex/relay.config.toml` 专门放中转配置，里面的地址、模型名和环境变量名照着你实际用的服务商文档填：

```toml
model = "gpt-5-codex" # 按中转服务商实际提供的模型名修改
model_provider = "my_relay"

[model_providers.my_relay]
name = "My Relay"
base_url = "https://你的中转服务商地址/v1"
env_key = "MY_RELAY_API_KEY"
wire_api = "responses"
```

注意 `wire_api = "responses"` 这一行：新版 Codex CLI 的 `wire_api` 只支持 `responses`，只兼容老 `/chat/completions` 接口的中转在现行版本上是跑不通的。

配好之后，切换前先把正在跑的旧 Codex 会话彻底关掉，免得旧进程还抱着旧配置不放；然后在同一个已经 `export` 了密钥环境变量的终端里拉起（如果直接从 macOS Dock 或 Windows 开始菜单点开 Codex 桌面端，它读不到终端临时 `export` 的变量，得把变量配进系统级用户环境或从该终端启动）：

```bash
export MY_RELAY_API_KEY="sk-xxxx"

# 指定走中转配置启动，先发一句不带敏感代码的短消息验一下连通和实际命中的地址
codex --profile relay

# 测完退出，不带参数（或传 --profile official）即回到官方通道
codex
```

项目根目录下的 `.codex/config.toml` 只适合放项目级偏好，覆盖不了提供商、认证和 profile 这类本机设置，所以切换方案一律放在用户家目录 `~/.codex/` 下。实在不想分 profile、非要手改主文件 `~/.codex/config.toml` 也行，记得先备份（改坏了直接把备份覆盖回去），注意别在同一份 TOML 里留下两个重名的 `[model_providers.xxx]` 段，也别把明文 Key 提交进 Git 仓库。

## 0x01 用 CC-Switch 图形化切换要注意什么

嫌手写 TOML 麻烦的话，社区开源的第三方小工具 [CC-Switch](https://github.com/farion1231/cc-switch) 也能拿来点选切换，下载时认准作者的 GitHub Releases 页面即可。点切换之前照样先把 `~/.codex` 目录备份一份；它本质上只是替你覆写本地配置文件，管不了服务商协议不兼容或额度用尽，激活新配置后一样得彻底重启 Codex 再发短消息核对一眼。

最后留几个心眼。第一，第三方中转网关在技术上能看到你发过去的所有代码片段、提示词和请求元数据；写写个人玩具项目无所谓，碰到公司核心仓库或者带内网地址、密钥的生产代码，先脱敏或者老老实实切回官方通道跑。第二，切完通道发现之前的聊天记录不见了先别慌，不同 provider 或不同工作目录的会话本来就是分开挂的，切回原来的配置和原目录自然就回来了。另外如果遇到官方登录完全正常、只有切到中转才报错，优先找中转服务商查上游；要是两边一起挂，再回头查本机网络和 OpenAI 状态页。

底层配置字段随版本升级偶有调整，拿不准的时候直接翻官方的 [Codex 身份验证说明](https://developers.openai.com/codex/auth) 和 [配置文件参考手册](https://developers.openai.com/codex/config-reference)。
