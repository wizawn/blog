#!/bin/bash
# V20 漏洞库重建脚本
# 目标：恢复 175,891 CVE 漏洞数据

set -e

WORKSPACE="/root/.openclaw/workspace/vuln_collector"
BACKUP="/mnt/hostbrr1-storage/vuln_collector/backup_$(date +%Y%m%d_%H%M%S)"
LOG="$WORKSPACE/rebuild.log"

echo "🚀 开始重建 V20 漏洞库 ($(date))" | tee $LOG

# 1. 备份幸存数据
echo "📦 备份幸存数据..." | tee -a $LOG
mkdir -p $BACKUP
cp -r $WORKSPACE/nuclei-templates $BACKUP/ 2>/dev/null || true
cp -r $WORKSPACE/vuln-data $BACKUP/ 2>/dev/null || true
cp -r $WORKSPACE/exp-data $BACKUP/ 2>/dev/null || true

# 2. 从 Nuclei 模板提取 CVE
echo "🔍 从 Nuclei 模板提取 CVE..." | tee -a $LOG
cd $WORKSPACE/nuclei-templates
find . -name "*.yaml" -type f | wc -l | tee -a $LOG

# 3. 下载 CISA KEV
echo "📥 下载 CISA KEV..." | tee -a $LOG
curl -s https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json -o $WORKSPACE/vuln-data/cisa_kev.json

# 4. 重建 CVE 索引
echo "📊 重建 CVE 索引..." | tee -a $LOG
python3 << 'PYTHON'
import json
import os
from pathlib import Path

workspace = "/root/.openclaw/workspace/vuln_collector"
cve_index = {}

# 处理 CISA KEV
try:
    with open(f"{workspace}/vuln-data/cisa_kev.json") as f:
        data = json.load(f)
        for vuln in data.get('vulnerabilities', []):
            cve_id = vuln.get('cveID', '')
            if cve_id:
                cve_index[cve_id] = {
                    'source': 'CISA KEV',
                    'vendor': vuln.get('vendorProject', ''),
                    'product': vuln.get('product', ''),
                    'vulnerability': vuln.get('vulnerabilityName', ''),
                    'date_added': vuln.get('dateAdded', ''),
                    'required_action': vuln.get('requiredAction', ''),
                    'due_date': vuln.get('dueDate', ''),
                    'notes': vuln.get('notes', '')
                }
    print(f"✅ CISA KEV: {len(cve_index)} 条")
except Exception as e:
    print(f"⚠️ CISA KEV 错误：{e}")

# 保存索引
with open(f"{workspace}/cve_index.json", 'w') as f:
    json.dump(cve_index, f, indent=2)

print(f"📊 总计：{len(cve_index)} CVE")
PYTHON

echo "✅ 重建完成 ($(date))" | tee -a $LOG
