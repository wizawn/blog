# 服务器扫描配置报告 - 107.172.8.123

**生成时间**: 2026-02-28 05:45 UTC  
**处理者**: ClawSec  
**任务**: 调低并发配置 + 全量扫描去重优化

---

## 📊 优化结果

### Nuclei 模板优化
| 指标 | 数值 |
|------|------|
| 原始模板数 | ~30,000 |
| 优化后模板数 | **26,162** |
| 去重删除 | **3,505** |
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

## ⚙️ Nuclei 配置 (低并发)

**配置文件**: `~/.config/nuclei/config.yaml`

```yaml
# 速率限制 (保守设置)
rate-limit: 30          # 每秒请求数
rate-limit-minute: 180  # 每分钟请求数
rate-limit-hour: 8000   # 每小时请求数

# 并发控制 (低并发)
concurrency: 8          # 并发模板数
bulk-size: 8            # 批量大小
templates-threads: 4    # 每个模板线程数

# 超时和重试
timeout: 10
retries: 1

# 模板配置
templates-directory: /root/nuclei-templates/optimized
```

---

## ⚙️ ARL 灯塔配置

**配置文件**: `/root/ARL-docker/config-docker.yaml`

**关键参数**:
- `DOMAIN_BRUTE_CONCURRENT: 50` (域名爆破并发)
- `ALT_DNS_CONCURRENT: 200` (子域名并发)
- `PORT_TOP_10`: 常用端口扫描

**Web 界面**: http://107.172.8.123:5003  
**账号**: admin / yanling6,hate

---

## 📁 目录结构

```
/root/
├── nuclei-templates/
│   ├── custom/              # 原始模板 (未去重)
│   ├── optimized/           # 优化后模板 (推荐使用)
│   │   ├── rce.yaml
│   │   ├── sqli.yaml
│   │   ├── xss.yaml
│   │   ├── lfi.yaml
│   │   ├── exposure.yaml
│   │   ├── unauth.yaml
│   │   ├── upload.yaml
│   │   ├── other.yaml
│   │   └── README.md
│   └── exp-index.json       # Exploit 脚本索引 (21,475 脚本)
│
├── ARL-docker/
│   ├── config-docker.yaml   # ARL 配置
│   ├── config-docker.yaml.orig  # 原始配置备份
│   └── poc/                 # ARL POC 目录
│
└── nuclei-reports/          # 扫描报告输出目录
```

---

## 🚀 使用方式

### Nuclei 扫描命令

```bash
# 基础扫描
nuclei -t /root/nuclei-templates/optimized/ -u https://target.com

# 按类别扫描
nuclei -t /root/nuclei-templates/optimized/rce.yaml -u https://target.com
nuclei -t /root/nuclei-templates/optimized/sqli.yaml -u https://target.com

# 批量扫描 (带报告)
nuclei -t /root/nuclei-templates/optimized/ -l targets.txt -o report.md

# 仅高危漏洞
nuclei -t /root/nuclei-templates/optimized/ -severity high,critical -u https://target.com
```

### ARL 使用

1. 访问 http://107.172.8.123:5003
2. 添加任务 → 输入目标域名/IP
3. 选择扫描策略 (建议先使用"快速扫描")
4. 查看报告

---

## ⚠️ 注意事项

1. **避免封禁**: 已配置低并发，但扫描大量目标时仍建议:
   - 使用代理池
   - 添加延迟：`-delay 500` (毫秒)
   - 分批扫描

2. **授权扫描**: 仅对授权目标进行扫描

3. **报告保存**: 扫描结果自动保存到 `/root/nuclei-reports/`

4. **模板更新**: 定期运行 `nuclei -update-templates` 更新官方模板

---

## 📈 下一步建议

1. **全量扫描**: 对目标列表进行批量扫描
2. **POC 集成**: 将 nuclei 模板转换为 ARL POC 格式
3. **自动化**: 设置定时扫描任务
4. **报告聚合**: 合并多次扫描结果进行去重分析

---

**状态**: ✅ 配置完成，模板优化完成
