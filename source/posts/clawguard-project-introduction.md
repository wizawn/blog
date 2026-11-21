---
title: "手搓一个轻量行情盯盘脚本 ClawGuard：K 线均线、资金费率与钉钉加签推送"
date: 2026-03-17T14:00:00+08:00
draft: false
categories: ["项目介绍"]
tags: ["ClawGuard", "Python", "行情监控", "价格预警", "钉钉机器人"]
description: "记录个人轻量级加密行情监控小项目 ClawGuard 的设计与实现：基于公开行情接口拉取现货与日 K 线均线，校准永续合约资金费率告警水位，通过钉钉 HMAC 加签机器人推送异动提醒。"
weight: 10
---

半夜被行情插针吵醒过两回之后，我干脆抽周末用 Python 攒了个自用的轻量盯盘小工具 `ClawGuard`。想法其实特简单：犯不着去订一堆几百美金一年的花哨看盘终端，就在手头一台闲置的 512MB 内存小鸡上常驻个脚本，每隔 60 秒去币安和 OKX 的公开接口拉一把现货价格、日线均线和永续合约资金费率；真遇上关键价位突破或者多空杠杆拥挤度异常，直接往我手机钉钉群里甩一条提醒；平时想顺手看眼走势，再挂一个轻量的 Flask + Bootstrap 5 + Chart.js 小后台（前端网页靠 WebSocket 接收后台每分钟轮询刷出来的新数据）。

个人源码仓库目前设成了私有归档状态，这里直接把核心模块拆法、计算代码和写的时候踩过的几个典型坑摊开记一笔。先声明一句，文里所有指标参数纯粹是写代码折腾记录，不构成任何投资交易建议。

## 0x00 别把"60 秒轮询采样"和"日均线"搅成一锅粥

自己动手写行情轮询脚本时，最容易犯的一个低级乌龙就是把时间尺度搞串台：主循环 `time.sleep(60)` 每分钟去抓一次最新成交价塞进数组，转头拿着最近 7 个点和 25 个点算平均数，嘴上却管它叫 `MA7（7 日均线）` 和 `MA25（25 日均线）`。一分钟采一个点，攒够 25 个点一共才过去了 25 分钟，算出来的其实是 1 分钟级别的超短线均线，要是拿这个数去套什么"跌破 25 日均线 5% 触发定投提醒"，那真是差到姥姥家去了。

所以在 `web/backend/services/analyzer.py` 里，短线异动和中线趋势必须拆成两条独立的数据源分开喂。60 秒一次的轮询只管盯瞬时价格突破（比如突破设定关口 `±1%`）以及明确标清尺度的分钟级滑动均线 `MA(7x1m)` / `MA(25x1m)`；真正要算 7 日、25 日均线拿来辅助看日线位置时，单独去调交易所公开的日 K 线接口（比如币安的 `GET /api/v3/klines?symbol=BTCUSDT&interval=1d&limit=30`），剔除最后一根尚未收盘的当日 K 线后，取已收盘的日线序列来算。至于 RSI、MACD、布林带以及历史策略回测这些更重的功能，目前还老老实实躺在待办列表里没往主进程里塞，也别信什么"套个简单 LSTM 就能做到 75% 短期预测准确率"的玄学，先把均线交叉和费率告警跑扎实比啥都强。

把分钟级滑动窗口里新手常漏写的"历史队列滚动追加"、"上一轮均线状态暂存"和网络抖动异常兜底写全，金叉和死叉双向告警的最小运行逻辑长这样：

```python
import time
from collections import deque
import requests

def monitor_1m_ma_loop(api_client, symbol: str = "BTCUSDT") -> None:
    prices: deque[float] = deque(maxlen=25)
    prev_ma7: float | None = None
    prev_ma25: float | None = None

    while True:
        try:
            price = float(api_client.get_spot_price(symbol))
        except requests.RequestException:
            time.sleep(60)
            continue

        prices.append(price)

        if len(prices) == 25:
            recent = list(prices)
            ma7 = sum(recent[-7:]) / 7.0
            ma25 = sum(recent) / 25.0

            if prev_ma7 is not None and prev_ma25 is not None:
                if ma7 > ma25 and prev_ma7 <= prev_ma25:
                    send_dingtalk_alert(f"[{symbol}] 1m 均线金叉，现价 {price:.2f}")
                elif ma7 < ma25 and prev_ma7 >= prev_ma25:
                    send_dingtalk_alert(f"[{symbol}] 1m 均线死叉，现价 {price:.2f}")

            prev_ma7, prev_ma25 = ma7, ma25

        save_tick_to_sqlite(symbol, price)
        time.sleep(60)
```

