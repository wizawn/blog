#!/bin/bash
# OpenClaw 自动备份脚本
# 执行：每日凌晨 2 点自动运行

BACKUP_DIR="/root/.openclaw/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "=== OpenClaw 自动备份 ==="
echo "时间：$(date)"
echo "目标：$BACKUP_DIR"

# 1. 备份配置文件
echo "备份配置文件..."
cp -r /root/.openclaw/workspace/*.md "$BACKUP_DIR/" 2>/dev/null
cp -r /root/.openclaw/workspace/tasks/*.md "$BACKUP_DIR/tasks/" 2>/dev/null
cp -r /root/.openclaw/workspace/tasks/*.yaml "$BACKUP_DIR/tasks/" 2>/dev/null

# 2. 备份 Nuclei 扫描结果
echo "备份扫描结果..."
cp /tmp/nuclei-*.json "$BACKUP_DIR/" 2>/dev/null
cp /tmp/openclaw_*.txt "$BACKUP_DIR/" 2>/dev/null

# 3. 备份 ARL 配置
echo "备份 ARL 配置..."
ssh root@107.172.8.123 "docker exec arl_mongodb mongodump --out /tmp/mongodb_backup --authenticationDatabase admin -u admin -p admin" 2>/dev/null
ssh root@107.172.8.123 "tar -czf /tmp/arl_config.tar.gz /root/arl-docker/" 2>/dev/null

# 4. 压缩备份
echo "压缩备份..."
cd "$BACKUP_DIR/.."
tar -czf "$(date +%Y%m%d).tar.gz" "$(date +%Y%m%d)"

# 5. 清理旧备份 (保留 30 天)
echo "清理旧备份..."
find /root/.openclaw/backups/ -name "*.tar.gz" -mtime +30 -delete

echo "备份完成！"
ls -lh "$BACKUP_DIR/../$(date +%Y%m%d).tar.gz"
