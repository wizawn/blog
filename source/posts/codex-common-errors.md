---
title: "Codex 常见报错怎么处理：capacity、429、503、usage_limit 一次看懂"
slug: "codex-common-errors"
date: 2026-09-18T12:40:00+08:00
draft: false
categories: ["Codex常见问题"]
tags: ["Codex", "429", "503", "usage_limit", "故障排查"]
description: "把 Codex 里最常撞见的几类报错拆开说清楚：哪些是服务端挤爆了等会儿就行，哪些是额度见底干等也没用。"
weight: 10
---

用 Codex 写代码的时候，界面上同样弹一句"请求发不出去"，背后的毛病可能差着十万八千里。有人一看见 `429` 就坐那儿死等，结果其实是 API 预付余额见底了；也有人刚撞见一次 `capacity` 就以为号废了，急着清配置换号。

遇到报错别光看弹窗标题，把完整的 HTTP 状态码和响应体里的 `error.code` 展开对照一下，基本一眼就能分清该怎么处理：

| 报错提示 / 状态码 | 实际是怎么回事 | 处理办法 |
|---|---|---|
| `Selected model is at capacity` | 当前选的这个模型算力池挤满了，高峰期很常见 | 歇几分钟再发，或者临时切个别的模型顶一下，顺手看一眼 [OpenAI 状态页](https://status.openai.com/)。单凭这一句说明不了账号有问题，要是所有模型连续好几个小时都报这个再去查账号。 |
| `server_is_overloaded`（多见于 `503`） | 服务端节点瞬时过载 | 响应头里带了 `Retry-After` 就照着秒数等；没带就自己拉长间隔重试，别连着狂点。 |
| `429` + `rate_limit_exceeded` | 发得太密、并发拉太高、单次上下文暴涨，或者同组织下别的脚本也在抢配额 | 响应头带了 `Retry-After` 就照着等，没带就按指数退避慢点发，设个合理的重试上限。 |
| `429` + `slow_down` | 请求增速太猛，哪怕还没摸到每分钟总额上限也会触发上游流量保护 | 有 `Retry-After` 先照着等，等速率平稳了再慢慢往上加，别一恢复又瞬间拉满。 |
| `429` + `insufficient_quota` / `credit_balance_exhausted` | API 账户预付余额花光了，或没绑有效计费方式 | 直接去后台充值或检查账单状态，坐着干等一万年也不会自己好。 |
| `429` + `project_spend_limit_exceeded` / `organization_spend_limit_exceeded` | 撞到了项目级或组织级的月度消费硬上限 | 先看清楚当前跑的是哪个项目的 Key，找组织管理员把对应项目的月限额调高，或者等下个账期刷新。 |
| `429` + `organization_usage_limit_exceeded` | 整个组织的层级（Tier）用量摸顶了 | 去后台看一眼当前的 Usage Tier，按规则提额或找官方支持申请扩容。 |
| `usage_limit_reached` | ChatGPT 订阅（Plus / Pro / Business）在当前时间窗口内的 Codex 额度用完了 | 去用量面板看一眼具体的 reset 时间点，要么等窗口重置，要么按页面给的选项加购额度包；找客服一般也不会给你人工提前清零。 |
| `server_unavailable` / `503 Service Unavailable` | 上游服务短暂抽风，或者本机代理出口断了 | 先看状态页和自己的代理节点通不通，确认网络没问题再慢速重试。 |
| `exceeded retry limit` | 客户端自带的几次自动重试全用光了 | 这句话本身只是个结果，往前翻它上面最后一条真正的报错（到底是 `429`、`503` 还是连接超时），照着上面那条修。 |

除了上面这几类，平时偶尔还会撞见 `400`、`401/403` 和 `500`：

- `401` 或 `403` 基本都是身份和权限的事。走官方订阅登录的先跑一下 `codex login status` 看看凭据过没过期；走 API Key 的查一下 Key 有没有被吊销、所属组织和项目对不对、出口地区受不受限，别一上来就瞎折腾重装网络。
- `400` 多半是传过去的模型名字拼错了、参数不兼容，或者拿只支持旧接口的中转去硬跑 Responses 协议。
- `500` 多半是服务端（官方或中转网关）内部出错，看一眼状态页等会儿再试就行。

排查顺序其实就一句话：先抓状态码和 `error.code`，账单和额度问题去后台花钱或等重置，过载问题换模型或歇会儿，最后都排除了再去动本地代理和会话。真要提工单找官方支持的时候，把客户端版本、模型名、报错时间（带时区）、完整报错与 `error.code`、请求 ID，以及换模型或换网络后能不能恢复记下来；外发前记得先把日志里的 API Key、`auth.json`、access token、代理密码和业务代码删干净。

官方参考文档可以翻这几篇：[错误代码说明](https://developers.openai.com/zh-Hans/api/docs/guides/error-codes)、[速率限制机制](https://developers.openai.com/zh-Hans/api/docs/guides/rate-limits)、[在 ChatGPT 计划中使用 Codex](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)。
