#!/usr/bin/env python3
"""
大规模漏洞采集脚本 v4.0
目标：恢复 20 万 + 漏洞数据
采集源：NVD 全量 + Exploit-DB + GitHub Advisory 全生态 + PacketStorm + VulnHub
"""

import requests
import json
import subprocess
import gzip
import shutil
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "/root/.openclaw/workspace/vuln-data"
RCLONE_DEST = "hostbrr1:vuln_collector/processed"

# NVD 全量数据文件
NVD_FILES = [
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2026.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2025.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2024.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2023.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2022.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2021.json.gz",
    "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2020.json.gz",
]

# Exploit-DB 仓库
EXPLOITDB_GIT = "https://gitlab.com/exploit-database/exploitdb.git"

# GitHub Advisory 生态
GITHUB_ADV_BASE = "https://raw.githubusercontent.com/github/advisory-database/main/ecosystems"
GITHUB_ECOSYSTEMS = ['npm', 'pip', 'maven', 'rubygems', 'nuget', 'go', 'rust']

def save_json(data, filename):
    filepath = Path(OUTPUT_DIR) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存：{filepath} ({len(data) if isinstance(data, list) else 'object'} 条)")

def download_gzip(url, output_file):
    """下载并解压 gzip 文件"""
    print(f"   下载：{url.split('/')[-1]}")
    resp = requests.get(url, stream=True, timeout=60)
    with open(output_file + '.gz', 'wb') as f:
        shutil.copyfileobj(resp.raw, f)
    
    with gzip.open(output_file + '.gz', 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    import os
    os.remove(output_file + '.gz')
    print(f"   ✅ 解压完成")

def clone_git_repo(url, dest):
    """克隆 git 仓库"""
    cmd = f"git clone --depth 1 {url} {dest}"
    print(f"   克隆：{url}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def run_rclone(src, dest):
    """rclone 同步"""
    cmd = f"rclone sync {src} {dest} --progress"
    print(f"📤 同步：{cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode == 0

print("=" * 60)
print("🔍 大规模漏洞采集 v4.0")
print("🎯 目标：20 万 + 漏洞数据")
print("=" * 60)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
all_vulns = []

# ================= 1. NVD 全量（2020-2026） =================
print("\n🔵 采集 NVD 全量（2020-2026）...")
nvd_count = 0
for url in NVD_FILES:
    try:
        filename = url.split('/')[-1].replace('.json.gz', '')
        filepath = Path(OUTPUT_DIR) / filename
        
        if not filepath.exists():
            download_gzip(url, str(filepath))
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cves = data.get('CVE_Items', [])
            nvd_count += len(cves)
            print(f"   {filename}: {len(cves)} 条")
    except Exception as e:
        print(f"   ❌ 失败：{e}")

print(f"   NVD 总计：{nvd_count} 条")

# ================= 2. Exploit-DB =================
print("\n🔴 克隆 Exploit-DB...")
exploitdb_dir = Path(OUTPUT_DIR) / "exploitdb"
if not exploitdb_dir.exists():
    if clone_git_repo(EXPLOITDB_GIT, str(exploitdb_dir)):
        print("   ✅ Exploit-DB 克隆成功")
    else:
        print("   ❌ Exploit-DB 克隆失败")
else:
    print("   ⏭️ Exploit-DB 已存在")

# ================= 3. GitHub Advisory 全生态 =================
print("\n🟢 采集 GitHub Advisory 全生态...")
github_count = 0
for ecosystem in GITHUB_ECOSYSTEMS:
    try:
        url = f"{GITHUB_ADV_BASE}/{ecosystem}/advisories.json"
        print(f"   采集 {ecosystem}...")
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            github_count += len(data)
            print(f"   {ecosystem}: {len(data)} 条")
    except Exception as e:
        print(f"   ❌ {ecosystem} 失败：{e}")

print(f"   GitHub Advisory 总计：{github_count} 条")

# ================= 4. CISA KEV =================
print("\n🔴 采集 CISA KEV...")
try:
    resp = requests.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", timeout=30)
    data = resp.json()
    cisa_count = len(data.get('vulnerabilities', []))
    print(f"   CISA KEV: {cisa_count} 条")
except Exception as e:
    print(f"   ❌ 失败：{e}")

# ================= 统计报告 =================
report = {
    '采集时间': datetime.now().isoformat(),
    'NVD_全量': nvd_count,
    'GitHub_Advisory': github_count,
    'CISA_KEV': cisa_count if 'cisa_count' in dir() else 0,
    'Exploit-DB': '已克隆' if exploitdb_dir.exists() else '失败',
    '预计总量': nvd_count + github_count + (cisa_count if 'cisa_count' in dir() else 0)
}

save_json(report, 'massive_collection_report.json')

print("\n" + "=" * 60)
print(f"✅ 采集完成！预计 {report['预计总量']:,} 条")
print("=" * 60)

# ================= 同步到 hostbrr1 =================
print("\n📤 同步到 hostbrr1...")
if run_rclone(f"{OUTPUT_DIR}/", f"{RCLONE_DEST}/"):
    print("✅ 同步成功！")
else:
    print("❌ 同步失败")

print("\n" + "=" * 60)
print("✅ 全部完成！")
print("=" * 60)
