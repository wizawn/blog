【3 个备选爆款标题】
1. 救命！在 Linux 上部署 AI 助手居然这么简单😱
2. 破防了！10 分钟搞定 OpenClaw Linux 部署🐧
3. 终于有人说真话了！Linux 部署 AI 助手全攻略🔧

【小红书正文完整内容】

谁懂啊！昨天花了一下午在 Linux 服务器上部署 OpenClaw，结果踩了一堆坑😭 今天把完整流程整理出来，希望能救一个是一个！

🐧 一、系统要求（先看这个！）

✅ 操作系统：Ubuntu 20.04+ / Debian 11+ / CentOS 8+
✅ 内存：4GB+ (推荐 8GB)
✅ 磁盘：10GB+ 可用空间
✅ Node.js: v20+
✅ Python: 3.10+

❌ 不满足的别硬上！会踩坑的！

🔧 二、安装步骤（跟着做就行）

1️⃣ 安装 Node.js

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

2️⃣ 安装 OpenClaw

```bash
npm install -g openclaw
openclaw --version
```

3️⃣ 初始化工作区

```bash
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace
openclaw init
```

4️⃣ 配置 API Keys

编辑 `~/.openclaw/workspace/TOOLS.md`:
```markdown
### DashScope (通义千问)
- Key: `sk-xxxxxxxxxxxxxxxx`
```

⚙️ 三、配置优化（重要！）

创建 systemd 服务：

```bash
cat > /etc/systemd/system/openclaw-gateway.service << EOF
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
EOF

systemctl daemon-reload
systemctl enable openclaw-gateway
systemctl start openclaw-gateway
```

🔍 四、常见问题（必看！）

❌ 问题 1：端口被占用
```bash
lsof -i :18789
kill -9 <PID>
```

❌ 问题 2：内存不足
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

❌ 问题 3：Node.js 版本不兼容
```bash
nvm install 20
nvm use 20
npm rebuild
```

✅ 五、验证安装

```bash
openclaw gateway status
openclaw message send "Hello OpenClaw!"
```

✨ 最后想说：

Linux 部署其实很简单！
关键是看好系统要求！
别跳过任何一步！
有问题评论区问我！

---

宝子们还有什么想了解的安全问题，评论区留言，我挨个出攻略！
记得点赞收藏关注，不然刷着刷着就找不到啦～

【适配标签】
#OpenClaw #Linux 部署 #AI 助手 #服务器配置 #运维教程 #技术分享 #程序员 #Linux 教程 #部署指南 #干货分享 #技术教程 #服务器运维 #开源项目 #AI 工具 #技术干货
