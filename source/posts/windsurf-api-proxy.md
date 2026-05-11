---
title: "Windsurf 开源反代工具：59 个 AI 模型一站式接入"
description: "有人把 Windsurf AI 编程 IDE 的后端扒出来，做成了 OpenAI 兼容的 API 代理。零 npm 依赖，支持多账号池轮转，5 分钟完成部署。"
date: 2026-04-19T14:45:00+08:00
draft: false
categories: ["教程"]
tags: ["Windsurf", "AI", "API 代理", "Claude", "开源工具"]
weight: -996
---

> **💬 联系方式 & 交流群**
> 
> **QQ**: 46333839  
> **微信**: GOV-HACK  
> 
> 添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~
> 
> 
> 

---

> 一分钟速读：WindsurfAPI 把 Windsurf IDE 的后端 Language Server 独立部署，封装成 OpenAI 兼容接口，支持 59 个大模型调用，自带账号管理和负载均衡。

---

## 项目背景

Windsurf 是一款专注于 AI 辅助编程的集成开发环境（之前叫 Codeium），在开发者圈子里口碑不错。它内置的 Language Server 负责与各种大模型通信，让开发者能在 IDE 里直接调用 Claude、GPT 等模型的能力。

一位 GitHub 开发者（@dwgx）发现，这个 Language Server 其实可以独立运行。于是他做了个有趣的尝试——把它从 IDE 里抽离出来，包装成标准的 OpenAI API 格式。

**项目仓库**：https://github.com/dwgx/WindsurfAPI

这样一来，你不需要打开 Windsurf 编辑器，也能通过 HTTP 接口调用那些 AI 模型。任何支持 OpenAI 协议的工具或 SDK，改个配置就能接入。

---

## 核心价值

### 1. 统一接口，多模型切换

不同 AI 厂商的 API 格式各不相同，想换个模型用用，得重新研究文档、调整代码。WindsurfAPI 把这些差异都屏蔽了，你只需要改一个参数：

```bash
model: "claude-opus-4-7-max"  # 切换模型
```

支持的模型阵容：

| 厂商 | 可用模型 |
|------|----------|
| Anthropic | Claude Opus 4.7 Max、4.6 |
| OpenAI | GPT-5.4、4o-mini |
| Google | Gemini 2.5 Flash |
| 其他 | DeepSeek、Grok、通义千问、Kimi 2.5、SWE |

### 2. 账号池与负载均衡

单个账号的调用次数有限制，团队协作或高频使用时很容易触顶。WindsurfAPI 允许多个账号组成资源池：

- 自动在账号间轮换请求
- 某个账号额度不足时自动切换
- 模型级别的故障不影响其他调用
- 实时监控账号状态，提前预警

从调用方的角度看，就像有一个「无限额度」的账号在背后支撑。

### 3. 零外部依赖

这个项目最让人印象深刻的是代码风格——完全不依赖第三方 npm 包，全部使用 Node.js 原生模块：

- HTTP 服务：`http`
- 文件系统：`fs`
- 路径处理：`path`
- 环境变量：`process.env`
- gRPC 通信：内置实现

在 JavaScript 生态里，这种「洁癖式」的写法相当罕见。好处也很明显：没有供应链攻击风险，部署简单，维护成本低。

### 4. Web 管理界面

访问 `http://你的服务器:3003/dashboard` 可以打开管理后台：

**账号管理功能**：
- 添加或删除 Windsurf 账号
- 启用/禁用特定账号
- 查看各账号的使用统计
- 批量导入 Token

**监控仪表盘**：
- 实时请求量
- 平均响应时间
- 错误率变化趋势
- 各模型调用占比

**代理与限流**：
- 全局 HTTP/SOCKS5 代理配置
- 单账号独立代理设置
- 模型访问白名单/黑名单
- 请求频率限制

对于需要管理多个账号的场景，这个界面能省不少事。

---

## 技术架构

系统分为四个层次：

```
客户端（OpenAI SDK / curl）
    ↓
WindsurfAPI（Node.js 服务，3003 端口）
    ↓
Language Server（gRPC，42100 端口）
    ↓
Windsurf 官方后端
```

关键接口 `/v1/chat/completions` 和 `/v1/models` 都已实现，兼容所有基于 OpenAI API 构建的工具：

- OpenAI 官方 SDK（Python、Node.js、Go 等语言）
- LangChain 框架
- LlamaIndex
- 其他第三方封装库

Python 调用示例：

```python
from openai import OpenAI

client = OpenAI(
    api_key="任意值",  # 实际验证由 WindsurfAPI 处理
    base_url="http://你的服务器:3003/v1"
)

response = client.chat.completions.create(
    model="claude-opus-4-7-max",
    messages=[{"role": "user", "content": "你好"}]
)
```

---

## 部署指南

### 前置条件

- Node.js 20 或更高版本
- 至少一个 Windsurf 账号（免费版即可）
- Language Server 可执行文件（需自行提取）

#### 提取 Language Server

该文件不包含在项目仓库中，需要从 Windsurf 官方安装包中提取：

```bash
# 下载安装包
wget https://downloads.windsurf.com/windsurf-linux.deb

# 解压
dpkg-deb -x windsurf-linux.deb windsurf-extracted

# 定位文件
find windsurf-extracted -name "language_server_linux_x64"
```

