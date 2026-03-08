#!/usr/bin/env python3
"""
ARL + Nuclei 联合扫描工具
- 从 ARL 获取目标 IP
- 使用自定义 Nuclei 模板扫描
- 实时汇报进度
"""

import requests
import subprocess
import json
import os
import time
from datetime import datetime

ARL_URL = "https://107.172.8.123:5003"
ARL_USERNAME = "admin"
ARL_PASSWORD = "yanling6,hate"
NUCLEI_TEMPLATES_DIR = "/root/.openclaw/workspace/01_Projects/02_漏洞采集库/vuln_collector/nuclei-templates/custom"
OUTPUT_DIR = "/root/.openclaw/workspace/reports/nuclei-scan"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*60)
print("ARL + Nuclei 联合扫描工具")
print("="*60)

# 1. 登录 ARL
print("\n[*] 登录 ARL...")
session = requests.Session()
login_resp = session.get(ARL_URL, verify=False)

import re
csrf = re.search(r'name="_csrf" value="([^"]+)"', login_resp.text)
csrf_token = csrf.group(1) if csrf else ""

login_data = f"username={ARL_USERNAME}&password={ARL_PASSWORD.replace(',', '%2C')}&_csrf={csrf_token}"
login_resp = session.post(
    f"{ARL_URL}/user/login",
    data=login_data,
    verify=False,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    allow_redirects=False
)

if login_resp.status_code == 302:
    print("[+] ARL 登录成功")
else:
    print(f"[!] ARL 登录失败：{login_resp.status_code}")
    # 尝试直接继续（可能已有 cookie）

# 2. 获取 ARL 中的 IP 列表
print("\n[*] 获取 ARL 目标 IP...")
try:
    ip_resp = session.get(f"{ARL_URL}/api/ip?page=1&size=10000", verify=False, timeout=30)
    if ip_resp.status_code == 200:
        ip_data = ip_resp.json()
        ips = [f"{item['ip']}:{item.get('port', '80')}" for item in ip_data.get('data', [])]
        print(f"[+] 获取到 {len(ips)} 个目标 IP")
    else:
        print(f"[!] 获取 IP 失败：{ip_resp.status_code}")
        ips = []
except Exception as e:
    print(f"[!] 获取 IP 出错：{e}")
    ips = []

if not ips:
    print("[!] 没有目标 IP，退出")
    exit(1)

# 保存 IP 列表
ip_file = "/tmp/arl_targets.txt"
with open(ip_file, 'w') as f:
    for ip in ips:
        f.write(ip + '\n')
print(f"[*] IP 列表已保存到 {ip_file}")

# 3. 准备 Nuclei 扫描
print(f"\n[*] Nuclei 模板目录：{NUCLEI_TEMPLATES_DIR}")
if not os.path.exists(NUCLEI_TEMPLATES_DIR):
    print(f"[!] 模板目录不存在")
    exit(1)

# 统计模板数量
template_count = sum(len(files) for _, _, files in os.walk(NUCLEI_TEMPLATES_DIR))
print(f"[*] 可用模板数：{template_count}")

# 4. 执行 Nuclei 扫描
scan_time = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(OUTPUT_DIR, f"nuclei-scan-{scan_time}.json")

print(f"\n[*] 开始 Nuclei 扫描...")
print(f"[*] 目标数：{len(ips)}")
print(f"[*] 输出文件：{output_file}")
print()

nuclei_cmd = f'''nuclei -l {ip_file} -t {NUCLEI_TEMPLATES_DIR} -json -o {output_file} -rate-limit 10 -concurrency 25 -timeout 10 -retries 2'''

print(f"[*] 执行命令：{nuclei_cmd}")
print()

try:
    result = subprocess.run(nuclei_cmd, shell=True, capture_output=False, timeout=7200)
    
    print()
    print("="*60)
    print("✅ 扫描完成!")
    print(f"   输出文件：{output_file}")
    print("="*60)
    
    # 统计结果
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            findings = [json.loads(line) for line in f if line.strip()]
        print(f"\n[+] 发现漏洞数：{len(findings)}")
        
        # 按严重程度统计
        by_severity = {}
        for f in findings:
            sev = f.get('info', {}).get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        print("\n按严重程度统计:")
        for sev, count in sorted(by_severity.items(), key=lambda x: -x[1]):
            print(f"  {sev}: {count}")
    
except subprocess.TimeoutExpired:
    print("\n[!] 扫描超时 (2 小时限制)")
except Exception as e:
    print(f"\n[!] 扫描出错：{e}")
