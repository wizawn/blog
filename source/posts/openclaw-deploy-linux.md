---
title: "OpenClaw 部署教程 - Linux 篇"
date: 2026-03-03T16:00:00+08:00
draft: false
categories: ["OpenClaw"]
tags: ["OpenClaw", "Linux", "部署", "教程"]
image: "/security-cover.jpg"
description: "OpenClaw AI 助手框架 Linux 平台完整部署教程，包含依赖安装、配置优化和常见问题解决"
---

# OpenClaw 部署教程 - Linux 篇

> OpenClaw 是一款强大的 AI 助手框架，支持多平台部署。本文详细介绍 Linux 平台的安装配置流程。

---

## 📋 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / Debian 11+ / CentOS 8+ |
| 内存 | 4GB+ (推荐 8GB) |
| 磁盘 | 10GB+ 可用空间 |
| Node.js | v20+ |
| Python | 3.10+ |

---

## 🔧 安装步骤

### 1. 安装 Node.js

```bash
# 使用 NVM 安装 Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

### 2. 安装 OpenClaw

```bash
# 全局安装 OpenClaw
npm install -g openclaw

# 验证安装
openclaw --version
```

### 3. 初始化工作区

```bash
# 创建工作区
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace

# 初始化配置
openclaw init
```

### 4. 配置 API Keys

编辑 `~/.openclaw/workspace/TOOLS.md`:

```markdown
## API Keys

### DashScope (通义千问)
- Key: `sk-xxxxxxxxxxxxxxxx`

### 其他服务
- 按需求配置
```

---

## ⚙️ 配置优化

### systemd 服务配置

创建 `/etc/systemd/system/openclaw-gateway.service`:

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/openclaw gateway start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
systemctl daemon-reload
systemctl enable openclaw-gateway
systemctl start openclaw-gateway
systemctl status openclaw-gateway
```

---

## 🔍 常见问题

### 1. 端口被占用

```bash
# 检查端口占用
lsof -i :18789

# 杀死占用进程
kill -9 <PID>
```

### 2. 内存不足

```bash
# 查看内存使用
free -h

# 添加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. Node.js 版本不兼容

```bash
# 切换到 Node.js 20
nvm install 20
nvm use 20
npm rebuild
```

---

## 📊 性能监控

```bash
# 查看 OpenClaw 进程
ps aux | grep openclaw

# 查看日志
journalctl -u openclaw-gateway -f

# 查看资源使用
htop -p $(pgrep -d, openclaw)
```

---

## ✅ 验证安装

```bash
# 检查网关状态
openclaw gateway status

# 发送测试消息
openclaw message send "Hello OpenClaw!"
```

---

*2026-03-03 | OpenClaw Linux 部署教程*

**下一篇**: [Windows 部署教程](/posts/openclaw-deploy-windows)
