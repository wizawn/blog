---
title: "Codex Tools v1.5.4 超详细教程 - 多账号管理 + API 反代完整指南（2026 最新版）"
date: 2026-03-26T11:35:00+00:00
lastmod: 2026-03-26T11:35:00+00:00
categories: ["tech"]
tags: ["tutorial", "codex", "tools", "api-proxy", "guide"]
draft: false
weight: 1
---






{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---



---

## 📋 前言

**这是一篇真正的零基础保姆级教程**，我会手把手带你从零开始，完整了解和使用 **Codex Tools v1.5.4**——一款基于 React + Tauri 的桌面工具，用来管理多个 Codex 账号，并提供本地 API 反代能力。

**本教程特点**：
- ✅ **完全从零开始**：假设你没有任何开发基础
- ✅ **真实测试验证**：所有步骤都已实际测试通过
- ✅ **包含所有坑点**：把可能遇到的问题都提前说明
- ✅ **持续更新维护**：跟随项目版本同步更新

**项目信息**：
- **GitHub 仓库**：https://github.com/170-carry/codex-tools
- **当前版本**：v1.5.4
- **技术栈**：React + Tauri (Rust)
- **支持系统**：macOS / Windows
- **许可证**：MIT（免费开源）

---

## ⚠️ 重要声明

1. **本项目仅供学习研究**：请遵守 OpenAI 相关服务条款
2. **严禁用于违规用途**：不要用于滥用、非法用途
3. **风险自担**：因使用本项目产生的风险和后果由使用者自行承担
4. **免费开源**：任何付费版本均为倒卖行为

---

## 🎯 核心功能

### 1. 多账号管理
- ✅ 支持 OAuth 登录导入
- ✅ 支持 JSON 文件批量导入
- ✅ 支持读取文件夹下的全部账号文件
- ✅ 导入后保留当前本机登录态

### 2. 用量查看与智能切换
- ✅ 展示每个账号的 **5 小时** 用量窗口
- ✅ 展示每个账号的 **1 周** 用量窗口
- ✅ 显示计划类型（Free/Plus/Team 等）
- ✅ 支持手动刷新和定时自动刷新
- ✅ 支持按余量排序和智能切换

### 3. 一键切换账号
- ✅ 一键切换账号并启动 Codex
- ✅ 找不到桌面应用时自动回退到 `codex app`
- ✅ 可选同步 Opencode OpenAI 授权
- ✅ 可选在切换后重启已选编辑器

### 4. API 反代（核心功能）
- ✅ 本地提供 OpenAI 兼容的 `/v1` 接口
- ✅ 使用已登录的 Codex 账号作为上游
- ✅ 支持固定端口、自定义端口
- ✅ 支持固定 API Key 和手动刷新
- ✅ 按账号余量自动挑选可用账号转发
- ✅ 可设置应用启动时自动启动 API 反代

### 5. 公网访问与桌面能力
- ✅ 集成 cloudflared，可将本地反代暴露到公网
- ✅ 支持快速隧道和命名隧道
- ✅ 可选 HTTP/2 协议
- ✅ 支持后台驻留、状态栏菜单
- ✅ 支持应用内更新和多语言界面

---

## 🖥️ 环境准备

### 系统要求

| 系统 | 版本要求 | 推荐度 |
|------|----------|--------|
| macOS | macOS 10.15+ | ⭐⭐⭐⭐⭐ |
| Windows | Windows 10/11 (64 位) | ⭐⭐⭐⭐ |
| Linux | 暂不支持 | ❌ |

### 前置软件

**如果你只是使用（不开发）**：
- ✅ 不需要安装任何额外软件
- ✅ 直接下载安装包即可

**如果你要开发/打包**：
- Node.js 20+
- Rust stable
- pnpm 9.15.9+

**查看系统版本**：

```bash
# macOS
sw_vers

# Windows (PowerShell)
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

---

## 📦 安装部署（3 种方式）

### 方式一：下载预编译版本（推荐新手）

#### 步骤 1：访问发布页面

打开浏览器访问：
- **GitHub Releases**：https://github.com/170-carry/codex-tools/releases

#### 步骤 2：下载对应版本

**macOS 用户**：
- Intel 芯片：下载 `Codex_Tools_x64.dmg` 或 `Codex_Tools_x64.app.tar.gz`
- Apple Silicon (M1/M2/M3)：下载 `Codex_Tools_aarch64.dmg` 或 `Codex_Tools_aarch64.app.tar.gz`

**Windows 用户**：
- 下载 `Codex_Tools_x64-setup.exe` 或 `Codex_Tools_x64.zip`

#### 步骤 3：安装应用

**macOS**：
1. 双击 `.dmg` 文件
2. 将 `Codex Tools.app` 拖拽到「应用程序」文件夹
3. 如果提示"已损坏"，执行以下命令修复：

```bash
sudo spctl --master-disable
sudo xattr -r -d com.apple.quarantine /Applications/Codex\ Tools.app
```

**Windows**：
1. 双击 `.exe` 安装包
2. 按照安装向导完成安装
3. 或在开始菜单找到应用

#### 步骤 4：首次启动

1. 打开「应用程序」文件夹（macOS）或开始菜单（Windows）
2. 找到并打开 `Codex Tools`
3. 首次启动可能会提示确认，点击"打开"即可

---

### 方式二：源码安装（适合开发者）

#### 步骤 1：安装前置环境

**安装 Node.js 20+**：

```bash
# macOS (使用 Homebrew)
brew install node@20

# Windows
# 访问 https://nodejs.org/ 下载安装包

# 验证安装
node --version  # 应显示 v20.x.x
```

**安装 Rust**：

```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Windows
# 访问 https://rustup.rs/ 下载 rustup-init.exe

# 验证安装
rustc --version  # 应显示 rustc 1.x.x
```

**安装 pnpm**：

```bash
npm install -g pnpm

# 验证安装
pnpm --version  # 应显示 9.15.9+
```

#### 步骤 2：克隆项目

```bash
# 选择安装目录
cd /tmp  # macOS/Linux
# 或 D:\tools  # Windows

# 克隆项目
git clone https://github.com/170-carry/codex-tools.git

# 进入项目目录
cd codex-tools
```

#### 步骤 3：安装依赖

```bash
# 安装 Node.js 依赖
pnpm install

# 安装时间：约 2-5 分钟（取决于网络）
```

#### 步骤 4：启动开发环境

```bash
# 启动桌面应用（开发模式）
pnpm run tauri dev

# 启动时间：约 30-60 秒
# 启动后会打开应用窗口
```

**开发模式特点**：
- ✅ 支持热重载
- ✅ 修改代码后自动刷新
- ✅ 控制台会显示日志

---

### 方式三：自行打包（适合高级用户）

#### 步骤 1：完成方式二的所有步骤

#### 步骤 2：执行打包命令

```bash
# macOS
pnpm run tauri build

# Windows
pnpm run tauri build
```

**打包时间**：约 5-15 分钟（首次打包需要编译 Rust 代码）

#### 步骤 3：查找打包产物

**macOS**：
```bash
ls -la src-tauri/target/release/bundle/dmg/
ls -la src-tauri/target/release/bundle/macos/
```

**Windows**：
```bash
dir src-tauri\target\release\bundle\msi\
dir src-tauri\target\release\bundle\app\
```

**产物说明**：
- `.dmg` / `.app` - macOS 安装包
- `.exe` / `.msi` - Windows 安装包

---

## 🎨 界面介绍

### 主界面布局

```
┌─────────────────────────────────────────┐
│  Codex Tools                    [设置]  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 账号列表                        │   │
│  │ ┌─────────────────────────────┐ │   │
│  │ │ 🟢 账号 1 (Free)           │ │   │
│  │ │    5h: 2.5h / 1w: 15h      │ │   │
│  │ └─────────────────────────────┘ │   │
│  │ ┌─────────────────────────────┐ │   │
│  │ │ 🟡 账号 2 (Plus)           │ │   │
│  │ │    5h: 4.8h / 1w: 20h      │ │   │
│  │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [刷新] [切换账号] [启动 Codex]        │
│                                         │
├─────────────────────────────────────────┤
│ [账号管理] [API 反代] [设置] [关于]    │
└─────────────────────────────────────────┘
```

### 底部导航栏

| 标签 | 功能 |
|------|------|
| **账号管理** | 查看和管理所有账号 |
| **API 反代** | 配置和启动 API 代理服务 |
| **设置** | 应用设置和偏好配置 |
| **关于** | 版本信息和帮助 |

---

## 🔧 详细使用教程

### 一、导入账号

#### 方法 1：OAuth 登录导入（推荐）

1. 点击「账号管理」标签
2. 点击「+ 添加账号」按钮
3. 选择「OAuth 登录」
4. 应用会自动生成授权链接并打开浏览器
5. 在浏览器中登录你的 Codex/ChatGPT 账号
6. 授权完成后会自动跳转回应用
7. 账号会自动导入并保存

**优点**：
- ✅ 最简单快捷
- ✅ 自动获取完整认证信息
- ✅ 不需要手动操作文件

#### 方法 2：上传 JSON 文件

1. 点击「账号管理」标签
2. 点击「+ 添加账号」按钮
3. 选择「导入 JSON 文件」
4. 选择一个或多个 `.json` 账号文件
5. 点击「导入」

**JSON 文件格式**：
```json
{
  "label": "我的账号 1",
  "account_id": "xxx-xxx-xxx",
  "auth_json": {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "session_token": "xxx"
  },
  "plan_type": "free"
}
```

#### 方法 3：读取文件夹

1. 点击「账号管理」标签
2. 点击「+ 添加账号」按钮
3. 选择「读取文件夹」
4. 选择包含多个 `.json` 文件的文件夹
5. 应用会自动读取所有账号文件

**适用场景**：
- ✅ 有大量账号需要批量导入
- ✅ 从其他工具迁移账号

#### 方法 4：同步当前设备登录

1. 确保你已经在 Codex 桌面应用或网页版登录
2. 点击「账号管理」标签
3. 点击「+ 添加账号」按钮
4. 选择「同步当前登录」
5. 应用会自动读取本机的登录凭证

**注意**：
- ⚠️ 只会同步当前登录的账号
- ⚠️ 不会覆盖正在使用的账号

---

### 二、查看账号用量

#### 手动刷新

1. 进入「账号管理」页面
2. 点击「刷新」按钮
3. 等待几秒钟，用量信息会更新

#### 自动刷新

1. 进入「设置」页面
2. 找到「用量自动刷新」选项
3. 设置刷新间隔（默认 30 分钟）
4. 开启自动刷新

#### 用量信息说明

每个账号会显示：

| 字段 | 说明 |
|------|------|
| **5h 用量** | 过去 5 小时的使用时长 |
| **1w 用量** | 过去 1 周的使用时长 |
| **计划类型** | Free / Plus / Team 等 |
| **状态** | 🟢 可用 / 🟡 受限 / 🔴 不可用 |

#### 按余量排序

1. 点击「用量」列标题
2. 账号会按余量从高到低排序
3. 再次点击会从低到高排序

---

### 三、切换账号并启动 Codex

#### 一键切换

1. 在账号列表中选择一个可用账号
2. 点击「切换账号」按钮
3. 等待应用切换到目标账号
4. 切换成功后会显示提示

#### 切换并启动 Codex

1. 在账号列表中选择一个可用账号
2. 点击「启动 Codex」按钮
3. 应用会：
   - 切换到目标账号
   - 自动启动 Codex 桌面应用
   - 如果找不到桌面应用，会回退到 `codex app`

#### 编辑器联动（可选）

1. 进入「设置」页面
2. 找到「编辑器联动」部分
3. 开启「切换账号后重启编辑器」
4. 选择你的编辑器（Cursor / VSCode 等）

**效果**：
- 切换账号后会自动重启编辑器
- 编辑器会使用新的账号认证

#### Opencode 授权同步（可选）

1. 进入「设置」页面
2. 找到「Opencode」部分
3. 开启「同步 Opencode 授权」

**效果**：
- 切换 Codex 账号时会同步更新 Opencode 的认证
- 适合同时使用两个工具的用户

---

### 四、API 反代（核心功能）

#### 什么是 API 反代？

简单说，就是在你的电脑上运行一个本地的 API 服务，让其他工具可以通过 OpenAI 兼容的接口调用 Codex 能力。

**工作原理**：
```
客户端（如 Cursor） → 本地 API (127.0.0.1:8787) → Codex 上游
```

#### 启动 API 反代

1. 点击底部导航栏的「API 反代」标签
2. 设置端口号（默认 8787）
3. 点击「启动」按钮
4. 等待服务启动成功
5. 界面会显示：
   - **Base URL**: `http://127.0.0.1:8787/v1`
   - **API Key**: `sk-xxxxxxxx`（自动生成）

#### 在 Cursor 中使用

1. 打开 Cursor
2. 点击设置图标 → Cursor Settings
3. 选择「Models」页面
4. 开启「OpenAI API Key」
5. 填入 API Key（从 Codex Tools 复制）
6. 开启「Override OpenAI Base URL」
7. 填入 Base URL：`http://127.0.0.1:8787/v1`
8. 在「Add or search model」中输入 `gpt-4`（或其他支持的模型）
9. 点击「Add Custom Model」

**完成！** 现在你可以在 Cursor 中使用 Codex 的能力了。

#### 在其他客户端中使用

**通用配置**：

| 配置项 | 值 |
|--------|-----|
| **API 类型** | OpenAI Compatible |
| **Base URL** | `http://127.0.0.1:8787/v1` |
| **API Key** | `sk-xxxxxxxx`（从 Codex Tools 复制） |
| **模型名称** | `gpt-4` 或 `gpt-5` |

**支持的工具**：
- ✅ Cursor
- ✅ VSCode (Continue 插件)
- ✅ JetBrains IDEs
- ✅ Any API 客户端

#### 支持的接口

| 接口 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /v1/models` | 获取模型列表 |
| `POST /v1/chat/completions` | 聊天补全（兼容 OpenAI） |
| `POST /v1/responses` | Responses 接口 |

#### 请求示例

```bash
# 健康检查
curl http://127.0.0.1:8787/health

# 获取模型列表
curl http://127.0.0.1:8787/v1/models \
  -H 'Authorization: Bearer sk-xxxx'

# 聊天补全
curl http://127.0.0.1:8787/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-xxxx' \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "1+1 等于几？"}
    ]
  }'
