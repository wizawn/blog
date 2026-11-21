---
title: "Windows 11 部署 OpenClaw 避坑记录：别拿管理员硬跑脚本，也别关 Defender"
date: 2026-03-17T15:00:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Windows", "PowerShell", "Node.js", "部署"]
description: "基于 Windows 11 与 PowerShell 7 实测整理 OpenClaw 安装配置流程，纠正错误的 HTML 安装地址、全局排除 node.exe 杀毒扫描与开放 0.0.0.0:18789 入站防火墙等高危误导操作。"
weight: 10
---

在 Windows 10 / 11 上装 OpenClaw，要是照着网上某些拼凑出来的所谓教程一步步敲，真能把自己坑得够呛：第一行 `irm https://docs.openclaw.ai/zh-CN/install | iex` 拉回来的其实是中文网页 HTML，直接报错收场；接着教程非逼你用管理员权限跑安装脚本，把路径和配置全塞进 Administrator 账户底下导致普通用户找不到命令；最要命的是，底下居然还教人敲 `Add-MpPreference -ExclusionProcess "node.exe"` 把整台电脑上所有 Node 进程的实时杀毒全废掉，再给 `18789` 控制端口加一条对全网放行的入站防火墙规则。

把这些害人的偏方全清出去之后，在 Windows 11 加 PowerShell 7 下装好 OpenClaw 其实非常清爽。其他系统的折腾记录见同系列的 [Linux 服务器篇](/posts/openclaw-deploy-linux/)、[macOS 篇](/posts/openclaw-deploy-macos/) 和 [Android Termux 篇](/posts/openclaw-deploy-android/)。

## 0x00 动手前先立三条规矩，在普通权限下装前置环境

打开终端之前，先把三条安全边界记牢。

第一条，日常跑安装脚本就在当前普通用户的 PowerShell 里跑，不要右键选"以管理员身份运行"。官方的 `install.ps1` 源码里压根没有任何管理员权限检查，只有中途调 `winget` 或 MSI 装系统级 Node.js / Git 时，系统自己会正常弹一次 UAC 确认框。全程提权跑 npm 全局安装，反而容易把全局 bin 目录和权限搞乱。

第二条，绝对不要给 `node.exe` 或整个 `.openclaw` 目录加 Windows Defender 全局排除项！2026 年初社区里就已经爆出过第三方插件仓库混入窃密脚本（Infostealer）的案例，一旦你把 `node.exe` 塞进杀毒白名单，整台电脑上任何来路不明的恶意 Node 脚本都能大摇大摆绕过查杀（真怀疑某次下载被误杀，在 PowerShell 里敲 `Get-MpThreat` 和 `Get-MpThreatDetection | Select-Object ThreatID, InitialDetectionTime, Resources` 看一眼隔离记录核实哈希，千万别抄错不存在的属性名，更别一刀切放行整个解释器）。

第三条，别去手配 `18789` 端口的公网入站防火墙规则。OpenClaw 网关默认只绑本机回环 `127.0.0.1:18789`，本机浏览器和命令行访问回环口根本不需要开入站防火墙；首次运行如果弹出 Windows 防火墙提示框，记得把"公用网络"的勾去掉，别把一个能调终端命令的 Agent 控制台敞在咖啡厅或酒店局域网上。

正式安装有两条路，优先推荐先把 PowerShell 升到 7.x（敲 `winget install --id Microsoft.PowerShell -e`）。

想省事直接跑官方 `install.ps1` 脚本的话，认准唯一官方域名 `openclaw.ai`（别乱跑别的近似域名以防供应链投毒）。如果你还在用系统自带的旧版 Windows PowerShell 5.1 遇到 SSL 握手报错，切记用 `-bor` 追加开启 TLS 1.2，别直接赋值把 TLS 1.3 给关掉了：

```powershell
# 仅旧版 PowerShell 5.1 需要；pwsh 7 默认已支持 TLS 1.2 / 1.3
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# 拉取官方安装脚本执行（自动调 winget 检查安装最新 Node LTS 并进 onboard 向导）
iwr -useb https://openclaw.ai/install.ps1 | iex
# 若想跳过向导稍后手配，改用带参调用：& ([scriptblock]::Create((irm https://openclaw.ai/install.ps1))) -NoOnboard

openclaw --version
```

要是国内网络抖动导致脚本报错一闪而过，先把脚本落盘到 `C:\temp`，套一层 `Start-Transcript` 把屏幕输出全录下来慢慢看（官方脚本本身不会自动生成什么 `openclaw-install.log` 文件；另外如果只想在当前这一个终端会话里临时放行本地未签名脚本，用的是 `-Scope Process`，关窗即失效，而 `-Scope CurrentUser` 会写进注册表永久保留）：

```powershell
New-Item -Path "C:\temp" -ItemType Directory -Force | Out-Null
Start-Transcript -Path "C:\temp\openclaw-install-transcript.txt"
iwr -Uri "https://openclaw.ai/install.ps1" -OutFile "C:\temp\install.ps1"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& "C:\temp\install.ps1"
Stop-Transcript
```

