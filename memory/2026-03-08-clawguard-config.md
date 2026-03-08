# 2026-03-08 ClawGuard-BNB 配置记录

## 时间
2026-03-08 10:15 UTC

## 任务内容
配置 ClawGuard-BNB 项目接入币安全球站 API

## 配置信息

### 币安 API 凭证
- **API Key**: `iYCJ5SftdKrt5GpYImqecIw0dlcmOgEaSWRZd4OeKC0MJgKvZX7tb7XFgTCRlWHd`
- **Secret Key**: `pZkiQITai2PyyUUhVOhCU3eATMHAB8oJkzJO1nMF6SEg3I0JvYWt9sTYwHvC4SGT`
- **API 端点**: `https://api.binance.com`（全球站）
- **测试网**: false（主网模式）

### 代理配置
- **新加坡节点**: 待配置（端口 7890）
- **韩国节点**: 待配置
- **印度节点**: 待配置

### 文件位置
- **项目目录**: `/root/.openclaw/workspace/ClawGuard-BNB/`
- **配置文件**: `/root/.openclaw/workspace/ClawGuard-BNB/.env`

## 当前状态

### ✅ 已完成
1. .env 配置文件创建
2. 币安 API Key 配置
3. 代理轮询配置框架

### ⏳ 待完成
1. Clash 代理启动（需配置文件路径）
2. 币安 API 连接测试（需代理）
3. 节点详情配置（新加坡/韩国/印度）

### ❌ 测试失败
- 直连币安 API：451 地区限制（需代理）

## 下一步
1. 获取 Clash 配置文件路径
2. 启动 Clash 代理
3. 测试币安 API 连接
4. 验证代理节点可用性

---
*最后更新：2026-03-08 10:31 UTC*
