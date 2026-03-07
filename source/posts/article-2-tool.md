---
title: "Nuclei 漏洞扫描器实战指南"
date: 2026-03-05
draft: false
categories: ["工具教程"]
tags: ["Nuclei", "漏洞扫描", "自动化"]
image: "/blog-cover-default.jpg"
description: "使用 Nuclei 进行自动化漏洞扫描的完整指南"
---

# Nuclei 漏洞扫描器实战指南

---

## 1. Nuclei 简介

Nuclei 是一款基于模板的现代化漏洞扫描器...

## 2. 安装配置

```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

## 3. 基础用法

```bash
nuclei -u https://target.com -t vulnerabilities/
```

## 4. 高级技巧

- 自定义模板
- 批量扫描
- 结果导出

---

*本文仅供学习参考，请勿用于非法用途*
