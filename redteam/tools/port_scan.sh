#!/bin/bash
# 🔒 ClawSec RedTeam - 端口扫描工具
# 用法：./port_scan.sh <target>

set -e

TARGET=$1
OUTPUT_DIR="/root/.openclaw/workspace/redteam/output/artifacts"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$TARGET" ]; then
    echo "用法：$0 <target>"
    echo "示例：$0 example.com 或 $0 192.168.1.1"
    exit 1
fi

echo "[🔍] 开始端口扫描：$TARGET"
echo "[📁] 输出目录：$OUTPUT_DIR"

mkdir -p "$OUTPUT_DIR"

# 1. 快速扫描 (Top 1000 端口)
echo "[1/3] Nmap 快速扫描 (Top 1000)..."
nmap -T4 --top-ports 1000 -oN "$OUTPUT_DIR/nmap_fast_${TARGET}_${TIMESTAMP}.txt" "$TARGET" 2>/dev/null || true
echo "    ✓ 快速扫描完成"

# 2. 服务版本检测 (针对开放端口)
echo "[2/3] 服务版本检测..."
nmap -sV -sC -oN "$OUTPUT_DIR/nmap_version_${TARGET}_${TIMESTAMP}.txt" "$TARGET" 2>/dev/null || true
echo "    ✓ 版本检测完成"

# 3. 全端口扫描 (可选，耗时)
echo "[3/3] Masscan 全端口扫描 (后台运行)..."
if command -v masscan &> /dev/null; then
    masscan -p1-65535 "$TARGET" --rate=1000 -oG "$OUTPUT_DIR/masscan_${TARGET}_${TIMESTAMP}.txt" &
    MASSCAN_PID=$!
    echo "    ⏳ Masscan 运行中 (PID: $MASSCAN_PID)"
else
    echo "    ⚠ masscan 未安装，跳过"
fi

echo ""
echo "[✅] 端口扫描启动完成"
echo "[📄] 快速扫描结果：$OUTPUT_DIR/nmap_fast_${TARGET}_${TIMESTAMP}.txt"
echo "[📄] 版本检测结果：$OUTPUT_DIR/nmap_version_${TARGET}_${TIMESTAMP}.txt"

# 提取开放端口
echo ""
echo "[📊] 开放端口摘要:"
grep "open" "$OUTPUT_DIR/nmap_version_${TARGET}_${TIMESTAMP}.txt" 2>/dev/null | head -20 || echo "    暂无结果"
