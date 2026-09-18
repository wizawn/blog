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

同样是“发不出去”，原因可能完全不同。先看完整报错和最后一次 HTTP 状态，再决定怎么处理。

| 提示 | 常见原因 | 建议 |
|---|---|---|
| `Selected model is at capacity` / `server_is_overloaded` | 所选模型当前容量不足或服务端过载 | 等几分钟、换一个可用模型、查看 [状态页](https://status.openai.com/)。持续影响所有模型时，再检查账号/工作区并联系支持；不要武断地认为一定不是账号问题。 |
| `429 Too Many Requests` / `slow_down` | 短时间请求太密、并发过高或 Token 增长过快 | 看到 `Retry-After` 就至少等够该时间；没有时采用逐渐拉长间隔的退避，不要连续狂点。 |
| `429` 搭配 `credit_balance_exhausted`、`spend_limit_exceeded` 等 | 余额、项目/组织支出或用量上限 | 单纯等待通常无效，应补余额、调整限额或联系管理员。 |
| `503`、`server_unavailable`、`server_is_overloaded` | 服务或模型暂时不可用 | 等待并查看状态页；不要无限重试。 |
| `usage_limit_reached` | 当前计划周期内的 Codex 用量达到上限 | 看 Codex 用量页/提示中的 reset 时间，按页面提供的“等待、加额度或升级”等选项处理。支持团队不会手动重置额度。 |
| `exceeded retry limit` | 客户端已经把重试次数用完 | 它不是新的根因；回看最后的 429、503 或网络错误。 |

另外，`401/403` 更像是登录、权限或工作区设置问题，先运行 `codex login status`，不要先反复换网络。任何问题都建议记录模型、客户端版本、时间（含时区）和请求 ID；反馈时删掉 API Key、`auth.json` 和代理密钥。

官方说明：[错误代码](https://developers.openai.com/zh-Hans/api/docs/guides/error-codes)｜[速率限制](https://developers.openai.com/zh-Hans/api/docs/guides/rate-limits)｜[Codex 用量](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)。
