# Nuclei 漏洞模板库

**生成时间**: 2026-03-02  
**数据来源**: CISA KEV + NVD  
**模板数量**: 2,019 条漏洞数据

---

## 模板命名规范

格式：`{cve_id}_{vuln_type}_{target}.yaml`

示例：
- `CVE-2022-20775_path-traversal_cisco-sdwan.yaml`
- `CVE-2026-20127_auth-bypass_cisco-catalyst.yaml`
- `CVE-2025-49113_deserialization_roundcube.yaml`

---

## 漏洞类型分类

| 类型 | 数量 | 示例 |
|------|------|------|
| RCE | - | 远程代码执行 |
| SQLi | - | SQL 注入 |
| XSS | - | 跨站脚本 |
| SSRF | - | 服务器端请求伪造 |
| Path-Traversal | - | 路径穿越 |
| Auth-Bypass | - | 认证绕过 |
| Deserialization | - | 反序列化 |
| Command-Injection | - | 命令注入 |
| Hardcoded-Credentials | - | 硬编码凭证 |

---

## 模板结构

```yaml
id: CVE-YYYY-NNNNN

info:
  name: 漏洞名称
  author: ClawSec
  severity: critical/high/medium/low
  description: 漏洞描述
  tags: cve,cisa,rce
  reference:
    - https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNNN

requests:
  - method: GET/POST
    path:
      - "{{BaseURL}}/vulnerable-endpoint"
    
    matchers-condition: and
    matchers:
      - type: word
        words:
          - "success_indicator"
      
      - type: status
        status:
          - 200
```

---

## 使用说明

```bash
# 扫描单个目标
nuclei -u https://target.com -t nuclei_templates/

# 扫描多个目标
nuclei -l targets.txt -t nuclei_templates/

# 按严重性筛选
nuclei -u https://target.com -t nuclei_templates/ -severity critical,high

# 按标签筛选
nuclei -u https://target.com -t nuclei_templates/ -tags cisa,rce
```

---

## 更新日志

- 2026-03-02: 初始版本（2,019 条）
- 数据来源：CISA KEV (1,529) + NVD (500)

---

*模板自动生成，使用前请验证*
