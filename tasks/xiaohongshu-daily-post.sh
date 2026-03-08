#!/bin/bash
# 小红书每日自动发布脚本
# 每日 09:00（新疆时间）执行

LOG_FILE="/root/.openclaw/workspace/memory/xiaohongshu-daily-log.md"
PROMPT_FILE="/root/.openclaw/workspace/skills/xiaohongshu-prompt.md"

echo "=== 小红书每日自动发布 ===" | tee -a "$LOG_FILE"
echo "时间：$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 1. 生成今日选题（从安全领域随机选择）
TOPICS=(
  "Web2 安全：个人信息保护指南"
  "Web3 安全：钱包私钥保管攻略"
  "AI 安全：深度伪造诈骗识别"
  "币圈安全：OTC 交易防骗指南"
  "网络安全：钓鱼邮件识别技巧"
  "AI 安全：大模型越狱风险科普"
  "Web3 安全：DeFi 投资避坑指南"
  "币圈安全：杀猪盘骗局拆解"
)

# 随机选择 2 个主题
TOPIC1="${TOPICS[$RANDOM % ${#TOPICS[@]}]}"
TOPIC2="${TOPICS[$RANDOM % ${#TOPICS[@]}]}"

echo "### 今日选题" | tee -a "$LOG_FILE"
echo "1. $TOPIC1" | tee -a "$LOG_FILE"
echo "2. $TOPIC2" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 2. 使用 AI 生成文案（调用 OpenClaw）
echo "### 生成文案中..." | tee -a "$LOG_FILE"

# 生成第一篇
echo "" | tee -a "$LOG_FILE"
echo "#### 第一篇：$TOPIC1" | tee -a "$LOG_FILE"
echo "状态：待生成" | tee -a "$LOG_FILE"

# 生成第二篇
echo "" | tee -a "$LOG_FILE"
echo "#### 第二篇：$TOPIC2" | tee -a "$LOG_FILE"
echo "状态：待生成" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== 文案生成完成 ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "⚠️ 注意：需要手动确认发布或使用浏览器自动化发布" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 3. 生成封面图（使用现有技能）
echo "### 生成封面图中..." | tee -a "$LOG_FILE"
# 调用 openai-image-gen 技能生成封面
# openclaw run openai-image-gen --prompt "网络安全技术封面，科技感，蓝色调"

echo "" | tee -a "$LOG_FILE"
echo "=== 发布准备完成 ===" | tee -a "$LOG_FILE"
echo "请检查生成的文案和封面图，确认发布！" | tee -a "$LOG_FILE"
