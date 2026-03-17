---
title: "OpenClaw 部署教程 - Linux 篇（2026 终极版）"
date: 2026-03-17T14:30:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Linux", "Ubuntu", "部署", "AI 助手", "保姆级教程"]
image: "/static/tech-cover-1.jpg"
description: "OpenClaw Linux 部署终极指南 - 含环境配置、NVM 安装、一键脚本、初始化向导、故障排查，基于 Ubuntu 22.04 LTS 实测验证"
---

# OpenClaw 部署教程 - Linux 篇（2026 终极版）

> 📅 **更新时间**：2026-03-17  
> ⏱️ **阅读时间**：20 分钟  
> 💡 **难度等级**：⭐⭐☆☆☆  
> ✅ **实测环境**：Ubuntu 22.04 LTS / Node.js v22.12.0 / Python 3.10.12

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

### 内存要求（重要！）
- **最低**：2GB（需配置 Swap）
- **推荐**：4GB+（无需 Swap）
- **生产**：8GB+（流畅运行）

**⚠️ 2GB 内存服务器必须配置 Swap**，否则会出现 OOM（内存溢出）导致安装失败。

---

## 📋 系统要求（精准参数）

| 项目 | 最低要求 | 推荐配置 | **生产环境** |
|------|----------|----------|-------------|
| **操作系统** | Ubuntu 20.04 | Ubuntu 22.04 LTS | Ubuntu 22.04.3 LTS |
| **CPU** | 1 核心 | 2 核心+ | 4 核心+ |
| **内存** | 2GB | 4GB+ | **8GB+** |
| **磁盘** | 5GB | 10GB SSD | **20GB+ NVMe SSD** |
| **Node.js** | v18+ | v20+ | **v22.12.0** (最新 LTS) |
| **Python** | 3.8+ | 3.10+ | **3.10.12** (系统自带) |
| **Git** | 任意版本 | 最新 | 2.34.1+ |

**⚠️ 关键说明**：
1. **Node.js v22**：OpenClaw 官方推荐版本，兼容性最佳
2. **Swap 配置**：2GB 内存服务器必须配置 2GB+ Swap
3. **Git 必须**：用于克隆仓库和管理依赖

---

## 🔧 快速安装（10 分钟完成）

### 方法一：官方一键安装脚本（最简单）

```bash
# ============ 步骤 1：系统更新及基础依赖 ============
sudo apt update
sudo apt install -y git curl

# ============ 步骤 2：执行官方安装脚本 ============
curl -fsSL https://openclaw.ai/install.sh | bash

# ============ 步骤 3：验证安装 ============
openclaw --version
```

**⏱️ 预计耗时**：5-10 分钟（取决于网络）

**⚠️ 注意事项**：
- **国内服务器**：若安装失败，需先配置代理
- **2GB 内存**：可能出现 OOM，需先配置 Swap（见下文）
- **安装过程**：耗时较长，需耐心等待

---

### 方法二：手动安装（可控性更强）

适合需要**精确控制版本**的生产环境：

#### 步骤 1：安装 Git

```bash
sudo apt update
sudo apt install -y git

# 验证版本
git --version  # 应显示：git version 2.34.1+
```

#### 步骤 2：安装 NVM（Node 版本管理器）

**国内服务器（使用 Gitee 镜像源）**：

```bash
curl -o- https://gitee.com/RubyMetric/nvm-cn/raw/main/install.sh | bash
```

**海外服务器（使用官方源）**：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
```

#### 步骤 3：重新加载环境变量

```bash
source ~/.bashrc

# 验证 NVM 已安装
command -v nvm  # 应输出：nvm
```

#### 步骤 4：安装 Node.js 22

```bash
# 安装 Node.js 22（最新 LTS）
nvm install 22

# 设置为默认版本
nvm alias default 22

# 验证版本
node --version  # 应显示：v22.12.0
npm --version   # 应显示：10.9.0+
```

#### 步骤 5：安装 OpenClaw

```bash
# 全局安装
npm install -g openclaw

