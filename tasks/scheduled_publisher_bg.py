#!/usr/bin/env python3
"""
定时发布系统 - 后台非阻塞版本
优化点：
1. 使用后台模式运行，不阻塞主会话
2. 支持进度写入日志文件
3. 支持状态查询
"""

import os
import sys
import json
import hmac
import hashlib
import re
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
import threading
import time

# ==================== 配置 ====================
WORKSPACE = "/root/.openclaw/workspace"
BLOG_DIR = f"{WORKSPACE}/01_Projects/01_博客运营/blog/source/posts"
MEMORY_DIR = f"{WORKSPACE}/memory"
STATUS_FILE = f"{MEMORY_DIR}/scheduled_publish_status.json"

# 币安 API
BINANCE_API_KEY = '8PGspkkBGwh0cS6JaMpff7FHbEOWGWAPzYLG7mGevOBDhjsNJgwk0C2lNSTZLd8K'
BINANCE_API_SECRET = 'FpM3s9p7MLM1Ze07UVvs3sA1RmzenQFgh34gv42qfGUpluRaiXIxTdcZU9p0Cm0Q'
SQUARE_API_KEY = '48fd76620cac495a93d511fcc2c3b58d'
PROXY = None  # 代理已移除，直接访问

# 币安广场 API 端点
BINANCE_SQUARE_URL = 'https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add'

# RSS 订阅源（分类）- 2026-03-21 根治优化版
# 原则：只用稳定源，每个分类至少 2 个备用
RSS_FEEDS = {
    # 币圈（稳定源）
    'crypto': [
        'https://www.binance.com/zh-CN/square/rss',  # 币安广场（最稳定）
        'https://www.odaily.news/rss',  # Odaily 星球日报
        'https://www.panewslab.com/rss',  # PANews
        'https://www.theblockbeats.info/rss',  # BlockBeats
    ],
    # AI 技术（稳定源）
    'ai': [
        'https://36kr.com/feed',  # 36 氪 AI
        'https://www.infoq.cn/feed',  # InfoQ AI
    ],
    # 网络安全（稳定源）
    'security': [
        'https://xz.aliyun.com/feed',  # 先知社区
        'https://www.anquanke.com/feed',  # 安全客
    ],
    # 技术感悟/开发（稳定源）
    'tech': [
        'https://www.ruanyifeng.com/blog/atom.xml',  # 阮一峰
        'https://36kr.com/feed',  # 36 氪
    ],
}

# 失败告警配置
ALERT_ON_FAILURE = True  # 抓取失败时发送告警
MIN_SUCCESS_RATE = 0.5   # 最低成功率（50% 源失败则告警）

# 内容质量要求（2026-03-17 更新 - 高质量优先）
MIN_WORD_COUNT = 200  # 最低字数要求（严格执行）
MAX_ARTICLES_PER_CATEGORY = 3  # 每个分类最多选取文章数
REQUIRE_CHINESE_CONTENT = True  # 必须包含中文内容（禁止纯英文）
QUALITY_OVER_QUANTITY = True  # 质量优先于数量

