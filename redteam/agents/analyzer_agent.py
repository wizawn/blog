#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Analyzer-Agent - 分析师
攻击面分析与策略规划
"""

class AnalyzerAgent:
    """分析师 Agent - 策略规划专家"""
    
    def __init__(self, recon_results: dict):
        self.recon = recon_results
        self.analysis = {
            "attack_vectors": [],
            "risk_score": 0,
            "recommended_path": [],
            "waf_detected": False,
            "difficulty": "medium"
        }
    
    def analyze(self) -> dict:
        """执行攻击面分析"""
        print("[📊] Analyzer-Agent 分析中...")
        
        # 分析攻击向量
        self._identify_attack_vectors()
        
        # 计算风险评分
        self._calculate_risk_score()
        
        # 生成攻击路径
        self._generate_attack_path()
        
        return self.analysis
    
    def _identify_attack_vectors(self):
        """识别攻击向量"""
        # Web 应用攻击面
        if any(p['port'] in ['80', '443'] for p in self.recon.get('ports', [])):
            self.analysis["attack_vectors"].append({
                "vector": "web_application",
                "confidence": 0.9,
                "tools": ["nuclei", "burp", "sqlmap"]
            })
        
        # CMS 攻击面
        for tech in self.recon.get('technologies', []):
            if 'WordPress' in tech:
                self.analysis["attack_vectors"].append({
                    "vector": "cms_exploitation",
                    "confidence": 0.85,
                    "tools": ["wpscan", "metasploit"]
                })
    
    def _calculate_risk_score(self):
        """计算整体风险评分 (0-100)"""
        score = 0
        
        # 基于开放端口
        score += len(self.recon.get('ports', [])) * 5
        
        # 基于潜在漏洞
        for vuln in self.recon.get('potential_vulnerabilities', []):
            if vuln.get('severity') == 'critical':
                score += 25
            elif vuln.get('severity') == 'high':
                score += 15
            elif vuln.get('severity') == 'medium':
                score += 8
        
        self.analysis["risk_score"] = min(score, 100)
        
        # 难度评估
        if score > 70:
            self.analysis["difficulty"] = "easy"
        elif score > 40:
            self.analysis["difficulty"] = "medium"
        else:
            self.analysis["difficulty"] = "hard"
    
    def _generate_attack_path(self):
        """生成推荐攻击路径"""
        self.analysis["recommended_path"] = [
            {"step": 1, "action": "信息收集", "status": "completed"},
            {"step": 2, "action": "漏洞扫描", "status": "pending"},
            {"step": 3, "action": "漏洞利用", "status": "pending"},
            {"step": 4, "action": "权限维持", "status": "pending"}
        ]
