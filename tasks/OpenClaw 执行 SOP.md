# OpenClaw 任务执行 SOP (标准作业程序)

**版本**: v1.0  
**生效日期**: 2026-03-04  
**执行人**: ClawSec

---

## 📋 任务前校验清单

### 1. 环境检查
- [ ] 确认使用远程服务器 (107.172.8.123)
- [ ] ARL 组件运行正常 (web/scheduler/worker/mongodb/rabbitmq)
- [ ] RabbitMQ 队列无积压
- [ ] 服务器资源充足 (CPU < 80%, 内存 < 80%)

### 2. 配置校验
- [ ] ARL Web 可访问 (https://107.172.8.123:5003)
- [ ] MongoDB 连接正常
- [ ] 推送通道正常 (钉钉/Telegram)

### 3. 目标准备
- [ ] IP 列表已准备 (/tmp/full_ips.txt)
- [ ] Nuclei 模板已更新
- [ ] 扫描速率已设定 (10 req/s 轻量 / 5 req/s 深度)

---

## 🚀 任务执行流程

### 阶段 1: 资产录入
```bash
# 1. 提取 IP (后台运行)
nohup python3 /tmp/full_extract.py > /tmp/ip_extract.log 2>&1 &

# 2. 导入 ARL
ssh root@107.172.8.123 "docker run --rm --network arl-docker_default -v /tmp:/tmp python:3.11-slim python3 /tmp/arl_import.py"
```

### 阶段 2: 扫描执行
```bash
# 轻量巡检 (高危 POC)
nuclei -l targets.txt -t high-severity/ -rate-limit 10 -concurrency 25

# 深度挖掘 (全量 POC)
nuclei -l targets.txt -t all/ -rate-limit 5 -concurrency 15
```

### 阶段 3: 进度追踪
- 每 2 小时检查一次任务状态
- 监控 RabbitMQ 队列长度
- 检查扫描日志有无错误

### 阶段 4: 结果归档
```bash
# 备份扫描结果
cp /tmp/nuclei-scan-*.json /root/.openclaw/workspace/reports/
git add reports/ && git commit -m "Scan results $(date +%Y%m%d)"
```

### 阶段 5: 漏洞验证
- 人工过滤误报
- 验证有效漏洞
- 整理 SRC 提交材料

### 阶段 6: 优化迭代
- 更新误报过滤规则
- 优化扫描模板
- 更新 POC 库

---

## ⚠️ 异常处理流程

### ARL 任务中断
1. 检查 RabbitMQ 状态：`docker logs arl_rabbitmq`
2. 重启 Worker: `docker restart arl_worker`
3. 检查队列：`docker exec arl_rabbitmq rabbitmqctl list_queues`

### 扫描速率失控
1. 立即终止：`pkill nuclei`
2. 检查配置：确认 rate-limit 参数
3. 降低并发：concurrency 减半重试

### 服务器资源告急
1. 暂停任务：`pkill nuclei`
2. 清理资源：`docker prune`
3. 分析原因：`htop` `df -h`

---

## 📊 验收标准

| 指标 | 目标值 | 检查频率 |
|------|--------|----------|
| 任务完成率 | ≥95% | 每日 |
| 误报率 | ≤30% | 每周 |
| 告警送达率 | 100% | 每日 |
| 数据备份 | 100% | 每次任务后 |
| 违规操作 | 0 | 持续监控 |

---

## 🔐 安全红线

1. **禁止本地执行** - 所有任务必须在远程服务器
2. **禁止未授权扫描** - 仅限合规 SRC 目标
3. **禁止高速率扫描** - 最大 10 req/s
4. **禁止数据外泄** - 扫描结果加密存储

---

*最后更新：2026-03-04*
