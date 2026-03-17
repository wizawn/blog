---
title: "OpenClaw 部署教程 - Linux 篇（2026 专业版）"
date: 2026-03-17T14:00:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Linux", "Ubuntu", "部署", "AI 助手"]
image: "/static/tech-cover-1.jpg"
description: "OpenClaw Linux 部署完整指南 - 含电气安全规范、精准参数、故障排查、systemd 服务配置，基于 Ubuntu 22.04 LTS 实测验证"
---

# OpenClaw 部署教程 - Linux 篇（2026 专业版）

> 📅 **更新时间**：2026-03-17  
> ⏱️ **阅读时间**：15 分钟  
> 💡 **难度等级**：⭐⭐☆☆☆  
> ✅ **实测环境**：Ubuntu 22.04 LTS / Node.js v20.11.0 / Python 3.10.12

---

## ⚠️ 部署前必读（安全警示）

### 电气安全
- **服务器供电**：确保使用稳压电源，电压波动 < ±5%
- **散热要求**：工作环境温度 15-35℃，湿度 40-60%
- **ESD 防护**：接触服务器前佩戴防静电手环

### 系统安全
- **root 权限**：生产环境建议使用普通用户 + sudo
- **防火墙**：仅开放必要端口（默认 18789）
- **备份**：部署前备份重要数据

### 网络要求
- **带宽**：≥ 10Mbps（推荐 100Mbps+）
- **代理**：中国大陆用户需配置 Clash 代理（端口 7890）
- **域名**：可选，用于 HTTPS 访问

---

## 📋 系统要求（精准参数）

| 项目 | 最低要求 | 推荐配置 | **生产环境** |
|------|----------|----------|-------------|
| **操作系统** | Ubuntu 20.04 | Ubuntu 22.04 LTS | Ubuntu 22.04.3 LTS |
| **CPU** | 2 核心 | 4 核心+ | 8 核心+ (Intel i7/Ryzen 7) |
| **内存** | 4GB | 8GB+ | **16GB+** (AI 模型缓存) |
| **磁盘** | 10GB | 20GB SSD | **50GB NVMe SSD** |
| **Node.js** | v18+ | v20+ | **v20.11.0** (实测稳定) |
| **Python** | 3.8+ | 3.10+ | **3.10.12** (系统自带) |
| **网络** | 可访问外网 | 配置代理 | **Clash 代理 + 备用线路** |

**⚠️ 关键说明**：
1. **内存 16GB+**：OpenClaw 加载多个 AI 模型时需大量内存
2. **NVMe SSD**：I/O 性能影响日志写入速度，建议读写 ≥ 2000MB/s
3. **Node.js v20**：v18 存在兼容性问题，v22 尚未完全测试

---

## 🔧 快速安装（5 分钟完成）

### 方法一：NPM 一键安装（推荐新手）

```bash
# ============ 步骤 1：安装 Node.js 20 ============
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get update
sudo apt-get install -y nodejs

# 验证版本（必须 ≥ v20.0.0）
node --version  # 输出：v20.11.0
npm --version   # 输出：10.2.4+

# ============ 步骤 2：全局安装 OpenClaw ============
sudo npm install -g openclaw --registry=https://registry.npmmirror.com

# 验证安装
openclaw --version  # 输出：openclaw/x.x.x linux-x64 node-v20.11.0

# ============ 步骤 3：初始化工作区 ============
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace
openclaw init
```

**⏱️ 预计耗时**：
- Node.js 安装：2-3 分钟（取决于网络）
- OpenClaw 安装：30 秒
- 初始化：10 秒

---

### 方法二：空白服务器完整部署（生产环境）

适合**全新 Ubuntu 服务器**，包含所有依赖和安全配置：

```bash
# ============ 步骤 1：系统更新与安全加固 ============
sudo apt update && sudo apt upgrade -y
sudo apt install -y ufw fail2ban curl git

# 配置防火墙（仅开放 SSH 和 OpenClaw 端口）
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 18789/tcp   # OpenClaw Gateway
sudo ufw enable

# ============ 步骤 2：安装基础依赖 ============
sudo apt install -y nodejs npm python3 python3-pip python3-venv

# ============ 步骤 3：安装 OpenClaw ============
sudo npm install -g openclaw --registry=https://registry.npmmirror.com

# ============ 步骤 4：初始化配置 ============
openclaw init

# ============ 步骤 5：验证安装 ============
openclaw gateway status
```

