#!/bin/bash
# 博客每日备份脚本
# 执行时间：每天 02:00 UTC

BACKUP_DIR="/root/.openclaw/backups/blog/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "=== 博客备份开始 ==="
echo "时间：$(date)"
echo "目标：$BACKUP_DIR"

# 备份博客文件
cp -r /root/.openclaw/workspace/01_Projects/01_博客运营/blog/ "$BACKUP_DIR/"

# 备份记忆文件
cp -r /root/.openclaw/workspace/02_Areas/记忆管理/memory/ "$BACKUP_DIR/memory/"

# 压缩备份
cd "$BACKUP_DIR/.."
tar -czf "$(date +%Y%m%d).tar.gz" "$(date +%Y%m%d)"

# 清理 30 天前的备份
find /root/.openclaw/backups/blog/ -name "*.tar.gz" -mtime +30 -delete

echo "=== 备份完成 ==="
echo "备份位置：$BACKUP_DIR"
ls -lh "$BACKUP_DIR/../$(date +%Y%m%d).tar.gz"
