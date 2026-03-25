# 博客部署日志 - 2026-03-06

## 部署信息

| 项目 | 内容 |
|------|------|
| **部署时间** | 2026-03-06 08:59 UTC |
| **部署 ID** | 1524bfb1-e71... |
| **状态** | ✅ success |
| **环境** | production |
| **博客地址** | https://blog.caowo.de/ |

---

## 新增文章

### 1. ARL 灯塔实战：10,000+ 海外站点资产收集全记录
- **文件**: `source/posts/arl-overseas-recon-2026.md`
- **分类**: 漏洞复现，资产收集
- **封面**: arl-overseas-cover.png
- **字数**: ~4000 字

### 2. 币安广场内容精选（索引页）
- **文件**: `source/posts/binance-index.md`
- **分类**: 币安广场
- **封面**: binance-content-cover.png
- **字数**: ~2300 字

### 3. 币安注册&KYC 完整教程（2026 最新版）
- **文件**: `source/posts/binance/binance-register-kyc-guide.md`
- **分类**: 币安广场，新手教程
- **封面**: binance-content-cover.png
- **字数**: ~3500 字

---

## 分类统计

| 分类 | 文章数 | 新增 |
|------|--------|------|
| 漏洞复现 | - | +1 |
| 资产收集 | - | +1 |
| 币安广场 | - | +2 |
| 新手教程 | - | +1 |

---

## Git 提交

| 提交 ID | 信息 |
|--------|------|
| bc90cf9 | Fix: 更新 Cloudflare Pages API Token |
| 608af86 | Feat: 添加自定义封面图（ARL/币安主题） |
| 1e932c2 | Feat: 新增 ARL 海外站点资产收集教程 + 币安广场内容分类 |

---

## 部署问题修复

**问题**: Cloudflare Token 无效
**解决**: 更新为新 token `axDrVCSg3Idlt6s8kGCyN3710egHlVczrGK9SeVr`
**状态**: ✅ 已修复

---

## 下次发布检查清单

- [ ] 检查 YAML front matter
- [ ] 确认文章在 `source/posts/` 目录
- [ ] 运行本地备份
- [ ] 验证 Cloudflare token 有效性

---

## 2026-03-17 04:40 UTC - 博客内容清理

**操作**: 删除 220 篇旧 auto-crypto 文章，保留重要技术文章
**保留内容**:
- 404-not-found.md
- 502-bad-gateway.md
- connection-reset.md
- hello-world.md
- 今日新文章 (AI Agent/内容工厂/RedTeam)
- auto-security/auto-tech 多样化内容

**结果**:
- Hugo 构建：178 页面，357ms
- Git 推送：成功
- 网站状态：HTTP 200 正常
- Cloudflare Pages：自动部署中

**内容策略**:
- 严格执行 200 字最低要求
- 多样化内容（安全/技术/币圈）
- 删除重复低质量 crypto 内容

---

*创建时间：2026-03-06 08:59 UTC | 最后更新：2026-03-17 04:40 UTC*
