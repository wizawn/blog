---
title: "基于 OpenClaw 的全市场实时监控方案"
date: 2026-03-01T14:00:00+08:00
draft: false
categories: ['教程系列']
tags: ['自动化', '监控', 'OpenClaw']
---

# 基于 OpenClaw 的全市场实时监控方案

> **适用场景：** 股市/贵金属/加密货币实时监控  
> **技术栈：** OpenClaw + Python + 多数据源 API  
> **部署难度：** ⭐⭐ (中等)

---

## 方案概述

本方案基于 OpenClaw AI Agent，实现 7×24 小时全市场实时监控，覆盖股市、贵金属、加密货币三大市场，支持价格告警、异动检测、多渠道通知。

### 核心能力

| 模块 | 功能 | 实现方式 |
|------|------|---------|
| 数据采集 | 多市场实时行情 | Cron + HTTP 请求 |
| 数据计算 | 指标计算/涨跌幅统计 | Python 脚本 |
| 规则引擎 | 阈值告警/异动检测 | 自然语言配置 |
| 告警通知 | 多渠道告警 | Telegram/邮件/钉钉 |
| 可视化 | 实时行情面板 | OpenClaw Dashboard |

---

## 环境准备

### 1. 部署环境

```bash
# 推荐：2 核 4G 云服务器 (Linux)
# 最低：2GB 内存，Windows/MacOS/Linux 均可

# 安装 Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 Python 3.8+
sudo apt-get install -y python3 python3-pip

# 安装 OpenClaw
npm install -g openclaw@latest

# 初始化
openclaw onboard --install-daemon
```

### 2. 安装核心技能

```bash
# 基础能力
openclaw skill install cron
openclaw skill install http-request
openclaw skill install python-script

# 金融监控专用
openclaw skill install crypto-monitor
openclaw skill install stock-monitor

# 通知渠道
openclaw skill install telegram-bot
openclaw skill install email-sender
```

### 3. API Key 配置

