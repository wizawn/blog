---
title: "OpenClaw 部署教程 - Windows 篇（2026 终极版）"
date: 2026-03-17T15:00:00+08:00
draft: false
weight: 100
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Windows", "PowerShell", "部署", "AI 助手", "保姆级教程"]
image: "/static/tech-cover-1.jpg"
description: "OpenClaw Windows 部署终极指南 - 含 PowerShell 一键安装、Node.js 22 配置、Git 环境、初始化向导、故障排查，基于 Windows 11 实测验证"
---


> **💬 联系方式 & 交流群**
> 
> **QQ**: 46333839  
> **微信**: GOV-HACK  
> 
> 添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~
> 
> ![微信赞赏码](/images/wechat-pay.jpg)
> 
> ![支付宝收款码](/images/alipay-pay.jpg)
> 
> ![微信二维码](/images/wechat-qr.jpg)

---

# OpenClaw 部署教程 - Windows 篇（2026 终极版）

> 📅 **更新时间**：2026-03-17  
> ⏱️ **阅读时间**：20 分钟  
> 💡 **难度等级**：⭐⭐☆☆☆  
> ✅ **实测环境**：Windows 11 专业版 / Node.js v22.1.0 / Git 2.46.0 / PowerShell 7.4

---

## ⚠️ 部署前必读（安全警示）

### 系统安全
- **管理员权限**：安装过程需要管理员权限，但运行时建议使用普通用户
- **防火墙**：首次运行会提示允许网络访问，需点击"允许"
- **杀毒软件**：Windows Defender 可能误报，需添加排除项
- **备份**：部署前备份重要数据

### 硬件要求
- **内存**：最低 4GB，推荐 8GB+（2GB 需配置虚拟内存）
- **磁盘**：至少 10GB 可用空间（推荐 SSD）
- **网络**：需访问外网（中国大陆用户需配置代理）

### 环境准备
- **PowerShell**：需以管理员身份运行
- **执行策略**：需设置为 `RemoteSigned`（允许运行签名脚本）
- **TLS 1.2**：必须启用（解决 SSL 连接问题）

---

## 📋 系统要求（精准参数）

| 项目 | 最低要求 | 推荐配置 | **生产环境** |
|------|----------|----------|-------------|
| **操作系统** | Windows 10 | Windows 11 | Windows 11 专业版 23H2 |
| **CPU** | 2 核心 | 4 核心+ | 8 核心+ (Intel i7/Ryzen 7) |
| **内存** | 4GB | 8GB+ | **16GB+** (AI 模型缓存) |
| **磁盘** | 10GB | 20GB SSD | **50GB NVMe SSD** |
| **Node.js** | v18+ | v20+ | **v22.1.0** (最新稳定) |
| **Git** | 任意版本 | 最新 | **2.46.0** |
| **PowerShell** | 5.1+ | 7.4+ | **7.4.1** |

**⚠️ 关键说明**：
1. **Node.js v22**：OpenClaw 官方推荐版本，兼容性最佳
2. **PowerShell 7**：比 5.1 更稳定，支持更多命令
3. **Git 必须**：用于克隆仓库和管理依赖

---

## 🔧 快速安装（10 分钟完成）

### 方法一：PowerShell 一键安装（推荐新手）

**完整流程**（复制粘贴到 PowerShell）：

```powershell
# ============ 步骤 1：以管理员身份运行 PowerShell ============
# 开始菜单 → 搜索 PowerShell → 右键 → 以管理员身份运行

# ============ 步骤 2：设置执行策略（允许运行脚本） ============
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# ============ 步骤 3：启用 TLS 1.2（解决 SSL 连接问题） ============
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ============ 步骤 4：执行安装脚本 ============
irm https://docs.openclaw.ai/zh-CN/install | iex

# ============ 步骤 5：验证安装 ============
openclaw --version
```

**⏱️ 预计耗时**：5-10 分钟（取决于网络）

