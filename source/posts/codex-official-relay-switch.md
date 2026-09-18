---
title: "Codex 官方订阅和中转怎么切换？手改配置与 CC-Switch 说明"
slug: "codex-official-relay-switch"
date: 2026-09-18T12:30:00+08:00
draft: false
weight: 50
categories: ["Codex常见问题"]
tags: ["Codex", "官方订阅", "中转", "CC-Switch", "配置"]
description: "分清 ChatGPT 登录、API Key 和第三方中转，用 profile 或 CC-Switch 安全切换 Codex 提供商。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

---

## 先分清两种登录

- **ChatGPT 登录**：使用订阅或工作区分配的 Codex 权限，额度、模型和重置时间由账号/工作区决定。
- **API Key 或中转**：走 API 计费和提供商自己的模型、限流与日志；并不等于把 ChatGPT 订阅“搬过去”。

在 CLI 中可用 `codex login status` 查看当前身份，用 `codex logout` 清除已保存的登录信息。

## 推荐用 profile 切换

官方支持在 `~/.codex/` 下建立多个 profile 文件，启动时选择，不必反复覆盖主配置：

```bash
codex --profile official
codex --profile relay
```

`~/.codex/relay.config.toml` 可以这样写一个**示例**（地址、环境变量名和模型名按服务商文档填写）：

```toml
model_provider = "my_relay"

[model_providers.my_relay]
name = "My relay"
base_url = "https://你的服务商地址/v1"
env_key = "MY_RELAY_API_KEY"
wire_api = "responses"
```

先复制备份原来的 `config.toml`，切换后完全退出并重开 Codex，再用一个很短的请求测试。项目目录里的 `.codex/config.toml` 不能覆盖提供商和身份验证设置，profile 应放在用户级目录。

## CC-Switch 能不能用

CC-Switch 是第三方工具，不是 OpenAI 官方产品。只从其[官方仓库或 Releases](https://github.com/farion1231/cc-switch) 下载；添加提供商后激活，关闭并重新打开 Codex，再检查模型名和请求地址是否正确。

中转服务能看到你发送的代码、提示词和可能的密钥，计费、留存和兼容性也由它决定。不要把 OpenAI OAuth/access token、`~/.codex/auth.json` 或 Cloudflare token 粘贴进文章、截图或中转配置。切换后历史记录暂时看不到，通常是 provider/session 不同，不代表数据被删除；切回原 provider 再检查即可。

参考：[Codex 身份验证](https://developers.openai.com/zh-Hans/docs/auth)｜[配置方案文件](https://developers.openai.com/zh-Hans/docs/config-file/config-reference)。
