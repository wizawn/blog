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

## 这是什么问题

`Reconnecting` 表示 Codex 与模型之间的流式连接中断，客户端正在自动重连。官方配置参考中，`stream_max_retries` 的默认值就是 5，所以“重试 5 次”本身不等于账号被封，也不等于额度用完。

## 按这个顺序处理

1. **先停手等一会儿**：只偶尔出现，通常是网络抖动、代理节点或模型临时繁忙。不要连续点击发送。
2. **更新并重启 Codex**：同时检查代理、DNS、IPv6 和公司网络是否拦截了 WebSocket；可以用手机热点做一次对照测试。
3. **只在反复出现时尝试改传输方式**：先备份 `~/.codex/config.toml`，在用户级配置中为兼容的 Responses 提供商增加以下选项（端点请以提供商文档为准）：

```toml
model_provider = "openai_http"

[model_providers.openai_http]
name = "OpenAI HTTP"
base_url = "https://你的兼容服务地址/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
```

这相当于要求该提供商使用 HTTP/SSE；`requires_openai_auth = true` **只适用于端点明确支持 OpenAI/ChatGPT 登录的情况**，不要把 OAuth 凭据填给普通中转。第三方中转应按其文档使用环境变量密钥。不是所有 Codex 版本或内置 `openai` 提供商都一定生效；改完后完全退出并重新打开 Codex。

## 仍然不行怎么办

删除刚才新增的配置段，或恢复备份，再换一个模型/新建会话。若只有某个模型失败，优先按“模型暂时不可用”处理；若所有模型长期失败，再记录客户端版本、模型、发生时间、完整报错和请求 ID，提交到 [OpenAI 帮助中心](https://help.openai.com/)。不要上传 `auth.json`、API Key 或任何代理密钥。

参考：[Codex 配置参考](https://developers.openai.com/zh-Hans/docs/config-file/config-reference)。