**⚠️ 注意事项**：
- **必须管理员权限**：否则安装失败
- **国内网络**：可能需要代理
- **安装过程**：自动安装 Node.js、Git、OpenClaw

---

### 方法二：分步安装（可控性更强，推荐）

适合需要**精确控制版本**或**排查问题**的场景：

#### 步骤 1：准备工作目录

```powershell
# 创建临时目录（存放安装包）
New-Item -Path "C:\temp" -ItemType Directory -Force
```

#### 步骤 2：启用 TLS 1.2

```powershell
# 必须执行，否则下载会失败
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
```

#### 步骤 3：安装 Node.js 22

```powershell
# 1. 下载 Node.js 22.1.0 64 位安装包
iwr -Uri "https://nodejs.org/dist/v22.1.0/node-v22.1.0-x64.msi" `
 -OutFile "C:\temp\node-v22.1.0-x64.msi" `
 -UseBasicParsing

# 2. 验证文件是否存在
if (Test-Path "C:\temp\node-v22.1.0-x64.msi") {
    Write-Host "✅ 文件存在，开始安装..."
    # 静默安装，/qn 表示无界面，/norestart 表示不自动重启
    Start-Process -FilePath "C:\temp\node-v22.1.0-x64.msi" `
     -ArgumentList "/qn /norestart" `
     -Wait
    Write-Host "✅ Node.js 安装完成！"
} else {
    Write-Host "❌ 错误：安装包未找到，请检查下载命令！"
}

# 3. 验证版本（需重新打开 PowerShell）
node -v   # 应显示：v22.1.0
npm -v    # 应显示：10.5.0+
```

**⏱️ 预计耗时**：3-5 分钟

#### 步骤 4：安装 Git

```powershell
# 1. 下载 Git for Windows 最新稳定版
iwr -Uri "https://github.com/git-for-windows/git/releases/download/v2.46.0.windows.1/Git-2.46.0-64-bit.exe" `
 -OutFile "C:\temp\Git-Setup.exe" `
 -UseBasicParsing

# 2. 静默安装（自动添加到 PATH）
Start-Process -FilePath "C:\temp\Git-Setup.exe" `
 -ArgumentList "/VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES /ADDLOCAL=ALL" `
 -Wait

Write-Host "✅ Git 安装完成，请重启 PowerShell 后验证！"

# 3. 验证（需重启 PowerShell）
git --version  # 应显示：git version 2.46.0.windows.1
```

**⏱️ 预计耗时**：2-3 分钟

#### 步骤 5：安装 OpenClaw

```powershell
# 方法 A：下载脚本到本地（推荐，可排查错误）
$scriptPath = "C:\temp\openclaw-install.ps1"
New-Item -Path "C:\temp" -ItemType Directory -Force | Out-Null
iwr -Uri "https://openclaw.ai/install.ps1" -OutFile $scriptPath -UseBasicParsing

# 执行脚本（会显示具体错误，而非闪退）
& $scriptPath

# 方法 B：一键安装（简单快速）
iwr -useb https://openclaw.bot/install.ps1 | iex

# 验证安装
openclaw --version
where openclaw
```

**⏱️ 预计耗时**：2-3 分钟

---

## ⚙️ 初始化配置（Onboarding 向导）

安装成功后会自动进入**初始化向导**，按以下步骤操作：

### 完整流程

```powershell
# 步骤 1：执行初始化向导
openclaw onboard --flow quickstart

# 步骤 2：启动 OpenClaw
openclaw start

# 步骤 3：测试运行
# 在聊天界面输入 "Hello"
# 应收到 AI 回复
```

### 详细步骤说明

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

### 配置 API Keys

**编辑配置文件**：

```powershell
notepad $env:USERPROFILE\.openclaw\workspace\TOOLS.md
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

### 配置代理（中国大陆用户必须）

**编辑配置文件**：

```powershell
notepad $env:USERPROFILE\.openclaw\config.json
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