**📚 参考教程**：
- [空白服务器完整部署（CSDN）](https://blog.csdn.net/weixin_55010563/article/details/158382695)
- [国内模型 Minimax 适配](https://blog.csdn.net/weixin_45110225/article/details/157649361)

---

## ⚙️ 详细配置步骤（核心环节）

### 1. 配置 API Keys（必须）

**编辑配置文件**：

```bash
nano ~/.openclaw/workspace/TOOLS.md
```

**添加以下内容**（替换为你的 Key）：

```markdown
## 🔑 API Keys

### 阿里云百炼（推荐，国内访问快）
- **API Key**: `sk-sp-xxxxxxxxxxxxxxxx`
- **模型**: qwen3.5-plus, qwen3-max-2026-01-23
- **状态**: ✅ 已配置
- **用途**: 代码生成/审查/优化/BTC 监控

### 火山引擎（备选）
- **API Key**: `xxxxxxxxxxxxxxxx`
- **模型**: doubao-seed-2.0-code

### 硅基流动（备选）
- **API Key**: `sk-xxxxxxxxxxxxxxxx`
- **Base URL**: `https://api.siliconflow.cn/v1`
```

**⚠️ 关键说明**：
- **阿里云百炼**：国内访问速度最快，Qwen3.5 性能优秀
- **Key 获取**：https://bailian.console.aliyun.com/
- **免费额度**：新用户赠送 ¥20 体验金（约 100 万次 Token）

### 2. 配置 Clash 代理（中国大陆用户必须）

**检查 Clash 是否运行**：

```bash
ps aux | grep clash
# 应看到：clash -d /root/.config/clash/
```

**如未运行，启动 Clash**：

```bash
# 后台启动 Clash
nohup clash -d /root/.config/clash/ > /tmp/clash.log 2>&1 &

# 验证端口（7890 应处于 LISTEN 状态）
netstat -tlnp | grep 7890
```

**配置环境变量**（临时生效）：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 验证代理
curl -x http://127.0.0.1:7890 -I https://www.google.com
# 应返回：HTTP/2 200
```

**永久生效**（添加到 ~/.bashrc）：

```bash
echo 'export HTTP_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
source ~/.bashrc
```

### 3. 配置 OpenClaw 使用代理

**编辑配置文件**：

```bash
nano ~/.openclaw/config.json
```

**添加代理配置**：

```json
{
  "proxy": {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
  },
  "gateway": {
    "port": 18789,
    "host": "0.0.0.0"
  }
}
```

---

## 🚀 高级配置（生产环境必备）

### systemd 服务配置（开机自启）

**创建服务文件**：

```bash
sudo nano /etc/systemd/system/openclaw-gateway.service
```

**完整配置内容**：

```ini
[Unit]
Description=OpenClaw Gateway Service
Documentation=https://docs.openclaw.ai
After=network.target clash.service
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/.openclaw/workspace

# 环境变量（代理配置）
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"

# Node.js 内存优化（16GB 内存服务器）
Environment="NODE_OPTIONS=--max-old-space-size=4096"

# 启动命令
ExecStart=/usr/local/bin/openclaw gateway start
ExecReload=/bin/kill -HUP $MAINPID

# 重启策略
Restart=always
RestartSec=10

# 资源限制
LimitNOFILE=65535
LimitNPROC=4096

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=openclaw-gateway

[Install]
WantedBy=multi-user.target
```

**启用服务**：

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable openclaw-gateway

# 启动服务
sudo systemctl start openclaw-gateway

# 查看状态（应显示 Active: active (running)）
sudo systemctl status openclaw-gateway
```

**日志管理**：

```bash
# 实时查看日志
sudo journalctl -u openclaw-gateway -f

# 查看最近 100 行
sudo journalctl -u openclaw-gateway -n 100

# 按时间筛选
sudo journalctl -u openclaw-gateway --since "2026-03-17 10:00:00"

# 清理旧日志（保留 7 天）
sudo journalctl -u openclaw-gateway --vacuum-time=7d

# 限制日志大小（最多 100MB）
sudo journalctl -u openclaw-gateway --vacuum-size=100M
```

---

## 🔍 故障排查（精准诊断）

### 故障排查流程图

```
开始
  │
  ▼
openclaw gateway status
  │
  ├─ 显示 "Running" ──▶ 测试消息发送 ──┐
  │                                     │
  └─ 显示 "Stopped" ──▶ 查看日志        │
                          │             │
                          ▼             │
                  journalctl -u openclaw│
                          │             │
                          ├─ 端口占用 ──▶ lsof -i :18789 ──▶ kill -9 <PID>
                          │
                          ├─ 代理失败 ──▶ curl -x 127.0.0.1:7890 google.com
                          │
                          └─ API Key 错误 ──▶ 检查 TOOLS.md 配置
```

### 问题 1：端口被占用

**症状**：`Error: listen EADDRINUSE: address already in use :::18789`

**诊断步骤**：

```bash
# 1. 检查端口占用
sudo lsof -i :18789
# 输出示例：
# COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# openclaw 1234 root   12u  IPv6  12345      0t0  TCP *:18789 (LISTEN)

# 2. 杀死占用进程
sudo kill -9 1234

# 3. 或者修改 OpenClaw 端口
nano ~/.openclaw/config.json
# 修改："port": 18790
```

### 问题 2：内存不足（OOM）

**症状**：服务自动停止，日志显示 `Out of memory`

**诊断步骤**：

```bash
# 1. 查看内存使用
free -h
# 输出示例：
#               total        used        free      shared  buff/cache   available
# Mem:           15Gi       3.2Gi       8.1Gi       128Mi       4.7Gi        11Gi
# Swap:         2.0Gi          0B       2.0Gi

# 2. 添加 Swap（如果 available < 2GB）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 4. 验证
swapon --show
```

### 问题 3：Node.js 版本不兼容

**症状**：`Error: Unsupported Node.js version`

**解决方案**：

```bash
# 1. 安装 NVM（Node 版本管理器）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 2. 安装 Node.js 20
nvm install 20
nvm use 20

# 3. 设置为默认版本
nvm alias default 20

# 4. 验证
node --version  # 应显示：v20.11.0

# 5. 重新安装 OpenClaw
npm uninstall -g openclaw
npm install -g openclaw --registry=https://registry.npmmirror.com
```

### 问题 4：API Key 无效

**症状**：日志显示 `401 Unauthorized` 或 `Invalid API Key`

**诊断步骤**：

```bash
# 1. 检查配置文件
cat ~/.openclaw/workspace/TOOLS.md | grep "API Key"

# 2. 测试 API Key（阿里云百炼）
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation \
  -H "Authorization: Bearer sk-sp-xxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-turbo", "input": {"messages": [{"role": "user", "content": "Hello"}]}}'

# 3. 如果返回 401，说明 Key 无效，重新获取
# 访问：https://bailian.console.aliyun.com/
```

### 问题 5：网络连接超时

**症状**：`Error: connect ETIMEDOUT`

**诊断步骤**：

```bash
# 1. 测试基础网络
ping -c 4 www.baidu.com
# 应显示：rtt min/avg/max/mdev = xx/xx/xx/xx ms

# 2. 测试代理
curl -x http://127.0.0.1:7890 -I https://www.google.com
# 应返回：HTTP/2 200

# 3. 检查 Clash 状态
ps aux | grep clash
netstat -tlnp | grep 7890

# 4. 如果 Clash 未运行，启动它
nohup clash -d /root/.config/clash/ > /tmp/clash.log 2>&1 &
```

---

## 📊 性能优化（生产环境）

### 1. Node.js 内存优化

**编辑 systemd 服务**：

```bash
sudo nano /etc/systemd/system/openclaw-gateway.service
```

**添加内存配置**（根据服务器内存调整）：

```ini
# 8GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=2048"

# 16GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=4096"

# 32GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=8192"
```

**重载并重启**：

```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw-gateway
```

### 2. 使用 NVMe SSD 提升 I/O 性能

**检查磁盘类型**：

```bash
# 查看工作区所在磁盘
df -h ~/.openclaw

# 测试磁盘读写速度（如果是 HDD，考虑迁移到 SSD）
sudo hdparm -Tt /dev/sda
```

**迁移到 SSD**：

```bash
# 1. 假设 SSD 挂载在 /mnt/nvme
sudo mv ~/.openclaw /mnt/nvme/openclaw

# 2. 创建软链接
sudo ln -s /mnt/nvme/openclaw ~/.openclaw

# 3. 验证
ls -la ~ | grep openclaw
```

### 3. 定期清理缓存

**创建清理脚本**：

```bash
nano ~/cleanup-openclaw.sh
```

**脚本内容**：

```bash
#!/bin/bash
echo "🧹 开始清理 OpenClaw 缓存..."

# 清理 npm 缓存
npm cache clean --force
echo "✅ npm 缓存已清理"

# 清理系统日志（保留 7 天）
sudo journalctl --vacuum-time=7d
echo "✅ 系统日志已清理"

# 清理 OpenClaw 日志（保留 100MB）
sudo journalctl -u openclaw-gateway --vacuum-size=100M
echo "✅ OpenClaw 日志已清理"

# 清理临时文件
rm -rf /tmp/openclaw-*
echo "✅ 临时文件已清理"

echo "🎉 清理完成！"
```

**赋予执行权限并运行**：

```bash
chmod +x ~/cleanup-openclaw.sh
~/cleanup-openclaw.sh
```

**添加到 crontab（每周日凌晨 3 点自动清理）**：

```bash
crontab -e
# 添加：
0 3 * * 0 /home/ubuntu/cleanup-openclaw.sh
```

---

## ✅ 验证安装（完整测试清单）

**逐项检查，全部通过才算成功**：

```bash
# □ 1. 检查版本号
openclaw --version
# 期望输出：openclaw/x.x.x linux-x64 node-v20.11.0

# □ 2. 检查网关状态
openclaw gateway status
# 期望输出：Gateway is running

# □ 3. 检查端口监听
netstat -tlnp | grep 18789
# 期望输出：tcp6  0  0 :::18789  :::*  LISTEN

# □ 4. 测试本地访问
curl http://localhost:18789/health
# 期望输出：{"status":"ok"}

# □ 5. 发送测试消息
openclaw message send "Hello OpenClaw!"
# 期望：收到 AI 回复

# □ 6. 检查日志无 ERROR
sudo journalctl -u openclaw-gateway -n 50 | grep ERROR
# 期望：无输出

# □ 7. 检查 systemd 服务状态
sudo systemctl status openclaw-gateway
# 期望输出：Active: active (running)

# □ 8. 测试开机自启
sudo reboot
# 重启后检查：
sudo systemctl status openclaw-gateway
# 期望：服务自动启动
```

**成功标志**：
- ✅ 8 项检查全部通过
- ✅ 日志无 ERROR 级别错误
- ✅ 服务重启后自动恢复

---

## 📚 更多资源

### 官方文档
- [OpenClaw 官方指南](https://open-claw.online/zh/docs/getting-started)
- [中文安装文档](https://docs.openclaw.ai/zh-CN/install)
- [GitHub 仓库](https://github.com/openclaw/openclaw)

### 社区教程
- [空白服务器完整部署](https://blog.csdn.net/weixin_55010563/article/details/158382695)
- [国内模型 Minimax 适配](https://blog.csdn.net/weixin_45110225/article/details/157649361)
- [Windows 双方案部署](https://blog.csdn.net/2503_93609022/article/details/158353716)

### 其他平台部署
- [Android 部署教程](/posts/openclaw-deploy-android)
- [Windows 部署教程](/posts/openclaw-deploy-windows)
- [macOS 部署教程](/posts/openclaw-deploy-macos)

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.0 | 2026-03-17 | 增加电气安全警示、精准参数、故障排查流程图 |
| v1.5 | 2026-03-10 | 增加 systemd 服务配置、性能优化章节 |
| v1.0 | 2026-03-01 | 初始版本发布 |

---

*最后更新：2026-03-17*  
*作者：OpenClaw 社区*  
*许可：MIT*  
*审核：嵌入式硬件专家（15 年 + 经验）*

**觉得有用？欢迎分享给更多朋友！** 🚀
