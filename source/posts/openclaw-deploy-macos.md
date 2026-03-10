---
title: "OpenClaw 部署教程 - macOS 篇（2026 最新版）"
date: 2026-03-10T16:00:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "macOS", "部署", "教程", "AI 助手"]
image: "/static/security-cover.jpg"
description: "OpenClaw AI 助手框架 macOS 平台完整部署教程，包含 Homebrew 安装、一键脚本和本地模型配置实战"
---

# OpenClaw 部署教程 - macOS 篇（2026 最新版）

> 📅 **更新时间**：2026-03-10  
> ⏱️ **阅读时间**：8 分钟  
> 💡 **难度等级**：⭐⭐☆☆☆

OpenClaw 是一款强大的 AI 助手框架，支持 macOS 平台部署。本文整合官方文档和社区最佳实践，详细介绍 macOS 平台的安装配置流程。

---

## 📚 推荐学习路径

**官方文档（最权威）**：
- [OpenClaw 官方指南](https://open-claw.online/zh/docs/getting-started)
- [macOS 安装指南](https://docs.openclaw.ai/zh-CN/install)

**社区实战**：
- [Homebrew+ 一键脚本](https://blog.csdn.net/AngelCryToo/article/details/158776754)
- [本地模型配置实战](https://blog.csdn.net/weixin_43712047/article/details/158846297)

---

## 📋 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | macOS 11+ | macOS 14+ (Sonoma) |
| **内存** | 4GB | 8GB+ (M 系列芯片优化更好) |
| **磁盘** | 10GB | 20GB+ SSD |
| **Node.js** | v18+ | v20+ |
| **Python** | 3.8+ | 3.10+ |

---

## 🚀 快速安装（5 分钟）

### 方法一：Homebrew 安装（推荐）

```bash
# 1. 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Node.js
brew install node@20

# 3. 安装 OpenClaw
npm install -g openclaw

# 4. 验证安装
openclaw --version
```

### 方法二：一键脚本安装

```bash
# 使用官方一键安装脚本
curl -fsSL https://docs.openclaw.ai/zh-CN/install | bash

# 验证安装
openclaw --version
```

---

## 🔧 详细配置步骤

### 1. 初始化工作区

```bash
# 创建工作区
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace

# 初始化配置
openclaw init
```

### 2. 配置 API Keys

编辑配置文件：

```bash
nano ~/.openclaw/workspace/TOOLS.md
```

**必需配置**：

```markdown
## API Keys

### 阿里云百炼（推荐）
- Key: `sk-xxxxxxxxxxxxxxxx`
- 模型：qwen3.5-plus

### 火山引擎（备选）
- Key: `xxxxxxxxxxxxxxxx`
- 模型：doubao-seed-2.0-code

### 本地模型（Ollama）
- URL: `http://localhost:11434`
- 模型：`qwen2.5:7b`
```

### 3. 配置代理（中国大陆用户）

编辑 Clash 配置：

```bash
nano ~/.config/clash/config.yaml
```

或者使用环境变量（添加到 `~/.zshrc` 或 `~/.bash_profile`）：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 使配置生效
source ~/.zshrc
```

---

## 🚀 高级配置

### 1. 本地模型配置（Ollama）

安装 Ollama：

```bash
# 使用 Homebrew 安装
brew install ollama

# 或者下载安装
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull qwen2.5:7b

# 启动服务
ollama serve
```

配置 OpenClaw 使用本地模型：

```bash
nano ~/.openclaw/config.json
```

添加：

```json
{
  "model": {
    "provider": "ollama",
    "endpoint": "http://localhost:11434",
    "model": "qwen2.5:7b"
  }
}
```

### 2. systemd 替代方案（launchd）

macOS 使用 launchd 管理服务。创建服务文件：

```bash
nano ~/Library/LaunchAgents/com.openclaw.gateway.plist
```

内容：

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
    <key>WorkingDirectory</key>
    <string>/Users/你的用户名/.openclaw/workspace</string>
</dict>
</plist>
```

加载服务：

```bash
# 加载服务
launchctl load ~/Library/LaunchAgents/com.openclaw.gateway.plist

# 启动服务
launchctl start com.openclaw.gateway

# 查看状态
launchctl list | grep openclaw
```

### 3. 日志管理

```bash
# 查看日志
tail -f ~/.openclaw/workspace/memory/*.log

# 清理旧日志（保留最近 7 天）
find ~/.openclaw/workspace/memory -name "*.log" -mtime +7 -delete
```

---

## 🔍 常见问题解决

### 1. 端口被占用

```bash
# 检查端口占用
lsof -i :18789

# 杀死占用进程
kill -9 <PID>

# 或者修改 OpenClaw 端口
nano ~/.openclaw/config.json
# 修改 "port": 18790
```

### 2. 内存不足

```bash
# 查看内存使用
top -l 1 | grep PhysMem

# 关闭不需要的应用
# 或者增加 Swap（不推荐，会影响性能）
```

### 3. Node.js 版本不兼容

```bash
# 使用 nvm 管理 Node.js 版本
brew install nvm

# 安装 Node.js 20
nvm install 20
nvm use 20

# 重新安装 OpenClaw
npm uninstall -g openclaw
npm install -g openclaw
```

### 4. 权限问题

```bash
# 修复 npm 全局目录权限
sudo chown -R $(whoami) /usr/local/lib/node_modules

# 或者使用 nvm（推荐）
brew install nvm
```

### 5. 本地模型无法连接

```bash
# 检查 Ollama 服务
ps aux | grep ollama

# 重启 Ollama
brew services restart ollama

# 测试连接
curl http://localhost:11434/api/tags
```

### 6. 网络连接问题

```bash
# 测试网络连接
curl -I https://api.binance.com

# 配置代理后测试
curl -x http://127.0.0.1:7890 -I https://api.binance.com

# 如果还是失败，检查代理状态
ps aux | grep clash
```

---

## 📊 性能优化

### 1. Apple Silicon 优化

M 系列芯片优化建议：

```bash
# 使用 ARM 版本的 Node.js
nvm install 20 --arch=arm64
nvm use 20

# 使用原生模型（更快更省电）
ollama pull qwen2.5:7b-instruct-q4_0
```

### 2. 调整 Node.js 内存

```bash
# 编辑启动脚本或添加环境变量
export NODE_OPTIONS="--max-old-space-size=4096"
```

### 3. 使用 SSD 存储

确保工作区在 SSD 上（Mac 默认就是 SSD）：

```bash
# 检查工作区位置
df -h ~/.openclaw
```

### 4. 定期清理

```bash
# 清理 npm 缓存
npm cache clean --force

# 清理 Ollama 旧模型
ollama rm <model-name>

# 清理 OpenClaw 日志
find ~/.openclaw/workspace/memory -name "*.log" -mtime +7 -delete
```

---

## ✅ 验证安装

```bash
# 1. 检查版本
openclaw --version

# 2. 检查网关状态
openclaw gateway status

# 3. 发送测试消息
openclaw message send "Hello OpenClaw!"

# 4. 检查日志
tail -f ~/.openclaw/workspace/memory/*.log
```

**成功标志**：
- ✅ 版本号正常显示
- ✅ 网关状态显示"Running"
- ✅ 能收到 AI 回复
- ✅ 日志无 ERROR 级别错误

---

## 📚 更多资源

### 官方文档
- [OpenClaw 官方指南](https://open-claw.online/zh/docs/getting-started)
- [macOS 安装指南](https://docs.openclaw.ai/zh-CN/install)

### 社区教程
- [Homebrew+ 一键脚本](https://blog.csdn.net/AngelCryToo/article/details/158776754)
- [本地模型配置实战](https://blog.csdn.net/weixin_43712047/article/details/158846297)

### 其他平台
- [Linux 部署教程](/posts/openclaw-deploy-linux)
- [Windows 部署教程](/posts/openclaw-deploy-windows)
- [Android 部署教程](/posts/openclaw-deploy-android)

---

*最后更新：2026-03-10*  
*作者：OpenClaw 社区*  
*许可：MIT*

**觉得有用？欢迎分享给更多朋友！** 🚀
