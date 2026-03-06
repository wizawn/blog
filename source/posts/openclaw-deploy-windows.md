---
title: "OpenClaw 部署教程 - Windows 篇"
date: 2026-03-03T16:05:00+08:00
draft: false
categories: ["OpenClaw"]
tags: ["OpenClaw", "Windows", "部署", "教程"]
image: "/static/tech-cover-1.jpg"
description: "OpenClaw AI 助手框架 Windows 平台完整部署教程，包含 WSL2 配置和原生安装方案"
---

# OpenClaw 部署教程 - Windows 篇

> Windows 用户可以选择 WSL2 或原生安装，推荐 WSL2 方案以获得更好的兼容性。

---

## 📋 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 21H2+ / Windows 11 |
| 内存 | 8GB+ (推荐 16GB) |
| 磁盘 | 20GB+ 可用空间 |
| Node.js | v20+ |
| Python | 3.10+ |

---

## 🔧 方案一：WSL2 安装 (推荐)

### 1. 启用 WSL2

```powershell
# 以管理员身份运行 PowerShell
wsl --install
wsl --set-default-version 2
```

重启电脑后，安装 Ubuntu：

```powershell
wsl --install -d Ubuntu-22.04
```

### 2. 在 WSL2 中安装

参考 [Linux 部署教程](/posts/openclaw-deploy-linux)

---

## 🔧 方案二：原生安装

### 1. 安装 Node.js

从 https://nodejs.org 下载 Windows 安装包，或使用 winget：

```powershell
winget install OpenJS.NodeJS.LTS
```

### 2. 安装 OpenClaw

```powershell
# 以管理员身份运行 PowerShell
npm install -g openclaw

# 验证安装
openclaw --version
```

### 3. 配置环境变量

添加用户环境变量：
- `OPENCLAW_WORKSPACE` = `C:\Users\<用户名>\openclaw-workspace`

### 4. 初始化

```powershell
cd C:\Users\<用户名>\openclaw-workspace
openclaw init
```

---

## ⚙️ 配置优化

### Windows Terminal 配置

推荐安装 Windows Terminal，配置 Profile：

```json
{
    "profiles": {
        "defaults": {
            "fontFace": "Cascadia Code",
            "fontSize": 12
        }
    }
}
```

### 防火墙配置

```powershell
# 允许 OpenClaw 通过防火墙
New-NetFirewallRule -DisplayName "OpenClaw Gateway" -Direction Inbound -LocalPort 18789 -Protocol TCP -Action Allow
```

---

## 🔍 常见问题

### 1. 权限问题

```powershell
# 以管理员身份运行 PowerShell
Start-Process powershell -Verb RunAs
```

### 2. npm 全局安装失败

```powershell
# 修改 npm 全局目录
npm config set prefix "C:\npm"

# 添加环境变量 PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\npm", "User")
```

### 3. WSL2 网络问题

```powershell
# 重置 WSL
wsl --shutdown
wsl
```

---

## ✅ 验证安装

```powershell
# 检查网关状态
openclaw gateway status

# 发送测试消息
openclaw message send "Hello from Windows!"
```

---

*2026-03-03 | OpenClaw Windows 部署教程*

**上一篇**: [Linux 部署教程](/posts/openclaw-deploy-linux)  
**下一篇**: [macOS 部署教程](/posts/openclaw-deploy-macos)
