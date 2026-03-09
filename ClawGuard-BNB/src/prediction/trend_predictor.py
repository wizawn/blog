
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
价格趋势预测模型
基于历史数据预测未来价格走势
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class TrendPredictor:
    """趋势预测器"""

    def __init__(self, client=None):
        """初始化预测器"""
        self.client = client
        self.scaler = StandardScaler()

    def predict_trend(self, symbol: str, interval: str = '1h',
                     periods: int = 24) -> Dict:
        """
        预测价格趋势

        Args:
            symbol: 交易对
            interval: 时间间隔
            periods: 预测周期数

        Returns:
            预测结果
        """
        try:
            # 获取历史数据
            from ..api.binance_client import BinanceClient
            if not self.client:
                self.client = BinanceClient()

            # 获取足够的历史数据（至少100个周期）
            klines = self.client.get_klines(symbol, interval, limit=500)

            if len(klines) < 50:
                return {
                    'success': False,
                    'error': '历史数据不足'
                }

            # 提取价格数据
            closes = [float(k[4]) for k in klines]
            timestamps = [k[0] for k in klines]

            # 1. 移动平均预测
            ma_prediction = self._moving_average_prediction(closes, periods)

            # 2. 线性回归预测
            lr_prediction = self._linear_regression_prediction(closes, periods)

            # 3. 趋势强度分析
            trend_strength = self._calculate_trend_strength(closes)

            # 4. 支撑位和阻力位
            support, resistance = self._calculate_support_resistance(closes)

            # 5. 综合预测（加权平均）
            final_prediction = self._weighted_prediction(
                ma_prediction, lr_prediction, trend_strength
            )

            # 6. 计算预测置信度
            confidence = self._calculate_confidence(closes, trend_strength)

            # 7. 生成交易建议
            recommendation = self._generate_recommendation(
                closes[-1], final_prediction, support, resistance, confidence
            )

            return {
                'success': True,
                'symbol': symbol,
                'current_price': closes[-1],
                'predictions': {
                    'moving_average': ma_prediction,
                    'linear_regression': lr_prediction,
                    'final': final_prediction
                },
                'trend': {
                    'direction': trend_strength['direction'],
                    'strength': trend_strength['strength'],
                    'confidence': confidence
                },
                'levels': {
                    'support': support,
                    'resistance': resistance
                },
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"预测失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _moving_average_prediction(self, prices: List[float],
                                   periods: int) -> float:
        """移动平均预测"""
        # 使用指数移动平均
        ema_short = self._calculate_ema(prices, 12)
        ema_long = self._calculate_ema(prices, 26)

        # 预测趋势延续
        trend = ema_short[-1] - ema_long[-1]
        prediction = prices[-1] + (trend * periods / 12)

        return round(prediction, 2)

    def _linear_regression_prediction(self, prices: List[float],
                                     periods: int) -> float:
        """线性回归预测"""
        # 准备数据
        X = np.array(range(len(prices))).reshape(-1, 1)
        y = np.array(prices)

        # 训练模型
        model = LinearRegression()
        model.fit(X, y)

        # 预测未来价格
        future_x = np.array([[len(prices) + periods - 1]])
        prediction = model.predict(future_x)[0]

        return round(prediction, 2)

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """计算指数移动平均"""
        ema = []
        multiplier = 2 / (period + 1)

        # 第一个EMA使用SMA
        ema.append(sum(prices[:period]) / period)

        # 后续EMA
        for i in range(period, len(prices)):
            ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)

        return ema

    def _calculate_trend_strength(self, prices: List[float]) -> Dict:
        """计算趋势强度"""
        # 使用最近50个数据点
        recent_prices = prices[-50:]

        # 计算线性回归斜率
        X = np.array(range(len(recent_prices))).reshape(-1, 1)
        y = np.array(recent_prices)

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        r_squared = model.score(X, y)

        # 判断趋势方向
        if slope > 0:
            direction = 'BULLISH'  # 上涨
        elif slope < 0:
            direction = 'BEARISH'  # 下跌
        else:
            direction = 'NEUTRAL'  # 中性

        # 趋势强度（基于R²和斜率）
        strength = min(abs(slope) * r_squared * 100, 100)

        return {
            'direction': direction,
            'strength': round(strength, 2),
            'slope': round(slope, 4),
            'r_squared': round(r_squared, 4)
        }

    def _calculate_support_resistance(self, prices: List[float]) -> Tuple[float, float]:
        """计算支撑位和阻力位"""
        recent_prices = prices[-100:]

        # 使用局部极值点
        highs = []
        lows = []

        for i in range(1, len(recent_prices) - 1):
            # 局部高点
            if (recent_prices[i] > recent_prices[i-1] and
                recent_prices[i] > recent_prices[i+1]):
                highs.append(recent_prices[i])

            # 局部低点
            if (recent_prices[i] < recent_prices[i-1] and
                recent_prices[i] < recent_prices[i+1]):
                lows.append(recent_prices[i])

        # 计算支撑位（低点的平均值）
        support = np.mean(lows) if lows else min(recent_prices)

        # 计算阻力位（高点的平均值）
        resistance = np.mean(highs) if highs else max(recent_prices)

        return round(support, 2), round(resistance, 2)

    def _weighted_prediction(self, ma_pred: float, lr_pred: float,
                           trend: Dict) -> float:
        """加权预测"""
        # 根据趋势强度调整权重
        strength = trend['strength'] / 100

        # 强趋势时更信任移动平均，弱趋势时更信任线性回归
        ma_weight = 0.3 + (strength * 0.4)
        lr_weight = 1 - ma_weight

        prediction = ma_pred * ma_weight + lr_pred * lr_weight

        return round(prediction, 2)

    def _calculate_confidence(self, prices: List[float], trend: Dict) -> float:
        """计算预测置信度"""
        # 基于多个因素计算置信度

        # 1. 趋势强度（0-40分）
        trend_score = trend['strength'] * 0.4

        # 2. R²值（0-30分）
        r_squared_score = trend['r_squared'] * 30

        # 3. 价格波动性（0-30分，波动越小置信度越高）
        volatility = np.std(prices[-50:]) / np.mean(prices[-50:])
        volatility_score = max(0, 30 - (volatility * 1000))

        confidence = trend_score + r_squared_score + volatility_score

        return round(min(confidence, 100), 2)

    def _generate_recommendation(self, current_price: float,
                                predicted_price: float,
                                support: float, resistance: float,
                                confidence: float) -> Dict:
        """生成交易建议"""
        price_change = ((predicted_price - current_price) / current_price) * 100

        # 判断操作建议
        if confidence < 50:
            action = 'HOLD'
            reason = f'预测置信度较低({confidence}%)，建议观望'
        elif price_change > 2:
            action = 'BUY'
            reason = f'预测价格上涨{price_change:.2f}%，建议买入'
        elif price_change < -2:
            action = 'SELL'
            reason = f'预测价格下跌{abs(price_change):.2f}%，建议卖出'
        else:
            action = 'HOLD'
            reason = f'预测价格变化较小({price_change:.2f}%)，建议持有'

        # 计算目标价位
        if action == 'BUY':
            target_price = resistance
            stop_loss = support
        elif action == 'SELL':
            target_price = support
            stop_loss = resistance
        else:
            target_price = current_price
            stop_loss = current_price

        return {
            'action': action,
            'reason': reason,
            'predicted_change': round(price_change, 2),
            'target_price': target_price,
            'stop_loss': stop_loss,
            'confidence': confidence
        }


