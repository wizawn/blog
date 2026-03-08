#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔒 ClawSec RedTeam Orchestrator
红队 AI Agent 矩阵总协调器

负责：
- 任务分发与调度
- Agent 间通信协调
- 共享状态管理
- 攻击链流程控制
"""

import json
import uuid
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# ============== 配置 ==============

WORKSPACE = Path("/root/.openclaw/workspace/redteam")
SHARED_STATE_FILE = WORKSPACE / "shared_state.json"
LOGS_DIR = WORKSPACE / "output" / "logs"
REPORTS_DIR = WORKSPACE / "output" / "reports"
ARTIFACTS_DIR = WORKSPACE / "output" / "artifacts"

# 确保目录存在
for d in [LOGS_DIR, REPORTS_DIR, ARTIFACTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============== 枚举与数据结构 ==============

class AgentRole(str, Enum):
    RECON = "recon"
    ANALYZER = "analyzer"
    EXPLOIT = "exploit"
    POST = "post"
    REPORTER = "reporter"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AttackPhase(str, Enum):
    RECONNAISSANCE = "reconnaissance"
    ANALYSIS = "analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"

@dataclass
class Task:
    id: str
    phase: str
    agent: str
    description: str
    status: str = "pending"
    result: Optional[Dict] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

@dataclass
class Target:
    domain: str
    ip: Optional[str] = None
    scope: List[str] = None
    rules_of_engagement: List[str] = None
    
    def __post_init__(self):
        if self.scope is None:
            self.scope = [self.domain]
        if self.rules_of_engagement is None:
            self.rules_of_engagement = ["authorized_testing_only"]

@dataclass
class SharedState:
    mission_id: str
    target: Dict
    current_phase: str
    tasks: List[Dict]
    findings: List[Dict]
    credentials: List[Dict]
    timeline: List[Dict]
    created_at: str
    updated_at: str

# ============== 共享状态管理器 ==============

class StateManager:
    def __init__(self, state_file: Path = SHARED_STATE_FILE):
        self.state_file = state_file
        self.state: Optional[SharedState] = None
    
    def init_mission(self, target: Target) -> str:
        """初始化新任务"""
        mission_id = f"mission_{uuid.uuid4().hex[:12]}"
        
        self.state = SharedState(
            mission_id=mission_id,
            target=asdict(target),
            current_phase=AttackPhase.RECONNAISSANCE.value,
            tasks=[],
            findings=[],
            credentials=[],
            timeline=[{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "mission_initialized",
                "target": target.domain
            }],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        self.save()
        self.log(f"🎯 任务初始化：{mission_id}")
        self.log(f"🎯 目标：{target.domain}")
        
        return mission_id
    
    def save(self):
        """保存状态到文件"""
        if self.state:
            self.state.updated_at = datetime.utcnow().isoformat()
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.state), f, indent=2, ensure_ascii=False)
    
    def load(self) -> bool:
        """加载现有状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.state = SharedState(**data)
                return True
        return False
    
    def add_task(self, task: Task):
        """添加任务"""
        if self.state:
            self.state.tasks.append(asdict(task))
            self.save()
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        if self.state:
            for task in self.state.tasks:
                if task['id'] == task_id:
                    task.update(kwargs)
                    self.save()
                    return True
        return False
    
    def add_finding(self, finding: Dict):
        """添加发现"""
        if self.state:
            finding['timestamp'] = datetime.utcnow().isoformat()
            self.state.findings.append(finding)
            self.save()
    
    def add_credential(self, cred: Dict):
        """添加凭证"""
        if self.state:
            cred['timestamp'] = datetime.utcnow().isoformat()
            self.state.credentials.append(cred)
            self.save()
    
    def next_phase(self):
        """进入下一阶段"""
        if self.state:
            phase_order = [p.value for p in AttackPhase]
            current_idx = phase_order.index(self.state.current_phase)
            if current_idx < len(phase_order) - 1:
                self.state.current_phase = phase_order[current_idx + 1]
                self.save()
                self.log(f"📍 进入阶段：{self.state.current_phase}")
                return self.state.current_phase
        return None
    
    def log(self, message: str):
        """添加日志"""
        if self.state:
            self.state.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": message
            })
            self.save()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

# ============== Agent 基类 ==============

