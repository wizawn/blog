from pymongo import MongoClient
client = MongoClient("mongodb://arl_mongodb:27017/", username="admin", password="admin")
db = client["arl"]
collection = db["ip"]
ips = []
with open("/tmp/arl_ips.txt") as f:
    for line in f:
        ip = line.strip()
        if ip and ":" in ip:
            ip_addr, port = ip.rsplit(":", 1)
            ips.append({"ip": ip_addr, "port": int(port), "group_id": 1})
print(f"准备导入 {len(ips)} 个 IP...")
batch_size = 1000
for i in range(0, len(ips), batch_size):
    batch = ips[i:i+batch_size]
    collection.insert_many(batch, ordered=False)
    print(f"  已导入 {min(i+batch_size, len(ips))}/{len(ips)}")
total = collection.count_documents({})
print(f"✅ 导入完成！ARL 总 IP 数：{total}")
client.close()