**验证代理**：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
Test-NetConnection api.binance.com -Port 443
# 应显示：TcpTestSucceeded : True
```

---

## 🚀 高级配置（生产环境必备）

### 1. 配置虚拟内存（4GB 内存推荐）

**检查当前虚拟内存**：

```powershell
# 查看系统信息
systeminfo | findstr "虚拟内存"
```

**手动配置（8GB 虚拟内存）**：

1. 右键"此电脑" → 属性
2. 高级系统设置 → 高级 → 性能设置
3. 高级 → 虚拟内存 → 更改
4. 取消"自动管理"
5. 选择 C 盘 → 自定义大小
6. 初始大小：8192 MB，最大值：8192 MB
7. 点击"设置" → 确定 → 重启

### 2. 配置 Windows 防火墙

**允许 OpenClaw 通过网络**：

```powershell
# 添加入站规则
New-NetFirewallRule -DisplayName "OpenClaw Gateway" `
 -Direction Inbound `
 -LocalPort 18789 `
 -Protocol TCP `
 -Action Allow

# 查看规则
Get-NetFirewallRule | Where-Object DisplayName -like "*OpenClaw*"
```

### 3. 配置 Windows Defender 排除项

**避免误报**：

```powershell
# 添加排除目录
Add-MpPreference -ExclusionPath "C:\Users\$env:USERNAME\.openclaw"

# 添加排除进程
Add-MpPreference -ExclusionProcess "node.exe"

# 验证排除项
Get-MpPreference | Select-Object ExclusionPath, ExclusionProcess
```

### 4. 开机自启（任务计划程序）

**创建启动脚本** `C:\openclaw-start.bat`：

```batch
@echo off
timeout /t 30 /nobreak
cd /d %USERPROFILE%\.openclaw\workspace
openclaw gateway start
exit
```

**添加到任务计划程序**：

1. 开始菜单 → 搜索"任务计划程序"
2. 右侧"创建基本任务"
3. 名称：`OpenClaw Gateway`
4. 触发器：**登录时**
5. 操作：**启动程序**
6. 程序/脚本：`C:\openclaw-start.bat`
7. 完成 → 输入管理员密码

**验证**：

```powershell
# 查看任务
Get-ScheduledTask | Where-Object TaskName -like "*OpenClaw*"

# 手动运行测试
Start-ScheduledTask -TaskName "OpenClaw Gateway"
```

---

## 🔍 故障排查（精准诊断）

### 问题 1：ExecutionPolicy 报错

**症状**：`cannot be loaded because running scripts is disabled on this system`

**解决方案**：

```powershell
# 1. 检查当前策略
Get-ExecutionPolicy -Scope CurrentUser

# 2. 临时设置（仅当前会话）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 3. 验证
Get-ExecutionPolicy -Scope CurrentUser
# 应显示：RemoteSigned

# 4. 重新运行安装脚本
& $scriptPath
```

### 问题 2：PATH 或命令找不到

**症状**：`openclaw : 无法将"openclaw"项识别为 cmdlet、函数、脚本文件`

**解决方案**：

```powershell
# 1. 检查 openclaw 路径
where openclaw

# 2. 如果无输出，说明未添加到 PATH
# 手动添加环境变量
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$npmPath = "$env:APPDATA\npm"
[Environment]::SetEnvironmentVariable("Path", "$userPath;$npmPath", "User")

# 3. 重新打开 PowerShell（必须）
# 关闭所有 PowerShell 窗口，重新打开

# 4. 验证
openclaw --version
```

### 问题 3：安装脚本闪退

**症状**：执行脚本后 PowerShell 直接关闭，看不到错误信息

**解决方案**：

```powershell
# 1. 下载脚本到本地（不要直接管道执行）
$scriptPath = "C:\temp\openclaw-install.ps1"
New-Item -Path "C:\temp" -ItemType Directory -Force | Out-Null
iwr -Uri "https://openclaw.ai/install.ps1" -OutFile $scriptPath -UseBasicParsing

