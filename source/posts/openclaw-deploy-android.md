---
title: "在 Android 手机 Termux 里硬跑 OpenClaw：原生依赖编译与幽灵进程被杀排查"
date: 2026-03-03T16:15:00+08:00
draft: false
categories: ["OpenClaw", "部署教程"]
tags: ["OpenClaw", "Android", "Termux", "移动端折腾"]
description: "记录在 Android Termux 环境下编译运行 OpenClaw 网关的折腾步骤：补齐 build-essential 原生编译链、解除 Android 12+ 幽灵进程限制（signal 9）与正确的前台保活方式。"
weight: 10
---

先把预期摆正：按 OpenClaw 官方的设计定位，Android 手机原本是作为轻量伴侣节点（Companion Node App）去配对连接你电脑或云服务器上跑着的 Gateway 网关的；直接在手机 Termux 里硬拉整套 Node.js 网关，属于非官方支持的极客折腾玩法。如果你手头有闲置小鸡或电脑，优先看同系列的 [Linux 服务器篇](/posts/openclaw-deploy-linux/)、[macOS 篇](/posts/openclaw-deploy-macos/) 或 [Windows 11 篇](/posts/openclaw-deploy-windows/)。

非要在手机里跑一趟的话，拦路虎主要有两个：一是 Android 底层用的是 Bionic libc，跟常规桌面 Linux 的 glibc 不兼容，不少 npm 原生扩展包没法直接用预编译二进制，必须在手机上当场编译；二是 Android 12 之后引入的后台幽灵进程杀手（Phantom Process Killer），照搬普通 Linux 教程跑不了几分钟就会突然吃一个 `[Process completed (signal 9)]` 暴毙。手头正好有台 8GB 内存的闲置安卓机，实测把整条链路踩平了一遍，顺手记一笔。

## 0x00 装同一渠道签名的 Termux 与原生编译链

