---
title: "软件系统安全赛2026分区赛 Web NodeJs"
date: 2026-04-22T06:00:53+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
---

## 原文摘要

该文章介绍了一道 Node.js CTF 题目的解题思路：攻击者首先利用 /changepassword 接口的 merge() 函数原型链污染漏洞，注入 isAdmin: true 提权为管理员；随后通过 CVE-2026-22709 绕过 vm2 沙箱执行任意命令；最后利用 root 权限的 /backup.sh 定时脚本，将 /flag 内容写入静态目录实现读取。核心链：原型污染提权 → v

## 文章来源

- **标题**: 软件系统安全赛2026分区赛 Web NodeJs
- **来源**: security
- **链接**: [https://xz.aliyun.com/news/91998](https://xz.aliyun.com/news/91998)
- **时间**: 2026-04-19 13:29:29

## 核心内容

该文章介绍了一道 Node.js CTF 题目的解题思路：攻击者首先利用 /changepassword 接口的 merge() 函数原型链污染漏洞，注入 isAdmin: true 提权为管理员；随后通过 CVE-2026-22709 绕过 vm2 沙箱执行任意命令；最后利用 root 权限的 /backup.sh 定时脚本，将 /flag 内容写入静态目录实现读取。核心链：原型污染提权 → v

---
*内容来源：security*
*原文链接：[https://xz.aliyun.com/news/91998](https://xz.aliyun.com/news/91998)*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-04-22T06:00:53.081735*
