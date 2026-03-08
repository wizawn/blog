# 🔒 ClawSec RedTeam AI Agent Matrix - 团队状态

## ✅ 系统状态：已就绪

**创建时间:** 2026-02-25 11:18 UTC  
**版本:** 1.0.0  
**指挥官:** ClawSec (🔒 AI 网络安全专家)

---

## 🎯 团队编制 (5/5)

| 角色 | 代号 | 状态 | 文件 | 职责 |
|------|------|------|------|------|
| 🔍 | Recon-Agent | ✅ Ready | `agents/recon_agent.py` | 信息收集、子域名枚举、端口扫描、指纹识别 |
| 📊 | Analyzer-Agent | ✅ Ready | `agents/analyzer_agent.py` | 攻击面分析、风险评分、攻击路径规划 |
| ⚔️ | Exploit-Agent | ✅ Ready | `agents/exploit_agent.py` | 漏洞利用、WebShell 部署、凭据获取 |
| 👤 | Post-Agent | ✅ Ready | `agents/post_agent.py` | 提权、内网发现、横向移动 |
| 📝 | Reporter-Agent | ✅ Ready | `agents/reporter_agent.py` | 报告生成、修复建议、攻击链路可视化 |

---

## 📁 项目结构

```
redteam/
├── README.md                 # 完整文档
├── QUICKSTART.md             # 快速启动指南
├── orchestrator.py           # 总协调器 (指挥 5 个 Agent)
├── agents/
│   ├── recon_agent.py        # 侦察兵
│   ├── analyzer_agent.py     # 分析师
│   ├── exploit_agent.py      # 突击手
│   ├── post_agent.py         # 潜伏者
│   └── reporter_agent.py     # 记录员
├── configs/
│   ├── recon_config.yaml     # 侦察配置
│   ├── exploit_config.yaml   # 利用配置
│   └── report_template.html  # 报告模板
├── tools/
│   ├── subdomain_enum.sh     # 子域名枚举脚本
│   └── port_scan.sh          # 端口扫描脚本
└── output/
    ├── reports/              # 生成的报告
    ├── logs/                 # 执行日志
    └── artifacts/            # 收集的数据
```

---

## 🚀 快速启动

### 1. 初始化系统
```bash
cd /root/.openclaw/workspace/redteam
python3 orchestrator.py --init
```

### 2. 执行完整渗透测试
```bash
python3 orchestrator.py --target example.com --mode full
```

### 3. 仅侦察模式
```bash
python3 orchestrator.py --target example.com --mode recon
```

### 4. 查看任务状态
```bash
python3 orchestrator.py --status
```

---

## 🎭 攻击链流程

```
[目标输入]
    ↓
┌─────────────────────────────────────────┐
│  Phase 1: Reconnaissance (侦察)          │
│  Agent: Recon-Agent                     │
│  输出：子域名、开放端口、技术栈           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Phase 2: Analysis (分析)                │
│  Agent: Analyzer-Agent                  │
│  输出：攻击向量、风险评分、推荐路径       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Phase 3: Exploitation (利用)            │
│  Agent: Exploit-Agent                   │
│  输出：漏洞利用、Shell、凭据              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Phase 4: Post-Exploitation (后渗透)     │
│  Agent: Post-Agent                      │
│  输出：提权、内网拓扑、横向移动           │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Phase 5: Reporting (报告)               │
│  Agent: Reporter-Agent                  │
│  输出：HTML/JSON 报告、修复建议            │
└─────────────────────────────────────────┘
    ↓
[完整报告]
```

---

## 🔧 工具依赖

### 已集成工具
- **子域名枚举:** subfinder, assetfinder, amass
- **端口扫描:** nmap, masscan
- **指纹识别:** whatweb, wappalyzer, nuclei
- **漏洞利用:** sqlmap, wpscan, hydra, metasploit
- **后渗透:** 内建模块

### 安装命令 (Kali/Parrot)
```bash
apt install subfinder assetfinder amass nmap masscan \
            whatweb wpscan sqlmap hydra metasploit-framework
```

---

## ⚠️ 安全约束

所有 Agent 遵循以下约束:

1. **Authorized Testing Only** - 仅限授权测试
2. **No Data Destruction** - 不破坏生产数据
3. **Log All Actions** - 所有操作记录日志
4. **Respect Scope** - 严格遵守测试范围
5. **Rollback Plan** - 利用前制定回滚计划

---

## 📊 当前任务

| 字段 | 值 |
|------|-----|
| 活跃任务 | 无 |
| 已完成任务 | 0 |
| 生成报告 | 0 |
| 发现漏洞 | 0 |

---

## 🔗 与 EvoMap 集成

每个 Agent 可作为独立节点注册到 EvoMap 网络:

- 共享发现的 Capsules (安全工具/脚本)
- 获取预验证的漏洞利用方案
- 贡献自己的 exploit 到网络

```python
from evomap_client import EvoMapClient
client = EvoMapClient(node_id="node_xxx")
capsules = client.fetch_promoted(category="security")
```

---

## 📞 联系与反馈

**创建者:** ClawSec (🔒)  
**用户:** 言少  
**方向:** SRC 挖掘、Web 渗透  

如有问题或建议，请更新相应配置文件或联系指挥官。

---

*Authorized Testing Only - 未经授权禁止使用*
