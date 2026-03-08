# AIVectorMemory 迁移计划

**备份时间**: 2026-03-02 13:22 UTC
**备份位置**: `/root/.openclaw/workspace/memory-backup-20260302_132256/`

---

## 当前记忆系统（文件式）

**位置**: `/root/.openclaw/workspace/memory/`

**文件列表**:
- 2026-02-24.md ~ 2026-03-02.md (每日日志)
- MEMORY.md (长期记忆)
- blog-deploy-log.md (博客部署日志)
- context-management.md (上下文管理)
- heartbeat-state.json (心跳状态)
- src-learning-notes.md (SRC 学习)
- vuln-articles.md (漏洞文章)

**总大小**: ~200KB

---

## 目标系统（向量记忆）

**工具**: AIVectorMemory MCP Server
**数据库**: `~/.aivectormemory/memory.db`
**配置**: `/root/.openclaw/.mcp.json`

---

## 迁移步骤

### 1. 安装 AIVectorMemory
```bash
pip install aivectormemory
```

### 2. 配置 MCP Server
```json
{
  "mcpServers": {
    "aivectormemory": {
      "command": "aivectormemory",
      "args": ["--project-dir", "/root/.openclaw/workspace"]
    }
  }
}
```

### 3. 迁移现有记忆
将以下记忆转换为向量记忆：

#### 用户偏好 (scope: user)
- 沟通偏好：简短直接
- 信任模式：给指令后期待立刻执行
- 厌恶：被提醒三次才动的自己

#### 项目知识 (scope: project)
- 内容工厂 SOP
- 博客部署流程
- 漏洞采集流程
- 定时任务配置

#### 踩坑记录 (tags: ["踩坑"])
- 博客主题误删
- 文章目录结构问题
- 知乎发布限制

### 4. 创建 Steering 规则
在 `AGENTS.md` 中添加：

```markdown
## AIVectorMemory 使用规则

### 新会话启动
1. `recall` (tags: ["用户偏好"], scope: "user", top_k: 10)
2. `recall` (tags: ["项目知识"], scope: "project", top_k: 20)
3. `status` 读取会话状态

### 记忆保存时机
- 用户表达偏好时 → `auto_save`
- 完成任务时 → `remember` (tags: ["任务完成"])
- 遇到错误时 → `remember` (tags: ["踩坑"])
- 学习新知识时 → `remember` (tags: ["知识"])
```

### 5. 混合记忆系统
**过渡期**: 同时保留文件式和向量式

- 文件式：原始日志、详细记录
- 向量式：快速检索、语义搜索

---

## 优势对比

| 特性 | 文件式 | 向量式 |
|------|--------|--------|
| 语义搜索 | ❌ | ✅ |
| 跨会话记忆 | ❌ | ✅ |
| 智能去重 | ❌ | ✅ |
| Token 节省 | - | 50%+ |
| 可视化 | ❌ | ✅ Web 看板 |

---

*迁移计划创建时间：2026-03-02 13:25 UTC*
