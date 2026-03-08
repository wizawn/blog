# Exp&POC 集合处理报告

**生成时间**: 2026-02-27T17:55:00Z  
**处理者**: ClawSec  
**来源**: 00_ALL_FILES_NAMED.zip (88,380 文件) + 现有仓库

---

## 📊 处理统计

### 文件分类处理

| 来源 | 文件数 | 处理方式 | 输出 |
|------|--------|----------|------|
| .txt/.md | 28,294 | 转换为 Nuclei | nuclei-templates/*.yaml |
| .xml | 27,362 | 转换为 Nuclei | nuclei-templates/*_from_xml.yaml |
| .py/.php/.pl/.rb/.c | 21,475 | 元数据索引 | exp-index.json |
| 其他 (html/asm/jar/exe 等) | ~11,249 | 原始存储 | raw-zip/ |
| **总计** | **88,380** | - | - |

### Nuclei 模板统计

**总模板数**: 55,656  
**分类分布**:
- RCE: 15,574 (28%)
- Other: 19,052 (34%)
- SQLi: 9,449 (17%)
- XSS: 5,541 (10%)
- Exposure: 2,531 (5%)
- LFI: 1,723 (3%)
- Unauth: 967 (2%)
- Upload: 819 (1%)

### Exploit 脚本索引

**总脚本数**: 21,475  
**含 CVE**: 1,943 (9%)  
**漏洞类型**:
- BOF (缓冲区溢出): 7,872 (37%)
- Unknown: 8,448 (39%)
- SQLi: 1,414 (7%)
- RCE: 1,270 (6%)
- Unauth: 1,006 (5%)
- Upload: 938 (4%)
- LFI: 403 (2%)
- XSS: 124 (1%)

---

## 📁 目录结构

```
okdrive:/exp-poc/
├── nuclei-templates/       # 官方 Nuclei 模板库 (93MB)
├── cve-exp/               # CVE 相关 exp (8KB)
├── exp-data/              # Exp 数据 (788KB)
├── raw-zip/               # 原始 zip 及解压文件 (6.1GB)
│   ├── 00_ALL_FILES_NAMED.zip
│   └── extracted/
└── processed/             # 处理后的文件
    ├── nuclei-templates/  # 转换的 Nuclei 模板 (27MB)
    │   ├── *.yaml
    │   └── stats.json
    └── exp-index.json     # 脚本索引 (5.8MB)
```

---

## 🚀 远程服务器部署

**服务器**: 107.172.8.123 (ARL 灯塔)  
**Nuclei 版本**: v3.7.0  
**模板位置**: `/root/nuclei-templates/custom/`  
**模板总数**: 55,656  
**索引文件**: `/root/nuclei-templates/exp-index.json`

### 使用方式

```bash
# 使用自定义模板扫描
nuclei -t /root/nuclei-templates/custom/ -u https://target.com

# 按类别扫描
nuclei -t /root/nuclei-templates/custom/rce.yaml -u https://target.com
nuclei -t /root/nuclei-templates/custom/sqli.yaml -u https://target.com

# 查看索引
cat /root/nuclei-templates/exp-index.json | jq '.vuln_types'
```

---

## ⚠️ 注意事项

1. **去重**: 已处理 35 个重复文件
2. **质量**: XML 转换的模板基于元数据生成，可能需要手动验证
3. **脚本索引**: 21k 脚本未转换为 Nuclei（主要是本地/二进制 exploit）
4. **剩余文件**: ~11k 其他格式文件（html/asm/jar/exe 等）保留原始格式

---

## 📈 下一步建议

1. **扩大采集**: 继续收集更多高质量 exp（GitHub、Exploit-DB、CVE 库）
2. **质量优化**: 手动验证关键模板，优化检测逻辑
3. **自动化**: 定期更新 nuclei-templates，合并新 CVE
4. **集成**: 将 exp-index.json 集成到 ARL 灯塔 POC 库

---

**状态**: ✅ 处理完成，已上传至 OneDrive 和远程服务器
