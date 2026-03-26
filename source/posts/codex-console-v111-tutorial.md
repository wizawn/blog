---
title: "Codex Console v1.1.1 超详细保姆级教程 - 从零到一完整部署指南（2026 最新版）"
date: 2026-03-26T09:15:00+00:00
lastmod: 2026-03-26T09:30:00+00:00
categories: ["tech"]
tags: ["tutorial", "codex", "guide", "open-source", "step-by-step"]
draft: false
---

## 📋 前言

<div style="background: #fff5f5; border: 2px solid #ff6b6b; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
<strong style="color: #ff6b6b; font-size: 1.2em;">❤️ 写教程不易，如果对您有帮助，欢迎赞赏支持！</strong><br>
微信/支付宝收款码已在文章底部 👇
</div>

**这是一篇真正的零基础保姆级教程**，我会手把手带你从零开始，完整部署和使用 Codex Console v1.1.1——一款免费开源的 OpenAI/Codex 账号注册管理工具。

**本教程特点**：
- ✅ **完全从零开始**：假设你没有任何编程基础
- ✅ **每步都有命令**：直接复制粘贴即可执行
- ✅ **包含所有坑点**：把可能遇到的问题都提前说明
- ✅ **真实测试验证**：所有步骤都已实际测试通过
- ✅ **持续更新维护**：跟随项目版本同步更新

**项目信息**：
- **GitHub 仓库**：https://github.com/dou-jiang/codex-console
- **基于项目**：cnlimiter/codex-manager（修复增强版）
- **许可证**：MIT（免费开源）
- **当前版本**：v1.1.1