```

#### 自动启动 API 反代

1. 进入「设置」页面
2. 找到「API 反代」部分
3. 开启「应用启动时自动启动」
4. 设置端口和 API Key（可选）

**效果**：
- ✅ 每次打开应用都会自动启动 API 反代
- ✅ 不需要手动操作

#### 公网访问（Cloudflared）

如果你想让其他设备也能访问 API 反代：

1. 点击「API 反代」标签
2. 找到「Cloudflared 公网访问」部分
3. 选择隧道类型：
   - **快速隧道**：临时隧道，重启后失效
   - **命名隧道**：持久隧道，需要配置
4. 点击「启动隧道」
5. 等待隧道建立成功
6. 复制公网地址（如 `https://xxx.trycloudflare.com`）

**注意**：
- ⚠️ 公网访问会暴露你的 API 到互联网
- ⚠️ 请确保 API Key 足够安全
- ⚠️ 建议设置访问限制

---

## 🔍 故障排查

### 问题 1：应用无法启动

**macOS 提示"已损坏"**：

```bash
sudo spctl --master-disable
sudo xattr -r -d com.apple.quarantine /Applications/Codex\ Tools.app
```

**Windows 闪退**：
1. 右键应用 → 以管理员身份运行
2. 检查是否有杀毒软件拦截
3. 重新下载安装包

