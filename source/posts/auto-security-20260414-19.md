---
title: "CVE-2026-39363：Vite开发服务器任意文件读取漏洞分析复现"
date: 2026-04-14T09:01:01+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
---


> **💬 ChatGPT Plus 充值服务**
> 
> | 套餐 | 价格 | 说明 |
> |------|------|------|
> | Plus 一个月 (无质保) | ¥15 | 掉了不补 |
> | Plus 一个月 (有质保) | ¥35 | 掉了包补 |
> | Pro 200 刀 (一个月无质保) | ¥350 | - |
> | Pro 200 刀 (一个月质保) | ¥550 | - |
> | Pro 100 刀 (一个月无质保) | ¥200 | - |
> 
> **微信联系购买，秒发货！**

---

## 原文摘要

漏洞来源漏洞描述Vite 是一个用于 JavaScript 的前端工具框架。在 6.0.0 到 6.4.2、7.3.2 和 8.0.5 之前的版本中，如果能够以不带 Origin 标头的方式连接到 Vite 开发服务器的 WebSocket，攻击者可以通过自定义 WebSocket 事件 `vite:invoke` 调用 `fetchModule`，并将 `file://...` 与 `?raw`

## 文章来源

- **标题**: CVE-2026-39363：Vite开发服务器任意文件读取漏洞分析复现
- **来源**: security
- **链接**: [https://xz.aliyun.com/news/91938](https://xz.aliyun.com/news/91938)
- **时间**: 2026-04-09 01:59:59

## 核心内容

漏洞来源漏洞描述Vite 是一个用于 JavaScript 的前端工具框架。在 6.0.0 到 6.4.2、7.3.2 和 8.0.5 之前的版本中，如果能够以不带 Origin 标头的方式连接到 Vite 开发服务器的 WebSocket，攻击者可以通过自定义 WebSocket 事件 `vite:invoke` 调用 `fetchModule`，并将 `file://...` 与 `?raw`

---
*内容来源：security*
*原文链接：[https://xz.aliyun.com/news/91938](https://xz.aliyun.com/news/91938)*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-04-14T09:01:01.119479*