class BaseAgent:
    def __init__(self, role: AgentRole, state_manager: StateManager):
        self.role = role
        self.state = state_manager
        self.name = f"{role.value}_agent"
    
    def execute(self, task: Task) -> Dict:
        """执行任务 (由子类实现)"""
        raise NotImplementedError
    
    def log(self, message: str):
        self.state.log(f"[{self.role.value.upper()}] {message}")

# ============== 具体 Agent 实现 ==============

class ReconAgent(BaseAgent):
    """侦察兵 - 信息收集"""
    
    TOOLS = [
        "subdomain_enum",
        "port_scan", 
        "fingerprint",
        "tech_stack",
        "dns_records",
        "whois_lookup"
    ]
    
    def execute(self, task: Task) -> Dict:
        self.log(f"🔍 开始侦察：{task.description}")
        
        target = self.state.state.target['domain']
        results = {
            "subdomains": [],
            "ports": [],
            "technologies": [],
            "dns_records": {},
            "potential_entry_points": []
        }
        
        # 模拟侦察结果 (实际应调用真实工具)
        self.log(f"  → 子域名枚举：{target}")
        results["subdomains"] = [
            f"www.{target}",
            f"api.{target}",
            f"admin.{target}",
            f"dev.{target}"
        ]
        
        self.log(f"  → 端口扫描：{target}")
        results["ports"] = [
            {"port": 80, "service": "http", "version": "nginx 1.18.0"},
            {"port": 443, "service": "https", "version": "nginx 1.18.0"},
            {"port": 22, "service": "ssh", "version": "OpenSSH 8.2"},
            {"port": 3306, "service": "mysql", "version": "MySQL 5.7"}
        ]
        
        self.log(f"  → 技术栈识别")
        results["technologies"] = [
            "WordPress 5.8",
            "PHP 7.4",
            "MySQL 5.7",
            "jQuery 3.6.0"
        ]
        
        # 识别潜在入口点
        if 80 in [p['port'] for p in results["ports"]]:
            results["potential_entry_points"].append({
                "type": "http_service",
                "risk": "medium",
                "description": "HTTP 服务暴露，可能存在 Web 漏洞"
            })
        
        if "WordPress" in str(results["technologies"]):
            results["potential_entry_points"].append({
                "type": "cms",
                "risk": "high",
                "description": "WordPress 可能存在的插件/主题漏洞"
            })
        
        self.state.add_finding({
            "type": "recon_summary",
            "data": results
        })
        
        self.log(f"  ✓ 侦察完成：发现 {len(results['subdomains'])} 个子域名，{len(results['ports'])} 个开放端口")
        
        return results

class AnalyzerAgent(BaseAgent):
    """分析师 - 策略规划"""
    
    def execute(self, task: Task) -> Dict:
        self.log(f"📊 开始分析：{task.description}")
        
        # 获取侦察结果
        recon_findings = [f for f in self.state.state.findings if f['type'] == 'recon_summary']
        if not recon_findings:
            return {"error": "需要先行侦察数据"}
        
        recon_data = recon_findings[-1]['data']
        
        analysis = {
            "attack_vectors": [],
            "risk_assessment": {},
            "recommended_path": [],
            "waf_detected": False,
            "difficulty_score": 0
        }
        
        # 分析攻击面
        self.log("  → 分析攻击向量")
        
        for port_info in recon_data.get("ports", []):
            if port_info['port'] == 80 or port_info['port'] == 443:
                analysis["attack_vectors"].append({
                    "vector": "web_application",
                    "confidence": 0.9,
                    "tools": ["nuclei", "sqlmap", "burp"]
                })
        
        for tech in recon_data.get("technologies", []):
            if "WordPress" in tech:
                analysis["attack_vectors"].append({
                    "vector": "cms_exploitation",
                    "confidence": 0.85,
                    "tools": ["wpscan", "metasploit"]
                })
        
        # 风险评估
        high_risk_count = len([e for e in recon_data.get("potential_entry_points", []) 
                               if e.get("risk") == "high"])
        
        analysis["risk_assessment"] = {
            "overall": "high" if high_risk_count > 0 else "medium",
            "high_risk_items": high_risk_count,
            "exploitability": 0.8
        }
        
        # 推荐攻击路径
        self.log("  → 生成攻击路径")
        analysis["recommended_path"] = [
            {
                "step": 1,
                "action": "WordPress 版本扫描",
                "tool": "wpscan",
                "expected": "识别已知漏洞"
            },
            {
                "step": 2,
                "action": "SQL 注入测试",
                "tool": "sqlmap",
                "expected": "获取数据库访问"
            },
            {
                "step": 3,
                "action": "文件上传测试",
                "tool": "burp",
                "expected": "获取 WebShell"
            }
        ]
        
        # 难度评分 (0-10)
        analysis["difficulty_score"] = 5 + high_risk_count * 2
        
        self.state.add_finding({
            "type": "analysis_summary",
            "data": analysis
        })
        
        self.log(f"  ✓ 分析完成：识别 {len(analysis['attack_vectors'])} 个攻击向量，难度评分 {analysis['difficulty_score']}/10")
        
        return analysis

