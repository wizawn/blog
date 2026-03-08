#!/usr/bin/env python3
"""
阿里云通义万相生图 API 封装
用于自动生成文章封面图
"""

import requests
import json
import time
import sys

API_KEY = "sk-681ae92c28354232b24c8970dfd98ed7"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"

def generate_image(prompt, size="1024*1024", n=1, timeout=180):
    """
    生成图片
    
    Args:
        prompt: 提示词
        size: 图片尺寸 (1024*1024, 720*1280, 1280*720)
        n: 生成数量
        timeout: 超时时间（秒）
    
    Returns:
        dict: 包含图片 URL 和状态信息
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    payload = {
        "model": "wanx-v1",
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": n}
    }
    
    try:
        # 提交任务
        resp = requests.post(URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            return {"success": False, "error": f"提交失败：{resp.text}"}
        
        result = resp.json()
        task_id = result["output"]["task_id"]
        
        # 轮询任务状态
        query_url = f"{URL}/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(3)
            resp = requests.get(query_url, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            status = data["output"].get("task_status", "UNKNOWN")
            
            if status == "SUCCEEDED":
                img_url = data["output"]["results"][0]["url"]
                return {
                    "success": True,
                    "url": img_url,
                    "task_id": task_id,
                    "prompt": prompt
                }
            elif status in ["FAILED", "CANCELED"]:
                return {
                    "success": False,
                    "error": data["output"].get("message", "任务失败"),
                    "task_id": task_id
                }
        
        return {"success": False, "error": "超时未完成"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 测试提示词
    prompts = [
        "网络安全科技感封面图，代码流如雨下落，黑客剪影前景，数字锁破碎，蓝色紫色霓虹灯光，赛博朋克美学，高细节，8K 分辨率",
        "AI 机器人穿黑客卫衣，机械键盘打字，全息代码投影，神经网络连接，未来网络安全实验室，蓝色橙色配色，动态姿势",
        "网络安全工具集合桌面俯拍，笔记本电脑显示终端代码，手机显示网络扫描，咖啡杯，深色桌面设置，霓虹装饰灯光"
    ]
    
    print("🎨 通义万相生图测试\n")
    
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/3] 生成：{prompt[:50]}...")
        result = generate_image(prompt, timeout=60)
        
        if result["success"]:
            print(f"✅ 成功：{result['url']}\n")
        else:
            print(f"❌ 失败：{result['error']}\n")
        
        time.sleep(2)
