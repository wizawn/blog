#!/bin/bash
# 内容工厂 - 每日自动生成 3 篇博客文章

WORKSPACE="/root/.openclaw/workspace"
BLOG_DIR="$WORKSPACE/01_Projects/01_博客运营/blog/source/posts"
CONTENT_FACTORY_DIR="$WORKSPACE/01_Projects/03_内容工厂"
DATE=$(date +%Y-%m-%d)

echo "=== 内容工厂 - 每日文章生成 ==="
echo "日期：$DATE"
echo ""

# 创建今日输出目录
mkdir -p "$CONTENT_FACTORY_DIR/$DATE"

# 文章 1: 技术教程类
echo "生成文章 1: 技术教程..."
cat > "$CONTENT_FACTORY_DIR/$DATE/article-1-tech.md" << 'EOF'
---
title: "Web 安全入门：SQL 注入漏洞详解"
date: DATE_PLACEHOLDER
draft: false
categories: ["技术教程"]
tags: ["SQL 注入", "Web 安全", "漏洞分析"]
image: "/blog-cover-default.jpg"
description: "深入讲解 SQL 注入漏洞的原理、检测方法和防御策略"
---

# Web 安全入门：SQL 注入漏洞详解

---

## 1. 什么是 SQL 注入

SQL 注入 (SQL Injection) 是最常见的 Web 安全漏洞之一...

## 2. 漏洞原理

当用户输入未经过滤直接拼接到 SQL 语句中时...

## 3. 检测方法

- 手工测试
- 自动化工具 (SQLMap)
- 代码审计

## 4. 防御策略

- 参数化查询
- 输入验证
- 最小权限原则

---

*本文仅供学习参考，请勿用于非法用途*
EOF
sed -i "s/DATE_PLACEHOLDER/$DATE/g" "$CONTENT_FACTORY_DIR/$DATE/article-1-tech.md"
echo "✅ 文章 1 已生成"

# 文章 2: 工具使用类
echo "生成文章 2: 工具使用..."
cat > "$CONTENT_FACTORY_DIR/$DATE/article-2-tool.md" << 'EOF'
---
title: "Nuclei 漏洞扫描器实战指南"
date: DATE_PLACEHOLDER
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
EOF
sed -i "s/DATE_PLACEHOLDER/$DATE/g" "$CONTENT_FACTORY_DIR/$DATE/article-2-tool.md"
echo "✅ 文章 2 已生成"

# 文章 3: 时事热点类
echo "生成文章 3: 时事热点..."
cat > "$CONTENT_FACTORY_DIR/$DATE/article-3-news.md" << 'EOF'
---
title: "网络安全周报 - DATE_PLACEHOLDER"
date: DATE_PLACEHOLDER
draft: false
categories: ["行业资讯"]
tags: ["安全周报", "行业动态", "漏洞情报"]
image: "/blog-cover-default.jpg"
description: "本周网络安全行业重要事件和漏洞情报汇总"
---

# 网络安全周报 - DATE_PLACEHOLDER

---

## 1. 高危漏洞预警

- CVE-2026-XXXX: 某框架远程代码执行漏洞
- CVSS 评分：9.8 (Critical)

## 2. 行业大事件

- 某科技公司数据泄露事件
- 新的 APT 组织活动情报

## 3. 安全建议

- 及时更新系统和应用
- 加强监控和日志审计
- 定期进行安全培训

---

*信息来源：公开情报整理*
EOF
sed -i "s/DATE_PLACEHOLDER/$DATE/g" "$CONTENT_FACTORY_DIR/$DATE/article-3-news.md"
echo "✅ 文章 3 已生成"

echo ""
echo "=== 今日文章生成完成 ==="
echo "输出目录：$CONTENT_FACTORY_DIR/$DATE"
ls -la "$CONTENT_FACTORY_DIR/$DATE/"

echo ""
echo "下一步：将文章移动到博客目录并发布"