| 市场 | API | 免费额度 | 注册地址 |
|------|-----|---------|---------|
| 加密货币 | Binance | 无需 Key | - |
| 美股 | Alpha Vantage | 5 次/分钟 | [注册](https://www.alphavantage.co/support/#api-key) |
| A 股 | Tushare | 基础免费 | [注册](https://tushare.pro) |
| 贵金属 | AllTick | 免费 | [GitHub](https://alltick.co) |

---

## 监控脚本

### 加密货币监控

```python
#!/usr/bin/env python3
# 加密货币监控 (Binance 公开 API)

import requests
import time

def get_crypto_price(symbol: str) -> dict:
    """获取加密货币价格"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": symbol}
    
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    
    return {
        "symbol": symbol,
        "price": float(data["lastPrice"]),
        "change_24h": float(data["priceChangePercent"]),
        "volume_24h": float(data["volume"])
    }

# 监控 BTC/ETH
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

while True:
    for symbol in symbols:
        data = get_crypto_price(symbol)
        print(f"{symbol}: ${data['price']:.2f} ({data['change_24h']:+.2f}%)")
        time.sleep(0.5)
    
    time.sleep(60)  # 每 60 秒更新
```

### 美股监控

```python
#!/usr/bin/env python3
# 美股监控 (Alpha Vantage API)

import requests

API_KEY = "你的 Alpha Vantage Key"

def get_stock_price(symbol: str) -> dict:
    """获取股票价格"""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }
    
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    quote = data.get("Global Quote", {})
    
    return {
        "symbol": symbol,
        "price": float(quote.get("05. price", 0)),
        "change": float(quote.get("10. change percent", "0").replace("%", ""))
    }

# 监控热门股票
symbols = ["AAPL", "GOOGL", "TSLA", "NVDA"]

for symbol in symbols:
    data = get_stock_price(symbol)
    print(f"{symbol}: ${data['price']:.2f} ({data['change']:+.2f}%)")
```

### 贵金属监控

```python
#!/usr/bin/env python3
# 贵金属监控 (AllTick API)

import requests

def get_metals_price(symbol: str) -> dict:
    """获取贵金属价格"""
    url = "https://api.alltick.io/api/v1/ticks"
    params = {"symbol": symbol}
    
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    
    return {
        "symbol": symbol,
        "price": float(data.get("price", 0)),
        "change": float(data.get("change", 0))
    }

# 监控黄金/白银
symbols = ["XAU", "XAG"]  # 黄金/白银

for symbol in symbols:
    data = get_metals_price(symbol)
    print(f"{symbol}: ${data['price']:.2f} ({data['change']:+.2f}%)")
```

---

## 告警规则配置

### 基础价格告警

```yaml
# OpenClaw 自然语言配置
监控规则:
  - 标的：BTC/ETH/SOL
    条件：24h 涨跌幅 > 3%
    动作：发送 Telegram 告警
  
  - 标的：AAPL/GOOGL/TSLA
    条件：价格突破支撑位/压力位
    动作：发送邮件通知
  
  - 标的：XAU/XAG(黄金/白银)
    条件：10 分钟内涨跌 > 2%
    动作：发送钉钉告警
```

### 技术指标告警

```python
# RSI 超买超卖告警
def check_rsi(prices: list) -> bool:
    """计算 RSI 指标"""
    # 计算逻辑...
    return rsi > 70 or rsi < 30

# MACD 金叉死叉告警
def check_macd(prices: list) -> str:
    """计算 MACD 指标"""
    # 计算逻辑...
    return "金叉" if macd > signal else "死叉"
```

---

## 通知渠道配置

### Telegram 通知

```python
import requests

def send_telegram(message: str):
    """发送 Telegram 消息"""
    bot_token = "你的 Bot Token"
    chat_id = "你的 Chat ID"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    
    requests.post(url, json=data)
```

### 邮件通知

```python
import smtplib
from email.mime.text import MIMEText

def send_email(subject: str, content: str):
    """发送邮件通知"""
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = "sender@example.com"
    msg["To"] = "receiver@example.com"
    
    server = smtplib.SMTP_SSL("smtp.example.com", 465)
    server.login("user", "password")
    server.send_message(msg)
```

---

## 部署运行

### 后台运行

**方法 1：systemd 守护 (推荐)**

```bash
# 创建服务文件
sudo nano /etc/systemd/system/market-monitor.service

# 粘贴以下内容：
[Unit]
Description=Market Monitor - 全市场实时监控
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/market-monitor
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/market-monitor/crypto-monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable market-monitor
sudo systemctl start market-monitor

# 查看状态
systemctl status market-monitor

# 查看日志
journalctl -u market-monitor -f
```

**方法 2：screen 后台**

```bash
# 使用 screen 后台运行
screen -S market-monitor
python3 crypto-monitor.py

# Ctrl+A, D 退出屏幕
# screen -r market-monitor 重新连接
```

---

## 监控面板

### OpenClaw Dashboard

```bash
# 安装 Dashboard 技能
openclaw skill install openclaw-dashboard

# 访问 Dashboard
http://localhost:18789
```

### 自定义面板

```python
# 使用 Flask 创建简单面板
from flask import Flask, render_template
import requests

app = Flask(__name__)

@app.route("/")
def index():
    # 获取实时行情
    btc_price = get_crypto_price("BTCUSDT")
    return render_template("index.html", btc=btc_price)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## 成本估算

| 项目 | 费用 |
|------|------|
| 云服务器 | ¥50-100/月 (2 核 4G) |
| API 费用 | 免费 (基础额度) |
| 通知费用 | 免费 (Telegram/邮件) |
| **总计** | **¥50-100/月** |

---

## 总结

本方案基于 OpenClaw 实现全市场实时监控，具有以下优势：

1. ✅ **低成本** - 每月仅需云服务器费用
2. ✅ **易部署** - 无需复杂开发，配置即可用
3. ✅ **高扩展** - 支持自定义指标和告警规则
4. ✅ **多渠道** - 支持 Telegram/邮件/钉钉通知

---

**参考资料：**
- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Binance API](https://binance-docs.github.io/apidocs/)
- [AllTick API](https://alltick.co)

---

*本文仅用于技术研究与教育目的，投资有风险，入市需谨慎。*