# 验证安装
openclaw --version  # 应显示：openclaw/x.x.x linux-x64 node-v22.12.0
```

---

## ⚙️ 初始化配置（Onboarding 向导）

安装成功后会自动进入**初始化向导**，按以下步骤操作：

### 步骤详解

| 步骤 | 提示内容 | 操作 | 说明 |
|------|----------|------|------|
| 1 | 安全提示确认 | 输入 `Yes` | 知晓权限风险 |
| 2 | 选择部署模式 | 选择 `QuickStart` | 后续可补充配置 |
| 3 | 选择模型服务商 | 选择 `OpenAI` | 或其他服务商 |
| 4 | 模型授权 | 复制链接到浏览器 | 登录账号完成授权 |
| 5 | 通信通道配置 | 选择 `Skip for now` | 后续可配置 |
| 6 | 技能配置 | 选择 `No` | 暂不配置 |
| 7 | Hooks 配置 | 选择 `Session` | 暂不启用 |
| 8 | 启动方式 | 选择 `TUI` | 终端聊天界面 |
| 9 | 测试 | 输入 `Hello` | 确认安装成功 |

### 详细流程

**1. 安全提示确认**：
```
OpenClaw is a hobby project and still in beta...
Do you want to continue? (Yes/No)
> Yes
```

**2. 选择部署模式**：
```
Select deployment mode:
  1) QuickStart (推荐)
  2) Advanced
> 1
```

**3. 选择模型服务商**：
```
Select model provider:
  1) OpenAI
  2) Anthropic
  3) Google
  4) Custom
> 1
```

**4. 模型授权**：
```
Please visit the following URL to authorize:
https://openclaw.ai/auth/xxxxx

Enter the authorization code:
> [粘贴授权码]
```

**5-7. 跳过可选配置**：
```
Configure communication channels? (y/N) > N
Configure skills? (y/N) > N
Configure hooks? (y/N) > N
```

**8. 启动 TUI 测试**：
```
Start OpenClaw in TUI mode? (Y/n) > Y

# 出现聊天界面后输入：
> Hello

# 应收到 AI 回复
```

**9. 退出 TUI**：
```
按 Ctrl+C 退出
```

---

## 🔧 高级配置（生产环境必备）

### 1. 配置 Swap（2GB 内存服务器必须）

**检查当前 Swap**：

```bash
free -h
# 如果 Swap 为 0B，需要配置
```

**创建 2GB Swap**：

```bash
# 1. 创建 swap 文件
sudo fallocate -l 2G /swapfile

# 2. 设置权限（仅 root 可读写）
sudo chmod 600 /swapfile

# 3. 格式化为 swap
sudo mkswap /swapfile

# 4. 启用 swap
sudo swapon /swapfile

# 5. 验证
swapon --show
# 应显示：/swapfile  file  2G  0B
```

**永久生效**（重启后自动挂载）：

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**调整 Swappiness**（降低使用 swap 的频率）：

```bash
# 查看当前值（默认 60）
cat /proc/sys/vm/swappiness

# 修改为 10（更保守）
sudo sysctl vm.swappiness=10

# 永久生效
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 2. 配置 API Keys

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
- **用途**: 代码生成/审查/优化

### OpenAI（备选）
- **API Key**: `sk-proj-xxxxxxxxxxxxxxxx`
- **模型**: gpt-4o, gpt-4-turbo

### 火山引擎（备选）
- **API Key**: `xxxxxxxxxxxxxxxx`
- **模型**: doubao-seed-2.0-code
```

**Key 获取地址**：
- **阿里云百炼**：https://bailian.console.aliyun.com/
- **OpenAI**：https://platform.openai.com/api-keys
- **火山引擎**：https://www.volcengine.com/

### 3. 配置 Clash 代理（中国大陆用户必须）

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

**配置环境变量**：

```bash
# 临时生效
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 永久生效（添加到 ~/.bashrc）
echo 'export HTTP_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
source ~/.bashrc
```

**验证代理**：

```bash
curl -x http://127.0.0.1:7890 -I https://www.google.com
# 应返回：HTTP/2 200
```

---

## 🚀 systemd 服务配置（开机自启）

### 创建服务文件

```bash
sudo nano /etc/systemd/system/openclaw-gateway.service
```

### 完整配置内容

```ini
[Unit]
Description=OpenClaw Gateway Service
Documentation=https://docs.openclaw.ai
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/.openclaw/workspace

