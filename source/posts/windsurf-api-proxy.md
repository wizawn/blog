---
title: "拆出 Windsurf 的 Language Server 做本地 API 反代：部署步骤与进程残留坑"
description: "梳理开源项目 dwgx/WindsurfAPI 的运行机制与部署细节：从安装包提取并校验二进制、配置强制 API_KEY 鉴权与单账号代理，到清理 42100 端口孤儿进程。"
date: 2026-04-19T14:45:00+08:00
draft: false
categories: ["AI 工具", "技术教程"]
tags: ["Windsurf", "API 代理", "Node.js", "开源工具"]
weight: 10
---

Windsurf（早年叫 Codeium）桌面端跟自家模型后端通信，编辑器界面本身并不直接发 HTTP 请求，全靠底下常驻的一个本地 `Language Server` 二进制进程走 gRPC 转发。

GitHub 上的 [`dwgx/WindsurfAPI`](https://github.com/dwgx/WindsurfAPI) 干了一件挺巧的事：只用 Node.js 原生内置模块（`http`、`fs`、`path`，配置全读 `process.env`，连内部 gRPC/protobuf 帧封装都是手搓的，全程零第三方 `npm` 包依赖，显著缩小了 `npm` 供应链投毒面）包了一层壳。它在本地拉起 `42100` 端口的 `Language Server`，对外在 `3003` 端口翻译成兼容 OpenAI 格式的 `/v1/chat/completions` 和 `/v1/models` 接口，还顺带做了个 `/dashboard` 管理页管账号和出口代理。

这项目在 2026 年 4 月之后陆续收紧了不少安全默认值，外面早期文章抄的配置片段有很多已经跑不通（比如空密钥现在直接报 `401`）或者留着大敞口。这里按上游最新代码把部署步骤和容易踩的坑重新顺一遍。

## 0x00 先把开源协议、服务条款与额度真相拎清

动手敲命令之前，有几笔账别算糊涂了。

首先是许可证和服务条款的区别。`WindsurfAPI` 源码本身挂的是 MIT 协议，作者在 README 里另外写了一段不希望被拿去商用、转售或代部署收费的个人态度说明；MIT 在法律层面并不禁止商用，真正卡死红线的是 Windsurf 官方的服务条款。上游 README 也把话挑得很明：这工具只适合个人在非 IDE 场景下自用调试，如果把一堆账号塞进池子里搞跨用户共享或绕过单号配额，直接违反 Windsurf 服务条款，随时会吃封号。

其次别轻信什么"套了反代就变无限额度"的说法。不同等级的 Windsurf 账号能调动的模型本来就分档：免费号一般只能摸到 `gpt-4o-mini`、`gemini-2.5-flash` 这类基础轻量模型，想调 `claude-opus-4-7-max`、`claude-sonnet-4.6`、`gpt-5.4` 或 `kimi-2.5` 这些高阶模型，全看账号自身的 Pro 订阅权限，而且每次调用照常扣减账期内的 Prompt Credits 配额（具体额度规则以官方定价页为准）。另外虽然 Node 壳子零 `npm` 依赖，底下真正干活的 `language_server_linux_x64` 毕竟还是闭源二进制，提取时记得核对 SHA-256 摘要，别去来路不明的网盘下魔改包。

## 0x01 提取二进制与最小权限部署

上游现在要求 Node.js `22.13` 及以上版本（Node 20 已经在 2026 年 4 月底正式结束维护了）。

`Language Server` 二进制不包含在 Git 仓库里，得从官方渠道提取。最省心的路子是直接用仓库里带的 `install-ls.sh` 辅助脚本（支持 `--sha256` 校验哈希），或者从已经装好 Windsurf 的机器目录（Linux 下一般在 `/opt/Windsurf/resources/app/extensions/windsurf/bin/language_server_linux_x64`，下了官方 `.deb` 包的话也可以 `dpkg-deb -x` 解出来找同名文件）里拷过来。

平时尽量别拿 `root` 身份去跑一个手里攥着账号 Token 的常驻服务，把目录权限划给普通运行用户更稳当：

```bash
sudo mkdir -p /opt/windsurf/data/db
sudo chown -R "$USER:$USER" /opt/windsurf

git clone https://github.com/dwgx/WindsurfAPI.git /opt/windsurf/app
cd /opt/windsurf/app

# 用仓库自带脚本拉取并校验二进制（若已从官方 .deb 用 dpkg-deb -x 解出同名文件，也可传本地路径 bash install-ls.sh /path/to/language_server_linux_x64）
bash install-ls.sh
chmod +x /opt/windsurf/language_server_linux_x64
```

接着写 `.env` 配置文件。这里有个跟早先教程截然不同的变化：新版上游把空的 `API_KEY` 改成了默认拒绝（fail-closed），哪怕你从本机 `127.0.0.1` 发请求，`API_KEY` 留空也会当场吃 `401`。同时 `DASHBOARD_PASSWORD` 必须设成强密码，监听地址在云服务器上优先锁死 `127.0.0.1`（别随手敲 `ufw allow 3003/tcp` 把明文 HTTP 面板敞给全网）：

```bash
cat > /opt/windsurf/app/.env << 'EOF'
HOST=127.0.0.1
PORT=3003
API_KEY=sk-替换成你自己的高强度随机密钥
DEFAULT_MODEL=claude-sonnet-4.6
MAX_TOKENS=8192
LOG_LEVEL=info
LS_BINARY_PATH=/opt/windsurf/language_server_linux_x64
LS_DATA_DIR=/opt/windsurf/data
LS_PORT=42100
DASHBOARD_PASSWORD=替换成后台登录强口令
EOF

chmod 600 /opt/windsurf/app/.env
```

顺嘴提一句 `DEFAULT_MODEL`：上游现在的示例默认值是 `claude-sonnet-4.6`，填的时候得确保这个型号名在模型列表里真实存在且你导入的账号有权限调，瞎填不认识的名字会直接回 `400 model_not_found`。配好后先在前台跑一把 `node src/index.js` 看看有没有报错。

## 0x02 导号、配代理与 SDK 联调

服务跑起来之后，本地开条 SSH 隧道（`ssh -L 3003:127.0.0.1:3003 user@server`）就能在浏览器打开 `http://127.0.0.1:3003/dashboard` 输密码进后台。导号有两条路子：要么直接在 `/dashboard` 页面上走 Google / GitHub OAuth 或邮箱密码一键登录入池；要么在已登录官方站点的浏览器里打开 `https://windsurf.com/show-auth-token` 拷出自己的 Token，在后台添加或直接发请求批量导进去（视上游版本鉴权要求带上后台会话或密钥）：

```bash
# 导入单个账号 Token
curl -X POST http://127.0.0.1:3003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"token": "你的_windsurf_token"}'

# 批量导入格式
curl -X POST http://127.0.0.1:3003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"accounts": [{"token": "token_1"}, {"token": "token_2"}]}'
```

如果部署机器连 Windsurf 官方后端需要挂代理，除了在 `/dashboard` 界面里点选，也能直接调接口配全局 HTTP 代理或者给某个账号单独绑一条 SOCKS5 出口：

```bash
# 配置全局 HTTP 代理
curl -X POST http://127.0.0.1:3003/proxy/config \
  -H "Content-Type: application/json" \
  -d '{"type": "http", "host": "127.0.0.1", "port": 7890}'

# 给指定编号的账号单独绑 SOCKS5 代理
curl -X POST http://127.0.0.1:3003/account/1/proxy \
  -H "Content-Type: application/json" \
  -d '{"type": "socks5", "host": "127.0.0.1", "port": 1080}'
```

测试对话接口的时候，切记请求头里一定要带上 `.env` 里配的那串 `API_KEY`（老教程全漏了 `Authorization` 头，跑起来一片 `401`）。拿不准模型 ID 叫啥，先 `GET /v1/models` 查一遍清单再调：

```bash
curl -s http://127.0.0.1:3003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-替换成你自己的高强度随机密钥" \
  -d '{
    "model": "claude-sonnet-4.6",
    "messages": [{"role": "user", "content": "用一句话解释 gRPC 和 REST 的区别"}],
    "stream": false
  }'
```

接进 Python 的 OpenAI 官方 SDK、LangChain 或 LlamaIndex 也是一模一样的改法，把 `base_url` 和 `api_key` 对齐就行：

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-替换成你自己的高强度随机密钥",
    base_url="http://127.0.0.1:3003/v1",
)