class ExploitAgent(BaseAgent):
    """突击手 - 漏洞利用"""
    
    EXPLOITS = {
        "sql_injection": ["sqlmap", "manual"],
        "xss": ["burp", "beef"],
        "rce": ["metasploit", "manual"],
        "wordpress": ["wpscan", "metasploit"],
        "bruteforce": ["hydra", "medusa"]
    }
    
    def execute(self, task: Task) -> Dict:
        self.log(f"⚔️ 开始利用：{task.description}")
        
        # 获取分析结果
        analysis_findings = [f for f in self.state.state.findings if f['type'] == 'analysis_summary']
        if not analysis_findings:
            return {"error": "需要先行分析数据"}
        
        results = {
            "exploits_attempted": [],
            "successes": [],
            "shells_obtained": [],
            "credentials_found": []
        }
        
        # 模拟利用过程
        self.log("  → 执行 WordPress 漏洞扫描")
        results["exploits_attempted"].append({
            "type": "wordpress_scan",
            "tool": "wpscan",
            "status": "completed"
        })
        
        # 模拟发现漏洞
        vuln_found = {
            "id": "WP-VULN-001",
            "type": "plugin_vulnerability",
            "severity": "critical",
            "description": "Contact Form 7 文件上传漏洞",
            "cvss": 9.8
        }
        
        self.log(f"  → 发现高危漏洞：{vuln_found['id']}")
        results["successes"].append(vuln_found)
        
        # 模拟获取 Shell
        self.log("  → 尝试获取 WebShell...")
        shell_info = {
            "type": "php_webshell",
            "path": "/wp-content/uploads/shell.php",
            "access_level": "www-data",
            "persistent": True
        }
        results["shells_obtained"].append(shell_info)
        self.log(f"  ✓ WebShell 已部署：{shell_info['path']}")
        
        # 模拟凭据获取
        self.log("  → 提取数据库凭据...")
        results["credentials_found"].append({
            "type": "database",
            "username": "wp_admin",
            "hash": "模拟哈希值",
            "source": "wp-config.php"
        })
        
        self.state.add_finding({
            "type": "exploitation_summary",
            "data": results
        })
        
        for cred in results["credentials_found"]:
            self.state.add_credential(cred)
        
        self.log(f"  ✓ 利用完成：{len(results['successes'])} 个漏洞利用成功，{len(results['shells_obtained'])} 个 Shell")
        
        return results

class PostAgent(BaseAgent):
    """潜伏者 - 后渗透/横向移动"""
    
    def execute(self, task: Task) -> Dict:
        self.log(f"👤 开始后渗透：{task.description}")
        
        # 获取利用结果
        exploit_findings = [f for f in self.state.state.findings if f['type'] == 'exploitation_summary']
        if not exploit_findings:
            return {"error": "需要先行利用数据"}
        
        results = {
            "privilege_escalation": [],
            "internal_network": [],
            "credentials_dumped": [],
            "lateral_movement": []
        }
        
        # 模拟提权
        self.log("  → 尝试本地提权...")
        results["privilege_escalation"].append({
            "method": "kernel_exploit",
            "from_user": "www-data",
            "to_user": "root",
            "success": True
        })
        self.log("  ✓ 提权成功：root 权限获取")
        
        # 模拟内网发现
        self.log("  → 内网拓扑发现...")
        results["internal_network"].append({
            "interface": "eth0",
            "ip": "192.168.1.100",
            "network": "192.168.1.0/24",
            "gateway": "192.168.1.1"
        })
        
        # 模拟发现内网主机
        internal_hosts = [
            {"ip": "192.168.1.10", "hostname": "dc01", "os": "Windows Server"},
            {"ip": "192.168.1.20", "hostname": "fileserver", "os": "Linux"},
            {"ip": "192.168.1.30", "hostname": "db01", "os": "Linux"}
        ]
        self.log(f"  → 发现 {len(internal_hosts)} 台内网主机")
        
        # 模拟横向移动
        self.log("  → 尝试横向移动...")
        results["lateral_movement"].append({
            "from": "192.168.1.100",
            "to": "192.168.1.20",
            "method": "ssh_key_reuse",
            "success": True
        })
        
        # 模拟凭据转储
        results["credentials_dumped"].append({
            "source": "/etc/shadow",
            "count": 5,
            "cracked": 3
        })
        
        self.state.add_finding({
            "type": "post_exploitation_summary",
            "data": results
        })
        
        self.log(f"  ✓ 后渗透完成：提权成功，发现 {len(internal_hosts)} 台内网主机")
        
        return results

