---
title: "macOS 上装 OpenClaw 踩坑记：装对脚本地址、接本地 Ollama 与 LaunchAgent 自启"
date: 2026-03-10T16:00:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "macOS", "Apple Silicon", "Ollama", "部署"]
description: "记录在 Apple Silicon 与 Intel Mac 上部署 OpenClaw 的实测步骤：避开把网页文档当安装脚本的乌龙，正确配置 openclaw.json、Ollama 本地模型与 launchd 后台服务。"
weight: 10
---

在 Mac（尤其是 M 系列芯片的 MacBook 或常年不关机的 Mac mini）上装 OpenClaw 本来几分钟就能收工，偏偏网上流出的几篇快餐教程造出了好几个让人抓狂的坑：最经典的一条是教人敲 `curl -fsSL https://docs.openclaw.ai/zh-CN/install | bash`，那个地址返回的明明是一整页 HTML 中文网页，直接管道喂给 `bash` 当场就是一屏幕语法报错；更损的还教人拿 `find ... -delete` 定时清 `~/.openclaw/workspace/memory/` 目录，谁照着敲谁就把 Agent 攒下来的记忆笔记全删光了。

这里把在 macOS（建议 macOS 14 Sonoma 及以上、8GB+ 统一内存）上实测走通的干净流程记一笔。其他系统可以翻同系列的 [Linux 服务器篇](/posts/openclaw-deploy-linux/)、[Windows 11 篇](/posts/openclaw-deploy-windows/) 和 [Android Termux 篇](/posts/openclaw-deploy-android/)。

## 0x00 装对 Node 24+ 与真正的官方安装脚本

OpenClaw 本身不需要装 Python，但当前版本对 Node.js 的门槛已经升到了 `>=24.16.0 <25 || >=26.1.0`。早年教程里写的 `brew install node@20` 一来版本太低装不上新版 OpenClaw（Node 20 也在 2026 年 4 月底正式 EOL），二来 Homebrew 里带版本号的 `node@20` / `node@24` 默认属于 keg-only，装完不手动把路径写进 `~/.zshrc`，终端里敲 `node` 压根找不到命令。

在 Mac 上装它就两条顺路，挑顺手的来就行。

第一条是直接跑主域名下的官方 `install.sh` 脚本（这才是真正的 shell 脚本地址，跑完会自动拉起首次配置向导）：

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw --version
```

第二条是用 Homebrew 装最新主线 Node 再全局装包。Apple Silicon 机型上 Homebrew 的根目录在 `/opt/homebrew`，权限天然归当前用户管，千万别照抄十年前的 Intel 老帖去敲什么 `sudo chown -R $(whoami) /usr/local/lib/node_modules`：

```bash
# 直接装主线最新 Node（若装 keg-only 的 node@24，记得把 /opt/homebrew/opt/node@24/bin 加进 ~/.zshrc 的 PATH）
brew install node
node -v && node -p process.arch   # M 系列芯片这里应打出 arm64

npm install -g openclaw
# npm 11.16+ 或 12+ 若拦截安装脚本，改用：npm install -g openclaw@latest --allow-scripts=openclaw
openclaw --version
```

要是你平时习惯拿 `nvm` 管多版本 Node，注意 `nvm` 官方文档明确说了不支持也不推荐 `brew install nvm`，直接跑 [`nvm-sh/nvm` 官方脚本](https://github.com/nvm-sh/nvm)后敲 `nvm install 26 && nvm alias default 26`（或 `24.22.1+` 及以上版本）就好。在 M 系列芯片上它会自动拉原生 `arm64` 编译包，根本不存在某些文章臆造出来的 `--arch=arm64` 参数。

手动装好全局包之后，敲下面这行进交互式向导（旧教程写的 `openclaw init` 根本不是有效命令），顺手让它把 macOS 的后台 `LaunchAgent` 服务一并装好：

```bash
openclaw onboard --install-daemon
```

## 0x01 配密钥、挂代理与接本地 Ollama 模型

配模型之前先把两条铁律焊在脑子里：主配置文件叫 `~/.openclaw/openclaw.json`（不是 `config.json`）；而且打死别把任何 API Key 写进 `~/.openclaw/workspace/TOOLS.md`！`TOOLS.md` 是喂给大模型读的工作区上下文提示词，密钥写进去既不会被当成配置加载，还会随着每一轮对话原封不动发给云端模型。正规做法是敲 `openclaw configure` 录入，或者写进 `~/.openclaw/.env` 后随手 `chmod 600 ~/.openclaw/.env ~/.openclaw/openclaw.json`。

国内网络连海外接口超时的话，在 `~/.zshrc` 里挂上本地代理并把回环地址排掉。测网络通不通的时候，直接 `curl` 你实际要用的模型服务商地址（比如 `curl -x http://127.0.0.1:7890 -I https://api.openai.com/v1/models` 或阿里云百炼 `https://dashscope.aliyuncs.com`），别跟着某些串台教程去 `curl` 币安接口，人家对不少地区 IP 直接回 `451`/`403`，白白误导排查方向：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,::1
export NODE_USE_ENV_PROXY=1
```

如果想借 M 系列芯片的统一内存配一套本地 Ollama 离线模型玩玩，留意别在 Mac 上敲那行 `curl -fsSL https://ollama.com/install.sh | sh`，Ollama 官方那个脚本只认 Linux，在 macOS 上跑会直接报错退出。Mac 上要么去官网拖 `Ollama.app`，要么直接用 Homebrew：