**购买与售后**：
- **微信**：`GOV-HACK`（添加请备注"兑换码购买"）
- **QQ**：`46333839`（工作日 9:00-18:00 在线）
- **闲鱼店铺**：[https://m.tb.cn/h.i7QE4Wd?tk=p30e5bSCPx2](https://m.tb.cn/h.i7QE4Wd?tk=p30e5bSCPx2)
- **商品**：Business Teams 席位/停车位拼车名额
- **售后支持**：微信/QQ/闲鱼私信均可联系

**商品海报**：

<img src="/images/codex-tm-poster.jpg" alt="Codex 拼车商品海报" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px;">

---

## ⚠️ 重要声明（必读）

### 1. 免费开源原则

**本项目永久免费开源**，任何付费版本均为倒卖行为！

- ❌ **禁止倒卖**：严禁倒卖本项目及相关衍生版本
- ❌ **禁止付费**：任何人向你收费提供本工具，请立即退款并举报
- ✅ **允许学习**：允许学习、研究、二次开发
- ✅ **允许分享**：允许分享给有需要的朋友

### 2. 合法使用提醒

- 请遵守 OpenAI 相关服务条款
- 严禁用于违规、滥用或非法用途
- 仅供学习、研究和技术交流使用
- 因使用本项目产生的风险和后果由使用者自行承担

### 3. 使用建议

- **新手建议**：先用小号测试，熟悉流程后再批量操作
- **时段选择**：避开北京时间 14:00 左右（美国午夜，封号高峰）
- **批量控制**：建议每批 10-50 个，不要一次性注册太多
- **数据备份**：定期导出账号数据，防止丢失

---

## 🎯 v1.1.1 版本更新内容

### 新增功能（5 项）

| 序号 | 功能 | 说明 |
|------|------|------|
| 1 | CloudMail 邮箱服务 | 完整支持服务注册、配置接入、邮件轮询、验证码提取 |
| 2 | newApi 上传支持 | 可配置选择不同导入目标类型（newApi/oldApi） |
| 3 | Codex 账号导出 | 导出的账号可直接用于登录、数据迁移、重新导入 |
| 4 | CPA proxy_url 支持 | CPA 服务配置中可直接保存并使用代理地址 |
| 5 | Outlook 状态识别 | 直观查看"已注册/未注册"状态，显示关联账号编号 |

### 功能优化（5 项）

| 序号 | 优化项 | 效果 |
|------|--------|------|
| 1 | 批量注册上限 | 从 100 个提升至 **1000 个** |
| 2 | OAuth token 刷新 | 完善异常处理，降低报错概率 |
| 3 | 批量验证流程 | 改为受控并发，减少卡死问题 |
| 4 | WebUI 端口冲突 | 自动切换可用端口，无需手动修改 |
| 5 | 字段迁移逻辑 | 启动时自动补齐新增字段，兼容旧数据 |

### BUG 修复（4 项）

| 序号 | 修复内容 | 影响 |
|------|----------|------|
| 1 | 模板渲染兼容 | 适配不同 Starlette 版本 |
| 2 | 六位数字误判 OTP | 避免无关文本被识别为验证码 |
| 3 | Outlook 大小写问题 | 避免 Outlook.com 因大小写误判 |
| 4 | Outlook 列表显示 | 修复列错位、乱码、占位文案问题 |

---

## 🖥️ 环境准备（按步骤操作）

### 第一步：确认操作系统

本教程支持以下操作系统：

| 系统 | 版本要求 | 推荐度 |
|------|----------|--------|
| Windows | Windows 10/11 (64 位) | ⭐⭐⭐⭐⭐ |
| macOS | macOS 10.15+ | ⭐⭐⭐⭐ |
| Linux | Ubuntu 20.04+/Debian 10+ | ⭐⭐⭐⭐ |
| Docker | 任意支持 Docker 的系统 | ⭐⭐⭐⭐⭐ |

**查看系统版本命令**：

```bash
# Windows（PowerShell）
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

# macOS
sw_vers

# Linux
cat /etc/os-release
```

### 第二步：安装 Python（3.10+）

#### Windows 安装 Python

1. **下载 Python**
   - 访问官网：https://www.python.org/downloads/
   - 下载 Python 3.10 或更高版本（推荐 3.11/3.12）
   - 选择 "Windows installer (64-bit)"

2. **安装 Python**
   - 双击安装包
   - ⚠️ **重要**：勾选 "Add Python to PATH"
   - 点击 "Install Now"

3. **验证安装**
   ```bash
   # 打开命令提示符（Win+R → cmd）
   python --version
   # 应显示：Python 3.10.x 或更高
   ```

#### macOS 安装 Python

```bash
# 使用 Homebrew（推荐）
brew install python@3.11

# 验证安装
python3 --version
```

#### Linux 安装 Python

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# CentOS/RHEL
sudo yum install python3.11 python3-pip

# 验证安装
python3 --version
```

### 第三步：安装 Git

#### Windows 安装 Git

1. 下载：https://git-scm.com/download/win
2. 双击安装，使用默认选项即可
3. 验证：
   ```bash
   git --version
   ```

#### macOS 安装 Git

```bash
# 使用 Homebrew
brew install git

# 或使用 Xcode 命令行工具
xcode-select --install
```

#### Linux 安装 Git

```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git

# 验证
git --version
```

### 第四步：准备代理环境（重要）

由于 OpenAI 服务限制，你需要准备可用的代理：

**代理要求**：
- 支持 HTTPS
- 稳定性好（推荐付费代理）
- 延迟低于 300ms
- 支持并发连接

**常见代理配置**：

```bash
# 本地代理示例（Clash）
HTTP 代理：http://127.0.0.1:7890
HTTPS 代理：http://127.0.0.1:7890

# 环境变量设置（临时）
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# Windows PowerShell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
```

**代理测试命令**：

```bash
# 测试代理是否可用
curl -x http://127.0.0.1:7890 https://www.google.com -I
# 返回 HTTP/2 200 表示正常
```

---

## 📦 安装部署（5 种方式任选）

### 方式一：源码安装（推荐新手）

#### 步骤 1：克隆项目

```bash
# 选择安装目录（Windows 示例：D:\tools\codex-console）
cd /tmp  # Linux/Mac

# 克隆项目
git clone https://github.com/dou-jiang/codex-console.git

# 进入项目目录
cd codex-console

# 查看项目结构
ls -la
```

**预期输出**：
```
drwxr-xr-x  9 root   4096 Mar 26 09:10 .
drwxrwxrwt 26 root   4096 Mar 26 09:10 ..
-rw-r--r--  1 root   1461 Mar 26 09:10 build.bat
-rw-r--r--  1 root   1185 Mar 26 09:10 build.sh
-rw-r--r--  1 root    647 Mar 26 09:10 docker-compose.yml
-rw-r--r--  1 root   8278 Mar 26 09:10 README.md
-rw-r--r--  1 root    303 Mar 26 09:10 requirements.txt
drwxr-xr-x  7 root   4096 Mar 26 09:10 src
drwxr-xr-x  4 root   4096 Mar 26 09:10 static
drwxr-xr-x  3 root   4096 Mar 26 09:10 templates
-rw-r--r--  1 root   5992 Mar 26 09:10 webui.py
```

#### 步骤 2：创建虚拟环境（强烈推荐）

**为什么使用虚拟环境**：
- 避免污染系统 Python 环境
- 方便管理依赖包
- 便于迁移和部署

```bash
# Python 3.10+ 内置 venv 模块
python -m venv .venv

# 激活虚拟环境
# Windows (CMD):
.venv\Scripts\activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux/Mac:
source .venv/bin/activate
```

**激活成功后**，命令行前会出现 `(.venv)` 标识：
```
(.venv) user@host:~/codex-console$
```

#### 步骤 3：安装依赖

```bash
# 方式 1：使用 pip（通用）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方式 2：使用 uv（更快，推荐）
# 先安装 uv
pip install uv

# 使用 uv 安装依赖
uv pip install -r requirements.txt
```

**依赖列表**（requirements.txt）：
```
certifi>=2024.0.0
cffi>=1.16.0
curl_cffi>=0.14.0
pycparser>=1.21
pydantic>=2.0.0
pydantic-settings>=2.0.0
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
jinja2>=3.1.0
python-multipart>=0.0.6
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
psycopg[binary]>=3.1.18
playwright>=1.40.0  # 自动绑卡依赖
```

**安装时间**：约 2-5 分钟（取决于网络）

**验证安装**：
```bash
pip list | grep -E "(fastapi|uvicorn|playwright)"
```

#### 步骤 4：安装 Playwright 浏览器（可选）

如需使用自动绑卡功能，需要安装 Playwright 浏览器：

```bash
# 安装浏览器
playwright install

# 安装系统依赖（Linux）
playwright install-deps
```

**注意**：这一步可能需要较长时间（10-20 分钟），如果暂时不需要绑卡功能可以跳过。

#### 步骤 5：配置文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（选择你熟悉的编辑器）
# Windows: 用记事本打开 .env
# Linux/Mac: nano .env 或 vim .env
```

**.env 配置示例**：

```ini
# ── Web UI 监听地址 ──────────────────────────────────────────
# 监听主机（默认 0.0.0.0，允许外部访问）
APP_HOST=0.0.0.0

# 监听端口（默认 8000，可自定义）
APP_PORT=8000

# Web UI 访问密码（⚠️ 强烈建议修改！）
APP_ACCESS_PASSWORD=your_strong_password_here

# ── 数据库 ───────────────────────────────────────────────────
# 本地 SQLite（默认，新手推荐）
APP_DATABASE_URL=data/database.db

# 远程 PostgreSQL（高级用户）
# APP_DATABASE_URL=postgresql://user:password@host:5432/dbname

# ── 代理配置（重要）
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890

# ── 第三方自动绑卡（可选）
# BIND_CARD_API_URL=https://your-workers-domain.dev/
# BIND_CARD_API_KEY=your_api_key_here
```

**⚠️ 安全提醒**：
- 务必修改 `APP_ACCESS_PASSWORD` 默认值
- 不要将 `.env` 文件上传到公开仓库
- 生产环境建议使用强密码（16 位以上，包含大小写、数字、符号）

#### 步骤 6：启动服务

```bash
# 方式 1：默认启动（127.0.0.1:8000）
python webui.py

# 方式 2：指定主机和端口（允许外部访问）
python webui.py --host 0.0.0.0 --port 8000

# 方式 3：设置访问密码
python webui.py --access-password your_password

# 方式 4：组合参数（推荐）
python webui.py --host 0.0.0.0 --port 8000 --access-password your_password

# 方式 5：调试模式（开发使用）
python webui.py --debug
```

**启动成功标志**：
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**访问 WebUI**：
- 本地访问：http://127.0.0.1:8000
- 远程访问：http://你的服务器 IP:8000
- 默认密码：admin123（如未在 .env 中修改）

---

### 方式二：Docker 部署（推荐生产环境）

#### 前置要求

- 已安装 Docker 和 Docker Compose
- Docker 版本：20.10+
- Docker Compose 版本：2.0+

**安装 Docker**：

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker

# 验证安装
docker --version
docker compose version
```

#### 使用 Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/dou-jiang/codex-console.git
cd codex-console

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

**访问服务**：
- WebUI: http://你的服务器 IP:1455
- noVNC（绑卡可视化）: http://你的服务器 IP:6080

---

## 🔧 常见问题解答

### 一、安装问题

**Q1: pip install 报错 "Could not find a version that satisfies the requirement"**

**解决**：
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q2: 虚拟环境激活失败**

**Windows PowerShell 执行策略问题**：
```powershell
# 临时允许执行脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 重新激活
.venv\Scripts\Activate.ps1
```

### 二、启动问题

**Q1: 端口被占用**

```
Error: [Errno 98] Address already in use
```

**解决**：
```bash
# 方式 1：更换端口
python webui.py --port
---

## 💖 赞赏支持

<div style="margin: 50px 0; padding: 30px 20px; border: 3px dashed #ff6b6b; border-radius: 15px; background: linear-gradient(135deg, #fff5f5 0%, #fff0f0 100%); text-align: center; box-shadow: 0 4px 15px rgba(255, 107, 107, 0.15);">
  <div style="font-size: 1.3em; font-weight: bold; color: #ff6b6b; margin-bottom: 10px;">
    <span style="font-size: 1.5em;">❤️</span>
    写教程不易，如果对您有帮助，可以赞赏一下吗？
    <span style="font-size: 1.5em;">❤️</span>
  </div>
  <p style="color: #666; font-size: 0.95em; margin: 10px 0 25px 0;">您的支持是我持续更新的最大动力！</p>
  
  <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-bottom: 25px;">
    <div style="text-align: center; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);">
      <img src="/images/wechat-pay.jpg" alt="微信赞赏" style="width: 200px; height: 200px; object-fit: cover; border-radius: 5px;">
      <p style="margin-top: 12px; font-weight: bold; font-size: 1.1em; color: #333;">微信</p>
    </div>
    <div style="text-align: center; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);">
      <img src="/images/alipay.jpg" alt="支付宝赞赏" style="width: 200px; height: 200px; object-fit: cover; border-radius: 5px;">
      <p style="margin-top: 12px; font-weight: bold; font-size: 1.1em; color: #333;">支付宝</p>
    </div>
  </div>
  
  <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid rgba(255, 107, 107, 0.2);">
    <p style="color: #ff6b6b; font-weight: bold; font-size: 1.1em; margin: 0;">🎉 感谢您的支持！</p>
  </div>
</div>
