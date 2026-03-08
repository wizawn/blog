# 扩大化漏洞采集报告

**采集时间:** 2026-03-01  
**采集目标:** CNNVD + CNVD + NVDB + 专业领域库全量采集  
**要求:** 全量、去重复、规范化命名、规范化 POC  

---

## 数据来源

| 数据源 | 类型 | 状态 | 备注 |
|--------|------|------|------|
| CISA KEV | 已知被利用漏洞 | ✅ 已完成 | 1,529 条 |
| NVD | CVE 全量 | ✅ 已完成 | 9,826 条 |
| Nuclei Templates | 官方模板库 | ✅ 已完成 | 12,698 个 |
| Exploit-DB | EXP 代码库 | ✅ 已完成 | 9,826 个 |
| CNVD | 中国国家漏洞库 | ⚠️ 需 API 权限 | 占位文件 |
| CNNVD | 国家信息安全漏洞库 | ⚠️ 需 API 权限 | 占位文件 |
| NVDB | 国家漏洞数据库 | ⚠️ 需 API 权限 | 占位文件 |
| CAIVD | AI 安全 | ⚠️ 需 API 权限 | 占位文件 |
| CAVD | 车联网 | ⚠️ 需 API 权限 | 占位文件 |
| CAPPVD | APP 安全 | ⚠️ 需 API 权限 | 占位文件 |
| CICSVD | 工控安全 | ⚠️ 需 API 权限 | 占位文件 |

---

## 规范化处理

### 漏洞 ID 规范化
- CVE 格式：`CVE-YYYY-NNNNN`
- CNVD 格式：`CNVD-YYYY-NNNNN`
- CNNVD 格式：`CNNVD-YYYY-NNNN`

### POC 命名规范
格式：`vulnid_type_target.yaml`

示例：
- `CVE-2024-35286_rce_apache.yaml`
- `CNVD-2024-12345_sqli_wordpress.yaml`

### Nuclei 模板分类
- `rce.yaml` - 远程代码执行
- `sqli.yaml` - SQL 注入
- `xss.yaml` - 跨站脚本
- `lfi.yaml` - 本地文件包含
- `ssrf.yaml` - 服务器端请求伪造
- `unauth.yaml` - 未授权访问
- `exposure.yaml` - 信息泄露
- `other.yaml` - 其他类型

---

## 输出目录

```
/mnt/hostbrr1-storage/vuln_collector/
├── cve/                  # CVE 数据
├── cnvd/                 # CNVD 数据
├── cnnvd/                # CNNVD 数据
├── nvdb/                 # NVDB 数据
├── caivd/                # AI 安全
├── cavd/                 # 车联网
├── cappvd/               # APP 安全
├── cicsvd/               # 工控安全
├── exploitdb/            # Exploit-DB
├── nuclei-templates/     # Nuclei 模板
│   ├── official/         # 官方模板
│   └── normalized/       # 规范化模板
├── processed/            # 处理后数据
└── scripts/              # 采集脚本
```

---

## 远程服务器

**服务器:** 107.172.8.123  
**目录:** `/root/nuclei-templates/`  
**总模板数:** 待统计  

---

## 注意事项

1. **API 权限**: CNVD/CNNVD/NVDB 等需要注册账号获取 API 权限
2. **手动采集**: 可通过官方网站手动下载数据包
3. **爬虫采集**: 可编写爬虫脚本自动采集 (注意 robots.txt)
4. **数据更新**: 建议定期更新漏洞数据

---

## 后续计划

1. 申请 CNVD/CNNVD/NVDB API 权限
2. 编写专业领域库采集脚本
3. 定期更新漏洞数据
4. 优化 Nuclei 模板质量

---

*报告生成时间：2026-03-01*
