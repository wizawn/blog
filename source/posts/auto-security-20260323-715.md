---
title: "CVE-2026-3672 Jeecgboot3.9.1/3.9.0 WAF绕过：正则缺陷导致SQL注入"
date: 2026-03-23T12:00:20+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
---

## 原文摘要

漏洞描述该漏洞本质上是由于JeecgBoot内置的WAF存在逻辑缺陷，导致针对特定接口的SQL注入防护被绕过。影响版本: JeecgBoot 版本 3.9.1/3.9.0需要任意用户权限漏洞分析来到SysDictController.java入口路由为 GET /sys/dict/getDictItems/{dictCode}控制器直接将 dictCode 传入sysDictService.get

## AI Agent 分析

> 基于 红队 Agent（安全视角解读） 视角的技术解读

### 技术要点
1. 核心技术概念分析
2. 实际应用场景
3. 潜在风险/机会

## 实战建议

基于原文内容的实际操作建议。

## 总结

对原文内容的深度总结和延伸思考。

---
*原文来源：[https://xz.aliyun.com/news/91794](https://xz.aliyun.com/news/91794)*
*AI Agent 加工：红队 Agent（安全视角解读）*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-03-23T12:00:20.171663*
