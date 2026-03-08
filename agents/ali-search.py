#!/usr/bin/env python3
"""
阿里云通义千问 Search API - 网页搜索替代方案
使用 DashScope + 网页爬取实现搜索功能
"""

import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import quote

# 使用阿里云 DashScope 的搜索增强能力
DASHSCOPE_API_KEY = "sk-xxx"  # 从配置读取

def search_web(query, num_results=5):
    """
    使用阿里云搜索 API 进行网页搜索
    返回搜索结果列表
    """
    # 方案 1: 使用 Bing/Google 搜索 + 爬虫（无需 API key）
    search_url = f"https://www.bing.com/search?q={quote(query)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            for item in soup.select('li.b_algo', limit=num_results):
                title_elem = item.select_one('h2 a')
                snippet_elem = item.select_one('.b_caption p')
                
                if title_elem and snippet_elem:
                    results.append({
                        "title": title_elem.text.strip(),
                        "url": title_elem.get('href'),
                        "snippet": snippet_elem.text.strip()
                    })
            
            return {"success": True, "results": results}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "Search failed"}

if __name__ == "__main__":
    # 测试搜索
    result = search_web("网络安全 AI 渗透测试 2026")
    print(json.dumps(result, ensure_ascii=False, indent=2))