### 问题 2：账号导入失败

**OAuth 登录失败**：
1. 检查网络连接
2. 确保浏览器能正常访问 ChatGPT
3. 清除浏览器缓存后重试
4. 尝试使用 JSON 文件导入

**JSON 文件导入失败**：
1. 检查 JSON 格式是否正确
2. 确保包含必要字段（`access_token`, `account_id`）
3. 检查文件编码是否为 UTF-8

### 问题 3：用量刷新失败

1. 检查账号是否已登录
2. 检查网络连接
3. 手动点击刷新按钮
4. 如果所有账号都失败，可能是网络问题

### 问题 4：API 反代无法启动

**端口被占用**：
```bash
# macOS/Linux
lsof -i :8787

# Windows
netstat -ano | findstr :8787
```

**解决方案**：
1. 关闭占用端口的应用
2. 或在 Codex Tools 中更换端口

**API Key 无效**：
1. 确保从「API 反代」页面复制正确的 API Key
2. 检查是否有多余空格
3. 尝试重新生成 API Key

### 问题 5：Cursor 无法连接

1. 检查 API 反代是否已启动
2. 检查 Base URL 是否正确（`http://127.0.0.1:8787/v1`）
3. 检查 API Key 是否正确
4. 尝试访问 `http://127.0.0.1:8787/health` 确认服务正常
5. 检查 Cursor 是否支持自定义 API