resp = client.chat.completions.create(
    model="claude-sonnet-4.6",
    messages=[{"role": "user", "content": "写一个极简的 Node.js HTTP 健康检查路由"}],
)
print(resp.choices[0].message.content)
```

## 0x03 PM2 守护与 `42100` 端口孤儿进程清理

首次用 PM2 托管后台常驻时，先装好 PM2 并配好开机自启（跑完 `pm2 startup` 记得按终端打印出来的提示把那行 `sudo env ...` 命令复制执行一遍）：

```bash
npm install -g pm2
pm2 start /opt/windsurf/app/src/index.js --name windsurf-api --cwd /opt/windsurf/app
pm2 save
pm2 startup
```

后面日常更新配置或重拉服务时，有个必踩的坑：千万别直接敲一句 `pm2 restart windsurf-api` 就走人。

因为整套服务分两层进程，Node 主进程监听 `3003`，底下还拉起了一个或多个（按单账号代理拆分实例时可能不止一个）监听 `42100` 起步端口的 `language_server_linux_x64` 子进程。直接 `pm2 restart` 很容易让旧的 `language_server` 脱离父进程变成孤儿进程（注意这是还在后台活蹦乱跳占着端口的 orphan 孤儿进程，不是已经退出没收尸的 zombie 僵尸进程）。不少老文章（甚至连仓库自带的 `update.sh` 脚本）都只清了 `3003` 端口，漏掉了底下的 `language_server` 子进程。

稳妥的重启姿势是停掉 PM2 任务后，把 `3003`、`42100` 端口以及当前运行用户名下残留的 `language_server_linux_x64` 进程一块儿清干净（Debian / Ubuntu 缺 `fuser` 命令的话先 `sudo apt install -y psmisc`；如果跑了 `bash update.sh` 拉新代码，跑完也建议补敲一次清理）：

```bash
pm2 stop windsurf-api
pm2 delete windsurf-api

# 连同残留的 Language Server 孤儿进程一并清理
fuser -k 3003/tcp 42100/tcp 2>/dev/null || true
pkill -u "$USER" -f language_server_linux_x64 || true
sleep 2

pm2 start /opt/windsurf/app/src/index.js --name windsurf-api --cwd /opt/windsurf/app
pm2 save
```

真有跨网远程调用需求的话，老老实实在前面挡一层带 HTTPS 证书的 Nginx 或 Caddy 反代，别让明文 Token 在公网上裸奔。
