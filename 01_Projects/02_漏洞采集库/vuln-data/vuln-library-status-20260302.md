# 漏洞库状态报告

**统计时间**: 2026-03-02 11:15 UTC  
**存储位置**: hostbrr1:vuln_collector/

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| **总对象数** | 253,518 个 |
| **总大小** | 2.794 GiB (3.0 GB) |
| **数据源** | 18+ 个 |

---

## 📁 目录结构

```
hostbrr1:vuln_collector/
├── backup_20260228_131843/    # 备份
├── caivd/                     # AI 安全漏洞库
├── cappvd/                    # APP 安全漏洞库
├── cavd/                      # 车联网漏洞库
├── cicsvd/                    # 工控安全漏洞库
├── cnnvd/                     # 国家信息安全漏洞库
├── cnvd/                      # 国家漏洞数据库
├── cve/                       # CVE 全量
├── exploitdb/                 # Exploit-DB
├── nuclei-exp/                # Nuclei 漏洞模板
├── nuclei-templates/          # Nuclei 官方模板
├── nvd/                       # NVD 全量
├── nvdb/                      # 国家漏洞数据库
├── poc_repos/                 # POC 仓库
├── processed/                 # 已处理数据
├── scripts/                   # 采集脚本
├── skills/                    # 技能库
├── src-reports/               # SRC 报告
└── vulhub/                    # Vulhub 靶场
```

---

## 📈 各数据源统计

| 数据源 | 对象数 | 大小 | 状态 |
|--------|--------|------|------|
| **processed/** | 5,288 | 99 MB | ✅ 已处理 |
| **poc_repos/** | ~100k | ~1 GB | ✅ POC 仓库 |
| **nvd/** | ~50k | ~500 MB | ✅ NVD 全量 |
| **cve/** | ~30k | ~300 MB | ✅ CVE 全量 |
| **exploitdb/** | ~20k | ~200 MB | ✅ Exploit-DB |
| **nuclei-templates/** | ~12k | ~50 MB | ✅ Nuclei 模板 |
| **cnvd/** | ~10k | ~100 MB | ✅ CNVD |
| **cnnvd/** | ~10k | ~100 MB | ✅ CNNVD |
| **其他** | ~15k | ~400 MB | ✅ 其他数据源 |

---

## 🎯 采集进度

### 已完成
- ✅ CISA KEV（1,529 条）
- ✅ NVD 全量（2002-2026）
- ✅ CNVD/CNNVD（国家级）
- ✅ Exploit-DB（完整镜像）
- ✅ Nuclei Templates（官方 + 社区）
- ✅ GitHub Advisory（多生态）
- ✅ Vulhub（靶场镜像）
- ✅ POC Repos（社区收集）

### 待补充
- ⏳ 实时增量采集（每日更新）
- ⏳ 漏洞关联分析
- ⏳ POC 自动化验证

---

## 📊 数据类型分布

| 类型 | 占比 |
|------|------|
| CVE 数据 | ~40% |
| POC/EXP | ~30% |
| Nuclei 模板 | ~15% |
| 报告/文档 | ~10% |
| 其他 | ~5% |

---

## 🔄 更新策略

### 每日更新
- CISA KEV（每日检查）
- NVD 最新 CVE（每日同步）
- GitHub Advisory（每周同步）

### 每周更新
- Exploit-DB（每周同步）
- Nuclei Templates（每周同步）

### 每月更新
- CNVD/CNNVD（每月同步）
- 全量数据去重（每月执行）

---

## 📈 下一步计划

1. **增量采集** - 每日自动同步新增 CVE
2. **POC 验证** - 自动化验证 POC 可用性
3. **模板生成** - 基于 CVE 自动生成 Nuclei 模板
4. **关联分析** - CVE-EXP-POC 关联
5. **情报整合** - 威胁情报整合

---

*报告生成时间：2026-03-02 11:15 UTC*
