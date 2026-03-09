#!/usr/bin/env python3
"""
市场分析 Skill
提供技术指标分析、趋势判断等功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill
from src.analysis.indicators import create_indicators
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MarketAnalysisSkill(BaseSkill):
    """市场分析 Skill"""

    def __init__(self):
        """初始化 Skill"""
        super().__init__()
        self.name = "market_analysis"
        self.version = "1.0.0"
        self.description = "市场分析 Skill，提供技术指标分析、趋势判断等功能"
        self.actions = [
            "analyze_indicators",
            "analyze_trend",
            "get_recommendation"
        ]
        self.indicators = create_indicators()

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行动作"""
        try:
            if action == "analyze_indicators":
                return self._analyze_indicators(params)
            elif action == "analyze_trend":
                return self._analyze_trend(params)
            elif action == "get_recommendation":
                return self._get_recommendation(params)
            else:
                return self.error_response(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Action execution failed: {e}", exc_info=True)
            return self.error_response(str(e))

    def _analyze_indicators(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析技术指标"""
        valid, error = self.validate_params(params, ['symbol'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = params.get('interval', '1h')

        analysis = self.indicators.analyze(symbol, interval)

        return self.success_response({
            'symbol': symbol,
            'interval': interval,
            'indicators': {
                'rsi': analysis.get('rsi', {}),
                'macd': analysis.get('macd', {}),
                'bollinger_bands': analysis.get('bollinger_bands', {}),
                'moving_averages': analysis.get('moving_averages', {})
            }
        })

    def _analyze_trend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析趋势"""
        valid, error = self.validate_params(params, ['symbol'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        interval = params.get('interval', '1h')

        analysis = self.indicators.analyze(symbol, interval)

        return self.success_response({
            'symbol': symbol,
            'interval': interval,
            'trend': analysis.get('trend', 'UNKNOWN'),
            'signal': analysis.get('signal', 'NEUTRAL'),
            'confidence': analysis.get('confidence', 0)
        })

    def _get_recommendation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取交易建议"""
        valid, error = self.validate_params(params, ['symbol'])
        if not valid:
            return self.error_response(error)

        symbol = params['symbol'].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        analysis = self.indicators.analyze(symbol, '1h')

        # 综合分析生成建议
        trend = analysis.get('trend', 'UNKNOWN')
        signal = analysis.get('signal', 'NEUTRAL')
        rsi = analysis.get('rsi', {}).get('value', 50)

        if signal == 'BUY' and rsi < 70:
            recommendation = 'BUY'
            reason = '技术指标显示买入信号，RSI 未超买'
        elif signal == 'SELL' and rsi > 30:
            recommendation = 'SELL'
            reason = '技术指标显示卖出信号，RSI 未超卖'
        else:
            recommendation = 'HOLD'
            reason = '当前无明确交易信号，建议观望'

        return self.success_response({
            'symbol': symbol,
            'recommendation': recommendation,
            'reason': reason,
            'trend': trend,
            'signal': signal,
            'rsi': rsi
        })


def create_skill():
    """创建 Skill 实例"""
    return MarketAnalysisSkill()


if __name__ == "__main__":
    skill = create_skill()
    print(f"Skill: {skill.name} v{skill.version}")
    print(f"Actions: {', '.join(skill.actions)}")
