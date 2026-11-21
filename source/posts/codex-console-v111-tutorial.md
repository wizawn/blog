---
title: "Codex Console 部署与排坑记录：源码运行、Docker 映射与安全配置"
date: 2026-03-26T09:15:00+00:00
lastmod: 2026-03-26T09:30:00+00:00
categories: ["AI 工具", "技术教程"]
tags: ["Codex", "Codex Console", "开源工具", "部署教程"]
draft: false
description: "整理开源项目 dou-jiang/codex-console（v1.1.1+）在本地与服务器上的部署流程，修正 /tmp 目录丢失、0.0.0.0 默认监听配弱口令、docker-compose 硬编码密码与 noVNC 端口裸奔等常见配置坑。"
weight: 10
---

[`dou-jiang/codex-console`](https://github.com/dou-jiang/codex-console) 是基于 [`cnlimiter/codex-manager`](https://github.com/cnlimiter/codex-manager) 二次维护的一套开源 Web 管理面板（MIT 协议，最初整理这篇记录时跑的是 `v1.1.1`，上游后续已迭代出 `v1.1.2` 及更新版本）。相比原版，它补上了 CloudMail 邮箱轮询取码、`newApi` / `oldApi` 导出对接、Codex 账号 JSON 导出回迁、CPA `proxy_url` 代理保存以及 Outlook 状态列展示，顺手还修了不同 Starlette 版本的模板渲染兼容、六位普通数字误判成验证码、Outlook 邮箱大小写识别错乱和并发验证卡死等一堆陈年小毛病。

在动手搭环境之前，先把丑话说在前面。第一，这项目从头到尾都是免费开源的，外面但凡改个标题拿去收费倒卖的直接绕道就行。第二，仓库依赖里带了 `playwright` 和批量自动化逻辑，拿工具搞批量自动注册或自动绑卡直接踩死在 OpenAI 服务条款的红线上，极易招来连坐封号，下面的部署笔记仅限在本地回环环境里学习研究它的 FastAPI + SQLAlchemy 工程实现，切勿拿去干违规滥用的活儿。

## 0x00 Python 3.11 与代理环境准备

这项目要求 Python `3.10` 及以上（平时直接装 `3.11` 或 `3.12` 最省事），外加 Git 和一个能稳当连上外网的本地 HTTP 代理。

在三类常见系统上装 Python 3.11 时各有各的小坑。Windows 10 / 11（64 位）直接去 [Python 官网](https://www.python.org/downloads/)下 64 位安装包，向导第一页底下那个 `Add Python to PATH` 千万记得勾上；如果想在 PowerShell 里看一眼系统版本，敲 `Get-ComputerInfo OsName,OsVersion` 最通吃，别抄英文教程里的 `systeminfo | findstr "OS Name"`，中文版 Windows 输出写的是"OS 名称"，那行命令敲下去半个字都筛不出来。

macOS 上用 Homebrew 跑完 `brew install python@3.11 git` 之后，注意终端里直接敲不带版本号的 `python3` 调出来的往往还是系统自带的 Xcode Command Line Tools 旧版本，后面建虚拟环境时老老实实指明 `python3.11` 最稳。

至于 Linux 服务器，直接选 Ubuntu 22.04+ 或 Debian 12+（早年的 Ubuntu 20.04 和 Debian 10 早就过了标准维护期，默认源里也没有现成的 `python3.11` 包；RHEL 8.8+ 或 Rocky / AlmaLinux 9+ 注意装 pip 时包名叫 `python3.11-pip`，别装成给系统老 Python 用的 `python3-pip`）：

```bash
# Ubuntu 22.04+ / Debian 12+
sudo apt update
sudo apt install -y git python3.11 python3.11-venv python3-pip

# RHEL 8.8+ / Rocky / AlmaLinux 9+
sudo dnf install -y git python3.11 python3.11-pip
```

开装依赖前先拿 `curl` 探一眼本地代理通不通（假设本机代理跑在 `127.0.0.1:7890`）：

```bash
curl -x http://127.0.0.1:7890 -I https://chatgpt.com
```

能痛快返回 HTTP 响应头再往下走，不然服务跑起来也是干卡着超时。

## 0x01 源码虚拟环境安装（千万别往 `/tmp` 里克隆）

见过不少抄来抄去的部署教程第一句就教人 `cd /tmp && git clone ...`，这习惯真是害人不浅：Linux 机器但凡重启一次，或者 macOS 跑一轮系统日常清理，`/tmp` 底下的目录连同你跑出来的默认 SQLite 数据库 `data/database.db` 和 `.env` 配置全会被清得渣都不剩。正经装软件就在自己的家目录 `~/apps` 或者 `/opt` 底下安家：

```bash
mkdir -p ~/apps && cd ~/apps
git clone https://github.com/dou-jiang/codex-console.git
cd codex-console

python3.11 -m venv .venv
source .venv/bin/activate
```

如果你在 Windows 的 PowerShell 里跑 `.venv\Scripts\Activate.ps1` 激活虚拟环境时撞上"在此系统上禁止运行脚本"的红字报错，只想在当前这一个终端窗口临时放行的话，把作用域设成 `-Scope Process` 就够了（网上爱抄的 `-Scope CurrentUser` 会永久改写当前用户的注册表策略，完全没必要）：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
# 若在传统 CMD 窗口下则直接运行：.venv\Scripts\activate.bat
```

进到虚拟环境（命令行前缀带 `(.venv)`）之后，把 `requirements.txt` 里的依赖装齐（里面主要是 FastAPI、Uvicorn、Pydantic v2、SQLAlchemy 2.x、`aiosqlite`、`psycopg[binary]>=3.1.18`、`curl_cffi` 和 `playwright`）。用传统 `pip` 或者更快的 `uv` 都行：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
# 网络拉包慢的话可以临时挂清华镜像：-i https://pypi.tuna.tsinghua.edu.cn/simple
# 或者装了 uv 的直接跑：uv pip install -r requirements.txt
```

平时如果只看后台管理代码、不碰浏览器自动化那一块，到这里依赖就已经齐活了；真需要拉起无头浏览器模块时，才需要额外下载几百兆的 Chromium 内核与系统图形库：

```bash
playwright install chromium
# Linux 服务器缺底层动态库时再补一句：
sudo $(which playwright) install-deps chromium
```

## 0x02 配 `.env` 的监听红线与 PostgreSQL v3 驱动说明

把仓库自带的环境变量模板拷一份出来改：

```bash
cp .env.example .env
```

打开 `.env` 填参数的时候，最要命的是监听地址和初始密码。上游代码默认就把监听地址设在 `0.0.0.0`，没配密码时回退的默认口令又是烂大街的 `admin123`，而不少教程还照着默认值原样留着直接往公网云服务器上跑。真这么干，不出半天后台里存的账号和 Token 就会被路过的扫描器洗劫一空。不管是本机还是远端服务器，一律建议把 `APP_HOST` 显式改成 `127.0.0.1` 回环口，启动前先把密码换成 16 位以上的随机强口令；人在外地要连服务器后台时，本地敲一条 `ssh -L 8000:127.0.0.1:8000 user@server` 走 SSH 隧道映射回来打开最稳当，或者老老实实在前面套一层带 HTTPS 证书的 Nginx 反代。

顺带提一嘴 PostgreSQL 连接串的细节：这项目装的是新一代的 `psycopg[binary]>=3.1.18`（即 psycopg 3），没装老的 `psycopg2`。虽然项目自身的配置加载函数会自动把 `postgresql://` 补全改写成 `postgresql+psycopg://`，但如果你把同一条连接串复用到自己写的外部 SQLAlchemy 备份或迁移脚本里，记得直接写全 `postgresql+psycopg://`，免得外部脚本默认去找不存在的 `psycopg2`。

整理后的一份干净 `.env` 示例：

```ini
# 仅监听本地回环口，拒绝公网明文裸奔
APP_HOST=127.0.0.1
APP_PORT=8000

# 启动前务必改成高强度随机口令，别留默认密码
APP_ACCESS_PASSWORD=请替换成16位以上随机强口令

# 默认走本地 SQLite（程序内部会将相对路径归一到项目目录下）
APP_DATABASE_URL=data/database.db

# 若切到外部 PostgreSQL，建议直接写全 +psycopg 驱动前缀
# APP_DATABASE_URL=postgresql+psycopg://user:password@127.0.0.1:5432/codex_console

# 出站代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

保存后顺手敲一句 `chmod 600 .env` 把配置文件权限收紧，然后启动 `webui.py`（命令行也支持临时传 `--host`、`--port`、`--access-password` 或 `--debug` 覆盖环境变量）：

```bash
python webui.py --host 127.0.0.1 --port 8000
```

看到终端打出就位提示就算跑通了，浏览器访问 `http://127.0.0.1:8000` 输密码就能进界面（`v1.1.1` 起如果默认端口被占，它会自动往后顺延找空端口并在终端打印实际端口）。

## 0x03 Docker Compose 部署与硬编码密码、`6080` 端口隐患

不想在宿主机折腾 Python 环境的话，也可以直接用仓库自带的 `docker-compose.yml`（需 Docker 20.10+ 与 Compose v2）。

这里有两处非常隐蔽的坑千万盯紧。第一，源码直接跑 `webui.py` 默认起在 `8000` 端口，而仓库里的 `docker-compose.yml` 固定把 WebUI 映射到了宿主机的 `1455` 端口（跟 Codex 本地 OAuth 回调常用的端口相同），同时还暴露了一个完全无密码（`x11vnc -nopw`）的 `6080` 端口给容器里的 `noVNC` 远程桌面画面用；第二，上游 `docker-compose.yml` 在 `environment:` 里直接写死了 `WEBUI_ACCESS_PASSWORD=admin123` 且没有挂载 `.env` 文件，如果你只改了外面的 `.env` 就敲 `up -d`，容器起来的密码依然是 `admin123`！

所以在云服务器上启动容器之前，务必先打开 `docker-compose.yml`，把 `WEBUI_ACCESS_PASSWORD=admin123` 改成你自己的强口令，再把 `ports` 全部加上回环前缀改成 `127.0.0.1:1455:1455` 和 `127.0.0.1:6080:6080`（防止 Docker 绕过 `ufw` 防火墙把管理口和无密码桌面捅到公网）：

```bash
# 先改好 docker-compose.yml 里的 WEBUI_ACCESS_PASSWORD 强口令与 127.0.0.1 端口绑定，再启动
docker compose up -d
docker compose logs -f

# 不用时停掉容器
docker compose down
```

## 0x04 两个高频启动问题速查

平时拉起服务最常碰见两件事。一是端口占用：`v1.1.1` 及之后版本遇到 `8000` 被占会自动往后找空端口（比如顺延到 `8001`），注意看一眼终端实际打出来的端口号，别一直守着旧端口刷页面；老版本报 `[Errno 98] Address already in use`（Windows 报 `[WinError 10048]`）或者你想固定死 `8000` 端口时，把占着端口的旧进程查出来关掉即可：

```bash
# Linux / macOS 查端口占用
lsof -i :8000

# Windows PowerShell / CMD 查占用 PID
netstat -ano | findstr :8000
```

二是 `pip install` 报 `Could not find a version that satisfies the requirement`。十次里有九次是因为当前激活的 Python 还是机器上的 `3.8` 或 `3.9` 老版本（装不上新版 `curl_cffi>=0.14.0`），敲 `python --version` 核对一眼版本、升级完 `pip` 再重装基本就过了。另外导出备份出来的账号 JSON 和 `data/database.db` 里全躺着明文令牌，平时备份记得加密收好，千万别手滑 `git add .` 推上公开仓库。
