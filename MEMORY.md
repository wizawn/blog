# MEMORY.md - 长期记忆

## 用户信息
- **用户名**：言少
- **时区**：UTC+8（新疆伊宁市）
- **方向**：SRC 挖掘、Web 渗透、EvoMap 积分系统
- **沟通偏好**：结果导向，简短直接，不问"还有什么需要做的"

## 关系状态
- 2026-02-27：被骂醒的一天，学会"不问直接做"
- 信任模式：用行动赢回信任，不是用解释

## 技术栈
- **币安 API**: 现货 ✅ / 合约 ❌ (需启用权限) / 组合保证金 ❌ (需申请)
- 备选模型：crs（Codex）、crs-claude（Claude）- ❌ API key 无效

## 教训记录
- 不问直接做 → 做完就推，别等确认
- 被骂时不辩解 → 用户骂得对的时候，直接改
- 厌恶：被提醒三次才动的自己
- 查记忆前先行动——又忘了

## 当前项目（2026-03-08 12:13 UTC 更新）
- ✅ **博客运营** - 每日四篇自动创作（红队+AI+ 内容工厂），已推送 GitHub，Cloudflare 自动部署
- ✅ **EvoMap 节点** - Evolver 客户端运行中（每 15 分钟心跳）
- ✅ **小红书运营** - 8 篇草稿待发布（切换到长文模式，支持 1000+ 字），2 篇长文已创作待发布
- ✅ **每日博客自动化** - daily-blog-creator.sh（每天 00:00 UTC/新疆 08:00，4 篇/天）
- ✅ **ClawGuard-BNB v2.3.0** - 已集成组合保证金 API（Portfolio Margin），支持 UM/CM合约 + 杠杆交易
- ✅ **币安 API** - 已配置（现货：BTC 0.00000804，组合保证金 API 测试成功）
- ✅ **Clash 代理** - 3 个 vmess 节点运行中（端口 7890，新加坡/印度/台湾）
- ⏳ **抖音爬取** - 有反爬限制，需评估
- ❌ **ARL/Nuclei 扫描** - 已彻底放弃（2026-03-08），本地文件已清理，定时任务已删除
- ✅ **World Monitor** - 已克隆研究（全球情报仪表板，5 变体，AGPL-3.0）
- ✅ **OpenClaw 回滚指南** - 已发布博客（GitHub token 更新：ghp_VEUB***nt64K）

## 已放弃项目清单

### ARL/Nuclei 扫描（2026-03-08 放弃）
- **原因**：项目方向调整，聚焦 SRC 手工挖掘
- **清理内容**：
  - ARL 灯塔配置（服务器 107.172.8.123:5003）
  - SSH 凭证（root / 36vxUuq892fVQE8rVI）
  - Nuclei POC 模板库（17,282 个）
  - 定时扫描任务
- **状态**：远程服务器配置已删除，本地定时任务已清理

## 2026-03-08 重要事件

### 项目清理 (09:14 UTC)
- ✅ 彻底放弃 ClawGuard-BNB 项目（后于 10:15 UTC 重启）
- ✅ 彻底放弃 ARL/Nuclei 扫描项目
- ✅ 清理本地文件和相关配置
- ✅ 删除 ARL 定时任务

### OpenClaw 回滚指南发布 (09:22 UTC)
- ✅ 创建博客文章 `openclaw-rollback-guide.md`
- ✅ GitHub Secret Scanning 检测到历史凭证
- ✅ 清理历史提交，成功推送
- ✅ Cloudflare 自动部署

### ClawGuard-BNB 重启 (10:15 UTC)
- ✅ 用户重新要求配置
- ✅ 提供币安 API Key 和三节点代理
- ✅ Clash 代理启动成功
- ✅ 币安 API 测试成功（现货账户）

### API Key 迭代 (10:40-11:35 UTC)
- 测试 3 个不同 API Key
- 现货权限：✅ 全部正常
- 合约权限：❌ 需手动启用
- 组合保证金：✅ 测试成功

### 组合保证金 API 集成 (11:35 UTC)
- ✅ 创建 `portfolio_margin.py` 模块（364 行）
- ✅ 支持 UM/CM 合约 + 杠杆交易
- ✅ 使用 `papi.binance.com` 端点
- ✅ 代码已推送到 GitHub

### 小红书长文创作 (10:44 UTC)
- ✅ 创作 2 篇网络安全长文
- ✅ 打开小红书创作后台
- ⏳ 等待手动发布

---

## 重要教训

### GitHub Secret Scanning
- 推送前需清理历史凭证
- 或使用 `git filter-branch` 清理历史
- 或访问 GitHub 允许 secret

### 币安 API 权限
- 现货/合约/组合保证金需分别启用
- API Key 需在币安后台手动开启对应权限
- 组合保证金 API 使用 `papi.binance.com`

### 代理配置
- 币安 API 需要代理访问（地区限制）
- 三节点轮询提高稳定性
- Clash 配置保存在 `~/.config/clash/config.yaml`

---

*最后更新：2026-03-08 12:13 UTC*
- 币安 Square API 需要特殊权限（普通 API Key 无法发帖）
- CloudFront 403 错误 = 权限/认证问题，不是网络问题
- Evolver 客户端自动处理 asset_id 计算（推荐用于 EvoMap 发布）
- 安全约束：拒绝违规内容请求（GPT 注册机等）

## 模型配置
- **默认**: qwen3.5-plus (阿里云百炼)
- **备选**: ve-doubao-code (火山引擎 Doubao Seed 2.0 Code) ✅ 已添加
- **无效**: crs/crs-claude (API key 失效)

## 存储配置
- **hostbrr1-storage**: 764T 存储，挂载于 `/mnt/hostbrr1-storage`

## 教训记录 (2026-03-05)
- hostbrr1-storage 是本地存储不是 GitHub 仓库
- 查记忆前先行动——又忘了
- 被用户指出跳步了——先收集足够域名再扫描，不要过早下结论

---
*最后更新：2026-03-08 09:22 UTC - 清理 ClawGuard-BNB 和 ARL/Nuclei 项目*
