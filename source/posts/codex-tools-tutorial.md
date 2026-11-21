---
title: "Codex Tools 桌面端折腾记录：多账号切号、本地反代与 Cursor 连通踩坑"
date: 2026-03-26T11:35:00+00:00
lastmod: 2026-03-26T11:35:00+00:00
categories: ["AI 工具", "技术教程"]
tags: ["Codex", "Codex Tools", "API 反代", "Tauri", "多账号管理"]
draft: false
description: "梳理开源桌面工具 170-carry/codex-tools 的安装打包、四类账号导入、窗口百分比看板与本地 /v1 反代用法，纠正乱关 macOS Gatekeeper 和在 Cursor 里直填 127.0.0.1 等常见误区。"
weight: 10
---

手里同时备了两三个 ChatGPT 订阅号轮换写代码的人，来回退登 Codex 桌面端是一件挺折磨人的事。[`170-carry/codex-tools`](https://github.com/170-carry/codex-tools)（MIT 开源，React + Rust Tauri 写的跨平台桌面小工具）干的就是这个脏活：把多个账号的登录态集中管起来，一眼看清每个号在 5 小时和 1 周窗口里消耗了百分之多少配额，点一下自动换号重开 Codex，顺带还能在本地起一个兼容 OpenAI 格式的 `/v1` 反代服务。

这篇记录最初是基于 `v1.5.4`（经历过 `v1.0.0` 重构 Tauri、`v1.4.0` 加自定义 Codex 路径、`v1.5.0` 重做 OAuth 与导入逻辑之后的一版）实测整理的，眼下上游 [Releases](https://github.com/170-carry/codex-tools/releases) 已经一路迭代到了 `v3.x`，安装包名字和细节以仓库最新挂出来的为准。动手前照例先把话挑明：软件完全免费开源，别去买任何收费倒卖包；另外把多个个人订阅号塞进池子里对外开共享反代，在 OpenAI 服务条款里妥妥算账号共享与规避单号限流，自己本机切号图个方便还行，千万别拿去开公共接口。

## 0x00 安装与源码打包（别一上来就关 macOS 全局 Gatekeeper）

平时自用压根不需要配前端和 Rust 编译链，直接去 [GitHub Releases](https://github.com/170-carry/codex-tools/releases) 下预编译好的桌面包就行。macOS 上 Apple Silicon（M 系列芯片）选 `Codex.Tools_<版本号>_aarch64.dmg`，Intel 芯片选 `Codex.Tools_<版本号>_x64.dmg`（页面里带 `.app.tar.gz` 后缀的是给应用内自动更新用的增量包，手动装选 `.dmg`）；Windows 64 位选 `Codex.Tools_<版本号>_x64-setup.exe`（NSIS 安装包）或者 `Codex.Tools_<版本号>_x64_en-US.msi`（注意官方并没有发过什么 Windows `.zip` 免安装包，也暂不支持 Linux 桌面端）。

这里必须重点纠正一个在中文教程圈流毒甚广的 macOS 排错命令。因为个人开源构建没交苹果开发者年费做公证，把 `Codex Tools.app` 拖进 `/Applications` 第一次双击时，系统常会弹"已损坏，无法打开"。很多教程张口就让人敲 `sudo spctl --master-disable` 把整台 Mac 的 Gatekeeper 安全防线彻底卸掉。千万别敲那一行！为了开一个小工具把系统对所有未知来路木马的拦截全关了纯属因噎废食，而且在 macOS 15 Sequoia 及更新系统上苹果也早就收紧了这道口子。你只需要单独摘掉这一个 App 身上的下载隔离扩展属性就够了：

```bash
xattr -dr com.apple.quarantine "/Applications/Codex Tools.app"
```

敲完再双击就能正常打开（或者去"系统设置 -> 隐私与安全性"底部点一次"仍要打开"）。至于 Windows 上要是装完双击闪退，也别信网上偏方去点什么"右键以管理员身份运行"：一个肚子里装着你全部账号明文 Token 的桌面程序没道理拿最高管理员权限跑，Tauri 应用在 Windows 上闪退九成是系统缺了底层的 Microsoft Edge WebView2 Runtime，补装一下官方 WebView2 运行时再看日志就能解决。

如果你打算自己拉源码改点功能或者亲手编译打包，先备好 Node.js 22 LTS（早年的 Node 20 已在 2026 年 4 月底结束维护；macOS 上如果用 `brew install node@22` 装这类 keg-only 版本公式，装完记得按提示把 `/opt/homebrew/opt/node@22/bin` 写进 `PATH` 或手动 `brew link`，不然敲 `node -v` 还是找不着）、Rust stable 工具链以及 `pnpm`：

```bash
mkdir -p ~/src && cd ~/src
git clone https://github.com/170-carry/codex-tools.git
cd codex-tools

pnpm install

# 开发模式启动（带前端热重载与控制台日志）
pnpm run tauri dev

# 正式编译打包（首次编 Rust 依赖大概五到十五分钟）
pnpm run tauri build
```

编完之后去产物目录捞安装包：macOS 落在 `src-tauri/target/release/bundle/dmg/` 和 `bundle/macos/` 下；Windows 则落在 `src-tauri\target\release\bundle\nsis\`（生成 `-setup.exe`）和 `bundle\msi\` 底下（有些老文章写成 `bundle\app\`，Windows 版 Tauri 压根没那个目录）。

## 0x01 四种账号导入方式、窗口百分比与编辑器联动

打开软件，底部导航栏清清爽爽就四块：`账号管理`、`API 反代`、`设置`、`关于`，平时也可以缩到状态栏菜单后台驻留。

点"账号管理 -> + 添加账号"，工具给了四条导入路子。如果你本机正好已经登着 Codex 桌面端，直接选"同步当前登录"最省事，它会把当前机器上的登录态直接读进来存好，不会冲掉你正在干的活；想加第二个、第三个号，选"OAuth 登录"，浏览器弹出来走完登录授权会自动跳回应用落库；要是你手里已经有以前导出来的备份文件，可以用"导入 JSON 文件"选单个或多个 `.json`，或者干脆选"读取文件夹"把整个目录里的账号文件一口气扫进来。导入时识别的 JSON 结构长这样：

```json
{
  "label": "主力工作号",
  "account_id": "acct_xxxxxxxx",
  "auth_json": {
    "access_token": "...",
    "refresh_token": "...",
    "session_token": "..."
  },
  "plan_type": "plus"
}
```

要是导入 JSON 报错，先查文件是不是标准 UTF-8 编码、里面有没有漏掉核心的 `access_token` 和 `account_id`。同时这里必须敲个警钟：从工具里导出备份的这些 JSON 文件里，明文躺着完整的 `access_token`、`refresh_token` 和 `session_token`！外人只要拿到这个文件，连你的密码和二步验证都不用问就能直接接管会话。导出来的备份文件务必立刻 `chmod 600` 收紧权限塞进加密盘里，打死别扔进网盘同步目录或者顺手提交进代码仓库。

账号进列表之后点一下"刷新"（也可以去设置里把"用量自动刷新"打开，默认 30 分钟刷一次，号多的话调成 1 小时更省心），每个号底下会列出计划类型（Free / Plus / Business / Pro）以及 `5h`、`1w` 两栏数字。注意这两栏显示的是当前 5 小时滚动窗口和 7 天周期内的已用配额百分比（`%`）及重置时刻，早年有些教程把它们硬翻译成"过去 5 小时用了几小时时长"，纯属外行看数字瞎猜。点一下用量列标题就能按剩余额度高低排序，挑余量最宽裕的号点"启动 Codex"，工具就会替你切好本机凭据并自动拉起 Codex 桌面端（要是你装在了非默认位置，可以在设置里改自定义 Codex 路径，找不到桌面包时它也会尝试回退调 `codex app`）。

设置页里还有两个很顺手的联动开关：一个是"切换账号后重启编辑器"，勾上之后切号时会自动帮你重开 VS Code 等关联编辑器让新凭据生效；另一个是"同步 Opencode 授权"，如果你平时同时在用 Opencode 和 Codex 两套工具，打开之后切一次号两边认证一块儿跟着换，省得两边各改一遍。

## 0x02 本地 `/v1` 反代与"Cursor 连不上 `127.0.0.1`"的经典坑

切到底部的 `API 反代` 标签页，填好端口（默认 `8787`，可以在设置里设成固定端口、固定密钥，甚至勾上随应用启动自动拉起反代），点一下启动，本机就多了一个按账号余量自动挑号转发的 OpenAI 兼容网关，默认地址是 `http://127.0.0.1:8787/v1`。详细协议说明也可以直接翻仓库里的 [`docs/api-proxy.md`](https://github.com/170-carry/codex-tools/blob/main/docs/api-proxy.md)。

这套本地网关一共暴露了四个常用端点：`GET /health` 做存活检查，`GET /v1/models` 拉可用模型清单，`POST /v1/chat/completions` 接传统对话补全，`POST /v1/responses` 接新版 Responses 协议。

在往第三方客户端里填地址之前，有两个十个人里八个人会栽跟头的坑。

第一个坑是模型名字别闭着眼睛瞎填 `gpt-4`。Codex 订阅上游跑的是 Codex 专用模型栈（比如 `gpt-5.x-codex` 系列），压根不认老掉牙的 `gpt-4`（除非反代自己做了别名映射，而且在不少 IDE 里填 `gpt-4` 还会跟软件内置模型名打架）。最稳的做法是反代启动后先敲两行 `curl` 探一下存活和真实模型列表，`/v1/models` 吐出来什么名字，你就往客户端里填什么名字：

```bash
# 1. 探一眼本地反代活没活着
curl -s http://127.0.0.1:8787/health

# 2. 查当前上游实际支持的模型 ID 列表（记得把 sk-xxxx 换成你在界面设的强密钥）
curl -s http://127.0.0.1:8787/v1/models \
  -H "Authorization: Bearer sk-xxxx"
```

拿到真实模型名之后，测一把 `chat/completions` 或 `responses` 能正常回话就算通了：

```bash
# 兼容 Chat Completions 调用
curl -s http://127.0.0.1:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-xxxx" \
  -d '{
    "model": "填入上面 /v1/models 返回的真实模型名",
    "messages": [{"role": "user", "content": "用一句话解释 Rust 的所有权"}]
  }'

# 原生 Responses 接口调用
curl -s http://127.0.0.1:8787/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-xxxx" \
  -d '{
    "model": "填入上面 /v1/models 返回的真实模型名",
    "input": "写一个最小的无锁计数器示意"
  }'
```

第二个大坑在 Cursor 上。很多教程手把手教大家打开 Cursor Settings -> Models，勾上 `Override OpenAI Base URL` 然后填进 `http://127.0.0.1:8787/v1`，结果一发消息全报错。原因一点不复杂：像 VS Code 里的 Continue、Cline、Roo Code 插件或者你自己写的本地 CLI 脚本，HTTP 请求是从你面前的这台电脑直接发出去的，连 `127.0.0.1:8787` 丝滑无比；唯独 Cursor 的自定义 OpenAI 接口请求，是先发回 Cursor 自家的远端云服务器，再由 Cursor 云端替你去连那个 Base URL。人家的云服务器怎么可能连得上你本机的 `127.0.0.1` 回环地址？所以在本地写代码想接这套反代，直接配给 Continue 或 Cline 这类纯本地直连插件最省心。

## 0x03 开 `cloudflared` 公网隧道前先把安全账算清

正是为了喂给 Cursor 云端或者出门在外拿别的设备连回家，`API 反代` 页面里直接集成了 `cloudflared`（可选走 HTTP/2 协议），支持一键拉起临时的快速隧道（Quick Tunnel，吐出一个 `https://xxx.trycloudflare.com` 公网地址）以及绑自己域名的持久命名隧道（Named Tunnel）。

真打算点下"启动隧道"把本地端口捅到公网上之前，千万把下面两件事想明白。

第一，免费的临时快速隧道（`trycloudflare.com`）压根没有所谓的"设置 IP 白名单"功能！有些文章嘴上劝你开了快速隧道去配 IP 白名单，纯属没用过瞎支招。一旦公网地址通了，全靠你设的那串本地 `sk-...` 密钥拦门，所以开隧道前必须先把反代 API Key 换成足够长的随机高熵字符串，用完随手关掉隧道。

第二，如果真有长期跨设备自用的刚需，别偷懒用临时隧道，老老实实绑自己的域名配 Named Tunnel，在 Cloudflare Zero Trust 后台叠一层 Cloudflare Access 策略（比如 Service Token 或邮箱验证码准入），把陌生扫描流量挡在边缘节点外头。要是碰到启动反代时报 `8787` 端口被占，macOS 下敲 `lsof -i :8787`、Windows 下敲 `netstat -ano | findstr :8787` 揪出撞车的进程，或者在设置里换个冷门端口固定住就完事了。遇到新版本的 Bug 可以去仓库的 [Issues](https://github.com/170-carry/codex-tools/issues) 或 [`changelog.md`](https://github.com/170-carry/codex-tools/blob/main/changelog.md) 翻最新动态。