## 0x01 永续合约资金费率阈值设在 `0.01%` 只会天天狼来了

除了盯现货价格和 24 小时成交量突增（比如放量超过 `50%`），顺带抓一下永续合约的资金费率（Funding Rate）对感知场内杠杆情绪挺有用，但告警线千万别照抄外行模板设成 `> 0.01%`。

熟悉币安 U 本位永续合约机制的人都知道，每 8 小时结算一次的默认基准利率本来就是 `+0.01%`。如果你把多头过热预警线卡在 `0.01%`，哪怕行情横盘纹丝不动，你的钉钉群也会从早响到晚。

实战里把阈值拉开安全垫才有参考意义：比如 8 小时费率冲到 `+0.05%` 乃至 `+0.10%` 以上，说明多头杠杆明显拥挤、做多持仓摩擦成本陡增；反过来跌穿 `-0.03%`，说明空头扎堆在给多头交补贴。这里顺嘴把概念说准：资金费率本质上是多空双方定期互付的持仓成本和拥挤度温度计，单靠费率本身并不会直接触发低倍仓位强平，拿它来警惕极端单边情绪正合适。

## 0x02 目录结构、钉钉 `HMAC-SHA256` 加签与零私钥原则

整个小工具的文件结构压得很扁，一眼就能看清谁管谁：

```text
ClawGuard/
  clawguard_with_ta.py        # 60 秒轮询主监控进程
  config.example.json         # 配置模板（复制为 config.json 后使用）
  requirements.txt            # Python 依赖（Flask / flask-sock / requests / pandas 等）
  scripts/                    # 启停与每日汇总辅助脚本
  web/
    backend/
      app.py                  # Flask 面板入口
      models/price_data.py    # SQLite 持久化表模型
      routes/                 # API 与后台视图路由
      services/               # binance.py、okx.py 与 analyzer.py
    frontend/                 # dashboard.html、settings.html 与静态资源
```

在 Debian 12 或 Ubuntu 24.04 这类默认开启了 PEP 668（`externally-managed-environment`）保护的新系统上部署时，直接拿系统级 `pip` 硬装会报错，先建个虚拟环境再装包，顺手把 `config.json` 的权限锁成 `600`（毕竟明文配置落在磁盘上，没接系统密钥环之前谁能读文件谁就能拿走你的机器人地址）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.json config.json
chmod 600 config.json

# 起后台监控与本地 Web 面板（默认只绑回环口）
python3 clawguard_with_ta.py &
python3 web/backend/app.py --host 127.0.0.1 --port 5000
```

`config.json` 里把要盯的交易对数组 `symbols`、钉钉机器人地址与加签密钥、出站代理和告警水位配齐就行：

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=...",
  "dingtalk_secret": "SEC开头的钉钉机器人加签密钥",
  "proxy": "http://127.0.0.1:7890",
  "monitor_interval": 60,
  "price_threshold_pct": 1.0,
  "funding_high_threshold": 0.0005,
  "funding_low_threshold": -0.0003
}
```

最后叮嘱两个实打实踩过的坑。

第一个是 API Key 的最小权限铁律：只拉现货价格、K 线和资金费率的纯监控脚本，压根不需要填任何交易所 API Key！币安和 OKX 的公开行情端点本来就是免鉴权直连的，配置里压根别留交易所密钥字段最踏实。就算你以后自己改代码想顺带查个人账户余额，去后台建 Key 时也只准勾"只读（Enable Reading）"并绑死服务器固定出口 IP，千万别给一个跑在小鸡上的盯盘脚本开"允许现货或合约交易"权限。另外部分司法管辖区对交易所接口访问有地域合规限制，挂代理请求前先确认符合平台服务条款。

第二个坑在钉钉推送报 `errcode: 310000` 上。现在建钉钉群自定义机器人强制要求三选一配安全设置，选最稳妥的"加签"模式拿到 `SEC...` 密钥之后，每次发 POST 请求前必须拿当前毫秒级时间戳拼上换行符和密钥（`f"{timestamp}\n{secret}"`）跑一遍 `HMAC-SHA256`，再做 Base64 和 `urllib.parse.quote_plus` 编码拼到 URL 的 `&timestamp=...&sign=...` 尾巴上，光往裸 Webhook 地址硬塞 JSON 是一条都发不出去的。

整套东西跑起来只占四五十兆内存，单次 HTTP 拉取虽然不到 1 秒就能回包，但既然底层走的是 60 秒轮询，行情异动的最大感知延迟自然也是 60 秒；等后面哪天空闲了，再把采集源换成交易所原生的 `wss://stream.binance.com:9443` WebSocket 实时流。
