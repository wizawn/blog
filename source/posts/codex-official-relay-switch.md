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

## 先分清三件事：订阅、API、真正的中转

| 方式 | 凭据/计费 | 失败时先看什么 |
|---|---|---|
| ChatGPT 官方登录 | 浏览器登录的账号或工作区；受计划、用量和重置时间影响 | `codex login status`、账号/工作区用量 |
| OpenAI API | API Key；按组织/项目的余额、限额和速率计费 | Key、项目、余额、`429`/`usage` 错误 |
| 第三方中转 | 服务商自己的 Key、模型、限流和日志 | 中转文档、接口兼容性、服务商状态 |

API Key 或中转不是“把 ChatGPT 订阅搬到另一个地址”。三者的会话、历史、权限和账单彼此独立。CLI 中可用 `codex login status` 查看当前官方登录，用 `codex logout` 清除本机保存的官方登录；不要为了切到 API 就把 `auth.json` 发给别人。

## 推荐用 profile 切换

官方支持在 `~/.codex/` 下建立多个 profile 文件，启动时选择，不必反复覆盖主配置。先备份原文件，再创建配置：

```bash
cp ~/.codex/config.toml ~/.codex/config.toml.backup-$(date +%Y%m%d-%H%M%S)
codex --profile official
codex --profile relay
```

`~/.codex/official.config.toml` 可以只放官方相关的个人偏好；`~/.codex/relay.config.toml` 可以这样写一个**示例**（地址、环境变量名和模型名按服务商文档填写）：

```toml
model_provider = "my_relay"

[model_providers.my_relay]
name = "My relay"
base_url = "https://你的服务商地址/v1"
env_key = "MY_RELAY_API_KEY"
wire_api = "responses"
```

切换时建议按这个顺序：

1. 关闭正在运行的 Codex 会话，避免旧进程继续使用旧配置。
2. 确认环境变量已在**启动 Codex 的同一个终端**中设置，再执行 `codex --profile relay`。
3. 用一句不含敏感信息的短请求测试；同时确认报错中的请求地址和模型确实属于目标提供商。
4. 测试完成后退出，再用 `codex --profile official` 切回官方。

项目目录里的 `.codex/config.toml` 只适合项目级偏好，不能覆盖提供商、认证、profile 等本机设置；profile 必须放在用户级 `~/.codex/profile-name.config.toml`。Codex 版本升级后配置键可能变化，先看当前版本的官方配置参考。

如果不想使用 profile，也可以手动编辑 `~/.codex/config.toml`：先备份，替换 `model_provider` 和对应的 `[model_providers.xxx]`，测试后不满意就把备份文件恢复。不要在同一份配置中留下两个同名提供商，也不要把真实 Key 写进 Git 仓库。

## CC-Switch 能不能用

CC-Switch 是第三方工具，不是 OpenAI 官方产品。只从其[官方仓库或 Releases](https://github.com/farion1231/cc-switch) 下载。一般流程是：备份 `~/.codex` 配置 → 添加提供商 → 填写服务商要求的地址、模型和 Key → 激活 → 完全重启 Codex → 发短请求验证。工具只是帮你改配置，不会替你解决服务商不兼容、额度或封禁问题；激活后仍要检查实际请求地址和模型。

中转服务通常能看到你发送的代码、提示词和请求元数据，计费、留存、审计和兼容性也由它决定。不要把 OpenAI OAuth/access token、`~/.codex/auth.json`、API Key 或 Cloudflare token 粘贴进文章、截图或中转配置。生产代码先脱敏，能不用中转处理的敏感项目不要使用不明服务商。

切换后历史记录暂时看不到，通常是 provider、账号或 session 不同，不代表数据被删除；先切回原 provider、原 profile 和原工作目录检查。若官方登录正常而中转失败，优先找中转服务商；若所有方式都失败，再看网络和 OpenAI 状态。

参考：[Codex 身份验证](https://developers.openai.com/zh-Hans/docs/auth)｜[配置方案文件](https://developers.openai.com/zh-Hans/docs/config-file/config-reference)。
