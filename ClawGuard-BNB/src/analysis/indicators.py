#!/usr/bin/env python3
"""
技术指标分析模块
提供常用技术指标计算：RSI, MACD, 布林带, EMA, SMA等
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal
import math

from ..api.binance_client import BinanceClient
from ..utils.logger import get_logger

logger = get_logger("indicators")


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self, client: Optional[BinanceClient] = None):
        """
        初始化技术指标计算器

        Args:
            client: 币安API客户端
        """
        self.client = client or BinanceClient()

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """
        获取K线数据

        Args:
            symbol: 交易对
            interval: 时间间隔（1m, 5m, 15m, 1h, 4h, 1d等）
            limit: 数量

        Returns:
            K线数据列表
        """
        try:
            klines = self.client.get_klines(symbol, interval, limit)

            formatted_klines = []
            for kline in klines:
                formatted_klines.append({
                    'open_time': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': kline[6],
                })

            return formatted_klines

        except Exception as e:
            logger.error(f"获取K线数据失败: {e}", exc_info=True)
            return []

    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        计算简单移动平均线 (SMA)

        Args:
            prices: 价格列表
            period: 周期

        Returns:
            SMA值列表
        """
        if len(prices) < period:
            return []

        sma = []
        for i in range(len(prices) - period + 1):
            avg = sum(prices[i:i + period]) / period
            sma.append(round(avg, 2))

        return sma

    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        计算指数移动平均线 (EMA)

        Args:
            prices: 价格列表
            period: 周期

        Returns:
            EMA值列表
        """
        if len(prices) < period:
            return []

        multiplier = 2 / (period + 1)
        ema = []

        # 第一个EMA值使用SMA
        sma = sum(prices[:period]) / period
        ema.append(sma)

        # 后续EMA值
        for i in range(period, len(prices)):
            ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(round(ema_value, 2))

        return ema

    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """
        计算相对强弱指标 (RSI)

        Args:
            prices: 价格列表
            period: 周期（默认14）

        Returns:
            RSI值列表（0-100）
        """
        if len(prices) < period + 1:
            return []

        # 计算价格变化
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # 分离涨跌
        gains = [max(change, 0) for change in changes]
        losses = [abs(min(change, 0)) for change in changes]

        rsi = []

        # 第一个RSI使用简单平均
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(round(100 - (100 / (1 + rs)), 2))

        # 后续RSI使用指数移动平均
        for i in range(period, len(changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(round(100 - (100 / (1 + rs)), 2))

        return rsi

    def calculate_macd(self, prices: List[float],
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> Dict:
        """
        计算MACD指标

        Args:
            prices: 价格列表
            fast_period: 快线周期（默认12）
            slow_period: 慢线周期（默认26）
            signal_period: 信号线周期（默认9）

        Returns:
            包含MACD线、信号线、柱状图的字典
        """
        if len(prices) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}

        # 计算快线和慢线EMA
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)

        # 对齐长度
        offset = len(ema_fast) - len(ema_slow)
        if offset > 0:
            ema_fast = ema_fast[offset:]

        # 计算MACD线
        macd_line = [round(ema_fast[i] - ema_slow[i], 2) for i in range(len(ema_slow))]

        # 计算信号线
        signal_line = self.calculate_ema(macd_line, signal_period)

        # 计算柱状图
        offset = len(macd_line) - len(signal_line)
        histogram = [round(macd_line[i + offset] - signal_line[i], 2)
                    for i in range(len(signal_line))]

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def calculate_bollinger_bands(self, prices: List[float],
                                   period: int = 20,
                                   std_dev: float = 2.0) -> Dict:
        """
        计算布林带

        Args:
            prices: 价格列表
            period: 周期（默认20）
            std_dev: 标准差倍数（默认2）

        Returns:
            包含上轨、中轨、下轨的字典
        """
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}

        middle_band = self.calculate_sma(prices, period)

        upper_band = []
        lower_band = []

        for i in range(len(middle_band)):
            # 计算标准差
            data_slice = prices[i:i + period]
            mean = middle_band[i]
            variance = sum((x - mean) ** 2 for x in data_slice) / period
            std = math.sqrt(variance)

            upper_band.append(round(mean + std_dev * std, 2))
            lower_band.append(round(mean - std_dev * std, 2))

        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }

    def calculate_atr(self, klines: List[Dict], period: int = 14) -> List[float]:
        """
        计算平均真实波幅 (ATR - Average True Range)

        Args:
            klines: K线数据
            period: 周期（默认14）

        Returns:
            ATR值列表
        """
        if len(klines) < period + 1:
            return []

        true_ranges = []

        for i in range(1, len(klines)):
            high = klines[i]['high']
            low = klines[i]['low']
            prev_close = klines[i-1]['close']

            # 真实波幅 = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # 计算ATR（使用EMA平滑）
        atr = []
        if len(true_ranges) >= period:
            # 第一个ATR使用SMA
            first_atr = sum(true_ranges[:period]) / period
            atr.append(round(first_atr, 2))

            # 后续使用EMA
            multiplier = 1 / period
            for i in range(period, len(true_ranges)):
                new_atr = (true_ranges[i] * multiplier) + (atr[-1] * (1 - multiplier))
                atr.append(round(new_atr, 2))

        return atr

    def calculate_kdj(self, klines: List[Dict], n: int = 9, m1: int = 3, m2: int = 3) -> Dict:
        """
        计算KDJ指标（随机指标）

        Args:
            klines: K线数据
            n: RSV周期（默认9）
            m1: K值平滑周期（默认3）
            m2: D值平滑周期（默认3）

        Returns:
            包含K、D、J值的字典
        """
        if len(klines) < n:
            return {'k': [], 'd': [], 'j': []}

        k_values = []
        d_values = []
        j_values = []

        # 初始K和D值
        k = 50
        d = 50

        for i in range(n - 1, len(klines)):
            # 计算RSV (未成熟随机值)
            period_klines = klines[i - n + 1:i + 1]
            close = klines[i]['close']
            high = max([kl['high'] for kl in period_klines])
            low = min([kl['low'] for kl in period_klines])

            if high == low:
                rsv = 50
            else:
                rsv = ((close - low) / (high - low)) * 100

            # 计算K值（RSV的移动平均）
            k = (rsv + (m1 - 1) * k) / m1

            # 计算D值（K值的移动平均）
            d = (k + (m2 - 1) * d) / m2

            # 计算J值
            j = 3 * k - 2 * d

            k_values.append(round(k, 2))
            d_values.append(round(d, 2))
            j_values.append(round(j, 2))

        return {
            'k': k_values,
            'd': d_values,
            'j': j_values
        }

    def calculate_obv(self, klines: List[Dict]) -> List[float]:
        """
        计算能量潮指标 (OBV - On-Balance Volume)

        Args:
            klines: K线数据

        Returns:
            OBV值列表
        """
        if len(klines) < 2:
            return []

        obv = [0]  # 初始OBV为0

        for i in range(1, len(klines)):
            volume = klines[i]['volume']
            close = klines[i]['close']
            prev_close = klines[i-1]['close']

            if close > prev_close:
                # 价格上涨，累加成交量
                obv.append(obv[-1] + volume)
            elif close < prev_close:
                # 价格下跌，减去成交量
                obv.append(obv[-1] - volume)
            else:
                # 价格不变，OBV不变
                obv.append(obv[-1])

        return [round(v, 2) for v in obv]

    def calculate_ichimoku(self, klines: List[Dict],
                          tenkan_period: int = 9,
                          kijun_period: int = 26,
                          senkou_b_period: int = 52) -> Dict:
        """
        计算一目均衡表 (Ichimoku Cloud)

        Args:
            klines: K线数据
            tenkan_period: 转换线周期（默认9）
            kijun_period: 基准线周期（默认26）
            senkou_b_period: 先行带B周期（默认52）

        Returns:
            包含各条线的字典
        """
        if len(klines) < senkou_b_period:
            return {
                'tenkan_sen': [],
                'kijun_sen': [],
                'senkou_span_a': [],
                'senkou_span_b': [],
                'chikou_span': []
            }

        def calculate_line(period, start_idx):
            """计算一目均衡表的线"""
            if start_idx + period > len(klines):
                return None

            period_klines = klines[start_idx:start_idx + period]
            high = max([kl['high'] for kl in period_klines])
            low = min([kl['low'] for kl in period_klines])
            return (high + low) / 2

        tenkan_sen = []  # 转换线
        kijun_sen = []   # 基准线
        senkou_span_a = []  # 先行带A
        senkou_span_b = []  # 先行带B
        chikou_span = []    # 迟行带

        for i in range(senkou_b_period - 1, len(klines)):
            # 转换线（9日高低平均）
            tenkan = calculate_line(tenkan_period, i - tenkan_period + 1)
            if tenkan:
                tenkan_sen.append(round(tenkan, 2))

            # 基准线（26日高低平均）
            kijun = calculate_line(kijun_period, i - kijun_period + 1)
            if kijun:
                kijun_sen.append(round(kijun, 2))

            # 先行带A（转换线和基准线的平均）
            if tenkan and kijun:
                senkou_a = (tenkan + kijun) / 2
                senkou_span_a.append(round(senkou_a, 2))

            # 先行带B（52日高低平均）
            senkou_b = calculate_line(senkou_b_period, i - senkou_b_period + 1)
            if senkou_b:
                senkou_span_b.append(round(senkou_b, 2))

            # 迟行带（收盘价）
            chikou_span.append(round(klines[i]['close'], 2))

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    def analyze_symbol(self, symbol: str, interval: str = "1h") -> Dict:
        """
        综合分析交易对

        Args:
            symbol: 交易对
            interval: 时间间隔

        Returns:
            分析结果字典
        """
        logger.info(f"分析交易对: {symbol} ({interval})")

        # 获取K线数据
        klines = self.get_klines(symbol, interval, limit=100)

        if not klines:
            return {}

        # 提取收盘价
        closes = [k['close'] for k in klines]

        # 计算各项指标
        rsi = self.calculate_rsi(closes)
        macd = self.calculate_macd(closes)
        bb = self.calculate_bollinger_bands(closes)
        sma_20 = self.calculate_sma(closes, 20)
        ema_12 = self.calculate_ema(closes, 12)

        # 当前价格
        current_price = closes[-1]

        # 分析结果
        analysis = {
            'symbol': symbol,
            'interval': interval,
            'current_price': current_price,
            'indicators': {}
        }

        # RSI分析
        if rsi:
            current_rsi = rsi[-1]
            analysis['indicators']['rsi'] = {
                'value': current_rsi,
                'signal': self._interpret_rsi(current_rsi)
            }

        # MACD分析
        if macd['histogram']:
            current_macd = macd['macd'][-1]
            current_signal = macd['signal'][-1]
            current_histogram = macd['histogram'][-1]

            analysis['indicators']['macd'] = {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_histogram,
                'signal': self._interpret_macd(current_macd, current_signal, current_histogram)
            }

        # 布林带分析
        if bb['middle']:
            current_upper = bb['upper'][-1]
            current_middle = bb['middle'][-1]
            current_lower = bb['lower'][-1]

            analysis['indicators']['bollinger_bands'] = {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'signal': self._interpret_bollinger(current_price, current_upper,
                                                    current_middle, current_lower)
            }

        # 移动平均线分析
        if sma_20 and ema_12:
            analysis['indicators']['moving_averages'] = {
                'sma_20': sma_20[-1],
                'ema_12': ema_12[-1],
                'signal': self._interpret_ma(current_price, sma_20[-1], ema_12[-1])
            }

        # 综合信号
        analysis['overall_signal'] = self._generate_overall_signal(analysis['indicators'])

        return analysis

    def _interpret_rsi(self, rsi: float) -> str:
        """解读RSI信号"""
        if rsi >= 70:
            return "超买 - 考虑卖出"
        elif rsi <= 30:
            return "超卖 - 考虑买入"
        else:
            return "中性"

    def _interpret_macd(self, macd: float, signal: float, histogram: float) -> str:
        """解读MACD信号"""
        if macd > signal and histogram > 0:
            return "看涨 - 金叉"
        elif macd < signal and histogram < 0:
            return "看跌 - 死叉"
        else:
            return "中性"

    def _interpret_bollinger(self, price: float, upper: float,
                            middle: float, lower: float) -> str:
        """解读布林带信号"""
        if price >= upper:
            return "超买 - 价格触及上轨"
        elif price <= lower:
            return "超卖 - 价格触及下轨"
        elif price > middle:
            return "偏强 - 价格在中轨上方"
        else:
            return "偏弱 - 价格在中轨下方"

    def _interpret_ma(self, price: float, sma: float, ema: float) -> str:
        """解读移动平均线信号"""
        if price > sma and price > ema:
            return "看涨 - 价格在均线上方"
        elif price < sma and price < ema:
            return "看跌 - 价格在均线下方"
        else:
            return "中性"

    def _generate_overall_signal(self, indicators: Dict) -> str:
        """生成综合信号"""
        bullish_count = 0
        bearish_count = 0

        for indicator, data in indicators.items():
            signal = data.get('signal', '')

            if '买入' in signal or '看涨' in signal or '金叉' in signal:
                bullish_count += 1
            elif '卖出' in signal or '看跌' in signal or '死叉' in signal:
                bearish_count += 1

        if bullish_count > bearish_count:
            return "🟢 看涨信号"
        elif bearish_count > bullish_count:
            return "🔴 看跌信号"
        else:
            return "🟡 中性信号"

    def print_analysis(self, symbol: str, interval: str = "1h"):
        """
        打印分析结果

        Args:
            symbol: 交易对
            interval: 时间间隔
        """
        analysis = self.analyze_symbol(symbol, interval)

        if not analysis:
            print("分析失败")
            return

        print("\n" + "=" * 60)
        print(f"📊 {analysis['symbol']} 技术分析 ({analysis['interval']})")
        print("=" * 60)
        print(f"\n💰 当前价格: ${analysis['current_price']:.2f}")
        print("\n📈 技术指标:")
        print("─" * 60)

        for indicator, data in analysis['indicators'].items():
            print(f"\n{indicator.upper().replace('_', ' ')}:")

            if indicator == 'rsi':
                print(f"  值: {data['value']:.2f}")
                print(f"  信号: {data['signal']}")

            elif indicator == 'macd':
                print(f"  MACD: {data['macd']:.2f}")
                print(f"  信号线: {data['signal']:.2f}")
                print(f"  柱状图: {data['histogram']:.2f}")
                print(f"  信号: {data['signal']}")

            elif indicator == 'bollinger_bands':
                print(f"  上轨: ${data['upper']:.2f}")
                print(f"  中轨: ${data['middle']:.2f}")
                print(f"  下轨: ${data['lower']:.2f}")
                print(f"  信号: {data['signal']}")

            elif indicator == 'moving_averages':
                print(f"  SMA(20): ${data['sma_20']:.2f}")
                print(f"  EMA(12): ${data['ema_12']:.2f}")
                print(f"  信号: {data['signal']}")

        print("\n" + "─" * 60)
        print(f"🎯 综合信号: {analysis['overall_signal']}")
        print("=" * 60 + "\n")


# 便捷函数
def create_indicators(client: Optional[BinanceClient] = None) -> TechnicalIndicators:
    """创建技术指标计算器"""
    return TechnicalIndicators(client)


def analyze(symbol: str, interval: str = "1h") -> Dict:
    """分析交易对（便捷函数）"""
    indicators = create_indicators()
    return indicators.analyze_symbol(symbol, interval)


if __name__ == "__main__":
    # 测试技术指标
    indicators = create_indicators()

    # 分析BTC
    indicators.print_analysis("BTCUSDT", "1h")

    # 分析ETH
    indicators.print_analysis("ETHUSDT", "1h")
