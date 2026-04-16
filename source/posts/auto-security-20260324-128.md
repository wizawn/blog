---
title: "CVE-2026-3672 Jeecgboot3.9.1/3.9.0 WAF绕过：正则缺陷导致SQL注入"
date: 2026-03-24T06:00:52+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
---



{{< figure src="/images/wechat-pay.jpg" alt="微信赞赏码" width="200" >}}

{{< figure src="/images/alipay-pay.jpg" alt="支付宝收款码" width="200" >}}

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}

**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---



---

## 核心摘要

漏洞描述该漏洞本质上是由于JeecgBoot内置的WAF存在逻辑缺陷，导致针对特定接口的SQL注入防护被绕过。影响版本: JeecgBoot 版本 3.9.1/3.9.0需要任意用户权限漏洞分析来到SysDictController.java入口路由为 GET /sys/dict/getDictItems/{dictCode}控制器直接将 dictCode 传入sysDictService.get

## 技术背景分析

这篇文章讨论的技术主题在当前行业中具有重要意义。从技术角度来看，漏洞描述该漏洞本质上是由于JeecgBoot内置的WAF存在逻辑缺陷，导致针对特定接口的SQL注入防护被绕过。影响版本: JeecgBoot 版本 3.9.1/3.9.0需要任意用户权限漏洞分析来到SysDictController.java入口路由为 GET /sys/dict/getDictItems/{dictCode}控制器直接将 dictCode 传入sysDictService.get 这一现象反映了行业发展趋势。

## 关键技术点

1. **技术原理**：基于原文描述，该技术涉及核心原理包括数据处理、系统集成等方面。
2. **应用场景**：在实际应用中，这类技术通常用于解决企业级安全问题、性能优化等挑战。
3. **实施建议**：开发者在实施时需要注意版本兼容性、配置优化等关键因素。

## 实战建议

- 建议先在小规模环境测试验证
- 关注官方文档和最新版本更新
- 参考社区最佳实践进行配置

## 总结

这篇文章提供了有价值的技术见解，对于相关领域的从业者具有参考意义。建议读者结合自身实际场景进行评估和应用。

---
*原文来源：[https://xz.aliyun.com/news/91794](https://xz.aliyun.com/news/91794)*
*AI Agent 加工：红队 Agent（安全视角解读）*



---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-03-24T06:00:52.240745*