下载 Termux 时有个新变化得交代清楚：以前老教程总说"Google Play 版停止更新了千万别下"，其实从 2024 年起官方已经在 Play 商店恢复了新版构建推送，真正推荐大家优先从 [F-Droid](https://f-droid.org/packages/com.termux/) 或 [Termux GitHub Releases](https://github.com/termux/termux-app/releases) 下的原因是插件签名兼容性。Play 版和 F-Droid 版用的是两套不同的签名密钥，如果你后面还要装调系统接口的 `Termux:API` 或者放桌面一键脚本的 `Termux:Widget`，主程序和所有附加组件必须出自同一个下载渠道，混装会因为签名冲突直接装不进去。

打开 Termux 先刷一遍软件源，然后把主线 Node.js 和 C/C++ 编译工具链一次性装齐。注意两个细节：一是 Termux 仓库里根本没有某些教程瞎写的 `build-tools` 这个包，真正的编译元包叫 `build-essential`（顺手带上 `binutils` 和 `python` 给 `node-gyp` 编译原生模块用）；二是当前新版 OpenClaw 要求 Node.js `>=24.16.0 <25 || >=26.1.0`，直接装跟进较快的主线 `nodejs` 包（别装可能滞后的 `nodejs-lts`），装完敲 `node -v` 核对一眼版本号：

```bash
termux-setup-storage
pkg update && pkg upgrade -y

pkg install -y nodejs python build-essential binutils git curl wget openssh
node -v   # 确认满足 v24.22.1+ 或 v26+
```

如果手机处在需要代理的网络环境，先确保手机上的代理客户端（比如 Clash Meta for Android，默认本地混合端口 `7890`）已经在后台跑起来了，再在 Termux 当前会话里挂好环境变量装全局包：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export NO_PROXY=localhost,127.0.0.1,::1
export NODE_USE_ENV_PROXY=1

npm install -g openclaw
# npm 11.16+ 或 12+ 若拦截安装脚本，改用：npm install -g openclaw@latest --allow-scripts=openclaw
openclaw --version
```

装完初始化直接敲 `openclaw onboard`（老文章写的 `openclaw init` 并不存在；而且在手机上别加 `--install-daemon`，Android 里既没有 `systemd` 也没有 `launchd`，传了也没法注册系统服务）：

```bash
openclaw onboard
```

跟桌面端一样，密钥老老实实走交互向导或写进 `~/.openclaw/.env`（配置落在 `~/.openclaw/openclaw.json`），别往 `workspace/TOOLS.md` 里塞。

## 0x01 解开三道保活紧箍咒：唤醒锁、电池无限制与幽灵进程上限

在安卓机上跑常驻服务，光写个脚本丢后台连息屏五分钟都撑不过去，必须把三处限制挨个解开。

第一处是拿住 Termux 的唤醒锁（Wakelock）。很多文章让你去"Termux 设置界面"里翻这个开关，其实根本不在那儿：要么下拉手机系统通知栏，在 Termux 那条常驻通知上点一下 `Acquire wakelock` 按钮，要么直接在终端里敲一行命令 `termux-wake-lock`。

第二处是在 Android 系统设置里给 Termux 松绑电池策略：进"系统设置 -> 应用 -> Termux -> 电池（或省电策略）"，把它改成"无限制（Unrestricted）"，允许息屏后继续用网和跑 CPU。

第三处最关键，专门治莫名其妙弹出来的 `signal 9` 强杀。Android 12 起默认限制全系统后台最多只能同时挂 32 个幽灵子进程，Node 网关再拉几个工具子进程分分钟撞线。如果你的手机已经是 Android 14 及以上版本，直接进系统"开发者选项"，往下翻找到"停用子进程限制（Disable child process restrictions）"把开关拨开就完事了；要是停在 Android 12 或 13，插上电脑用 `adb` 敲下面两行把上限拉满：

```bash
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
```

## 0x02 用 `tmux` 挂前台 `gateway run` 与桌面快捷小组件

因为 Termux 默认没有跑系统级服务管理器，直接敲 `openclaw gateway start` 是起不来守护进程的。最省心的土办法是装个 `tmux`，在持久会话里跑前台阻塞的 `openclaw gateway run`（或者你熟悉 `runit` 的话也可以装 `termux-services` 用 `sv` 管）：

```bash
pkg install -y tmux
termux-wake-lock

tmux new -s claw
openclaw gateway run
# 跑稳后按 Ctrl+B 松手再按 D 挂回后台；下次敲 tmux attach -t claw 随时切回来看输出
```

如果你想在手机主屏幕上摆一个点一下就拉起网关的图标，光在家目录写个普通 `.sh` 脚本是没用的，得配合同渠道安装的 `Termux:Widget` 应用，并且把启动脚本严格放进 `~/.shortcuts/` 目录底下：

```bash
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/start-openclaw.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
tmux has-session -t claw 2>/dev/null || tmux new-session -d -s claw 'openclaw gateway run'
EOF
chmod +x ~/.shortcuts/start-openclaw.sh
```

回手机桌面长按添加 `Termux:Widget` 小组件，就能看到 `start-openclaw.sh` 躺在列表里了。

## 0x03 连通测试、频道告警语法与存储清理

新开一个 Termux 终端窗口，先跑一条单轮 Agent 指令看模型能不能正常回话（再次提醒别敲成 `openclaw message send`，那个是发频道通知用的）：

```bash
openclaw gateway status
openclaw agent --message "Hello from Termux, reply OK only."
```

要是你想把这台闲置手机当成一个低功耗本地探针，定时探一下远端服务器活没活着、异常时往自己的 Telegram 推条消息，注意两件事：一是从手机 SSH 连远端服务器管机器时，用普通用户加公钥认证（`ssh user@your-server`），别在手机脚本里绑服务器 `root`；二是 `openclaw message send` 正确的传参写法是 `--channel` 指定通道类型、`--target` 填具体的数字会话 `chat_id`（前提是在 `openclaw.json` 里已经配好了对应的 Telegram Bot）：

```bash
cat > ~/check-server.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
if ! curl -fsS --max-time 10 https://blog.caowo.de/ >/dev/null; then
    openclaw message send --channel telegram --target "你的_Chat_ID" --message "告警：博客站点探测超时"
fi
EOF
chmod +x ~/check-server.sh
```

装好同渠道的 `Termux:API` 安卓客户端并 `pkg install -y termux-api` 之后，就能用系统的 JobScheduler 每隔两小时（`7200000` 毫秒，Android 规定最短间隔不能低于 15 分钟）调一次这个巡检脚本：

```bash
termux-job-scheduler --script ~/check-server.sh --period-ms 7200000
```

跑一阵子觉得手机空间紧了，敲 `pkg clean && npm cache clean --force` 清掉残留包缓存；想看 Termux 到底吃了多少闪存，敲 `du -sh $PREFIX ~` 才准（`~/.termux` 目录里只装了几 KB 的终端配色和按键配置，真正的几十个 G 全在 `$PREFIX` 和家目录底下）。