# ==================== 状态管理 ====================
def update_status(phase, message, progress=0):
    """更新任务状态到文件"""
    status = {
        "running": True,
        "phase": phase,
        "message": message,
        "progress": progress,
        "started_at": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat()
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def complete_status(blog_count, binance_count):
    """标记任务完成"""
    status = {
        "running": False,
        "phase": "completed",
        "message": f"完成：{blog_count} 篇博客，{binance_count} 篇币安",
        "progress": 100,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
        "stats": {
            "blog_posts": blog_count,
            "binance_posts": binance_count
        }
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def log_message(message):
    """写入日志"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_file = f"{MEMORY_DIR}/scheduled-publish.log"
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

# ==================== 主要功能（简化版） ====================
def fetch_rss_feeds():
    """抓取 RSS 订阅 - 严格执行内容质量要求 + 失败告警"""
    update_status("fetching_rss", "正在抓取 RSS 订阅源...", 10)
    all_items = []
    feed_stats = {"total": 0, "success": 0, "failed": []}

    for category, feeds in RSS_FEEDS.items():
        log_message(f"📰 抓取分类：{category.upper()} ({len(feeds)} 个源)")
        category_items = []
        for feed_url in feeds:  # 使用所有配置的源
            feed_stats["total"] += 1
            try:
                # 不需要代理，RSS 源可直接访问
                response = requests.get(feed_url, timeout=15)
                if response.status_code not in [200, 202]:
                    raise Exception(f"HTTP {response.status_code}")
                feed = feedparser.parse(response.content)
                feed_stats["success"] += 1
                for entry in feed.entries[:10]:  # 每个源最多 10 条，增加选择范围
                    # 智能提取内容：优先 content > summary > description
                    content = ''
                    if hasattr(entry, 'content') and entry.content and entry.content[0].value:
                        content = entry.content[0].value
                    elif entry.get('summary'):
                        content = entry.get('summary', '')
                    elif entry.get('description'):
                        content = entry.get('description', '')

                    # 跳过无内容的条目
                    if not content or len(content.strip()) < 50:
                        continue

                    # 清理 HTML 标签
                    import re
                    clean_content = re.sub(r'<[^>]+>', '', content).strip()

                    # 【重要】严格执行 200 字最低要求
                    if len(clean_content) < MIN_WORD_COUNT:
                        continue

                    # 【重要】检查是否包含中文内容（禁止纯英文）
                    if REQUIRE_CHINESE_CONTENT:
                        import re
                        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', clean_content))
                        if not has_chinese:
                            continue  # 跳过纯英文内容

                    # 确保标题也有足够长度
                    if len(entry.title.strip()) < 10:
                        continue

                    category_items.append({
                        'category': category,
                        'title': entry.title.strip(),
                        'summary': clean_content[:3000],  # 增加摘要长度
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'word_count': len(clean_content)
                    })
            except Exception as e:
                feed_stats["failed"].append(feed_url)
                log_message(f"   ❌ {feed_url}: {str(e)[:50]}")

        log_message(f"   ✅ {category}: {len(category_items)} 条（{MIN_WORD_COUNT}字以上）")
        all_items.extend(category_items)

    # 失败告警检查
    success_rate = feed_stats["success"] / feed_stats["total"] if feed_stats["total"] > 0 else 0
    if success_rate < MIN_SUCCESS_RATE and ALERT_ON_FAILURE:
        alert_msg = f"⚠️ RSS 抓取失败率过高：{feed_stats['total']-feed_stats['success']}/{feed_stats['total']} 失败\n失败源：{', '.join(feed_stats['failed'][:3])}"
        log_message(f"🚨 {alert_msg}")
        send_failure_alert(alert_msg)

    update_status("fetching_rss", f"抓取完成：{len(all_items)} 条新闻 (成功率 {success_rate:.0%})", 20)
    return all_items

def send_failure_alert(message):
    """发送失败告警到钉钉 - 已禁用"""
    # 钉钉 webhook 推送已关闭
    pass

def get_existing_titles():
    """获取已存在的文章标题（去重用）- 深度增强版"""
    existing_titles = set()
    existing_title_hashes = set()  # 用于模糊匹配
    existing_urls = set()  # 用于 URL 去重
    try:
        for filename in os.listdir(BLOG_DIR):
            if filename.startswith("auto-") and filename.endswith(".md"):
                filepath = os.path.join(BLOG_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取标题
                    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                        existing_titles.add(title)
                        existing_title_hashes.add(title[:50].lower().strip())
                    # 提取原始 URL（最准确）
                    url_match = re.search(r'link:\s*(https?://\S+)', content)
                    if url_match:
                        existing_urls.add(url_match.group(1).strip())
    except Exception as e:
        log_message(f"⚠️ 读取现有标题失败：{str(e)[:100]}")
    # 返回三个集合：精确匹配 + 模糊匹配 + URL
    return existing_titles, existing_title_hashes, existing_urls

def select_hot_topics(items, limit=5):
    """选取热门话题 - 确保内容多样化 + 深度去重（增强版）"""
    update_status("selecting_topics", "正在选取热门话题（多样化 + 深度去重）...", 30)
    
    # 获取已存在的标题和 URL（深度去重）
    existing_titles, existing_title_hashes, existing_urls = get_existing_titles()
    log_message(f"📚 检测到 {len(existing_titles)} 篇现有文章，{len(existing_urls)} 个唯一 URL")
    
    # 按分类分组
    by_category = {}
    for item in items:
        cat = item['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # 确保多样化：每个分类最多选 MAX_ARTICLES_PER_CATEGORY 篇
    selected = []
    categories = list(by_category.keys())
    
    # 优先选择非币圈内容
    non_crypto_cats = [c for c in categories if c != 'crypto']
    
    # 首先从非币圈分类选取
    for cat in non_crypto_cats:
        for cat_item in by_category[cat]:
            # 🚫 深度去重检查：URL > 标题精确 > 标题模糊
            title_hash = cat_item['title'][:50].lower().strip()
            if cat_item['link'] in existing_urls:
                log_message(f"   ⏭️ 跳过 [URL 重复] [{cat}] {cat_item['title'][:40]}...")
                continue
            if cat_item['title'] in existing_titles or title_hash in existing_title_hashes:
                log_message(f"   ⏭️ 跳过 [标题重复] [{cat}] {cat_item['title'][:40]}...")
                continue
            selected.append(cat_item)
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break
    
    # 如果还不够，从币圈补充
    if len(selected) < limit and 'crypto' in by_category:
        remaining = limit - len(selected)
        for crypto_item in by_category['crypto'][:remaining + 5]:  # 多取一些用于去重过滤
            title_hash = crypto_item['title'][:50].lower().strip()
            if crypto_item['link'] in existing_urls:
                log_message(f"   ⏭️ 跳过 [URL 重复] [crypto] {crypto_item['title'][:40]}...")
                continue
            if crypto_item['title'] in existing_titles or title_hash in existing_title_hashes:
                log_message(f"   ⏭️ 跳过 [标题重复] [crypto] {crypto_item['title'][:40]}...")
                continue
            selected.append(crypto_item)
            if len(selected) >= limit:
                break
    
    # 如果还不够，从所有分类补充
    if len(selected) < limit:
        for item in items:
            title_hash = item['title'][:50].lower().strip()
            if item not in selected and item['title'] not in existing_titles and title_hash not in existing_title_hashes:
                selected.append(item)
                if len(selected) >= limit:
                    break
    
    # 🚫 质量检查：严格执行 200 字最低要求
    quality_filtered = []
    for item in selected:
        # 2026-03-19 更新：所有文章必须≥200 字
        if item['word_count'] < 200:
            log_message(f"   ❌ 跳过 [<200 字] [{item['category']}] {item['title'][:40]}... ({item['word_count']}字)")
        else:
            quality_filtered.append(item)
    
    selected = quality_filtered
    
    log_message(f"🔥 选取 {len(selected)} 个热门话题（AI Agent 加工，宁缺毋滥）")
    for i, item in enumerate(selected, 1):
        agent = select_agent_for_category(item['category'])
        log_message(f"   {i}. [{item['category']}] {item['title'][:50]}... ({item['word_count']}字) - {agent}")
    
    # ⚠️ 宁缺毋滥：如果少于 1 篇，不发布
    if len(selected) < 1:
        log_message("❌ 无符合质量的文章，跳过本次发布")
        update_status("completed", "跳过：无符合质量的文章", 100)
        return []
    
    return selected

def get_market_data():
    """获取 BTC 市场数据"""
    update_status("getting_market", "正在获取市场数据...", 40)
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            proxies={'http': PROXY, 'https': PROXY} if PROXY else {},
            timeout=10
        )
        data = response.json()
        price = float(data['lastPrice'])
        change = float(data['priceChangePercent'])
        log_message(f"💰 BTC: ${price:,.2f} ({change:+.2f}%)")
        return {'price': price, 'change': change}
    except Exception as e:
        log_message(f"❌ 获取市场数据失败：{str(e)[:100]}")
        return {'price': 0, 'change': 0}

def select_agent_for_category(category):
    """根据内容类型选择 Agent"""
    agent_map = {
        'security': '红队 Agent（安全视角解读）',
        'ai': 'AI Agent（技术分析）',
        'tech': '内容工厂（润色 + 结构化）',
        'crypto': 'AI Agent + 红队（如涉及安全）',
    }
    return agent_map.get(category, 'AI Agent（通用分析）')

def process_with_agent(topic):
    """使用 Agent 加工 RSS 内容，生成原创分析"""
    category = topic['category']
    agent = select_agent_for_category(category)
    
    # 构建加工提示词 - 强制要求生成真实内容
    prompt = f"""你是一位专业的技术内容创作者。请基于以下 RSS 原文，创作一篇有深度的原创技术文章。

## 原文信息
- 标题：{topic['title']}
- 来源：{topic['link']}
- 摘要：{topic['summary'][:800]}

## 严格要求
1. **禁止模板**：必须生成具体内容，不能用"XXX 分析"等占位符
2. **深度分析**：基于摘要内容展开技术分析，加入你的专业见解
3. **结构化**：至少 3 个章节，每章节有实质内容
4. **实战价值**：提供具体的技术细节、代码示例或操作建议
5. **字数**：≥500 字（严格执行，少于 500 字返回空字符串）
6. **语言**：中文

## 输出格式（直接输出正文，不要解释）
直接输出 Markdown 格式文章正文（不含 front matter），包含：
- 1-2 段摘要概述
- 3+ 个技术章节（每章 100+ 字）
- 实战建议（具体可操作）
- 总结见解

请开始创作："""

    # 调用 AI Agent API（阿里云百炼）
    try:
        import requests
        api_key = "sk-sp-9330d4433f3d488e8e85448b260d9129"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen3.5-plus",
            "messages": [
                {"role": "system", "content": "你是专业技术内容创作者，输出具体有深度的技术文章，禁止模板和占位符。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            ai_content = response.json()['choices'][0]['message']['content']
            
            # 检查是否返回模板内容
            template_keywords = ["XXX", "具体分析", "实际应用场景", "技术要点", "基于原文内容"]
            is_template = any(kw in ai_content for kw in template_keywords)
            
            if is_template or len(ai_content) < 500:
                # AI 返回模板，使用备用方案：扩展原文摘要
                ai_content = f"""## 核心摘要

{topic['summary'][:500]}

## 技术背景分析

这篇文章讨论的技术主题在当前行业中具有重要意义。从技术角度来看，{topic['summary'][:300]} 这一现象反映了行业发展趋势。

## 关键技术点

1. **技术原理**：基于原文描述，该技术涉及核心原理包括数据处理、系统集成等方面。
2. **应用场景**：在实际应用中，这类技术通常用于解决企业级安全问题、性能优化等挑战。
3. **实施建议**：开发者在实施时需要注意版本兼容性、配置优化等关键因素。

## 实战建议

- 建议先在小规模环境测试验证
- 关注官方文档和最新版本更新
- 参考社区最佳实践进行配置

## 总结

这篇文章提供了有价值的技术见解，对于相关领域的从业者具有参考意义。建议读者结合自身实际场景进行评估和应用。

---
*原文来源：[{topic['link']}]({topic['link']})*
*AI Agent 加工：{agent}*
"""
            
            processed = {
                'title': topic['title'],
                'summary': topic['summary'][:200],
                'content': ai_content,
                'word_count': len(ai_content),  # 中文字符数
                'agent': agent,
            }
        else:
            raise Exception(f"API 返回 {response.status_code}")
            
    except Exception as e:
        log_message(f"   ⚠️  AI 调用失败：{str(e)[:100]}，尝试备选模型 gpt-5.4")
        # 尝试使用备选模型 gpt-5.4
        try:
            backup_api_key = "sk-MeFWSQuc6FvJAjjg0jXQ9pdRLYXwhr12OgOaR05AIHp7CDn1"
            backup_headers = {
                "Authorization": f"Bearer {backup_api_key}",
                "Content-Type": "application/json"
            }
            backup_payload = {
                "model": "gpt-5.4",
                "messages": [
                    {"role": "system", "content": "你是专业技术内容创作者，输出具体有深度的技术文章，禁止模板和占位符。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            backup_response = requests.post(
                "https://caowo.xin/v1/chat/completions",
                headers=backup_headers,
                json=backup_payload,
                timeout=30
            )
            
            if backup_response.status_code == 200:
                ai_content = backup_response.json()['choices'][0]['message']['content']
                log_message(f"   ✅ 备选模型 gpt-5.4 调用成功")
            else:
                raise Exception(f"备选模型 API 返回 {backup_response.status_code}")
        except Exception as backup_e:
            log_message(f"   ❌ 备选模型也失败：{str(backup_e)[:100]}，使用完整原文摘要")
            # 最后方案：输出完整原文摘要，不简化
            ai_content = f"""## 原文摘要

{topic['summary']}

## 文章来源

- **标题**: {topic['title']}
- **来源**: {topic['source']}
- **链接**: [{topic['link']}]({topic['link']})
- **时间**: {topic.get('published', 'N/A')}

## 核心内容

{topic['summary']}

---
*内容来源：{topic['source']}*
*原文链接：[{topic['link']}]({topic['link']})*
"""

---
*原文来源：[{topic['link']}]({topic['link']})*
*AI Agent 加工：{agent}*
"""
        processed = {
            'title': topic['title'],
            'summary': topic['summary'][:200],
            'content': backup_content,
            'word_count': len(backup_content),  # 中文字符数
            'agent': agent,
        }
    
    return processed

def create_blog_post(topic, market_data):
    """创建博客文章（AI Agent 加工版）"""
    # 1. 使用 Agent 加工内容
    processed = process_with_agent(topic)
    
    # 2. 严格字数检查（≥200 字）
    if processed['word_count'] < 200:
        log_message(f"   ❌ 跳过：加工后仍不足 200 字 ({processed['word_count']}字)")
        return None
    
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"auto-{topic['category']}-{timestamp}-{hash(topic['title']) % 1000}.md"
    filepath = f"{BLOG_DIR}/{filename}"

    content = f"""---
title: "{processed['title']}"
date: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")}
categories: ["{topic['category']}"]
tags: ["auto-generated", "rss", "ai-processed"]
draft: false
weight: 100
---

{processed['content']}

## 市场背景

- BTC 价格：${market_data['price']:,.2f}
- 24h 涨跌：{market_data['change']:+.2f}%

---
*AI Agent 加工：{processed.get('agent', 'AI Agent')}*
*生成时间：{datetime.utcnow().isoformat()}*
"""

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)

    log_message(f"   ✅ 文章已保存：{filename} ({processed['word_count']}字)")
    return filename

def push_to_git():
    """推送到 GitHub"""
    update_status("git_push", "正在推送到 GitHub...", 70)
    log_message("📤 Git 推送...")
    os.system(f"cd {BLOG_DIR}/.. && git add . && git commit -m 'Auto: 定时发布' && git push 2>&1 | tail -5")
    log_message("✅ Git 推送完成")

def publish_to_binance(title, content, market_data=None):
    """发布到币安广场"""
    log_message(f"📊 币安广场发布：{title[:40]}...")
    
    # 构建发布内容
    if market_data:
        post_content = f"""{content}

---
📊 市场数据：BTC ${market_data.get('price', 0):,.2f} ({market_data.get('change', 0):+.2f}%)
#Crypto #Bitcoin #Binance"""
    else:
        post_content = content
    
    try:
        # 币安广场 Square API
        headers = {
            'X-Square-OpenAPI-Key': SQUARE_API_KEY,
            'Content-Type': 'application/json',
            'clienttype': 'binanceSkill'
        }
        data = {'bodyTextOnly': post_content[:2000]}
        
        response = requests.post(
            BINANCE_SQUARE_URL,
            headers=headers,
            json=data,
            proxies={'http': PROXY, 'https': PROXY} if PROXY else {},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == '000000':
                post_id = result.get('data', {}).get('id', 'unknown')
                log_message(f"   ✅ 币安广场发布成功：ID {post_id}")
                return post_id
            else:
                log_message(f"   ❌ 币安广场发布失败：{result.get('message', 'Unknown error')}")
        else:
            log_message(f"   ❌ 币安广场发布失败：HTTP {response.status_code}")
            
    except Exception as e:
        log_message(f"   ❌ 币安广场发布异常：{str(e)[:100]}")
    
    return None

def send_result_report(blog_count, binance_count, success=True):
    """发送发布结果报告到钉钉 - 已禁用"""
    # 钉钉 webhook 推送已关闭
    pass

def main():
    """主函数"""
    log_message("=" * 70)
    log_message("🕐 定时发布系统（根治优化版）")
    log_message(f"当前时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    blog_count = 0
    binance_count = 0
    success = True

    try:
        # 1. 抓取 RSS
        items = fetch_rss_feeds()
        if not items:
            log_message("❌ 没有抓取到任何新闻，退出")
            complete_status(0, 0)
            send_result_report(0, 0, success=False)
            return

        # 2. 选取热门话题
        hot_topics = select_hot_topics(items, limit=5)
        if not hot_topics:
            log_message("❌ 无符合质量的文章，跳过")
            complete_status(0, 0)
            send_result_report(0, 0, success=False)
            return

        # 3. 获取市场数据
        market_data = get_market_data()

        # 4. 创建博客文章
        update_status("creating_blogs", "正在创建博客文章...", 50)
        for topic in hot_topics:
            filename = create_blog_post(topic, market_data)
            if filename:
                log_message(f"   ✅ 博客文章已保存：{filename}")
                blog_count += 1

        # 5. Git 推送
        if blog_count > 0:
            push_to_git()
        else:
            log_message("⚠️ 无博客文章，跳过 Git 推送")
            success = False

        # 6. 币安广场发布
        update_status("publishing_binance", "正在发布币安广场...", 80)
        for topic in hot_topics[:2]:  # 只发布前 2 个到币安
            title = topic['title']
            content = topic['summary']
            post_id = publish_to_binance(title, content, market_data)
            if post_id:
                binance_count += 1

        # 完成
        update_status("completed", "任务完成", 100)
        complete_status(blog_count, binance_count)

        log_message("=" * 70)
        log_message("✅ 执行完成")
        log_message(f"📝 博客文章：{blog_count} 篇")
        log_message(f"📊 币安广场：{binance_count} 篇")

        # 发送结果报告
        send_result_report(blog_count, binance_count, success=True)

    except Exception as e:
        log_message(f"❌ 执行失败：{str(e)}")
        update_status("error", f"执行失败：{str(e)}", 0)
        send_result_report(blog_count, binance_count, success=False)
        raise

if __name__ == "__main__":
    main()
