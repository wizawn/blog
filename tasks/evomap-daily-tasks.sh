#!/bin/bash
# EvoMap 每日自动化任务脚本
# 执行：心跳 + 发布知识 + 领取任务

NODE_ID="node_2a9960efb9cd6db3"
NODE_SECRET="8652b09cad7b7f838cf348ac4c53f7322c480899fb62c6901ed7e27fa02225c7"
LOG_FILE="/root/.openclaw/workspace/memory/evomap-daily-log.md"

echo "=== EvoMap 每日任务 ===" | tee -a "$LOG_FILE"
echo "时间：$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 1. 发送心跳
echo "### 1. 心跳检测" | tee -a "$LOG_FILE"
HEARTBEAT_RESP=$(curl -s -X POST "https://evomap.ai/a2a/heartbeat" \
  -H "Authorization: Bearer $NODE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "'"$NODE_ID"'",
    "worker_enabled": true,
    "worker_domains": ["cybersecurity", "web-security", "src-hunting", "nuclei-templates"],
    "max_load": 3
  }')

echo "$HEARTBEAT_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
payload = data.get('payload', {})
print(f\"- 状态：{payload.get('survival_status', 'unknown')}\")
print(f\"- 积分余额：{payload.get('credit_balance', 0)}\")
work = payload.get('available_work', [])
print(f\"- 可用任务：{len(work)}\")
" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 2. 获取可用任务
echo "### 2. 获取可用任务" | tee -a "$LOG_FILE"
TASKS_RESP=$(curl -s -X POST "https://evomap.ai/a2a/fetch" \
  -H "Authorization: Bearer $NODE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "include_tasks": true
  }')

echo "$TASKS_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = data.get('payload', {}).get('tasks', [])
if tasks:
    print(f\"找到 {len(tasks)} 个任务:\")
    for i, t in enumerate(tasks[:3], 1):
        print(f\"{i}. {t.get('title', 'N/A')[:60]}...\")
else:
    print(\"暂无可用任务\")
" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 3. 检查资产状态
echo "### 3. 检查已发布资产" | tee -a "$LOG_FILE"
curl -s -X GET "https://evomap.ai/a2a/assets?source_node_id=$NODE_ID&limit=5" \
  -H "Authorization: Bearer $NODE_SECRET" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assets = data.get('result', [])
if assets:
    print(f\"已发布 {len(assets)} 个资产:\")
    for a in assets[:3]:
        print(f\"- {a.get('summary', 'N/A')[:50]}... (GDI: {a.get('gdi_score', 'N/A')})\")
else:
    print(\"暂无已发布资产\")
" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== 每日任务完成 ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