如果你更喜欢分步自己装运行时，当前新版 OpenClaw 要求 Node.js `>=24.16.0 <25 || >=26.1.0`，千万别再去下两年前非 LTS 的老包 `node-v22.1.0-x64.msi`（机器上装过旧版的话可以先敲 `winget uninstall --id OpenJS.NodeJS.LTS` 或去设置里卸掉）。直接拿 `winget` 装最新 LTS 版 Node 和 Git：

```powershell
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
```

装完一定关掉当前窗口重开一个新的 PowerShell 让 `Path` 刷新，确认 `node -v` 和 `git --version` 正常显示后，全局装 `openclaw`（拉包慢可以先 `npm config set registry https://registry.npmmirror.com`）并进初始化向导：

```powershell
npm install -g openclaw
# npm 11.16+ 或 12+ 若拦截安装脚本，改用：npm install -g openclaw@latest --allow-scripts=openclaw
openclaw --version   # 正常打印类似 2026.x.y 的日历版本号

# 进入交互式向导，并自动在 Windows 任务计划程序里注册后台服务
openclaw onboard --install-daemon
```

万一重开窗口敲 `openclaw` 还是报"无法将 openclaw 项识别为 cmdlet"，先敲 `npm config get prefix` 看一眼你的 npm 全局目录（通常是 `$env:APPDATA\npm`），确认它在当前用户的 `Path` 环境变量里就行。

## 0x01 配好 `openclaw.json` 与代理（拿 `curl.exe` 测，别用 `Test-NetConnection`）

进 `openclaw onboard` 选 `QuickStart` 走完模型授权之后，后续想加阿里云百炼、火山引擎或 OpenAI 的 API Key，照样守住那两条老规矩：绝对不要往 `$env:USERPROFILE\.openclaw\workspace\TOOLS.md` 里贴密钥（那是每次对话都会喂给模型的上下文提示词）；真正的主配置文件叫 `$env:USERPROFILE\.openclaw\openclaw.json`（不是瞎编的 `config.json`，网关地址也保持默认的回环绑定，千万别手改成 `"host": "0.0.0.0"`）。录入密钥直接敲 `openclaw configure`，或者写进 `$env:USERPROFILE\.openclaw\.env`。

在国内网络下挂本地代理（比如 Clash 的 `127.0.0.1:7890`）时，有个很多 Windows 教程都在犯的常识错误：设完 `$env:HTTPS_PROXY` 之后敲 `Test-NetConnection` 去测端口通不通。`Test-NetConnection` 走的是底层直连 TCP 探测，压根不看你的 HTTP 代理环境变量，测通测不通都跟代理没半毛钱关系！真要验代理链路，直接调 Windows 10/11 自带的 `curl.exe` 带上 `-x` 去请求目标模型接口：

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
$env:NO_PROXY = "localhost,127.0.0.1,::1"
$env:NODE_USE_ENV_PROXY = "1"

curl.exe -x http://127.0.0.1:7890 -I https://api.openai.com/v1/models
```

## 0x02 计划任务自启、连通验收与搬迁工作区注意事项

你完全不需要往 `C:\` 盘根目录手写什么 `openclaw-start.bat` 再手动绑任务计划程序。前面跑 `openclaw onboard --install-daemon`（或补跑一句 `openclaw gateway install`）的时候，工具已经自动在 Windows 任务计划程序里建好了合规的后台任务，平时直接用内置命令管启停、验连通性就行：

```powershell
# 1. 看网关状态与监听地址（正常只应看到 127.0.0.1:18789 处于 LISTENING，别抄串台教程去期待 systemd 的 active 输出）
openclaw gateway status
netstat -ano | findstr :18789

# 2. 跑一轮单次 Agent 对话测试模型回复（别敲成往外部频道发消息的 openclaw message send）
openclaw agent --message "Reply with PONG only."

# 3. 进终端对话界面或拉起本地浏览器面板（没有 openclaw start 这个命令；网页面板要 token 时敲 openclaw gateway auth-token --show）
openclaw tui
# 或：openclaw dashboard
```

要是 `18789` 端口跟本机别的软件撞车了，拿 `netstat -ano | findstr :18789` 最后一列的 PID 去关掉冲突进程，或者在 `openclaw.json` 里把 `gateway.port` 换个空闲端口后 `openclaw gateway restart`。

日常用久了还有三件小事留个心眼。第一，看实时运行日志直接敲 `openclaw logs --follow`，千万别跑任何清理脚本去删 `$env:USERPROFILE\.openclaw\workspace\memory\` 底下的文件，那里头放的是 Agent 记忆而非日志。第二，4GB 小内存老机器想看当前虚拟内存分页文件够不够大，敲不挑中英文系统语言的 `Get-CimInstance Win32_PageFileUsage` 一眼就能看清。第三，如果 C 盘满了想把 `.openclaw` 整个搬去别的固态盘并建 `SymbolicLink` 软链接，动手搬之前必须先敲 `openclaw gateway stop` 把后台网关停干净，并且在打开了系统"开发者模式"（或提权）的窗口里执行 `New-Item -ItemType SymbolicLink`。更多细节可翻 [OpenClaw 官方文档](https://docs.openclaw.ai/zh-CN/install) 与 [GitHub 仓库](https://github.com/openclaw/openclaw)。
