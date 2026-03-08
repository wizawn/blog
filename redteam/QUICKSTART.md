# 🚀 RedTeam 快速启动指南

## 1️⃣ 系统初始化

```bash
cd /root/.openclaw/workspace/redteam
python3 orchestrator.py --init
```

## 2️⃣ 执行渗透测试

### 完整攻击链 (侦察→分析→利用→后渗透→报告)
```bash
python3 orchestrator.py --target example.com --mode full
```

### 仅侦察模式
```bash
python3 orchestrator.py --target example.com --mode recon
```

### 侦察 + 分析 (不执行利用)
```bash
python3 orchestrator.py --target example.com --mode analyze
```

## 3️⃣ 查看状态

```bash
python3 orchestrator.py --status
```

## 4️⃣ 输出文件位置

```
redteam/
├── output/
│   ├── reports/          # 生成的报告 (JSON + HTML)
│   ├── logs/             # 执行日志
│   └── artifacts/        # 收集的子域名、端口扫描结果等
├── shared_state.json     # 当前任务状态
└── configs/              # Agent 配置文件
```

## 5️⃣ Agent 角色说明

| Agent | 职责 | 输出 |
|------|------|------|
| 🔍 Recon-Agent | 子域名枚举、端口扫描、指纹识别 | 资产清单、开放端口、技术栈 |
| 📊 Analyzer-Agent | 攻击面分析、风险评分、路径规划 | 攻击向量、推荐路径、难度评分 |
| ⚔️ Exploit-Agent | 漏洞利用、WebShell 部署、凭据获取 | 漏洞列表、Shell 位置、凭据 |
| 👤 Post-Agent | 提权、内网发现、横向移动 | 内网拓扑、提权方法、横向路径 |
| 📝 Reporter-Agent | 报告生成、修复建议 | PDF/HTML 报告 |

## 6️⃣ 自定义配置

编辑 `configs/` 目录下的 YAML 文件:

- `recon_config.yaml` - 侦察工具配置
- `exploit_config.yaml` - 利用模块配置

## 7️⃣ 工具依赖

安装所需工具:

```bash
# Kali/Parrot 已预装大部分工具
apt install subfinder assetfinder amass nmap masscan sqlmap wpscan hydra

# 或使用 Docker
docker pull projectdiscovery/nuclei
docker pull sqlmapproject/sqlmap
```

## 8️⃣ 与 EvoMap 集成

每个 Agent 可作为独立节点注册到 EvoMap，共享发现的 Capsules:

```python
# 在 Agent 中添加 EvoMap 集成
from evomap_client import EvoMapClient

client = EvoMapClient(node_id="node_xxx")
capsules = client.fetch_promoted(category="security")
```

## ⚠️ 安全提醒

- **仅限授权测试** - 所有操作必须获得书面授权
- **遵守法律** - 符合当地网络安全法规
- **日志审计** - 所有操作自动记录到 `output/logs/`
- **可追溯** - 每次任务生成唯一 Mission ID

---

**创建者:** ClawSec (🔒 AI 网络安全专家)
**版本:** 1.0.0
**日期:** 2026-02-25
