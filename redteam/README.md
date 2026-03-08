# 🔒 ClawSec RedTeam AI Agent Matrix

Web 渗透红队 AI Agent 矩阵系统 - 5 人制自动化攻击链

## 📋 团队架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    ClawSec RedTeam Matrix                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                              │
│  │   Commander  │ ← 用户/总指挥 (ClawSec)                      │
│  └──────┬───────┘                                              │
│         │                                                      │
│         ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Orchestrator (协调器)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                      │
│    ┌────┴────┬──────────┬──────────┬──────────┐               │
│    ▼         ▼          ▼          ▼          ▼               │
│ ┌──────┐ ┌───────┐ ┌────────┐ ┌───────┐ ┌────────┐           │
│ │Recon │ │Analyzer│ │Exploit │ │ Post  │ │Reporter│           │
│ │侦察兵 │ │ 分析师  │ │ 突击手  │ │ 潜伏者  │ │ 记录员  │           │
│ └──────┘ └───────┘ └────────┘ └───────┘ └────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 核心 Agent 角色

| 角色代号 | 职能定位 | 核心能力 | 决策逻辑 |
|---------|---------|---------|---------|
| **Recon-Agent** (侦察兵) | 信息收集 | 子域名枚举、端口扫描、指纹识别、社工库检索 | "发现目标开放 80 端口，运行老旧 WordPress，建议 CMS 漏洞扫描" |
| **Analyzer-Agent** (分析师) | 策略规划 | 漏洞关联分析、攻击路径推演、风险评分 | "目标有 SQL 注入但存在 WAF，建议低速扫描或 WAF 绕过" |
| **Exploit-Agent** (突击手) | 漏洞利用 | MSF 调用、SQLMap 注入、XSS/CSRF Payload、弱口令爆破 | "检测到 SQL 注入特征，正在尝试 union select... 成功获取 shell" |
| **Post-Agent** (潜伏者) | 后渗透/横向 | 权限提升、内网拓扑发现、凭据抓取、横向移动 | "已获取 Web 服务器权限，发现内网 3 台主机，尝试 SMB 横向移动" |
| **Reporter-Agent** (记录员) | 报告与复盘 | PDF/HTML 报告生成、修复建议、攻击链路可视化 | "本次演练发现 3 个高危漏洞，详细利用步骤已记录" |

## 📁 目录结构

```
redteam/
├── README.md                 # 本文档
├── orchestrator.py           # 总协调器 (指挥 5 个 Agent)
├── shared_state.json         # 共享状态/记忆
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
├── output/
│   ├── reports/              # 生成的报告
│   ├── logs/                 # 执行日志
│   └── artifacts/            # 收集的凭证/数据
└── tools/
    ├── subdomain_enum.sh     # 子域名枚举
    ├── port_scan.sh          # 端口扫描
    └── vuln_scanner.sh       # 漏洞扫描
```

## 🚀 快速启动

```bash
# 1. 初始化团队
cd /root/.openclaw/workspace/redteam
python3 orchestrator.py --init

# 2. 执行任务
python3 orchestrator.py --target example.com --mode full

# 3. 查看状态
python3 orchestrator.py --status

# 4. 生成报告
python3 orchestrator.py --report
```

## 📊 攻击链流程

```
[目标输入] → Recon → Analyzer → Exploit → Post → Reporter → [完整报告]
                ↓           ↓          ↓         ↓
           信息收集    策略规划    漏洞利用   后渗透
                ↓           ↓          ↓         ↓
           资产清单    攻击路径    Shell    内网控制
```

## ⚠️ 安全约束

- **仅限授权测试** - 所有操作必须获得书面授权
- **Authorized Testing Only** - 约束写入每个 Agent 配置
- **日志审计** - 所有操作记录到 `output/logs/`
- **可追溯** - 每次攻击链生成唯一任务 ID

## 🔗 与 EvoMap 集成

- 每个 Agent 可作为独立节点注册到 EvoMap
- 共享发现的 Capsules/Genes
- 复用网络中的预验证解决方案

---

**创建者:** ClawSec (🔒 AI 网络安全专家)
**版本:** 1.0.0
**日期:** 2026-02-25
