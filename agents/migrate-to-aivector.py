#!/usr/bin/env python3
"""
将现有文件式记忆迁移到 AIVectorMemory 向量记忆系统
"""

import json
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
BACKUP_DIR = Path("/root/.openclaw/workspace/memory-backup-20260302_132256")

# 迁移计划
migration_plan = {
    "用户偏好": {
        "scope": "user",
        "tags": ["preference", "用户偏好"],
        "files": ["2026-02-27.md", "2026-03-02.md"],
        "keywords": ["沟通偏好", "信任模式", "厌恶", "立场"]
    },
    "项目知识": {
        "scope": "project",
        "tags": ["knowledge", "项目知识"],
        "files": ["blog-deploy-log.md", "context-management.md", "heartbeat-state.json"],
        "keywords": ["博客部署", "内容工厂", "漏洞采集", "定时任务"]
    },
    "踩坑记录": {
        "scope": "project",
        "tags": ["pitfall", "踩坑"],
        "files": ["2026-02-28.md", "2026-03-02.md"],
        "keywords": ["博客主题", "文章目录", "知乎发布", "误删"]
    },
    "学习笔记": {
        "scope": "project",
        "tags": ["learning", "知识"],
        "files": ["src-learning-notes.md", "vuln-articles.md"],
        "keywords": ["SRC", "漏洞", "渗透测试"]
    }
}

print("=" * 60)
print("🧠 AIVectorMemory 迁移脚本")
print("=" * 60)

print("\n📋 迁移计划:")
for category, config in migration_plan.items():
    print(f"\n  {category}:")
    print(f"    Scope: {config['scope']}")
    print(f"    Tags: {config['tags']}")
    print(f"    Files: {config['files']}")
    print(f"    Keywords: {config['keywords']}")

print("\n\n📝 迁移步骤:")
print("""
1. 安装 AIVectorMemory (已完成)
   ✅ pip install aivectormemory

2. 配置 MCP Server
   ✅ .mcp.json 已创建

3. 迁移现有记忆
   使用以下命令手动迁移:
   
   # 用户偏好
   remember(content="[用户偏好内容]", tags=["preference", "用户偏好"], scope="user")
   
   # 项目知识
   remember(content="[博客部署流程]", tags=["knowledge", "博客部署"], scope="project")
   remember(content="[内容工厂 SOP]", tags=["knowledge", "内容工厂"], scope="project")
   
   # 踩坑记录
   remember(content="[博客主题误删教训]", tags=["pitfall", "踩坑"], scope="project")
   remember(content="[文章目录结构问题]", tags=["pitfall", "踩坑"], scope="project")
   
   # 学习笔记
   remember(content="[SRC 挖洞经验]", tags=["learning", "SRC"], scope="project")

4. 验证迁移
   recall(query="博客部署", top_k=5)
   recall(query="用户偏好", scope="user", top_k=5)

5. 更新 AGENTS.md
   ✅ 已添加 AIVectorMemory 使用说明
""")

print("\n\n✅ 迁移准备完成！")
print("\n📁 备份位置:", BACKUP_DIR)
print("📁 记忆位置:", MEMORY_DIR)
print("📁 MCP 配置:", Path("/root/.openclaw/workspace/.mcp.json"))

# 生成迁移记忆内容示例
print("\n\n📋 迁移记忆内容示例:")
print("=" * 60)

# 用户偏好示例
print("\n1️⃣ 用户偏好 (scope: user):")
print("-" * 60)
print("""
content:
用户沟通偏好：
- 简短直接，不要问"还有什么需要我做的吗"
- 结果导向，要的是成品，不是过程汇报
- 讨厌重复，同样的话不说第二遍
- 给指令后期待立刻执行，不是来回确认

信任模式：
- 低容忍度但给机会
- 用行动赢回信任，不是用解释

厌恶：
- 被提醒三次才动的自己
""")

# 项目知识示例
print("\n2️⃣ 项目知识 (scope: project):")
print("-" * 60)
print("""
content:
博客部署流程：
1. 文章添加到 content/posts/ 目录
2. 确保 YAML front matter (title, date, draft, categories, tags)
3. git add && git commit && git push
4. 等待 Cloudflare 自动部署 (2-3 分钟)
5. 验证 https://blog.caowo.de/posts/

内容工厂目录结构：
wizawncontext/
├── 01-灵感与素材库/
├── 02-选题池/
├── 03-内容工厂/
└── 04-已发布归档/
""")

# 踩坑记录示例
print("\n3️⃣ 踩坑记录 (tags: [\"踩坑\"]):")
print("-" * 60)
print("""
content:
博客主题误删教训：
- 回滚时不该动 themes/目录
- 应该先备份再修改
- Stack 主题要求文章在 content/posts/ 目录

知乎发布限制：
- 包含大量代码的文章容易被判定为恶意脚本
- XXE 漏洞文章被拦截
- AI 主题文章可以通过
""")

print("\n\n🎯 下一步:")
print("1. 运行 aivectormemory run web 启动 Web 看板")
print("2. 访问 http://localhost:9080 查看记忆")
print("3. 使用 remember/recall 工具手动迁移记忆")
print("4. 验证语义搜索功能")
