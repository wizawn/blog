---
title: "OpenClaw 部署教程 - macOS 篇"
date: 2026-03-03T16:10:00+08:00
draft: false
categories: ["OpenClaw"]
tags: ["OpenClaw", "macOS", "部署", "教程"]
image: "/static/security-cover.jpg"
description: "OpenClaw AI 助手框架 macOS 平台完整部署教程，支持 Intel 和 Apple Silicon"
---

# OpenClaw 部署教程 - macOS 篇

> 支持 Intel 和 Apple Silicon (M1/M2/M3) 芯片

---

## 📋 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 12.0+ (Monterey+) |
| 芯片 | Intel / Apple Silicon |
| 内存 | 8GB+ (推荐 16GB) |
| 磁盘 | 10GB+ 可用空间 |
| Node.js | v20+ |
| Python | 3.10+ |

---

## 🔧 安装步骤

### 1. 安装 Homebrew (如未安装)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Apple Silicon 需要添加环境变量：

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 2. 安装 Node.js

```bash
brew install node@20
```

### 3. 安装 OpenClaw

```bash
npm install -g openclaw

# 验证安装
openclaw --version
```

### 4. 初始化工作区

```bash
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace
openclaw init
```

---

## ⚙️ 配置优化

### launchd 服务配置

创建 `~/Library/LaunchAgents/com.openclaw.gateway.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/openclaw</string>
        <string>gateway</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

加载服务：

```bash
launchctl load ~/Library/LaunchAgents/com.openclaw.gateway.plist
launchctl start com.openclaw.gateway
```

---

## 🔍 常见问题

### 1. Apple Silicon 兼容性问题

```bash
# 使用 Rosetta 2 运行 (仅 Intel 包)
arch -x86_64 openclaw gateway start
```

### 2. 权限问题

```bash
# 修复 npm 权限
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

### 3. 端口被占用

```bash
# 查看端口占用
lsof -i :18789

# 杀死进程
kill -9 <PID>
```

---

## ✅ 验证安装

```bash
# 检查网关状态
openclaw gateway status

# 发送测试消息
openclaw message send "Hello from macOS!"
```

---

*2026-03-03 | OpenClaw macOS 部署教程*

**上一篇**: [Windows 部署教程](/posts/openclaw-deploy-windows)  
**下一篇**: [Android 部署教程](/posts/openclaw-deploy-android)
