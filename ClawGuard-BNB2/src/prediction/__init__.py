#!/usr/bin/env python3
"""
预测模块初始化
"""

from .trend_predictor import TrendPredictor, predict_price_trend
from .event_analyzer import EventAnalyzer, analyze_market_events
from .auto_trading_engine import AutoTradingEngine

__all__ = [
    'TrendPredictor',
    'predict_price_trend',
    'EventAnalyzer',
    'analyze_market_events',
    'AutoTradingEngine'
]
