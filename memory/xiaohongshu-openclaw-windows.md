【3 个备选爆款标题】
1. 破防了！Windows 部署 OpenClaw 居然有 2 种方案😱
2. 救命！WSL2 安装 AI 助手真的太香了🪟
3. 终于有人说真话了！Windows 部署全攻略🔧

【小红书正文完整内容】

谁懂啊！在 Windows 上部署 OpenClaw 踩了好多坑😭 今天把 WSL2 和原生安装两种方案都整理出来，希望能救一个是一个！

🪟 一、系统要求（先看！）

✅ 操作系统：Windows 10 21H2+ / Windows 11
✅ 内存：8GB+ (推荐 16GB)
✅ 磁盘：20GB+ 可用空间
✅ Node.js: v20+
✅ Python: 3.10+

❌ 不满足的别硬上！

🔧 二、方案一：WSL2 安装（强烈推荐！）

1️⃣ 启用 WSL2

以管理员身份运行 PowerShell：
wsl --install
wsl --set-default-version 2

重启电脑后，安装 Ubuntu：
wsl --install -d Ubuntu-22.04

2️⃣ 在 WSL2 中安装

参考我之前的 Linux 部署教程！
（看我的主页，有详细教程）

3️⃣ 优势

✅ 兼容性好
✅ 和 Linux 环境一致
✅ 不容易踩坑
✅ 推荐使用！

🔧 三、方案二：原生安装

1️⃣ 安装 Node.js

从 nodejs.org 下载安装包
或使用 winget：
winget install OpenJS.NodeJS.LTS

2️⃣ 安装 OpenClaw

以管理员身份运行 PowerShell：
npm install -g openclaw
openclaw --version

3️⃣ 配置环境变量

添加用户环境变量：
OPENCLAW_WORKSPACE = C:\Users\<用户名>\openclaw-workspace

4️⃣ 初始化

cd C:\Users\<用户名>\openclaw-workspace
openclaw init

⚙️ 四、配置优化（重要！）

Windows Terminal 配置：

推荐安装 Windows Terminal
配置 Cascadia Code 字体
fontSize: 12

防火墙配置：

New-NetFirewallRule -DisplayName "OpenClaw Gateway" -Direction Inbound -LocalPort 18789 -Protocol TCP -Action Allow

🔍 五、常见问题（必看！）

❌ 问题 1：权限问题

以管理员身份运行 PowerShell
Start-Process powershell -Verb RunAs

❌ 问题 2：npm 全局安装失败

npm config set prefix "C:\npm"
添加环境变量 PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\npm", "User")

❌ 问题 3：WSL2 网络问题

wsl --shutdown
wsl

✅ 六、验证安装

openclaw gateway status
openclaw message send "Hello from Windows!"

✨ 最后想说：

Windows 部署推荐 WSL2！
原生安装会有兼容性问题！
有问题评论区问我！

---

宝子们还有什么想了解的安全问题，评论区留言，我挨个出攻略！
记得点赞收藏关注，不然刷着刷着就找不到啦～

【适配标签】
#OpenClaw #Windows 部署 #WSL2 #AI 助手 #技术教程 #程序员 #Windows 教程 #部署指南 #干货分享 #技术分享 #服务器运维 #开源项目 #AI 工具 #技术干货 #安装教程
