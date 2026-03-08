#!/bin/bash
# ARL IP 批量导入脚本

IP_FILE="/tmp/openclaw_ips_unique.txt"

if [ ! -f "$IP_FILE" ]; then
    echo "错误：IP 文件不存在 ($IP_FILE)"
    exit 1
fi

IP_COUNT=$(wc -l < "$IP_FILE")
echo "准备导入 $IP_COUNT 个 IP 到 ARL MongoDB..."

docker run --rm --network arl-docker_default -v /tmp:/tmp python:3.11-slim bash -c '
pip install pymongo==3.13.0 -q 2>/dev/null

python << PYEOF
from pymongo import MongoClient
import time

client = MongoClient("mongodb://arl_mongodb:27017/", 
                     username="admin", 
                     password="admin",
                     serverSelectionTimeoutMS=5000)

db = client["arl"]
ips_collection = db["ip"]

with open("/tmp/openclaw_ips_unique.txt", "r") as f:
    ips = [line.strip() for line in f if line.strip()]

print("准备导入 {} 个 IP...".format(len(ips)))

success = 0
for i, ip in enumerate(ips):
    try:
        ips_collection.insert_one({
            "ip": ip,
            "group_id": 1,
            "created_at": time.time(),
            "updated_at": time.time(),
            "source": "openclaw_exposure_watch"
        })
        success += 1
    except Exception as e:
        pass
    
    if (i + 1) % 20 == 0:
        print("已导入 {}/{}".format(i + 1, len(ips)))
        time.sleep(0.2)

print("")
print("✅ 导入完成！成功：{}/{}".format(success, len(ips)))

count = ips_collection.estimated_document_count()
print("MongoDB IP 总数：{}".format(count))
PYEOF
'

echo ""
echo "=== 验证导入结果 ==="
docker exec arl_mongodb mongo --quiet -u admin -p admin --eval '
print("IP 总数：" + db.ip.count());
db.ip.find({source: "openclaw_exposure_watch"}).limit(5).forEach(function(ip) {
  print("  - " + ip.ip);
});
'
