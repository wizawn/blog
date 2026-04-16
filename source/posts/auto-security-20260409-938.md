---
title: "CVE-2026-5027 漏洞分析：Langflow 路径穿越导致任意文件写入"
date: 2026-04-09T09:00:53+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
---


> **💬 联系方式 & 交流群**
> 
> **QQ**: 46333839  
> **微信**: GOV-HACK  
> 
> 添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~
> 
> ![微信赞赏码](/images/wechat-pay.jpg)
> 
> ![支付宝收款码](/images/alipay-pay.jpg)
> 
> ![微信二维码](/images/wechat-qr.jpg)

---

## 原文摘要

Langflow作为一款广泛使用的AI低代码开发平台，在≤1.8.4版本中存在高危路径穿越与任意文件写入漏洞（CVE-2026-5027）。该漏洞源于平台POST /api/v2/files文件上传接口对filename参数缺乏有效安全校验，攻击者可通过构造包含../等路径穿越序列的恶意文件名，突破系统预设的上传目录限制，实现对服务器任意路径的文件写入操作。漏洞利用条件宽松，需低权限用户登录即可远

## 文章来源

- **标题**: CVE-2026-5027 漏洞分析：Langflow 路径穿越导致任意文件写入
- **来源**: security
- **链接**: [https://xz.aliyun.com/news/91906](https://xz.aliyun.com/news/91906)
- **时间**: 2026-04-03 08:10:19

## 核心内容

Langflow作为一款广泛使用的AI低代码开发平台，在≤1.8.4版本中存在高危路径穿越与任意文件写入漏洞（CVE-2026-5027）。该漏洞源于平台POST /api/v2/files文件上传接口对filename参数缺乏有效安全校验，攻击者可通过构造包含../等路径穿越序列的恶意文件名，突破系统预设的上传目录限制，实现对服务器任意路径的文件写入操作。漏洞利用条件宽松，需低权限用户登录即可远

---
*内容来源：security*
*原文链接：[https://xz.aliyun.com/news/91906](https://xz.aliyun.com/news/91906)*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-04-09T09:00:53.008725*
