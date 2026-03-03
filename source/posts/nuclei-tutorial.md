---
title: "Nuclei 漏洞扫描器从入门到精通"
date: 2026-03-01T15:00:00+08:00
draft: false
categories: ['教程系列']
tags: ['Nuclei', '漏洞扫描', '教程']
---

# Nuclei 漏洞扫描器从入门到精通

> **工具名称：** Nuclei  
> **GitHub:** https://github.com/projectdiscovery/nuclei  
> **适用场景：** Web 漏洞扫描、批量检测、CI/CD 集成

---

## 工具概述

Nuclei 是一款基于模板的漏洞扫描器，支持快速编写自定义检测规则，是目前最流行的开源漏洞扫描工具之一。

### 核心优势

- ✅ **模板化** - YAML 格式，易读易写
- ✅ **速度快** - 支持并发扫描
- ✅ **社区活跃** - 3000+ 官方模板
- ✅ **易于集成** - 支持 CI/CD、API 调用

---

## 环境搭建

### 1. 安装 Nuclei

```bash
# Linux/macOS
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Docker
docker pull projectdiscovery/nuclei:latest

# 验证安装
nuclei -version
```

### 2. 更新模板

```bash
# 更新模板库
nuclei -update-templates

# 查看模板统计
nuclei -templates-stats
```

### 3. 配置 API Key (可选)

```bash
# 配置 PDCP API Key
nuclei -auth
```

---

## 基础使用

### 1. 扫描单个目标

```bash
# 基础扫描
nuclei -u https://target.com

# 指定模板
nuclei -u https://target.com -t cves/

# 指定严重程度
nuclei -u https://target.com -s critical,high
```

### 2. 批量扫描

```bash
# 从文件读取目标
nuclei -l targets.txt

# 指定输出文件
nuclei -l targets.txt -o results.txt

# JSON 格式输出
nuclei -l targets.txt -json export.json
```

### 3. 自定义模板扫描

```bash
# 使用自定义模板
nuclei -u https://target.com -t /path/to/custom-template.yaml

# 使用标签过滤
nuclei -u https://target.com -t cves/ -tags log4j
```

---

## 高级用法

### 1. 并发控制

```bash
# 设置并发数
nuclei -u https://target.com -c 50

# 设置速率限制
nuclei -u https://target.com -rl 100
```

### 2. 漏洞验证

```bash
# 只运行 POC 不利用
nuclei -u https://target.com -v

# 显示详细输出
nuclei -u https://target.com -debug
```

### 3. CI/CD 集成

```yaml
# GitHub Actions 示例
name: Nuclei Scan
on: [push]
jobs:
  nuclei:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Nuclei Scan
        uses: projectdiscovery/nuclei-action@main
        with:
          target: ${{ github.event.repository.url }}
```

---

## 模板编写

### 1. 模板结构

```yaml
id: example-vulnerability

info:
  name: Example Vulnerability
  author: yourname
  severity: high
  description: Vulnerability description
  tags: cve,web

requests:
  - method: GET
    path:
      - "{{BaseURL}}/vulnerable-path"
    matchers-condition: and
    matchers:
      - type: word
        words:
          - "vulnerable"
      - type: status
        status:
          - 200
```

### 2. 常见 Payload

**SQL 注入检测：**
```yaml
requests:
  - method: GET
    path:
      - "{{BaseURL}}/id=1'"
    matchers:
      - type: word
        words:
          - "SQL syntax"
          - "MySQL"
```

**XSS 检测：**
```yaml
requests:
  - method: GET
    path:
      - "{{BaseURL}}/search?q=<script>alert(1)</script>"
    matchers:
      - type: word
        part: body
        words:
          - "<script>alert(1)</script>"
```

**目录遍历检测：**
```yaml
requests:
  - method: GET
    path:
      - "{{BaseURL}}/../../../../etc/passwd"
    matchers:
      - type: regex
        regex:
          - "root:.*:0:0:"
```

---

## 实战案例

### 案例 1：Log4Shell 批量检测

```bash
nuclei -l targets.txt \
  -t cves/2021/CVE-2021-44228.yaml \
  -o log4shell-results.txt
```

### 案例 2：CVE 批量扫描

```bash
nuclei -l targets.txt \
  -t cves/ \
  -s critical,high \
  -c 50 \
  -o cve-scan-results.txt
```

### 案例 3：API 安全扫描

```bash
nuclei -l api-targets.txt \
  -t exposures/apis/ \
  -t misconfiguration/ \
  -o api-scan-results.txt
```

---

## 性能优化

### 1. 提升扫描速度

```bash
# 增加并发
nuclei -c 100

# 禁用更新检查
nuclei -duc

# 禁用彩色输出
nuclei -nc
```

### 2. 减少误报

```bash
# 使用多个匹配器
nuclei -u https://target.com -t custom-template.yaml

# 启用验证
nuclei -u https://target.com -v
```

---

## 常用模板推荐

| 模板分类 | 模板数量 | 使用场景 |
|---------|---------|---------|
| CVE | 1000+ | 已知漏洞检测 |
| 默认 | 500+ | 基础安全检测 |
| 暴露 | 300+ | 敏感信息泄露 |
| 错误配置 | 200+ | 配置错误检测 |

---

## 总结

Nuclei 是渗透测试必备工具，建议：

1. **熟练掌握** - 日常扫描必备
2. **编写模板** - 针对特定目标定制
3. **持续更新** - 保持模板最新
4. **合法使用** - 仅用于授权测试

---

**参考资料：**
- https://github.com/projectdiscovery/nuclei
- https://nuclei.projectdiscovery.io/
- https://github.com/projectdiscovery/nuclei-templates

---

*本文仅用于安全研究与教育目的，请勿用于非法用途。*
