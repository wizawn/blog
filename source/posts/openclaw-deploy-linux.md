---
title: "OpenClaw 在 Ubuntu 服务器上的部署记录：Node 24、守护进程与回环端口安全"
date: 2026-03-17T14:30:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Linux", "Ubuntu", "Node.js", "部署"]
description: "基于 Ubuntu 22.04 / 24.04 LTS 实测整理 OpenClaw 服务端安装流程：修正 Node.js 版本门槛、API Key 存放位置、systemd 用户级守护服务与 18789 控制端口的安全隧道访问方式。"
weight: 10
---

折腾过 OpenClaw 的人大概都领教过网上那批拼凑教程有多坑：有的煞有介事写一段云服务器机房佩戴防静电手环的荒唐话，有的教人把 `18789` 控制端口直接对公网防火墙敞开，有的在 `systemd` 单元里写 `openclaw gateway start` 搞出一秒重启一次的死循环，最离谱的还让人把明文 API Key 往工作区提示词文件 `TOOLS.md` 里塞。

趁着在 Ubuntu LTS 云主机上重搭环境，把当前版本实测跑得通、也不留安全敞口的完整步骤重新顺一遍。其他端的折腾笔记可以对照看站内的 [macOS 篇](/posts/openclaw-deploy-macos/)、[Windows 11 篇](/posts/openclaw-deploy-windows/) 和 [Android Termux 篇](/posts/openclaw-deploy-android/)。

## 0x00 动手前先核对三件事：Swap、Node 24 门槛与端口边界

往一台 Linux 云主机上装 OpenClaw 之前，先把下面三条底线摸清。

第一件是小内存机器必须先挂 Swap。跑 `npm` 全局安装构建和拉起 Node 网关的瞬间内存冲得挺高，2GB 内存裸机不挂 Swap 十有八九会在半道卡死断掉 SSH（4GB 以上内存一般不用操心）。敲 `free -h` 要是看到 `Swap` 那栏是 `0B`，先划一个 2G 的交换文件垫底，顺手把 `swappiness` 调保守一点：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

第二件是认准当前版本的 Node.js 门槛。OpenClaw 是纯 Node.js 写的 CLI（本身压根不依赖 Python，只有少数外挂脚本型 Skill 才会调 Python），版本号走的是形如 `2026.x.y` 的日历版本（CalVer）。早先它只要求 Node 22，随着上游迭代，新版 `package.json` 里的 `engines.node` 已经抬高到了 `>=24.16.0 <25 || >=26.1.0`，照着旧帖装 Node 18、20 乃至老版 22 都会直接报 `Unsupported Node.js version`。

第三件是严禁拿 `root` 裸跑 Agent，也严禁把 `18789` 端口放进公网防火墙。OpenClaw 网关手握文件读写和终端命令执行大权，默认只监听本机回环 `127.0.0.1:18789`。服务器的 UFW 或云安全组只放行你自己的 SSH 端口就够了，打死别敲 `ufw allow 18789`；人在外面想开网页控制台，走一条 SSH 本地端口转发或者 Tailscale 内网组网最踏实。

## 0x01 官方 `install.sh` 与 NVM 手动安装

先切到一个带 `sudo` 权限的普通用户登录机器，别全程挂着 `root` 干活。如果机器在国内机房需要走本机代理（比如监听在 `127.0.0.1:7890` 的 Clash / Mihomo），开装前先把环境变量挂上，尤其记得在 `NO_PROXY` 里把本机回环地址排掉，免得一会儿本地网关自检流量也傻乎乎往代理里绕：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,::1
# Node 24+ 内置 fetch 读取环境变量代理可一并带上：
export NODE_USE_ENV_PROXY=1
```

图省事的话直接走官方的 `install.sh` 一键脚本（确认 `git` 和 `curl` 已装好；脚本跑完默认会自动拉起交互式的 `openclaw onboard` 向导，想跳过向导稍后自己配可以写成 `curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard`）：

```bash
sudo apt update && sudo apt install -y git curl
curl -fsSL https://openclaw.ai/install.sh | bash
```

要是更习惯自己拿 `nvm` 管 Node 版本，去 [`nvm-sh/nvm` 官方仓库](https://github.com/nvm-sh/nvm)拉最新的 `v0.40.x` 安装脚本（国内机器拉不动 GitHub 的话再换镜像源，装包慢也可以 `npm config set registry https://registry.npmmirror.com`），直接装推荐的 Node 26（或者 Node 24 LTS 的 `v24.22.1+` 及以上版本，避开更早 `24.x` 子版本上的根证书信任链告警）：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc

nvm install 26
nvm alias default 26
node -v   # 确认输出 v26.12.1+ 或 v24.22.1+