# 2. 手动执行（会显示具体错误）
& $scriptPath

# 3. 如果还是失败，查看错误日志
Get-Content C:\temp\openclaw-install.log -Tail 50
```

### 问题 4：Node.js 版本不兼容

**症状**：`Error: Unsupported Node.js version`

**解决方案**：

```powershell
# 1. 查看当前版本
node -v

# 2. 卸载旧版本（控制面板 → 程序和功能）
# 或者使用 PowerShell
winget uninstall "Node.js"

# 3. 重新安装 Node.js 22
iwr -Uri "https://nodejs.org/dist/v22.1.0/node-v22.1.0-x64.msi" `
 -OutFile "C:\temp\node-v22.1.0-x64.msi"
Start-Process -FilePath "C:\temp\node-v22.1.0-x64.msi" `
 -ArgumentList "/qn /norestart" -Wait

# 4. 重新打开 PowerShell 验证
node -v  # 应显示：v22.1.0
```

### 问题 5：防火墙或 Defender 拦截

**症状**：网络连接超时，或被 Defender 隔离

**解决方案**：

```powershell
# 1. 检查防火墙规则
Get-NetFirewallRule | Where-Object DisplayName -like "*OpenClaw*"

# 2. 添加入站规则（如果不存在）
New-NetFirewallRule -DisplayName "OpenClaw Gateway" `
 -Direction Inbound `
 -LocalPort 18789 `
 -Protocol TCP `
 -Action Allow

# 3. 检查 Defender 隔离区
Get-MpThreatDetection | Select-Object ThreatName, DetectionTime

# 4. 恢复被隔离文件（如果有）
# Windows 安全中心 → 病毒和威胁防护 → 保护历史记录 → 还原

# 5. 添加排除项
Add-MpPreference -ExclusionPath "$env:USERPROFILE\.openclaw"
```

### 问题 6：端口被占用

**症状**：`Error: listen EADDRINUSE: address already in use :::18789`

**解决方案**：

```powershell
# 1. 检查端口占用
netstat -ano | findstr :18789
# 输出示例：TCP  0.0.0.0:18789  0.0.0.0:0  LISTEN  1234

# 2. 杀死占用进程
taskkill /F /PID 1234

# 3. 或者修改 OpenClaw 端口
notepad $env:USERPROFILE\.openclaw\config.json
# 修改："port": 18790

# 4. 重启服务
openclaw gateway restart
```

### 问题 7：npm 安装失败

**症状**：`npm ERR! code EACCES` 或 `npm ERR! permissions`

**解决方案**：

```powershell
# 1. 清理 npm 缓存
npm cache clean --force

# 2. 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 3. 修改 npm 全局目录
npm config set prefix "C:\npm-global"

# 4. 添加环境变量
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;C:\npm-global", "User")

# 5. 重新打开 PowerShell，重新安装
npm install -g openclaw
```

---

## ✅ 验证安装（完整测试清单）

**逐项检查，全部通过才算成功**：

```powershell
# □ 1. 检查版本号
openclaw --version
# 期望输出：openclaw/x.x.x win32-x64 node-v22.1.0

# □ 2. 检查网关状态
openclaw gateway status
# 期望输出：Gateway is running

# □ 3. 检查端口监听
netstat -ano | findstr :18789
# 期望输出：TCP  0.0.0.0:18789  0.0.0.0:0  LISTEN

# □ 4. 测试本地访问
Test-NetConnection localhost -Port 18789
# 期望输出：TcpTestSucceeded : True

# □ 5. 发送测试消息
openclaw message send "Hello OpenClaw!"
# 期望：收到 AI 回复

# □ 6. 检查日志无 ERROR
Get-Content $env:USERPROFILE\.openclaw\workspace\memory\*.log -Tail 50 | Select-String "ERROR"
# 期望：无输出