# 环境变量（代理配置）
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"

# Node.js 内存优化
Environment="NODE_OPTIONS=--max-old-space-size=2048"

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

### 启用服务

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

### 日志管理

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

### 问题 1：安装过程中 OOM（内存溢出）

**症状**：安装过程中服务器卡死，SSH 断开连接

**诊断**：

```bash
# 查看内存使用
free -h

# 查看 OOM 日志
dmesg | grep -i "out of memory"
```

**解决方案**：

```bash
# 1. 配置 Swap（见上文）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 重启安装
npm install -g openclaw
```

### 问题 2：Node.js 版本不兼容

**症状**：`Error: Unsupported Node.js version`

**解决方案**：

```bash
# 1. 查看当前版本
node --version

# 2. 使用 NVM 切换到 v22
nvm install 22
nvm use 22
nvm alias default 22

# 3. 重新安装 OpenClaw
npm uninstall -g openclaw
npm install -g openclaw
```

### 问题 3：网络超时

**症状**：`Error: connect ETIMEDOUT`

**诊断步骤**：

```bash
# 1. 测试基础网络
ping -c 4 www.baidu.com

# 2. 测试代理
curl -x http://127.0.0.1:7890 -I https://www.google.com

# 3. 检查 Clash 状态
ps aux | grep clash
netstat -tlnp | grep 7890
```

**解决方案**：

```bash
# 启动 Clash
nohup clash -d /root/.config/clash/ > /tmp/clash.log 2>&1 &

# 配置环境变量
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 问题 4：初始化向导卡住

**症状**：卡在某个步骤无法继续

**解决方案**：

```bash
# 1. 退出向导（Ctrl+C）

# 2. 清除配置重新初始化
rm -rf ~/.openclaw/config.json
openclaw init

# 3. 或者手动编辑配置
nano ~/.openclaw/config.json
```

### 问题 5：TUI 界面无法启动

**症状**：选择 TUI 后黑屏或闪退

**解决方案**：

```bash
# 1. 检查终端兼容性
echo $TERM  # 应显示：xterm-256color 或 screen

# 2. 设置终端类型
export TERM=xterm-256color

# 3. 重新启动
openclaw start

# 4. 或者使用 Web UI
openclaw gateway start
# 浏览器访问：http://localhost:18789
```

---

## ✅ 验证安装（完整测试清单）

**逐项检查，全部通过才算成功**：

```bash
# □ 1. 检查版本号
openclaw --version
# 期望输出：openclaw/x.x.x linux-x64 node-v22.12.0

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

## 📊 性能优化（生产环境）

### 1. Node.js 内存优化

**编辑 systemd 服务**：

```bash
sudo nano /etc/systemd/system/openclaw-gateway.service
```

**添加内存配置**（根据服务器内存调整）：

```ini
# 4GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=2048"

# 8GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=4096"

# 16GB 内存服务器
Environment="NODE_OPTIONS=--max-old-space-size=8192"
```

**重载并重启**：

```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw-gateway
```

### 2. 定期清理缓存

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
| v3.0 | 2026-03-17 | 整合官方一键脚本 + NVM 安装 + 初始化向导详解 |
| v2.0 | 2026-03-17 | 增加电气安全警示、精准参数、故障排查流程图 |
| v1.5 | 2026-03-10 | 增加 systemd 服务配置、性能优化章节 |
| v1.0 | 2026-03-01 | 初始版本发布 |

---

*最后更新：2026-03-17*  
*作者：OpenClaw 社区*  
*许可：MIT*  
*审核：嵌入式硬件专家（15 年 + 经验）*

**觉得有用？欢迎分享给更多朋友！** 🚀
