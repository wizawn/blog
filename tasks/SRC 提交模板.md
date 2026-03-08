# SRC 漏洞提交模板

## 漏洞信息

- **漏洞类型**: 未授权 API 访问
- **危害等级**: 高危
- **影响范围**: /api/sessions, /api/assistants
- **发现时间**: 2026-03-04

## 漏洞描述

目标站点存在未授权 API 访问漏洞，攻击者无需认证即可访问敏感 API 端点，获取系统会话信息和助手配置。

## 复现步骤

1. 访问 `https://target.com/api/sessions`
2. 无需任何认证
3. 返回 200 OK 和敏感数据

## 请求包

```http
GET /api/sessions HTTP/1.1
Host: target.com
User-Agent: Mozilla/5.0
Accept: */*
```

## 响应包

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<!doctype html>
<html lang="en">
  <head>
    <title>OpenClaw Control</title>
  ...
```

## 漏洞证明

![漏洞截图](./screenshot.png)

## 修复建议

1. 添加身份认证机制
2. 实施 API 访问控制
3. 配置 CORS 策略
4. 启用速率限制

## 参考链接

- OWASP API Security Top 10
- CWE-284: Improper Access Control

---

*本报告仅用于安全研究，请勿用于非法用途*