npm install -g openclaw
# 若当前 npm 版本为 11.16+ 或 12+ 拦截了生命周期安装脚本，改用：
# npm install -g openclaw@latest --allow-scripts=openclaw
openclaw --version   # 正常会打印类似 2026.x.y 的日历版本号
```

注意走 `npm install -g` 不会自动弹初始化向导，装完自己敲一行命令进交互式 TUI 向导，顺带让它把当前用户的后台守护服务一块儿装好：

```bash
openclaw onboard --install-daemon
```

## 0x02 向导配置与 API Key 落盘位置（千万别塞进 `TOOLS.md`！）

跑起 `openclaw onboard` 之后是个上下方向键选择的交互界面：读完风险提示确认继续，部署模式选 `QuickStart`，挑你主力用的模型服务商（选 OpenAI Codex 订阅授权的话终端会吐出 `auth.openai.com` 的登录授权链接，复制回本地浏览器登完即可），至于聊天通道、Skills 和 Hooks 第一次配全选 `Skip for now`，先把主干跑通再说。

这里必须单独拎出一个流毒极广的大坑：绝对不要把任何 API Key 写进 `~/.openclaw/workspace/TOOLS.md` 里！

`workspace/TOOLS.md` 是工作区里的提示词说明文档，每次对话都会被直接拼进大模型上下文里发往云端。往里面填密钥，一来程序根本不会把它当成供应商配置去读，二来等于每聊一句话就把你的明文私钥往外广播一次。

OpenClaw 真正的主配置文件叫 `~/.openclaw/openclaw.json`（也不是很多旧帖瞎写的 `config.json`；万一向导配劈了想重来，直接跑 `openclaw onboard` 或 `openclaw configure`，别去敲根本不存在的 `openclaw init`）。录入各家模型密钥走下面三条正规路子：

1. 直接敲交互命令 `openclaw configure` 按菜单填进去；
2. 写进 `~/.openclaw/.env` 环境变量文件（比如 `OPENAI_API_KEY=sk-...` 或百炼、火山对应的变量名），写完立刻用 `chmod 600 ~/.openclaw/.env ~/.openclaw/openclaw.json` 把读写权限锁死；
3. 需要配第三方兼容接口的自定义 `baseUrl` 时，对照[官方文档](https://docs.openclaw.ai/zh-CN/install)编辑 `~/.openclaw/openclaw.json` 里的 `models.providers` 字段（顺嘴提一句，外面搜索引擎常能搜到的 `open-claw.online` 并非官方站点且早已失效，查文档认准 `docs.openclaw.ai` 和 [GitHub 主仓](https://github.com/openclaw/openclaw)）。

## 0x03 用官方用户级 `systemd` 托管，躲开 `gateway start` 重启死循环

前面执行 `openclaw onboard --install-daemon`（或者单独补敲一句 `openclaw gateway install`）的时候，工具其实已经在你当前普通用户底下注册好了标准的 systemd 用户级单元 `openclaw-gateway.service`。想让它在你断开 SSH 之后继续常驻后台、机器重启后自动拉起，只需要给当前账号开一下 `linger`：

```bash
sudo loginctl enable-linger "$USER"

systemctl --user enable --now openclaw-gateway
systemctl --user status openclaw-gateway
```

平时启停直接敲 `openclaw gateway status|restart|stop` 就行。如果你因为特殊运维要求非要自己手写 `/etc/systemd/system/` 底下的单元文件，千万避开老教程里的三处硬伤：一是运行用户别填 `root`；二是 `[Unit]` 里如果写了 `Wants=network-online.target`，必须配对写上 `After=network-online.target`（光写 `After=network.target` 根本不会等外网就绪）；三是 `ExecStart` 必须写绝对路径的 Node 加前台阻塞运行的 `openclaw gateway run`（4G/8G 机器有需要可加 `Environment="NODE_OPTIONS=--max-old-space-size=2048"`），绝对不能写成 `openclaw gateway start`！因为 `gateway start` 只是通知服务管理器拉起网关后立刻退出的控制命令，塞进 `Type=simple` 配 `Restart=always` 里就会一秒钟退一次、陷入无限重启死循环。

## 0x04 验收自检、SSH 隧道面板与日志维护

服务挂稳之后，敲下面几条命令把底验清：

```bash
# 1. 查网关运行状态与环境健康度
openclaw gateway status
openclaw doctor

# 2. 用 ss 检查 18789 监听地址（Ubuntu 22.04+ 默认没装老掉牙的 netstat）
# 正常只应看到 127.0.0.1:18789；要是看见 0.0.0.0:18789 或 :::18789 说明控制面裸奔了，赶紧改回回环！
ss -tlnp | grep 18789

# 3. 跑一轮单次 Agent 对话看模型回不回话
# 切记别敲成 openclaw message send，那条命令是往已绑定的 Telegram/Discord 频道外发通知用的，必须传 --target
openclaw agent --message "Hello, reply with PONG only."
```

想在命令行里直接开聊就敲 `openclaw tui`（极简 SSH 客户端如果遇到界面花屏或黑屏，先 `export TERM=xterm-256color` 再进；另外根本没有 `openclaw start` 这个子命令）。想在本地电脑浏览器里打开图形控制台，在自己电脑终端起一条 SSH 端口转发：

```bash
ssh -N -L 18789:127.0.0.1:18789 你的用户名@服务器IP
```

连上之后本地浏览器打开 `http://127.0.0.1:18789/` 就能安全进面板了（首次打开提示输入网关共享 Token 时，回服务器终端敲一句 `openclaw gateway auth-token --show` 取出来贴进去即可）。

平时盯实时日志直接敲 `openclaw logs --follow`（新版按日切分的日志文件默认放在 `~/.openclaw/logs/` 下，早期版本在 `/tmp/openclaw/`，拿不准直接看 `openclaw logs` 打印的路径），或者查用户级 journal：`journalctl --user -u openclaw-gateway -f`。要是小硬盘机器想控住系统日志总体积，直接敲 `sudo journalctl --vacuum-time=7d` 或在 `/etc/systemd/journald.conf` 里配 `SystemMaxUse=200M`（注意 `journalctl` 的 `--vacuum-*` 是针对全局日志库的，跟 `-u openclaw-gateway` 写在一块儿也不会只清单个服务；别把带 `sudo` 的交互命令裸塞进普通用户的 `crontab` 里，没配免密在后台只会静默报错）。万一之前安装时机器真断连死机过，补一句 `sudo dmesg | grep -i "out of memory"` 或 `journalctl -k` 就能确认是不是吃了内核 OOM（Ubuntu 20.10+ 默认开了 `kernel.dmesg_restrict=1`，不加 `sudo` 普通用户读不到内核环缓冲）。
