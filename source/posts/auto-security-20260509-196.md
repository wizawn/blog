---
title: "HackTheBox AirTouch：一场从 SNMP 泄露打进 WPA2 无线内网的攻击链"
date: 2026-05-09T06:01:03+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
link: "https://xz.aliyun.com/news/92102"
---

## 原文摘要

本文记录 HackTheBox 靶机 AirTouch 的完整渗透过程。初始阶段仅发现 SSH 服务开放，但通过 UDP 扫描定位到 SNMP 服务，并利用默认 community string 读取到 consultant 账号密码。登录后发现目标处于 Docker 容器化无线实验环境中，进一步枚举虚拟无线网卡与网络拓扑。随后针对 AirTouch-Internet 执行监听、Deauth 攻击

## 文章来源

- **标题**: HackTheBox AirTouch：一场从 SNMP 泄露打进 WPA2 无线内网的攻击链
- **来源**: security
- **链接**: [https://xz.aliyun.com/news/92102](https://xz.aliyun.com/news/92102)
- **时间**: 2026-05-08 10:15:01

## 核心内容

本文记录 HackTheBox 靶机 AirTouch 的完整渗透过程。初始阶段仅发现 SSH 服务开放，但通过 UDP 扫描定位到 SNMP 服务，并利用默认 community string 读取到 consultant 账号密码。登录后发现目标处于 Docker 容器化无线实验环境中，进一步枚举虚拟无线网卡与网络拓扑。随后针对 AirTouch-Internet 执行监听、Deauth 攻击

---
*内容来源：security*
*原文链接：[https://xz.aliyun.com/news/92102](https://xz.aliyun.com/news/92102)*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-05-09T06:01:03.572385+00:00*
