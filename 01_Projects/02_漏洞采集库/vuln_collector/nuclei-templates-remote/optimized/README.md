# Nuclei Templates - 优化版

**生成时间**: 2026-02-28  
**处理者**: ClawSec  
**来源**: 自定义模板库去重优化

---

## 统计

| 指标 | 数值 |
|------|------|
| 原始模板数 | ~30,000 |
| 优化后模板数 | 26,162 |
| 去重删除 | 3,505 |
| 总大小 | 12MB |

### 分类分布

| 类别 | 模板数 | 大小 |
|------|--------|------|
| RCE | 12,364 | 5.6MB |
| Other | 4,326 | 1.7MB |
| SQLi | 3,185 | 1.4MB |
| Exposure | 2,108 | 1.2MB |
| XSS | 1,620 | 868KB |
| LFI | 1,640 | 759KB |
| Upload | 788 | 366KB |
| Unauth | 131 | 53KB |

---

## 使用方式

### 基础扫描
nuclei -t /root/nuclei-templates/optimized/ -u https://target.com

### 按类别扫描
nuclei -t /root/nuclei-templates/optimized/rce.yaml -u https://target.com

### 低并发扫描 (避免被封)
nuclei -t /root/nuclei-templates/optimized/ -rate-limit 30 -concurrency 8 -bulk-size 8 -u https://target.com

---

## 配置说明

配置文件：~/.config/nuclei/config.yaml

保守设置 (避免触发 WAF/封禁):
- rate-limit: 30 req/s
- concurrency: 8
- bulk-size: 8
- timeout: 10s

---

## 目录结构

/root/nuclei-templates/
- custom/              原始模板 (未去重)
- optimized/           优化后模板 (推荐使用)
- exp-index.json       Exploit 脚本索引
