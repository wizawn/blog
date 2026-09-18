---
title: "Codex 提示 Reconnecting 5 次，怎么处理？"
slug: "codex-reconnecting-5-times"
date: 2026-09-18T12:20:00+08:00
draft: false
weight: 50
categories: ["Codex常见问题"]
tags: ["Codex", "Reconnecting", "网络排查", "Responses API"]
description: "Codex 反复 Reconnecting，重试五次后才响应时，按网络、客户端和传输方式逐步排查。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

---

## 先给结论：5 次是重试上限，不是封号提示

`Reconnecting` 表示流式连接中断，Codex 正在重新建立连接。官方配置参考中，`stream_max_retries` 的默认值是 5，所以“重试 5 次”只说明这一次请求的连接重试用完了，不能据此判断账号被封、订阅失效或额度用完。真正要看的是最后一条错误、HTTP 状态码和是否只影响某一个模型。

## 先判断是哪一类

- **只有偶尔一次**：更像 Wi-Fi、代理节点、DNS 或服务端瞬时抖动。等几十秒后重新发一次即可。
- **同一个模型总失败，换模型正常**：优先按模型容量或临时过载处理，先换模型或查看状态页。
- **所有模型、所有会话都失败**：再检查登录状态、代理出口、时间/证书、工作区权限和客户端版本。
- **一输入就重连，换网络也一样**：可能是配置中的 `base_url`、协议或认证方式不匹配，不要盲目增加重试次数。

## 按顺序排查，避免反复点击

1. **停止连点，等待一次完整重试**。如果错误中有 `Retry-After`，至少等够该时间；没有时也不要每秒重复发送，这会把临时限流变成更严重的限流。
2. **做一次网络对照**。暂时关闭不必要的代理规则，或用手机热点测试；同时检查 DNS、系统时间、IPv6 和公司防火墙是否拦截 HTTPS/WebSocket。热点正常而家中网络失败，通常不是账号问题。
3. **更新并完全重启 Codex**。保存当前输入，升级到较新的稳定版本，退出应用（不是只关窗口）后重新打开，再用一句很短的请求测试。
4. **检查登录和模型范围**。官方登录可以运行 `codex login status`；API/中转则检查对应环境变量是否仍存在、模型名是否由服务商支持。只换模型就恢复时，不要先改认证文件。
5. **只有确认是兼容端点的传输问题时，才改配置**。先备份配置，改一项，重启后测试；不要同时改代理、模型和登录方式，否则无法知道是哪一步起作用。

## 需要 HTTP/SSE 时的配置示例

下面只适用于**明确支持 OpenAI Responses API 的兼容端点**。它把 WebSocket 关闭，改为 HTTP/SSE；不是所有 Codex 版本或内置提供商都支持同样的覆盖方式。

```toml
model_provider = "openai_http"

[model_providers.openai_http]
name = "OpenAI HTTP"
base_url = "https://你的兼容服务地址/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
```

这相当于要求该提供商使用 HTTP/SSE。注意三点：

1. `requires_openai_auth = true` **只**适用于端点明确支持 OpenAI/ChatGPT 登录的情况；普通中转不要填 OAuth 登录信息。
2. 第三方中转应按其文档使用 `env_key` 或环境变量密钥，不能把 API Key 直接写进公开仓库或截图。
3. 如果服务商只支持 Chat Completions、不支持 Responses API，`wire_api = "responses"` 也会失败；先看服务商文档，不要靠猜。

改完后完全退出并重新打开 Codex。仍失败就删除新增配置段、恢复备份，再回到原来的配置验证。不要把 `stream_max_retries` 无限制调大：连接本身不通时，只会让你等更久，也可能造成重复请求。

## 仍然不行：这样收集信息最有用

恢复备份后，记录以下内容再提交到[OpenAI 帮助中心](https://help.openai.com/)：客户端版本、操作系统、所用模型、发生时间和时区、是官方登录还是 API/中转、最后一条完整报错、请求 ID（如果有）、换网络或换模型后的结果。可以截取错误文字，但要遮住邮箱、代码、API Key、OAuth/access token、`auth.json` 和中转密钥。

不要先删除整个 `~/.codex` 目录，也不要把“重装、清空凭据、换多个中转”同时做掉；这些操作可能丢失本地配置和排查线索。

参考：[Codex 配置参考](https://developers.openai.com/zh-Hans/docs/config-file/config-reference)｜[OpenAI 错误代码](https://developers.openai.com/zh-Hans/api/docs/guides/error-codes)。
