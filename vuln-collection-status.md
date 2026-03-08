# 漏洞全量采集状态报告

**采集时间:** 2026-03-01 06:27 UTC  
**采集目标:** CVE + CNVD + EXP + POC 全量采集  
**要求:** 全量、去重复、规范化命名、规范化 POC  

---

## 数据来源

| 数据源 | 类型 | 状态 |
|--------|------|------|
| CISA KEV | 已知被利用漏洞 | ✅ 采集中 |
| NVD | CVE 全量 (2020-2026) | ✅ 采集中 |
| Nuclei Templates | 官方漏洞模板 | ✅ 采集中 |
| Exploit-DB | EXP 代码库 | ✅ 采集中 |
| CNVD | 中国国家漏洞库 | ⏳ 待采集 |

---

## 采集脚本

**位置:** `/mnt/hostbrr1-storage/vuln_collector/scripts/full_vuln_collector.py`

**功能:**
1. CISA KEV 采集
2. NVD CVE 采集 (2020-2026)
3. Nuclei Templates 克隆和解析
4. Exploit-DB 克隆
5. 去重和规范化处理

---

## 规范化标准

### 漏洞 ID 规范化
- CVE 格式：`CVE-YYYY-NNNNN`
- CNVD 格式：`CNVD-YYYY-NNNNN`

### POC 命名规范
格式：`vulnid_type_target.yaml`

示例：
- `CVE-2024-35286_rce_apache.yaml`
- `CNVD-2024-12345_sqli_wordpress.yaml`

### 去重规则
1. 按漏洞 ID 去重
2. 保留数据源最全的记录
3. 合并多来源信息

---

## 输出目录

```
/mnt/hostbrr1-storage/vuln_collector/
├── cve/              # CVE 数据
├── cnvd/             # CNVD 数据
├── exploitdb/        # Exploit-DB
├── nuclei-templates/ # Nuclei 模板
├── processed/        # 处理后数据
└── scripts/          # 采集脚本
```

---

## 预计完成时间

**乐观估计:** 30-60 分钟  
**保守估计:** 1-2 小时  

---

*报告生成时间：2026-03-01 06:27 UTC*