### 安装流程

```bash
# 1. 获取项目
git clone https://github.com/dwgx/WindsurfAPI.git
cd WindsurfAPI

# 2. 部署 Language Server
mkdir -p /opt/windsurf
cp language_server_linux_x64 /opt/windsurf/
chmod +x /opt/windsurf/language_server_linux_x64

# 3. 准备数据目录
mkdir -p /opt/windsurf/data/db

# 4. 设置环境变量
cat > .env << 'EOF'
PORT=3003
API_KEY=
DEFAULT_MODEL=gpt-4o-mini
MAX_TOKENS=8192
LOG_LEVEL=info
LS_BINARY_PATH=/opt/windsurf/language_server_linux_x64
LS_PORT=42100
DASHBOARD_PASSWORD=你的密码
EOF

# 5. 运行服务
node src/index.js
```

服务启动后监听 `http://0.0.0.0:3003`。

#### 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| PORT | HTTP 服务端口 | 3003 |
| API_KEY | API 访问密钥（可选） | 空 |
| DEFAULT_MODEL | 默认使用的模型 | gpt-4o-mini |
| MAX_TOKENS | 单次请求最大 token 数 | 8192 |
| LOG_LEVEL | 日志详细程度 | info |
| LS_BINARY_PATH | Language Server 文件路径 | 必填 |
| LS_PORT | Language Server 端口 | 42100 |
| DASHBOARD_PASSWORD | 管理后台登录密码 | 必填 |

### 进程守护（PM2）

```bash
# 安装 PM2
npm install -g pm2

# 启动应用
pm2 start src/index.js --name windsurf-api

# 持久化配置
pm2 save

# 配置开机自启
pm2 startup
```

#### 重启的正确方式

**不要使用 `pm2 restart`**，这会导致 Language Server 进程残留成为僵尸进程。

推荐做法：

```bash
pm2 stop windsurf-api
pm2 delete windsurf-api
fuser -k 3003/tcp 2>/dev/null
sleep 2
pm2 start src/index.js --name windsurf-api --cwd /root/WindsurfAPI
```

先完全停止并删除进程，清理端口占用，再重新启动。

### 网络配置

```bash
# Ubuntu 防火墙
ufw allow 3003/tcp

# CentOS 防火墙
firewall-cmd --add-port=3003/tcp --permanent
firewall-cmd --reload

# 云服务器：在安全组规则中开放 3003 端口
```

### 配置 Windsurf 账号

```bash
# 单个账号（使用 Token）
curl -X POST http://localhost:3003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"token": "你的 windsurf-token"}'

# 批量添加
curl -X POST http://localhost:3003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"accounts": [{"token": "token1"}, {"token": "token2"}]}'
```

#### 获取 Token

1. 启动 Windsurf IDE
2. 进入设置（Settings）
3. 找到 Account 或 Profile 页面
4. 复制 Token 字符串

如果找不到 Token 选项，也可以使用账号密码方式登录，但 Token 方式更安全便捷。

### 验证部署

```bash
curl http://localhost:3003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "你好"}],
  "stream": false
}'
```

收到正常响应即表示部署成功。

---

## 使用须知

### 开源协议

项目采用 MIT 许可证，但作者在 README 中附加了额外条款：

- 禁止商业用途（除非获得书面授权）
- 禁止转售或代部署服务
- 个人学习和研究不受限制

使用前请仔细阅读相关条款。

### 安全建议

**管理后台密码必须设置**：`DASHBOARD_PASSWORD` 环境变量不要留空，否则任何人都能访问你的后台并查看账号信息。

### 代理支持

如果服务器网络需要代理，可以在管理后台配置：

```bash
# 全局代理配置
curl -X POST http://localhost:3003/proxy/config \
  -H "Content-Type: application/json" \
  -d '{"type": "http", "host": "proxy.example.com", "port": 8080}'

# 单账号代理
curl -X POST http://localhost:3003/account/1/proxy \
  -H "Content-Type: application/json" \
  -d '{"type": "socks5", "host": "proxy.example.com", "port": 1080}'
```

支持 HTTP 和 SOCKS5 两种协议，可以全局配置也可以为单个账号单独设置。

### 模型访问权限

Windsurf 对不同订阅等级的账号开放了不同的模型：

- **免费账号**：gpt-4o-mini、gemini-2.5-flash 等基础模型
- **Pro 订阅**：Claude 系列、GPT-5.4、Kimi 2.5 等高级模型

具体可用模型列表可在管理后台查看。

### 调用限额

Windsurf 对账号实行周限额制度：

| 账号类型 | 周调用次数 | 备注 |
|----------|------------|------|
| 免费版 | 约 300 次 | 仅限基础模型 |
| Pro 版 | 约 2000 次 | 全部模型可用 |

多账号池的设计初衷就是为了解决这个问题。

---

## 结语

开源社区的魅力在于，总有人能发现工具的新用法。

把 IDE 的后端独立出来变成通用 API 代理，这种思路值得借鉴。如果你对这类项目感兴趣，不妨去 GitHub 上给作者点个 Star。

---

**项目仓库**：https://github.com/dwgx/WindsurfAPI

---

本文仅做技术分享，请遵守开源协议和相关法律法规。
