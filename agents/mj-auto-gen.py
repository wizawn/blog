#!/usr/bin/env python3
"""
Midjourney 自动生图脚本（Discord Bot 方案）
需要：Discord Bot Token + Midjourney 服务器 ID
"""

import discord
import asyncio
import re
import sys

# 配置（从环境变量读取更安全）
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"
MJ_SERVER_ID = "YOUR_SERVER_ID_HERE"  # Midjourney Discord 服务器 ID
MJ_CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"  # 生图频道 ID

# 提示词列表
PROMPTS = [
    "网络安全科技感封面图，代码流如雨下落，黑客剪影前景，数字锁破碎，蓝色紫色霓虹灯光，赛博朋克美学，高细节，8K 分辨率 --ar 16:9 --v 6",
    "AI 机器人穿黑客卫衣，机械键盘打字，全息代码投影，神经网络连接，未来网络安全实验室，蓝色橙色配色，动态姿势 --ar 16:9 --v 6",
    "网络安全工具集合桌面俯拍，笔记本电脑显示终端代码，手机显示网络扫描，咖啡杯，深色桌面设置，霓虹装饰灯光 --ar 3:4 --v 6"
]

class MJBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
    
    async def on_ready(self):
        print(f"✅ Bot 已登录：{self.user}")
        
        # 获取频道
        channel = self.get_channel(int(MJ_CHANNEL_ID))
        if not channel:
            print("❌ 未找到频道")
            await self.close()
            return
        
        print(f"✅ 频道：{channel.name}")
        
        # 发送生图请求
        for i, prompt in enumerate(PROMPTS, 1):
            print(f"\n[{i}/{len(PROMPTS)}] 发送：{prompt[:50]}...")
            await channel.send(f"/imagine prompt: {prompt}")
            await asyncio.sleep(5)  # 避免频率限制
        
        print("\n✅ 所有任务已发送")
        await self.close()

if __name__ == "__main__":
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ 请配置 Discord Bot Token")
        print("\n使用方法:")
        print("1. 访问 https://discord.com/developers/applications 创建 Bot")
        print("2. 复制 Token 填入脚本")
        print("3. 邀请 Bot 到 Midjourney 服务器")
        print("4. 运行脚本")
        sys.exit(1)
    
    client = MJBot()
    client.run(DISCORD_TOKEN)
