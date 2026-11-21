---
title: "Codex 提示 Reconnecting 5 次，怎么处理？"
slug: "codex-reconnecting-5-times"
date: 2026-09-18T12:20:00+08:00
draft: false
categories: ["Codex常见问题"]
tags: ["Codex", "Reconnecting", "网络排查", "Responses API"]
description: "看到 Codex 连跳 5 次 Reconnecting 先别慌着换号，那是默认的流式重连上限，按网络、模型和协议顺序排一遍很快就能定位。"
weight: 10
---

群里隔三差五就有人截图问：Codex 界面上连着蹦了 5 次 `Reconnecting`，最后直接断掉，是不是账号被风控封了？

其实跟封号没半毛钱关系。Codex 在流式接收响应时一旦中途断流就会尝试重连，官方配置里控制流式重连次数的 `stream_max_retries` 默认值是 `5`（普通 HTTP 请求重试 `request_max_retries` 默认是 `4`）。跳满 5 次只说明这一轮重连配额用光了，真正说明病因的是重连耗尽后吐出来的最后那一行具体报错和 HTTP 状态码。

## 0x00 先看症状对号入座，别连着狂点

撞上断流先停手别每秒狂按发送，不然本来只是瞬时抖动，硬生生被你点成真限流。对照现象大概分四种情况处理：

如果半天只偶发这么一回，多半是 Wi-Fi 抖了、代理节点切线或者上游瞬时抽风，如果响应头里带了 `Retry-After` 就按秒数等够，没带就缓几十秒重发一次。如果是死磕某一个模型必断、换个别的模型立马顺畅，那是目标模型算力池拥堵，先换模型干活并看一眼官方状态页，千万别手欠去改认证文件。

要是所有模型、开新会话全断，就得做一次干净的网络对照：拿手机开个热点连上去发一句短话试试，同时看一眼本机系统时间准不准、DNS 和 IPv6 有没有抽风、公司内网防火墙有没有拦 HTTPS 或 WebSocket。手机热点秒通而家里宽带死活不通，锅多半在本地路由、运营商 DNS 或代理分流规则上；跑官方登录的顺手敲一下 `codex login status` 看凭据还在不在，跑中转的确认终端里对应的 API Key 环境变量没丢。

最后一种是一敲回车秒进重连，怎么换网都没用，这基本都是自己改过的 `config.toml` 出了岔子：`base_url` 拼错了、服务商根本不支持 Responses API，或者中间网关拦了 WebSocket。

## 0x01 兼容网关拦 WebSocket 时，切回 HTTP/SSE

部分反代、CDN 或兼容网关已经支持了 OpenAI 的 `/responses` 接口，但没配好 WebSocket 升级头（`Upgrade: websocket`），导致客户端一建 WebSocket 流就断。确认是这个毛病时，先备份好原配置，在提供商段里加一行 `supports_websockets = false` 强制退回走 HTTP SSE 流。

这里一定要分清你接的是第三方中转还是公司内网底下的官方认证端点，两者的鉴权写法绝对不能混：

```toml
# 情况 A：接第三方兼容服务商（用 env_key 传中转 Key，严禁开启 requires_openai_auth！）
model_provider = "custom_http"

[model_providers.custom_http]
name = "Custom Responses HTTP"
base_url = "https://你的兼容服务地址/v1"
env_key = "CUSTOM_API_KEY"
wire_api = "responses"
supports_websockets = false
```

```toml
# 情况 B：仅限走官方自有端点但公司防火墙拦了 WebSocket（切勿填任何第三方地址！）
model_provider = "openai_http"

[model_providers.openai_http]
name = "OpenAI Responses HTTP"
base_url = "https://chatgpt.com/backend-api/codex"
requires_openai_auth = true
wire_api = "responses"
supports_websockets = false
```

面对任何第三方中转地址千万别开 `requires_openai_auth = true`，否则 Codex 会把你本机的官方 ChatGPT OAuth 令牌直接发给第三方服务器。另外如果中转商压根没实现 Responses API、只支持旧版 Chat Completions，单关 WebSocket 也救不活，得先翻服务商文档确认协议支持情况。

每次只改一项配置，别一着急把重装客户端、清凭据、换中转全搅在一块儿干，更别去删整个 `~/.codex` 目录；改完把 Codex 彻底退出重开（光关窗口没退出后台进程是不生效的），测完没改善就把备份文件覆盖回去。也别去把 `stream_max_retries` 调成几十上百，底层链路不通的时候硬拉高重试上限，除了干等更久和多发一堆重复请求之外没有任何意义。

要是更新到最新稳定版、切手机热点、恢复默认配置全试过了还是断，把客户端版本、操作系统、模型名、当前走的是官方登录还是 API/中转、带时区的发生时间、请求 ID、换网络或换模型后的结果以及最后一条完整报错（隐去邮箱、代码、`auth.json` 和各类密钥）记下来发给 [OpenAI 帮助中心](https://help.openai.com/) 就行。相关字段定义见 [Codex 配置参考](https://developers.openai.com/codex/config-reference) 与 [OpenAI 错误代码说明](https://developers.openai.com/zh-Hans/api/docs/guides/error-codes)。