class ReporterAgent(BaseAgent):
    """记录员 - 报告生成"""
    
    def execute(self, task: Task) -> Dict:
        self.log(f"📝 开始生成报告：{task.description}")
        
        # 收集所有阶段数据
        findings = self.state.state.findings
        credentials = self.state.state.credentials
        timeline = self.state.state.timeline
        
        report = {
            "mission_id": self.state.state.mission_id,
            "target": self.state.state.target['domain'],
            "executive_summary": "",
            "findings_count": len(findings),
            "critical_findings": 0,
            "high_findings": 0,
            "credentials_compromised": len(credentials),
            "recommendations": [],
            "timeline": timeline,
            "detailed_findings": findings
        }
        
        # 生成执行摘要
        report["executive_summary"] = f"""
针对 {report['target']} 的渗透测试已完成。

本次测试共发现 {report['findings_count']} 个安全问题，
其中高危漏洞 {report['high_findings']} 个，
已获取 {report['credentials_compromised']} 组敏感凭据。

建议立即修复关键漏洞并加强安全监控。
"""
        
        # 生成修复建议
        report["recommendations"] = [
            {
                "priority": "critical",
                "action": "更新 WordPress 及所有插件到最新版本",
                "impact": "防止已知漏洞利用"
            },
            {
                "priority": "high",
                "action": "部署 WAF 并配置规则",
                "impact": "阻止常见 Web 攻击"
            },
            {
                "priority": "medium",
                "action": "实施多因素认证",
                "impact": "降低凭据泄露风险"
            },
            {
                "priority": "low",
                "action": "定期安全审计",
                "impact": "持续监控安全状态"
            }
        ]
        
        # 保存报告
        report_file = REPORTS_DIR / f"{self.state.state.mission_id}_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"  ✓ 报告已保存：{report_file}")
        
        # 生成 HTML 报告 (简化版)
        html_report = self._generate_html_report(report)
        html_file = REPORTS_DIR / f"{self.state.state.mission_id}_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        self.log(f"  ✓ HTML 报告已保存：{html_file}")
        
        return report
    
    def _generate_html_report(self, report: Dict) -> str:
        """生成 HTML 报告"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>渗透测试报告 - {report['target']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #c0392b; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .finding {{ border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
        .critical {{ border-color: #c0392b; }}
        .high {{ border-color: #e74c3c; }}
        .medium {{ border-color: #f39c12; }}
        .low {{ border-color: #27ae60; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <h1>🔒 渗透测试报告</h1>
    <p><strong>任务 ID:</strong> {report['mission_id']}</p>
    <p><strong>目标:</strong> {report['target']}</p>
    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>执行摘要</h2>
        <pre>{report['executive_summary']}</pre>
    </div>
    
    <h2>统计</h2>
    <table>
        <tr><th>指标</th><th>数值</th></tr>
        <tr><td>发现总数</td><td>{report['findings_count']}</td></tr>
        <tr><td>凭据泄露</td><td>{report['credentials_compromised']}</td></tr>
    </table>
    
    <h2>修复建议</h2>
    <table>
        <tr><th>优先级</th><th>建议</th><th>影响</th></tr>
        {''.join(f"<tr><td>{r['priority'].upper()}</td><td>{r['action']}</td><td>{r['impact']}</td></tr>" for r in report['recommendations'])}
    </table>
    
    <h2>时间线</h2>
    <ul>
        {''.join(f"<li>{t['timestamp']}: {t['event']}</li>" for t in report['timeline'][:10])}
    </ul>
</body>
</html>
"""

# ============== 主协调器 ==============

