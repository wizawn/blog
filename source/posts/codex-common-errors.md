---
title: "Codex 常见报错怎么处理：capacity、429、503、usage_limit 一次看懂"
slug: "codex-common-errors"
date: 2026-09-18T12:40:00+08:00
draft: false
weight: 50
categories: ["Codex常见问题"]
tags: ["Codex", "429", "503", "usage_limit", "故障排查"]
description: "用简单的方式区分 Codex 模型过载、请求限流、服务不可用和周期额度用尽，并给出对应处理办法。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

---

同样是“发不出去”，原因可能完全不同。先看完整报错、HTTP 状态和 `error.code`，再决定怎么处理；不要看到一个 `429` 就一律等，也不要看到 `capacity` 就马上换账号。

| 提示 | 常见原因 | 建议 |
|---|---|---|
| 提示/状态 | 常见原因 | 先做什么 |
|---|---|---|
| `Selected model is at capacity` | 目标模型当前没有足够容量；常见于模型瞬时拥堵 | 等几分钟，换一个可用模型，查看[状态页](https://status.openai.com/)。如果所有模型长期失败，再检查账号/工作区并联系支持；不能仅凭这句话断言账号没问题或一定被标记。 |
| `server_is_overloaded`（通常为 `503`） | 模型或服务端暂时过载 | 有 `Retry-After` 就按它等待；没有时逐步拉长间隔，并查看状态页。 |
| `429 Too Many Requests`、`rate_limit_error` | 请求太密、并发过高、Token 突然增长，或同一组织的其他程序也在用额度 | 降低并发，停止重复点击；按 `Retry-After` 等待，没有时用逐渐加长的退避，只重试有限次数。 |
| `429` + `slow_down` | 流量增长过快，即使还没达到每分钟上限也可能触发 | 让请求速率稳定下来，等一段时间后再逐步恢复，不要短时间内把并发重新拉满。 |
| `429` + `credit_balance_exhausted` | API 预付余额耗尽 | 补充余额；单纯等待不会恢复。 |
| `429` + `project_spend_limit_exceeded` / `organization_spend_limit_exceeded` | 项目或组织支出上限 | 让管理员调整对应限额，或等账期恢复；先确认是哪个项目在发请求。 |
| `429` + `organization_usage_limit_exceeded` | 组织用量上限达到 | 联系组织管理员或 OpenAI 支持申请更高的用量上限。 |
| `usage_limit_reached` | ChatGPT/Codex 计划周期内的使用量达到上限 | 查看 Codex 用量页面或提示中的 reset 时间，按页面提供的等待、加额度或升级选项处理；支持团队通常不会人工提前重置周期额度。 |
| `server_unavailable`、`503 Service Unavailable` | 服务暂时不可用、网络出口异常，或客户端重试已耗尽 | 先确认状态页、网络和代理，再按退避规则重试；不要无限循环。 |
| `exceeded retry limit` | 客户端已经用完本次请求的重试次数 | 它不是新的根因，回看它前面的最后一个 `429`、`503`、超时或连接错误。 |

另外，`401/403` 更像是登录、权限、组织/项目或地区设置问题：官方登录先运行 `codex login status`，API 则检查 Key、组织和项目；不要先反复换网络。`400` 往往是参数、模型名或接口格式不对；`500` 是服务端内部错误，短暂等待并查状态页即可。

## 一个简单的判断流程

1. 看 HTTP 状态和 `error.code`，不要只看界面上一行摘要。
2. `401/403` 先查登录和权限；`429` 先区分限流、余额和组织/项目上限。
3. `503`、`server_is_overloaded` 或 `capacity` 先等、换模型、查状态页；不要因为一次过载就重装客户端。
4. 只有在等待和退避后仍失败，才做网络/代理对照，并尝试新会话。

向支持反馈时记录模型、客户端版本、请求时间和时区、完整错误、HTTP 状态、`error.code`、请求 ID（如有）、是否换模型/网络后恢复。反馈时删掉 API Key、`auth.json`、OAuth/access token、代码和代理密钥。官方建议对于限流遵守 `Retry-After`，并限制重试次数；账单、余额和用量错误不能靠继续重试解决。

官方说明：[错误代码](https://developers.openai.com/zh-Hans/api/docs/guides/error-codes)｜[速率限制](https://developers.openai.com/zh-Hans/api/docs/guides/rate-limits)｜[Codex 用量](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)。