# □ 7. 检查服务状态
openclaw gateway status
# 期望输出：Active: active (running)

# □ 8. 测试开机自启
# 重启电脑后检查：
openclaw gateway status
# 期望：服务自动启动
```

**成功标志**：
- ✅ 8 项检查全部通过
- ✅ 日志无 ERROR 级别错误
- ✅ 服务重启后自动恢复

---

## 📊 性能优化（生产环境）

### 1. 使用 SSD 存储

**检查工作区位置**：

```powershell
# 查看工作区路径
openclaw status

# 如果不在 SSD，迁移工作区
Move-Item "$env:USERPROFILE\.openclaw" "D:\openclaw"
New-Item -ItemType SymbolicLink `
 -Path "$env:USERPROFILE\.openclaw" `
 -Target "D:\openclaw"
```

### 2. 增加 Node.js 内存

**编辑启动配置**：

```powershell
# 临时生效（当前会话）
$env:NODE_OPTIONS="--max-old-space-size=4096"

# 永久生效（添加到环境变量）
[Environment]::SetEnvironmentVariable("NODE_OPTIONS", "--max-old-space-size=4096", "User")
```

### 3. 定期清理缓存

**创建清理脚本** `C:\cleanup-openclaw.ps1`：

```powershell
Write-Host "🧹 开始清理 OpenClaw 缓存..."

# 清理 npm 缓存
npm cache clean --force
Write-Host "✅ npm 缓存已清理"

# 清理临时文件
Remove-Item "C:\temp\openclaw-*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ 临时文件已清理"

# 清理日志（保留最近 7 天）
$daysToKeep = 7
$cutoffDate = (Get-Date).AddDays(-$daysToKeep)
Get-ChildItem "$env:USERPROFILE\.openclaw\workspace\memory\*.log" | Where-Object { $_.LastWriteTime -lt $cutoffDate } | Remove-Item
Write-Host "✅ 旧日志已清理"

Write-Host "🎉 清理完成！"
```

**运行清理脚本**：

```powershell
# 以管理员身份运行
powershell -ExecutionPolicy Bypass -File C:\cleanup-openclaw.ps1
```

**添加到任务计划程序（每周日凌晨 3 点）**：

1. 任务计划程序 → 创建基本任务
2. 名称：`OpenClaw Cleanup`
3. 触发器：**每周**，周日，凌晨 3:00
4. 操作：**启动程序**
5. 程序：`powershell.exe`
6. 参数：`-ExecutionPolicy Bypass -File C:\cleanup-openclaw.ps1`

---

## 📚 更多资源

### 官方文档
- [OpenClaw 官方指南](https://open-claw.online/zh/docs/getting-started)
- [中文安装文档](https://docs.openclaw.ai/zh-CN/install)
- [GitHub 仓库](https://github.com/openclaw/openclaw)

### 社区教程
- [原生+Docker 双方案](https://blog.csdn.net/2503_93609022/article/details/158353716)
- [Windows 保姆级教程](https://open-claw.online/zh/docs/windows-install)

### 其他平台部署
- [Linux 部署教程](/posts/openclaw-deploy-linux)
- [Android 部署教程](/posts/openclaw-deploy-android)
- [macOS 部署教程](/posts/openclaw-deploy-macos)

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v3.0 | 2026-03-17 | 整合 PowerShell 一键脚本 + Node.js 22 + Git 环境 + 初始化向导详解 |
| v2.0 | 2026-03-10 | 增加安全警示、精准参数、故障排查流程 |
| v1.5 | 2026-03-05 | 增加 Docker 方案、性能优化章节 |
| v1.0 | 2026-03-01 | 初始版本发布 |

---

*最后更新：2026-03-17*  
*作者：OpenClaw 社区*  
*许可：MIT*  
*审核：嵌入式硬件专家（15 年 + 经验）*

**觉得有用？欢迎分享给更多朋友！** 🚀
