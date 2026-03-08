#!/usr/bin/env python3
"""
扩大化漏洞采集脚本 v2.0
支持：CISA KEV + NVD + GitHub Advisory + OpenCVE
原则：免钥、去重、规范化命名、Nuclei 范式
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# ================= 配置区域 =================
OUTPUT_DIR = "/root/.openclaw/workspace/vuln-data"
# 直连访问（无需代理）
PROXY = None

# API 端点（免钥）
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
GITHUB_ADVISORY_BASE = "https://raw.githubusercontent.com/github/advisory-database/main/ecosystems"
OPENCVE_BASE = "https://www.opencve.io/api/cve"

# 采集时间范围（最近 30 天）
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=30)

# ================= 工具函数 =================
def save_json(data, filename):
    """保存 JSON 数据"""
    filepath = Path(OUTPUT_DIR) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 保存：{filepath} ({len(data)} 条)")

def load_json(filename):
    """加载 JSON 数据"""
    filepath = Path(OUTPUT_DIR) / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def normalize_cve_id(cve_id):
    """规范化 CVE ID 格式"""
    return cve_id.upper().strip()

def generate_nuclei_filename(cve_id, vuln_type, target):
    """生成 Nuclei 规范的文件名"""
    vuln_type = vuln_type.lower().replace(' ', '_')
    target = target.lower().replace(' ', '_').replace('.', '')
    return f"{cve_id}_{vuln_type}_{target}.yaml"

# ================= 数据采集 =================
def collect_cisa_kev():
    """采集 CISA KEV（已知被利用漏洞）"""
    print("\n🔴 采集 CISA KEV...")
    try:
        resp = requests.get(CISA_KEV_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        vulns = []
        for item in data.get('vulnerabilities', []):
            vulns.append({
                'source': 'CISA_KEV',
                'cve_id': normalize_cve_id(item.get('cveID', '')),
                'vendor': item.get('vendorProject', ''),
                'product': item.get('product', ''),
                'name': item.get('vulnerabilityName', ''),
                'date_added': item.get('dateAdded', ''),
                'description': item.get('shortDescription', ''),
                'priority': 'CRITICAL'  # CISA 都是高危
            })
        
        save_json(vulns, 'cisa_kev.json')
        return vulns
    except Exception as e:
        print(f"❌ CISA 采集失败：{e}")
        return []

def collect_nvd():
    """采集 NVD（最近 30 天）"""
    print("\n🔵 采集 NVD...")
    vulns = []
    
    try:
        # NVD 免钥限制：每 30 秒 5 次请求，需要分页
        start_date = START_DATE.strftime('%Y-%m-%dT%H:%M:%S')
        end_date = END_DATE.strftime('%Y-%m-%dT%H:%M:%S')
        
        page = 0
        page_size = 100  # 每页 100 条
        
        while True:
            url = f"{NVD_BASE_URL}?lastModStartDate={start_date}&lastModEndDate={end_date}&resultsPerPage={page_size}&startIndex={page * page_size}"
            
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"⚠️ NVD 请求失败：{resp.status_code}")
                break
            
            data = resp.json()
            cves = data.get('vulnerabilities', [])
            
            if not cves:
                break
            
            for item in cves:
                cve = item.get('cve', {})
                vulns.append({
                    'source': 'NVD',
                    'cve_id': normalize_cve_id(cve.get('id', '')),
                    'description': cve.get('descriptions', [{}])[0].get('value', ''),
                    'severity': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN'),
                    'score': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0),
                    'references': [ref.get('url', '') for ref in cve.get('references', [])[:5]],
                    'last_modified': cve.get('lastModified', '')
                })
            
            print(f"  已采集 {len(vulns)} 条...")
            page += 1
            
            # NVD 免钥限流
            import time
            time.sleep(6)  # 每 6 秒一次请求（安全余量）
            
            # 最多采集 500 条（免钥限制）
            if len(vulns) >= 500:
                print("⚠️ 达到免钥采集上限（500 条）")
                break
        
        save_json(vulns, 'nvd_recent.json')
        return vulns
    except Exception as e:
        print(f"❌ NVD 采集失败：{e}")
        return []

def collect_github_advisory(ecosystem='npm'):
    """采集 GitHub Advisory Database"""
    print(f"\n🟢 采集 GitHub Advisory ({ecosystem})...")
    try:
        url = f"{GITHUB_ADVISORY_BASE}/{ecosystem}/advisories.json"
        resp = requests.get(url, proxies={'http': PROXY, 'https': PROXY}, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        vulns = []
        
        for item in data:
            vulns.append({
                'source': 'GitHub_Advisory',
                'cve_id': normalize_cve_id(item.get('schema_version', '')),
                'ecosystem': ecosystem,
                'package': item.get('package', {}).get('name', ''),
                'severity': item.get('severity', ''),
                'summary': item.get('summary', ''),
                'description': item.get('details', ''),
                'references': item.get('references', [])
            })
        
        save_json(vulns, f'github_advisory_{ecosystem}.json')
        return vulns
    except Exception as e:
        print(f"❌ GitHub Advisory 采集失败：{e}")
        return []

def collect_opencve():
    """采集 OpenCVE（演示站）"""
    print("\n🟡 采集 OpenCVE...")
    vulns = []
    
    try:
        # OpenCVE 演示站限流，只采集前 100 条
        url = f"{OPENCVE_BASE}?per_page=100"
        resp = requests.get(url, proxies={'http': PROXY, 'https': PROXY}, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                vulns.append({
                    'source': 'OpenCVE',
                    'cve_id': normalize_cve_id(item.get('id', '')),
                    'summary': item.get('summary', ''),
                    'severity': item.get('cvss', {}).get('severity', ''),
                    'score': item.get('cvss', {}).get('score', 0),
                    'updated_at': item.get('updated_at', '')
                })
        
        save_json(vulns, 'opencve.json')
        return vulns
    except Exception as e:
        print(f"❌ OpenCVE 采集失败：{e}")
        return []

# ================= 数据合并去重 =================
def merge_and_dedup(all_vulns):
    """合并多源数据并去重"""
    print("\n🔄 合并去重...")
    
    # 按 CVE ID 去重
    dedup_dict = {}
    for vuln in all_vulns:
        cve_id = vuln.get('cve_id', '')
        if not cve_id:
            continue
        
        # 优先级：CISA > NVD > GitHub > OpenCVE
        priority = {'CISA_KEV': 1, 'NVD': 2, 'GitHub_Advisory': 3, 'OpenCVE': 4}
        source_priority = priority.get(vuln.get('source', ''), 99)
        
        if cve_id not in dedup_dict or source_priority < priority.get(dedup_dict[cve_id].get('source', ''), 99):
            dedup_dict[cve_id] = vuln
    
    merged = list(dedup_dict.values())
    print(f"✅ 去重后：{len(merged)} 条（原始 {len(all_vulns)} 条）")
    
    save_json(merged, 'merged_vulns_dedup.json')
    return merged

# ================= 主程序 =================
def main():
    print("=" * 60)
    print("🔍 扩大化漏洞采集 v2.0")
    print(f"📅 时间范围：{START_DATE.date()} ~ {END_DATE.date()}")
    print("=" * 60)
    
    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # 采集各数据源
    all_vulns = []
    
    # 1. CISA KEV（优先级最高）
    cisa_vulns = collect_cisa_kev()
    all_vulns.extend(cisa_vulns)
    
    # 2. NVD（最近 30 天，限 500 条）
    nvd_vulns = collect_nvd()
    all_vulns.extend(nvd_vulns)
    
    # 3. GitHub Advisory（NPM 生态）
    github_vulns = collect_github_advisory('npm')
    all_vulns.extend(github_vulns)
    
    # 4. OpenCVE（演示站，前 100 条）
    opencve_vulns = collect_opencve()
    all_vulns.extend(opencve_vulns)
    
    # 合并去重
    merged_vulns = merge_and_dedup(all_vulns)
    
    # 生成统计报告
    report = {
        '采集时间': datetime.now().isoformat(),
        '数据源': {
            'CISA_KEV': len(cisa_vulns),
            'NVD': len(nvd_vulns),
            'GitHub_Advisory': len(github_vulns),
            'OpenCVE': len(opencve_vulns)
        },
        '总计（去重前）': len(all_vulns),
        '总计（去重后）': len(merged_vulns),
        '去重率': f"{(1 - len(merged_vulns)/len(all_vulns))*100:.1f}%" if all_vulns else 0
    }
    
    save_json(report, 'collection_report.json')
    
    print("\n" + "=" * 60)
    print("✅ 采集完成！")
    print(f"📊 总计：{len(merged_vulns)} 条漏洞数据")
    print(f"📁 输出目录：{OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