class RedTeamOrchestrator:
    def __init__(self):
        self.state_manager = StateManager()
        self.agents = {
            AgentRole.RECON: ReconAgent(AgentRole.RECON, self.state_manager),
            AgentRole.ANALYZER: AnalyzerAgent(AgentRole.ANALYZER, self.state_manager),
            AgentRole.EXPLOIT: ExploitAgent(AgentRole.EXPLOIT, self.state_manager),
            AgentRole.POST: PostAgent(AgentRole.POST, self.state_manager),
            AgentRole.REPORTER: ReporterAgent(AgentRole.REPORTER, self.state_manager)
        }
    
    def run_mission(self, target_domain: str, mode: str = "full") -> str:
        """执行完整任务"""
        
        target = Target(domain=target_domain)
        mission_id = self.state_manager.init_mission(target)
        
        print(f"\n{'='*60}")
        print(f"🔒 ClawSec RedTeam 任务启动")
        print(f"{'='*60}")
        print(f"任务 ID: {mission_id}")
        print(f"目  标：{target_domain}")
        print(f"模  式：{mode}")
        print(f"{'='*60}\n")
        
        # 阶段 1: 侦察
        self._execute_phase(AttackPhase.RECONNAISSANCE, AgentRole.RECON, "信息收集与资产发现")
        
        if mode in ["full", "recon"]:
            # 阶段 2: 分析
            self._execute_phase(AttackPhase.ANALYSIS, AgentRole.ANALYZER, "攻击面分析与策略规划")
        
        if mode == "full":
            # 阶段 3: 利用
            self._execute_phase(AttackPhase.EXPLOITATION, AgentRole.EXPLOIT, "漏洞利用与权限获取")
            
            # 阶段 4: 后渗透
            self._execute_phase(AttackPhase.POST_EXPLOITATION, AgentRole.POST, "后渗透与横向移动")
        
        # 阶段 5: 报告 (始终执行)
        self._execute_phase(AttackPhase.REPORTING, AgentRole.REPORTER, "报告生成与复盘")
        
        print(f"\n{'='*60}")
        print(f"✅ 任务完成：{mission_id}")
        print(f"{'='*60}\n")
        
        return mission_id
    
    def _execute_phase(self, phase: AttackPhase, agent_role: AgentRole, description: str):
        """执行单个阶段"""
        self.state_manager.log(f"📍 阶段：{phase.value}")
        
        task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            phase=phase.value,
            agent=agent_role.value,
            description=description,
            status=TaskStatus.RUNNING.value,
            started_at=datetime.utcnow().isoformat()
        )
        
        self.state_manager.add_task(task)
        
        agent = self.agents[agent_role]
        try:
            result = agent.execute(task)
            self.state_manager.update_task(
                task.id,
                status=TaskStatus.COMPLETED.value,
                result=result,
                completed_at=datetime.utcnow().isoformat()
            )
        except Exception as e:
            self.state_manager.update_task(
                task.id,
                status=TaskStatus.FAILED.value,
                error=str(e),
                completed_at=datetime.utcnow().isoformat()
            )
            self.state_manager.log(f"❌ 任务失败：{e}")
        
        self.state_manager.next_phase()

# ============== CLI 入口 ==============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="🔒 ClawSec RedTeam Orchestrator")
    parser.add_argument("--target", "-t", help="目标域名")
    parser.add_argument("--mode", "-m", default="full", choices=["full", "recon", "analyze"],
                       help="执行模式：full=完整攻击链，recon=仅侦察，analyze=侦察 + 分析")
    parser.add_argument("--status", "-s", action="store_true", help="查看当前任务状态")
    parser.add_argument("--init", "-i", action="store_true", help="初始化系统")
    
    args = parser.parse_args()
    
    orchestrator = RedTeamOrchestrator()
    
    if args.init:
        print("✅ RedTeam 系统已初始化")
        print(f"📁 工作目录：{WORKSPACE}")
        return
    
    if args.status:
        if orchestrator.state_manager.load():
            state = orchestrator.state_manager.state
            print(f"\n📊 当前任务状态")
            print(f"任务 ID: {state.mission_id}")
            print(f"目  标：{state.target['domain']}")
            print(f"阶  段：{state.current_phase}")
            print(f"任  务：{len(state.tasks)}")
            print(f"发  现：{len(state.findings)}")
            print(f"凭  证：{len(state.credentials)}\n")
        else:
            print("⚠️  无活动任务")
        return
    
    if args.target:
        orchestrator.run_mission(args.target, args.mode)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
