# 博客部署检查清单

## ⚠️ 发布前必查（每次推送前逐项确认）

### 1. 敏感信息检查
- [ ] 确认无 `.env` 文件包含在提交中
- [ ] 确认无 API Key、Secret、Token 等敏感信息
- [ ] 确认无数据库密码、服务器凭证
- [ ] 运行 `git status` 检查是否有意外文件

**检查命令**：
```bash
# 检查是否有敏感文件
git status --short | grep -E "\.env|credentials|secret|key"

# 检查提交内容是否包含敏感词
git diff --cached | grep -iE "api_key|secret|password|token"
```

### 2. 仓库结构检查
- [ ] 确认只推送博客相关文件
- [ ] 确认无 ClawGuard-BNB、03_Resources、agents、redteam 等不相干目录
- [ ] 确认当前在正确的子仓库目录：`01_Projects/01_博客运营/blog/`

**正确仓库结构**：
```
blog/
├── .github/workflows/deploy.yml
├── config.toml
├── content/posts/      # 或 source/posts/
├── layouts/
├── public/
├── static/
└── themes/
```

**错误结构**（出现以下目录立即停止）：
- ❌ ClawGuard-BNB/
- ❌ 03_Resources/
- ❌ 02_Areas/
- ❌ agents/
- ❌ redteam/
- ❌ memory/
- ❌ tasks/

### 3. 文章内容检查
- [ ] 确认文章在正确的目录（source/posts/ 或 content/posts/）
- [ ] 确认 YAML front matter 完整（title、date、categories、tags、draft）
- [ ] 确认图片链接可访问（测试 cdn.nodeimage.com 或其他图床）
- [ ] 确认无"Plus"等敏感字眼（替换为"Business Team"）
- [ ] 运行本地 Hugo 构建测试

**本地测试命令**：
```bash
cd /root/.openclaw/workspace/01_Projects/01_博客运营/blog
hugo --gc --minify --forceSyncStatic
# 检查 public/posts/ 下文章是否正常生成
grep -c "白屏" public/posts/codex-tm-redeem-guide/index.html  # 应 > 0
grep -c "cdn.nodeimage.com" public/posts/codex-tm-redeem-guide/index.html  # 应 > 0
```

### 4. Git 操作检查
- [ ] 确认当前分支是 `main`（不是 master）
- [ ] 确认远程仓库是 `wizawn/blog`（不是其他仓库）
- [ ] 提交信息清晰描述变更内容

**检查命令**：
```bash
git branch          # 应在 main 分支
git remote -v       # 应指向 wizawn/blog
git log -1          # 确认最近提交
```

### 5. 推送后验证
- [ ] 检查 GitHub Actions 构建状态（成功/失败）
- [ ] 检查 Cloudflare Pages 部署状态
- [ ] 访问博客确认文章正常显示
- [ ] 检查图片是否正常加载

**验证命令**：
```bash
# 检查 GitHub 提交
curl -s "https://api.github.com/repos/wizawn/blog/commits?per_page=3" | jq -r '.[].commit.message'

# 检查 GitHub Actions
curl -s "https://api.github.com/repos/wizawn/blog/actions/runs?per_page=3" | jq -r '.workflow_runs[] | "\(.status) - \(.conclusion) - \(.head_commit.message)"'

# 检查博客内容
curl -sL "https://blog.caowo.de/posts/codex-tm-redeem-guide/" | grep -c "白屏"
curl -sL "https://blog.caowo.de/posts/codex-tm-redeem-guide/" | grep -c "cdn.nodeimage.com"
```

---

## 🚨 历史问题回顾（2026-03-25 教训）

### 问题 1：敏感凭证泄露
**问题**：币安 API Key/Secret 被推送到 GitHub
**影响**：需要删除整个 git 历史，强制推送
**解决**：
```bash
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch ClawGuard-BNB/.env' --prune-empty --tag-name-filter cat -- --all
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all
```

### 问题 2：仓库结构混乱
**问题**：wizawn/blog 仓库包含 3 万+ 个不相干文件
**影响**：需要删除 master 分支，重新设置默认分支
**解决**：
```bash
# 设置 main 为默认分支
curl -X PATCH -H "Authorization: Bearer <token>" -d '{"default_branch":"main"}' https://api.github.com/repos/wizawn/blog

# 删除 master 分支
curl -X DELETE -H "Authorization: Bearer <token>" https://api.github.com/repos/wizawn/blog/git/refs/heads/master
```

### 问题 3：Hugo 图片不显示
**问题**：markdown 图片语法被 Hugo 过滤，HTML 标签被 goldmark 阻止
**影响**：文章内容截断，图片不显示
**解决**：
```toml
# config.toml 添加
[markup.goldmark.renderer]
  unsafe = true
```
```html
<!-- 使用 HTML img 标签而非 markdown -->
<img src="https://cdn.nodeimage.com/i/xxx.webp" alt="描述" style="max-width: 100%;">
```

### 问题 4：定时发布失败
**问题**：
- 15:00 发布错过（后台进程未运行）
- 18:00 发布失败（Clash 代理退出）
**影响**：当日发布成功率仅 57%（4/7）
**解决**：
```bash
# 添加 Cron 定时任务
0 6,9,12,15,18,21,23 * * * cd /root/.openclaw/workspace && /usr/bin/python3 tasks/scheduled_publisher_bg.py >> logs/cron_publish.log 2>&1

# 确保 Clash 代理运行
nohup clash -d /root/.config/clash -f /root/.config/clash/config.yaml > /root/.config/clash/clash.log 2>&1 &
```

---

## 📋 发布流程（标准 SOP）

### 发布前
1. 在 blog 子目录操作：`cd /root/.openclaw/workspace/01_Projects/01_博客运营/blog`
2. 运行敏感信息检查
3. 运行本地 Hugo 构建测试
4. 确认文章和图片正常

### 发布中
1. `git add <files>`
2. `git commit -m "docs: 描述清楚变更内容"`
3. `git push`（确认推送到 wizawn/blog）

### 发布后
1. 检查 GitHub Actions 构建状态
2. 等待 2-3 分钟让 Cloudflare Pages 部署
3. 访问博客验证文章和图片
4. 更新 memory/blog-deploy-log.md

---

## 🔑 关键配置

### .gitignore（确保包含）
```
.env
*.env
node_modules/
.DS_Store
logs/
*.log
```

### config.toml（关键配置）
```toml
[markup.goldmark.renderer]
  unsafe = true  # 允许 HTML 标签

baseURL = 'https://blog.caowo.de/'
contentDir = 'source'  # 或 'content'
```

### .github/workflows/deploy.yml（关键配置）
```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    submodules: recursive  # 递归拉取子模块
    fetch-depth: 0
```

---

*最后更新：2026-03-26 01:05 UTC*
*教训来源：2026-03-25 发布事故*
