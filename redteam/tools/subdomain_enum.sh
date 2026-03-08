#!/bin/bash
# 🔒 ClawSec RedTeam - 子域名枚举工具
# 用法：./subdomain_enum.sh <target>

set -e

TARGET=$1
OUTPUT_DIR="/root/.openclaw/workspace/redteam/output/artifacts"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$TARGET" ]; then
    echo "用法：$0 <target_domain>"
    echo "示例：$0 example.com"
    exit 1
fi

echo "[🔍] 开始子域名枚举：$TARGET"
echo "[📁] 输出目录：$OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 1. Subfinder
echo "[1/5] Subfinder 扫描..."
if command -v subfinder &> /dev/null; then
    subfinder -d "$TARGET" -o "$OUTPUT_DIR/subfinder_${TARGET}_${TIMESTAMP}.txt" 2>/dev/null || true
    echo "    ✓ Subfinder 完成"
else
    echo "    ⚠ subfinder 未安装，跳过"
fi

# 2. Assetfinder
echo "[2/5] Assetfinder 扫描..."
if command -v assetfinder &> /dev/null; then
    assetfinder "$TARGET" > "$OUTPUT_DIR/assetfinder_${TARGET}_${TIMESTAMP}.txt" 2>/dev/null || true
    echo "    ✓ Assetfinder 完成"
else
    echo "    ⚠ assetfinder 未安装，跳过"
fi

# 3. Amass (如果安装)
echo "[3/5] Amass 扫描..."
if command -v amass &> /dev/null; then
    amass enum -d "$TARGET" -o "$OUTPUT_DIR/amass_${TARGET}_${TIMESTAMP}.txt" 2>/dev/null || true
    echo "    ✓ Amass 完成"
else
    echo "    ⚠ amass 未安装，跳过"
fi

# 4. 暴力枚举 (常见子域名)
echo "[4/5] 暴力枚举常见子域名..."
COMMON_SUBS="www api admin dev test staging prod mail vpn ftp blog shop app mobile cdn static"
> "$OUTPUT_DIR/bruteforce_${TARGET}_${TIMESTAMP}.txt"

for sub in $COMMON_SUBS; do
    if dig +short "$sub.$TARGET" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
        echo "$sub.$TARGET" >> "$OUTPUT_DIR/bruteforce_${TARGET}_${TIMESTAMP}.txt"
    fi
done
echo "    ✓ 暴力枚举完成"

# 5. 合并去重
echo "[5/5] 合并结果..."
cat "$OUTPUT_DIR"/*"${TARGET}_${TIMESTAMP}.txt" 2>/dev/null | sort -u > "$OUTPUT_DIR/all_subdomains_${TARGET}_${TIMESTAMP}.txt"

COUNT=$(wc -l < "$OUTPUT_DIR/all_subdomains_${TARGET}_${TIMESTAMP}.txt")
echo ""
echo "[✅] 子域名枚举完成"
echo "[📊] 发现子域名数量：$COUNT"
echo "[📄] 结果文件：$OUTPUT_DIR/all_subdomains_${TARGET}_${TIMESTAMP}.txt"
