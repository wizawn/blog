---
title: "HackTheBox Horizontall 靶机渗透实战：从 Strapi NoSQL 注入到 Laravel Debug RCE 提权全过程"
date: 2026-05-18T12:01:03+00:00
categories: ["security"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
link: "https://xz.aliyun.com/news/92144"
---

## 原文摘要

本文是 HackTheBox Horizontall 靶机的详细渗透测试记录。通过端口扫描发现 Web 服务，在前端 JS 文件中提取出隐藏子域名 api-prod.horizontall.htb，识别出 Strapi CMS（3.0.0-beta.17.4）。利用 CVE-2019-18818（NoSQL 注入重置管理员密码）获取管理员权限，再结合 CVE-2019-19606（插件安装命令注入

## 文章来源

- **标题**: HackTheBox Horizontall 靶机渗透实战：从 Strapi NoSQL 注入到 Laravel Debug RCE 提权全过程
- **来源**: security
- **链接**: [https://xz.aliyun.com/news/92144](https://xz.aliyun.com/news/92144)
- **时间**: 2026-05-17 13:13:05

## 核心内容

本文是 HackTheBox Horizontall 靶机的详细渗透测试记录。通过端口扫描发现 Web 服务，在前端 JS 文件中提取出隐藏子域名 api-prod.horizontall.htb，识别出 Strapi CMS（3.0.0-beta.17.4）。利用 CVE-2019-18818（NoSQL 注入重置管理员密码）获取管理员权限，再结合 CVE-2019-19606（插件安装命令注入

---
*内容来源：security*
*原文链接：[https://xz.aliyun.com/news/92144](https://xz.aliyun.com/news/92144)*


## 市场背景

- BTC 价格：$0.00
- 24h 涨跌：+0.00%

---
*AI Agent 加工：红队 Agent（安全视角解读）*
*生成时间：2026-05-18T12:01:03.885149+00:00*
