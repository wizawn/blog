# 小红书自动发布配置

## 发布时间
- **每日**: 新疆时间 09:00（UTC 01:00）
- **数量**: 2 篇/天
- **方式**: 自动选题 + 自动生成 + 自动发布

## 选题范围

### Web2 安全
- 个人信息保护
- 钓鱼邮件识别
- 密码安全攻略
- 设备安全防护

### Web3 安全
- 钱包私钥保管
- 智能合约漏洞
- DeFi 投资避坑
- 链上诈骗识别

### AI 安全
- 深度伪造识别
- AI 诈骗防范
- 数据投喂风险
- Prompt 安全科普

### 币圈安全
- OTC 交易防骗
- 杀猪盘拆解
- 传销币识别
- 交易所选择

## 创作流程

1. **自动选题** - 从选题库随机选择 2 个主题
2. **AI 生成文案** - 使用 xiaohongshu-prompt.md 生成爆款文案
3. **自动生成封面** - 调用 openai-image-gen 生成封面图
4. **浏览器发布** - 使用 xiaohongshu-ops-skill 自动发布

## 配置文件

- **Prompt**: `/root/.openclaw/workspace/skills/xiaohongshu-prompt.md`
- **脚本**: `/root/.openclaw/workspace/tasks/xiaohongshu-daily-post.sh`
- **日志**: `/root/.openclaw/workspace/memory/xiaohongshu-daily-log.md`
- **Cron 日志**: `/root/.openclaw/workspace/memory/xiaohongshu-cron.log`

## Cron 配置

```bash
0 1 * * * /root/.openclaw/workspace/tasks/xiaohongshu-daily-post.sh
```

## 账号配置

- **平台**: 小红书
- **登录方式**: 浏览器扫码（已登录）
- **Browser Profile**: openclaw
- **用户 ID**: 631e9d20000000001501563c

---
*配置时间：2026-03-07 01:54 UTC*
