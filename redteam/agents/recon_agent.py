#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Recon-Agent - 侦察兵
信息收集与资产发现
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

class ReconAgent:
    """侦察兵 Agent - 信息收集专家"""
    
    def __init__(self, target: str, output_dir: str = None):
        self.target = target
        self.output_dir = Path(output_dir) if output_dir else Path("/tmp/recon")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            "subdomains": [],
            "ports": [],
            "technologies": [],
            "dns_records": {},
            "screenshots": [],
            "potential_vulnerabilities": []
        }
    
    def run_subfinder(self) -> list:
        """Subfinder 子域名枚举"""
        print(f"[🔍] Subfinder 扫描 {self.target}...")
        output_file = self.output_dir / f"subfinder_{self.target}.txt"
        
        try:
            result = subprocess.run(
                ["subfinder", "-d", self.target, "-o", str(output_file)],
                capture_output=True, text=True, timeout=300
            )
            
            if output_file.exists():
                with open(output_file) as f:
                    self.results["subdomains"] = [line.strip() for line in f if line.strip()]
            
            print(f"    ✓ 发现 {len(self.results['subdomains'])} 个子域名")
        except Exception as e:
            print(f"    ⚠ Subfinder 执行失败：{e}")
        
        return self.results["subdomains"]
    
    def run_nmap(self, ports: str = "1-10000") -> list:
        """Nmap 端口扫描"""
        print(f"[🔍] Nmap 端口扫描 {self.target}...")
        output_file = self.output_dir / f"nmap_{self.target}.txt"
        
        try:
            result = subprocess.run(
                ["nmap", "-sV", "-sC", "-oN", str(output_file), "-p", ports, self.target],
                capture_output=True, text=True, timeout=600
            )
            
            # 解析开放端口 (简化解析)
            if output_file.exists():
                with open(output_file) as f:
                    for line in f:
                        if "open" in line.lower():
                            parts = line.split()
                            if len(parts) >= 3:
                                self.results["ports"].append({
                                    "port": parts[0].split("/")[0],
                                    "service": parts[2] if len(parts) > 2 else "unknown"
                                })
            
            print(f"    ✓ 发现 {len(self.results['ports'])} 个开放端口")
        except Exception as e:
            print(f"    ⚠ Nmap 执行失败：{e}")
        
        return self.results["ports"]
    
    def run_whatweb(self) -> list:
        """WhatWeb 技术栈识别"""
        print(f"[🔍] WhatWeb 指纹识别 {self.target}...")
        
        try:
            result = subprocess.run(
                ["whatweb", "-v", self.target],
                capture_output=True, text=True, timeout=120
            )
            
            # 提取技术栈信息
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if "[" in line and "]" in line:
                        self.results["technologies"].append(line.strip())
            
            print(f"    ✓ 识别 {len(self.results['technologies'])} 项技术")
        except Exception as e:
            print(f"    ⚠ WhatWeb 执行失败：{e}")
        
        return self.results["technologies"]
    
    def analyze_vulnerabilities(self):
        """基于侦察结果分析潜在漏洞"""
        print("[📊] 分析潜在漏洞...")
        
        # 检查常见漏洞
        for tech in self.results["technologies"]:
            if "WordPress" in tech:
                self.results["potential_vulnerabilities"].append({
                    "type": "cms",
                    "severity": "medium",
                    "description": "WordPress 可能存在插件/主题漏洞",
                    "recommendation": "运行 wpscan 进行详细扫描"
                })
            
            if "Apache" in tech and "2.2" in tech:
                self.results["potential_vulnerabilities"].append({
                    "type": "web_server",
                    "severity": "high",
                    "description": "老旧 Apache 版本可能存在已知漏洞",
                    "recommendation": "升级到最新版本"
                })
        
        # 检查开放的危险端口
        dangerous_ports = {
            "21": "FTP 服务可能允许匿名登录",
            "23": "Telnet 明文传输，建议使用 SSH",
            "3306": "MySQL 直接暴露，建议限制访问",
            "6379": "Redis 未授权访问风险"
        }
        
        for port_info in self.results["ports"]:
            port = port_info.get("port", "")
            if port in dangerous_ports:
                self.results["potential_vulnerabilities"].append({
                    "type": "exposed_service",
                    "severity": "high",
                    "description": dangerous_ports[port],
                    "port": port
                })
        
        print(f"    ✓ 识别 {len(self.results['potential_vulnerabilities'])} 个潜在风险")
    
    def full_recon(self) -> dict:
        """执行完整侦察流程"""
        print(f"\n{'='*50}")
        print(f"🔍 Recon-Agent 启动")
        print(f"目标：{self.target}")
        print(f"{'='*50}\n")
        
        self.run_subfinder()
        self.run_nmap()
        self.run_whatweb()
        self.analyze_vulnerabilities()
        
        # 保存结果
        result_file = self.output_dir / f"recon_result_{self.target}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[✅] 侦察完成")
        print(f"[📄] 结果保存：{result_file}")
        print(f"{'='*50}\n")
        
        return self.results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python3 recon_agent.py <target>")
        print("示例：python3 recon_agent.py example.com")
        sys.exit(1)
    
    target = sys.argv[1]
    agent = ReconAgent(target)
    results = agent.full_recon()
    
    # 打印摘要
    print("\n📊 侦察摘要:")
    print(f"  子域名：{len(results['subdomains'])}")
    print(f"  开放端口：{len(results['ports'])}")
    print(f"  技术栈：{len(results['technologies'])}")
    print(f"  潜在风险：{len(results['potential_vulnerabilities'])}")
