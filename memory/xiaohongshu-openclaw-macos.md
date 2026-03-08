【3 个备选爆款标题】
1. 救命！macOS 部署 OpenClaw 居然这么丝滑🍎
2. 破防了！M1/M2/M3芯片都能完美运行😱
3. 终于有人说真话了！macOS 部署全攻略🔧

【小红书正文完整内容】

谁懂啊！在 MacBook 上部署 OpenClaw 踩了好多坑😭 今天把完整流程整理出来，Intel 和 Apple Silicon 芯片都适用！

🍎 一、系统要求（先看！）

✅ 操作系统：macOS 12.0+ (Monterey+)
✅ 芯片：Intel / Apple Silicon (M1/M2/M3)
✅ 内存：8GB+ (推荐 16GB)
✅ 磁盘：10GB+ 可用空间
✅ Node.js: v20+
✅ Python: 3.10+

❌ 不满足的别硬上！

🔧 二、安装步骤（超简单！）

1️⃣ 安装 Homebrew（如未安装）

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Apple Silicon 需要添加环境变量：
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

2️⃣ 安装 Node.js

brew install node@20

3️⃣ 安装 OpenClaw

npm install -g openclaw
openclaw --version

4️⃣ 初始化工作区

mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace
openclaw init

⚙️ 三、配置优化（重要！）

launchd 服务配置：

创建 ~/Library/LaunchAgents/com.openclaw.gateway.plist:

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

加载服务：
launchctl load ~/Library/LaunchAgents/com.openclaw.gateway.plist
launchctl start com.openclaw.gateway

🔍 四、常见问题（必看！）

❌ 问题 1：Apple Silicon 兼容性

使用 Rosetta 2 运行（仅 Intel 包）：
arch -x86_64 openclaw gateway start

❌ 问题 2：权限问题

mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

❌ 问题 3：端口被占用

lsof -i :18789
kill -9 <PID>

✅ 五、验证安装

openclaw gateway status
openclaw message send "Hello from macOS!"

✨ 最后想说：

macOS 部署真的很简单！
Homebrew 一键搞定！
M1/M2/M3 都能完美运行！
有问题评论区问我！

---

宝子们还有什么想了解的安全问题，评论区留言，我挨个出攻略！
记得点赞收藏关注，不然刷着刷着就找不到啦～

【适配标签】
#OpenClaw #macOS 部署 #M1 #M2 #M3 #AI 助手 #技术教程 #程序员 #macOS 教程 #部署指南 #干货分享 #技术分享 #服务器运维 #开源项目 #AI 工具 #技术干货 #安装教程