def predict_price_trend(symbol: str, interval: str = '1h',
                       periods: int = 24) -> Dict:
    """
    预测价格趋势（便捷函数）

    Args:
        symbol: 交易对
        interval: 时间间隔
        periods: 预测周期数

    Returns:
        预测结果
    """
    predictor = TrendPredictor()
    return predictor.predict_trend(symbol, interval, periods)


if __name__ == '__main__':
    # 测试预测功能
    result = predict_price_trend('BTCUSDT', '1h', 24)

    if result['success']:
        print("\n" + "=" * 60)
        print(f"价格趋势预测 - {result['symbol']}")
        print("=" * 60)
        print(f"\n当前价格: ${result['current_price']:.2f}")
        print(f"预测价格: ${result['predictions']['final']:.2f}")
        print(f"预测变化: {result['recommendation']['predicted_change']:+.2f}%")
        print(f"\n趋势方向: {result['trend']['direction']}")
        print(f"趋势强度: {result['trend']['strength']:.2f}%")
        print(f"预测置信度: {result['trend']['confidence']:.2f}%")
        print(f"\n支撑位: ${result['levels']['support']:.2f}")
        print(f"阻力位: ${result['levels']['resistance']:.2f}")
        print(f"\n交易建议: {result['recommendation']['action']}")
        print(f"建议理由: {result['recommendation']['reason']}")
        print(f"目标价位: ${result['recommendation']['target_price']:.2f}")
        print(f"止损价位: ${result['recommendation']['stop_loss']:.2f}")
        print("=" * 60 + "\n")
    else:
        print(f"预测失败: {result['error']}")
