
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

#!/usr/bin/env python3
"""
合约事件分析系统
监控和分析链上事件，识别交易机会
集成 Twitter、Telegram 监控和 NLP 情感分析
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


def integrate_social_media_monitoring():
    """集成社交媒体监控到事件分析器"""
    from ..data_sources.twitter_monitor import get_twitter_monitor
    from ..data_sources.telegram_monitor import get_telegram_monitor
    from ..analysis.nlp_sentiment import get_sentiment_analyzer

    twitter = get_twitter_monitor()
    telegram = get_telegram_monitor()
    sentiment = get_sentiment_analyzer()

    def on_social_event(event: Dict):
        """处理社交媒体事件"""
        text = event.get('text', '')

        # NLP 情感分析
        sentiment_result = sentiment.analyze(text)

        # 构建事件数据
        analyzed_event = {
            'source': event.get('source', 'unknown'),
            'text': text,
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'confidence': sentiment_result['confidence'],
            'priority': event.get('priority', 'MEDIUM'),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"社交媒体事件: {analyzed_event['source']} - {analyzed_event['sentiment']} ({analyzed_event['sentiment_score']:.2f})")

        # 这里可以触发交易信号
        if abs(sentiment_result['score']) > 0.5 and sentiment_result['confidence'] > 0.7:
            logger.warning(f"强烈情感信号: {sentiment_result['sentiment']} - {text[:100]}")

    # 添加回调
    twitter.add_callback(on_social_event)
    telegram.add_callback(on_social_event)

    # 启动监控
    twitter.start()
    telegram.start()

    logger.info("社交媒体监控已集成到事件分析器")

    return {
        'twitter': twitter,
        'telegram': telegram,
        'sentiment': sentiment
    }


class EventAnalyzer:
    """事件分析器"""

    def __init__(self, client=None):
        """初始化事件分析器"""
        self.client = client
        self.alert_thresholds = {
            'volume_spike': 3.0,  # 交易量激增倍数
            'price_spike': 0.05,  # 价格异常变动（5%）
            'large_order': 100000,  # 大额订单（USDT）
            'order_book_imbalance': 0.7  # 订单簿失衡比例
        }

    def analyze_market_events(self, symbol: str) -> Dict:
        """
        分析市场事件

        Args:
            symbol: 交易对

        Returns:
            事件分析结果
        """
        try:
            from ..api.binance_client import BinanceClient
            if not self.client:
                self.client = BinanceClient()

            events = []

            # 1. 交易量异常检测
            volume_event = self._detect_volume_anomaly(symbol)
            if volume_event:
                events.append(volume_event)

            # 2. 价格异常检测
            price_event = self._detect_price_anomaly(symbol)
            if price_event:
                events.append(price_event)

            # 3. 订单簿分析
            orderbook_event = self._analyze_orderbook(symbol)
            if orderbook_event:
                events.append(orderbook_event)

            # 4. 大额交易检测
            large_trades = self._detect_large_trades(symbol)
            if large_trades:
                events.extend(large_trades)

            # 5. 市场情绪分析
            sentiment = self._analyze_market_sentiment(symbol)

            # 6. 生成交易信号
            signals = self._generate_trading_signals(events, sentiment)

            return {
                'success': True,
                'symbol': symbol,
                'events': events,
                'sentiment': sentiment,
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"事件分析失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _detect_volume_anomaly(self, symbol: str) -> Optional[Dict]:
        """检测交易量异常"""
        try:
            # 获取最近24小时的K线数据
            klines = self.client.get_klines(symbol, '1h', limit=24)

            if len(klines) < 24:
                return None

            # 提取交易量
            volumes = [float(k[5]) for k in klines]

            # 计算平均交易量和标准差
            avg_volume = np.mean(volumes[:-1])  # 排除最新的
            current_volume = volumes[-1]

            # 检测异常
            if current_volume > avg_volume * self.alert_thresholds['volume_spike']:
                return {
                    'type': 'VOLUME_SPIKE',
                    'severity': 'HIGH',
                    'message': f'交易量激增 {current_volume/avg_volume:.2f}x',
                    'data': {
                        'current_volume': round(current_volume, 2),
                        'average_volume': round(avg_volume, 2),
                        'spike_ratio': round(current_volume/avg_volume, 2)
                    },
                    'impact': 'BULLISH' if current_volume > avg_volume * 4 else 'NEUTRAL'
                }

            return None

        except Exception as e:
            logger.error(f"交易量异常检测失败: {e}")
            return None

    def _detect_price_anomaly(self, symbol: str) -> Optional[Dict]:
        """检测价格异常"""
        try:
            # 获取最近的K线数据
            klines = self.client.get_klines(symbol, '5m', limit=12)  # 1小时

            if len(klines) < 12:
                return None

            # 提取价格
            closes = [float(k[4]) for k in klines]

            # 计算价格变化
            price_change = (closes[-1] - closes[0]) / closes[0]

            # 检测异常
            if abs(price_change) > self.alert_thresholds['price_spike']:
                return {
                    'type': 'PRICE_SPIKE',
                    'severity': 'HIGH',
                    'message': f'价格异常变动 {price_change*100:+.2f}%',
                    'data': {
                        'start_price': round(closes[0], 2),
                        'current_price': round(closes[-1], 2),
                        'change_percent': round(price_change * 100, 2)
                    },
                    'impact': 'BULLISH' if price_change > 0 else 'BEARISH'
                }

            return None

        except Exception as e:
            logger.error(f"价格异常检测失败: {e}")
            return None

    def _analyze_orderbook(self, symbol: str) -> Optional[Dict]:
        """分析订单簿"""
        try:
            # 获取订单簿深度
            depth = self.client.get_order_book(symbol, limit=100)

            # 计算买卖盘总量
            bid_volume = sum(float(bid[1]) for bid in depth['bids'])
            ask_volume = sum(float(ask[1]) for ask in depth['asks'])

            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return None

            # 计算买卖比
            bid_ratio = bid_volume / total_volume

            # 检测失衡
            if bid_ratio > self.alert_thresholds['order_book_imbalance']:
                return {
                    'type': 'ORDERBOOK_IMBALANCE',
                    'severity': 'MEDIUM',
                    'message': f'买盘占比 {bid_ratio*100:.1f}%，买压强劲',
                    'data': {
                        'bid_volume': round(bid_volume, 2),
                        'ask_volume': round(ask_volume, 2),
                        'bid_ratio': round(bid_ratio, 3)
                    },
                    'impact': 'BULLISH'
                }
            elif bid_ratio < (1 - self.alert_thresholds['order_book_imbalance']):
                return {
                    'type': 'ORDERBOOK_IMBALANCE',
                    'severity': 'MEDIUM',
                    'message': f'卖盘占比 {(1-bid_ratio)*100:.1f}%，卖压强劲',
                    'data': {
                        'bid_volume': round(bid_volume, 2),
                        'ask_volume': round(ask_volume, 2),
                        'bid_ratio': round(bid_ratio, 3)
                    },
                    'impact': 'BEARISH'
                }

            return None

        except Exception as e:
            logger.error(f"订单簿分析失败: {e}")
            return None

    def _detect_large_trades(self, symbol: str) -> List[Dict]:
        """检测大额交易"""
        try:
            # 获取最近的成交记录
            trades = self.client.get_recent_trades(symbol, limit=100)

            large_trades = []

            for trade in trades:
                value = float(trade['price']) * float(trade['qty'])

                if value > self.alert_thresholds['large_order']:
                    large_trades.append({
                        'type': 'LARGE_TRADE',
                        'severity': 'MEDIUM',
                        'message': f'大额{trade["isBuyerMaker"] and "卖单" or "买单"} ${value:,.0f}',
                        'data': {
                            'price': float(trade['price']),
                            'quantity': float(trade['qty']),
                            'value': round(value, 2),
                            'side': 'SELL' if trade['isBuyerMaker'] else 'BUY'
                        },
                        'impact': 'BEARISH' if trade['isBuyerMaker'] else 'BULLISH'
                    })

            # 只返回最近的5个大额交易
            return large_trades[:5]

        except Exception as e:
            logger.error(f"大额交易检测失败: {e}")
            return []

    def _analyze_market_sentiment(self, symbol: str) -> Dict:
        """分析市场情绪"""
        try:
            # 获取最近的K线数据
            klines = self.client.get_klines(symbol, '15m', limit=20)

            if len(klines) < 20:
                return {'sentiment': 'NEUTRAL', 'score': 50}

            # 计算多个指标
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            # 1. 价格趋势（40分）
            price_trend = (closes[-1] - closes[0]) / closes[0]
            price_score = min(max(price_trend * 1000 + 20, 0), 40)

            # 2. 交易量趋势（30分）
            volume_trend = (volumes[-1] - np.mean(volumes[:-1])) / np.mean(volumes[:-1])
            volume_score = min(max(volume_trend * 50 + 15, 0), 30)

            # 3. 波动性（30分，低波动性得分高）
            volatility = np.std(closes) / np.mean(closes)
            volatility_score = max(0, 30 - (volatility * 3000))

            # 综合得分
            total_score = price_score + volume_score + volatility_score

            # 判断情绪
            if total_score > 65:
                sentiment = 'BULLISH'
            elif total_score < 35:
                sentiment = 'BEARISH'
            else:
                sentiment = 'NEUTRAL'

            return {
                'sentiment': sentiment,
                'score': round(total_score, 2),
                'components': {
                    'price_trend': round(price_score, 2),
                    'volume_trend': round(volume_score, 2),
                    'volatility': round(volatility_score, 2)
                }
            }

        except Exception as e:
            logger.error(f"市场情绪分析失败: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 50}

    def _generate_trading_signals(self, events: List[Dict],
                                  sentiment: Dict) -> List[Dict]:
        """生成交易信号"""
        signals = []

        # 统计事件影响
        bullish_count = sum(1 for e in events if e.get('impact') == 'BULLISH')
        bearish_count = sum(1 for e in events if e.get('impact') == 'BEARISH')

        # 综合判断
        if sentiment['sentiment'] == 'BULLISH' and bullish_count > bearish_count:
            signals.append({
                'action': 'BUY',
                'strength': 'STRONG',
                'reason': f'市场情绪看涨({sentiment["score"]:.0f}分)，{bullish_count}个看涨事件',
                'confidence': min(sentiment['score'] + bullish_count * 5, 95)
            })
        elif sentiment['sentiment'] == 'BEARISH' and bearish_count > bullish_count:
            signals.append({
                'action': 'SELL',
                'strength': 'STRONG',
                'reason': f'市场情绪看跌({sentiment["score"]:.0f}分)，{bearish_count}个看跌事件',
                'confidence': min((100 - sentiment['score']) + bearish_count * 5, 95)
            })
        elif bullish_count > bearish_count + 2:
            signals.append({
                'action': 'BUY',
                'strength': 'MEDIUM',
                'reason': f'{bullish_count}个看涨事件，市场可能上涨',
                'confidence': 60 + bullish_count * 5
            })
        elif bearish_count > bullish_count + 2:
            signals.append({
                'action': 'SELL',
                'strength': 'MEDIUM',
                'reason': f'{bearish_count}个看跌事件，市场可能下跌',
                'confidence': 60 + bearish_count * 5
            })
        else:
            signals.append({
                'action': 'HOLD',
                'strength': 'WEAK',
                'reason': '市场信号不明确，建议观望',
                'confidence': 50
            })

        return signals


def analyze_market_events(symbol: str) -> Dict:
    """
    分析市场事件（便捷函数）

    Args:
        symbol: 交易对

    Returns:
        事件分析结果
    """
    analyzer = EventAnalyzer()
    return analyzer.analyze_market_events(symbol)


if __name__ == '__main__':
    # 测试事件分析
    result = analyze_market_events('BTCUSDT')

    if result['success']:
        print("\n" + "=" * 60)
        print(f"市场事件分析 - {result['symbol']}")
        print("=" * 60)

        print(f"\n检测到 {len(result['events'])} 个事件:")
        for event in result['events']:
            print(f"\n[{event['severity']}] {event['type']}")
            print(f"  {event['message']}")
            print(f"  影响: {event.get('impact', 'N/A')}")

        print(f"\n市场情绪: {result['sentiment']['sentiment']}")
        print(f"情绪得分: {result['sentiment']['score']:.2f}/100")

        print(f"\n交易信号:")
        for signal in result['signals']:
            print(f"  操作: {signal['action']} ({signal['strength']})")
            print(f"  理由: {signal['reason']}")
            print(f"  置信度: {signal['confidence']:.0f}%")

        print("=" * 60 + "\n")
    else:
        print(f"分析失败: {result['error']}")
