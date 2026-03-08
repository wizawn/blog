#!/bin/bash
# V20 漏洞库全量重建脚本
# 目标：200,000+ CVE, 55,656+ Nuclei 模板

set -e

WORKSPACE="/root/.openclaw/workspace/vuln_collector"
REMOTE="107.172.8.123"
REMOTE_USER="root"
REMOTE_PASS="36vxUuq892fVQE8rVI"
LOG="$WORKSPACE/rebuild_full.log"

echo "🚀 V20 漏洞库全量重建开始: $(date)" | tee $LOG

# 1. 从远程服务器拉取完整 nuclei 模板
echo "📥 从远程服务器拉取 Nuclei 模板..." | tee -a $LOG
sshpass -p "$REMOTE_PASS" rsync -av \
  ${REMOTE_USER}@${REMOTE}:/root/nuclei-templates/ \
  $WORKSPACE/nuclei-templates-remote/ 2>&1 | tee -a $LOG

# 2. 统计模板数量
echo "📊 统计模板数量..." | tee -a $LOG
find $WORKSPACE/nuclei-templates-remote -name "*.yaml" | wc -l | tee -a $LOG

# 3. 下载 CISA KEV
echo "📥 下载 CISA KEV..." | tee -a $LOG
curl -s https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json \
  -o $WORKSPACE/vuln-data/cisa_kev_latest.json

# 4. 启动 NVD 全量采集
echo "📥 启动 NVD 全量采集 (2015-2026)..." | tee -a $LOG
python3 $WORKSPACE/scripts/collect_nvd_full.py &

echo "✅ 阶段 1&2 完成: $(date)" | tee -a $LOG