```bash
brew install ollama
brew services start ollama

# 默认的 qwen2.5:7b 标签本身就是均衡度更好的 Q4_K_M 量化且自动走 Apple Metal 加速，犯不着去拉精度更糙的 q4_0
ollama pull qwen2.5:7b
curl -s http://127.0.0.1:11434/api/tags
```

确认本地 `11434` 端口通了，跑 `openclaw onboard` 或 `openclaw configure` 把本地 Ollama 原生地址 `http://127.0.0.1:11434`（注意末尾别加 `/v1`，走原生口才能正常兼容工具调用）加进 `~/.openclaw/openclaw.json` 的 `models.providers` 底下就行。不过丑话说在前面：`7b` 这种小体量本地模型用来日常闲聊还行，一旦让 Agent 连续调多步文件与终端工具，受限于上下文窗口和函数调用能力，翻车率比前沿云端大模型高得多。

## 0x02 `LaunchAgent` 开机自启的三个常见雷区

只要前面跑过 `openclaw onboard --install-daemon` 或 `openclaw gateway install`，官方 CLI 其实已经在 `~/Library/LaunchAgents/ai.openclaw.gateway.plist` 帮你生成好了合规的服务文件，平时用 `openclaw gateway status|restart|stop` 就能管得妥妥帖帖。

如果你因为定制环境变量想自己手写一份 `~/Library/LaunchAgents/com.openclaw.gateway.plist`，动手前先敲 `openclaw gateway uninstall` 把官方自动注册的那份 `ai.openclaw.gateway` 卸掉（免得两份 `KeepAlive` 任务同时抢 `18789` 端口死循环），然后绕开老文章常犯的三个错：第一，Apple Silicon 上 Homebrew 装出来的 `node` 和 `openclaw` 在 `/opt/homebrew/bin` 下，不在 `/usr/local/bin`（走 `nvm` 安装的则替换成 `which node` 和 `which openclaw` 打出的实际绝对路径）；第二，`launchd` 默认只认 `/usr/bin:/bin:/usr/sbin:/sbin` 这几个系统目录，不在 `EnvironmentVariables` 里把对应的 `bin` 目录补进 `PATH` 的话，脚本开头的 `#!/usr/bin/env node` 直接抓瞎；第三，启动子命令最后一项必须写前台常驻的 `run`（也就是 `openclaw gateway run`），写成 `start` 调完就会立刻退出，配上 `KeepAlive=true` 当场变成死循环重拉：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/node</string>
        <string>/opt/homebrew/bin/openclaw</string>
        <string>gateway</string>
        <string>run</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/你的用户名/.openclaw/workspace</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw-launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw-launchd.err.log</string>
</dict>
</plist>
```

在如今的 macOS 上加载用户服务，也别再用早就淘汰的 `launchctl load` 了，改用现代的 `bootstrap` 和 `kickstart` 子命令：

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.gateway.plist
launchctl kickstart -k gui/$(id -u)/com.openclaw.gateway
```

## 0x03 连通验收与日志路径（别动 `workspace/memory`！）

配完敲下面几行验一下成色：

```bash
openclaw gateway status
# 发一条单轮测试指令验证模型回复（别敲成往聊天软件发通知的 openclaw message send）
openclaw agent --message "你好，只回复 OK 两个字母即可"

# 进终端聊天界面，或拉起本地浏览器面板（默认绑在 127.0.0.1:18789）
openclaw tui
# 或：openclaw dashboard
```

要是启动时报 `18789` 端口被占，敲 `lsof -i :18789` 揪出撞车的进程，或者去 `~/.openclaw/openclaw.json` 里把 `gateway.port` 改成别的空闲端口（临时跑也可以直接敲 `openclaw gateway --port 18790`）。至于有些文章在 Mac 排错里写"内存不够就手动加 Swap"，纯属把 Linux 经验硬搬过来了：macOS 的交换空间全由系统内核在 `/private/var/vm` 下自动动态管理，根本不用也没法像 Linux 那样手搓 `/swapfile`，8G 内存吃紧时少开几个浏览器标签页或者卸掉不用的 Ollama 本地模型（`ollama rm <模型名>`）最管用。

最后再叮嘱一遍日志位置：`~/.openclaw/workspace/memory/` 目录里装的全是 Agent 的长期记忆 Markdown 文件，压根不是系统日志！看实时运行日志直接敲 `openclaw logs --follow`（新版真实日志文件按天落在 `~/.openclaw/logs/` 底下，旧版本在 `/tmp/openclaw/`，以 `openclaw logs` 输出路径为准），千万别往 `workspace/memory` 目录跑任何定时删除脚本。更多配置项可随时查 [OpenClaw 官方文档](https://docs.openclaw.ai/zh-CN/install) 与 [GitHub 仓库](https://github.com/openclaw/openclaw)。