---

## 💡 使用技巧

### 1. 账号管理技巧

- **定期刷新用量**：设置自动刷新，保持用量信息最新
- **按余量排序**：快速找到可用额度最高的账号
- **使用标签**：给账号添加标签（如"工作"、"个人"）
- **备份账号**：定期导出账号 JSON 文件备份

### 2. API 反代技巧

- **固定端口**：避免每次启动端口变化
- **设置强 API Key**：不要使用默认的弱 Key
- **监控日志**：查看 API 调用日志，了解使用情况
- **限制访问**：如果开启公网访问，设置 IP 白名单

### 3. 性能优化

- **关闭不用的功能**：如不需要 API 反代，可以关闭
- **减少自动刷新频率**：设置为 1 小时或更长
- **清理旧账号**：删除不再使用的账号

---

## 📊 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v1.5.4 | 2026-03 | 修复端口占用、稳定性优化 |
| v1.5.3 | 2026-03 | 修复稳定性问题 |
| v1.5.0 | 2026-03 | 重做账号导入、OAuth 登录优化 |
| v1.4.1 | 2026-02 | 去除工作区相关功能 |
| v1.4.0 | 2026-02 | 支持自定义 Codex 路径 |
| v1.3.2 | 2026-02 | UI 优化 |
| v1.0.0 | 2026-01 | 重构为 Tauri 应用 |

---

## 🔗 相关链接

- **GitHub 仓库**：https://github.com/170-carry/codex-tools
- **问题反馈**：https://github.com/170-carry/codex-tools/issues
- **更新日志**：https://github.com/170-carry/codex-tools/blob/main/changelog.md
- **API 反代文档**：https://github.com/170-carry/codex-tools/blob/main/docs/api-proxy.md

---

## 📝 总结

**Codex Tools** 是一款功能强大的多账号管理工具，核心优势：

### ✅ 优点
- 界面简洁，易于上手
- 支持多种账号导入方式
- 用量查看直观清晰
- API 反代功能强大
- 支持公网访问
- 免费开源

### ⚠️ 注意事项
- 目前仅支持 macOS 和 Windows
- Linux 暂不支持
- 公网访问需注意安全

### 🎯 适用人群
- 有多个 Codex 账号的用户
- 需要在多个工具间切换账号
- 需要使用 API 反代功能
- 开发者和技术爱好者

---

*最后更新：2026-03-26*

*本教程基于 codex-tools v1.5.4 编写，具体操作请以实际版本为准。*
*使用本工具请遵守 OpenAI 相关服务条款，严禁用于违规用途。*