"""
ClawGuard-BNB 单元测试
测试核心功能模块
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestProxyManager(unittest.TestCase):
    """测试代理管理器"""

    def setUp(self):
        from src.network.proxy_manager import ProxyManager, ProxyConfig

        self.ProxyManager = ProxyManager
        self.ProxyConfig = ProxyConfig

    def test_proxy_config_creation(self):
        """测试代理配置创建"""
        config = self.ProxyConfig(
            proxy_type='http',
            host='127.0.0.1',
            port=7890
        )

        self.assertEqual(config.proxy_type, 'http')
        self.assertEqual(config.host, '127.0.0.1')
        self.assertEqual(config.port, 7890)

    def test_proxy_url_generation(self):
        """测试代理URL生成"""
        config = self.ProxyConfig(
            proxy_type='http',
            host='127.0.0.1',
            port=7890
        )

        url = config.get_proxy_url()
        self.assertEqual(url, 'http://127.0.0.1:7890')

    def test_proxy_url_with_auth(self):
        """测试带认证的代理URL"""
        config = self.ProxyConfig(
            proxy_type='http',
            host='127.0.0.1',
            port=7890,
            username='user',
            password='pass'
        )

        url = config.get_proxy_url()
        self.assertEqual(url, 'http://user:pass@127.0.0.1:7890')

    def test_proxy_manager_initialization(self):
        """测试代理管理器初始化"""
        manager = self.ProxyManager()

        self.assertFalse(manager.enabled)
        self.assertIsNone(manager.current_proxy)
        self.assertEqual(len(manager.proxy_pool), 0)


class TestOutputFormatter(unittest.TestCase):
    """测试输出格式化器"""

    def setUp(self):
        from src.utils.output_formatter import OutputFormatter

        self.OutputFormatter = OutputFormatter

    def test_json_mode_price(self):
        """测试JSON模式价格输出"""
        formatter = self.OutputFormatter(json_mode=True)

        ticker = {
            'symbol': 'BTCUSDT',
            'price': '68234.50',
            'priceChangePercent': '2.34',
            'highPrice': '69100.00',
            'lowPrice': '66500.00',
            'volume': '28456.78'
        }

        result = formatter.format_price('BTCUSDT', ticker)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['symbol'], 'BTCUSDT')
        self.assertEqual(result['price'], 68234.50)
        self.assertEqual(result['change_percent'], 2.34)

    def test_human_mode_price(self):
        """测试人类可读模式价格输出"""
        formatter = self.OutputFormatter(json_mode=False)

        ticker = {
            'symbol': 'BTCUSDT',
            'price': '68234.50',
            'priceChangePercent': '2.34'
        }

        result = formatter.format_price('BTCUSDT', ticker)

        self.assertIsInstance(result, str)
        self.assertIn('BTCUSDT', result)
        self.assertIn('68234.50', result)


class TestNLPIntentRecognizer(unittest.TestCase):
    """测试NLP意图识别器"""

    def setUp(self):
        from src.nlp.intent_recognizer import IntentRecognizer

        self.recognizer = IntentRecognizer()

    def test_query_price_intent(self):
        """测试价格查询意图"""
        intent, confidence = self.recognizer.recognize("BTC现在多少钱？")

        self.assertEqual(intent, 'query_price')
        self.assertGreater(confidence, 0.8)

    def test_buy_order_intent(self):
        """测试买入意图"""
        intent, confidence = self.recognizer.recognize("用1000 USDT买入BTC")

        self.assertEqual(intent, 'place_buy_order')
        self.assertGreater(confidence, 0.8)

    def test_sell_order_intent(self):
        """测试卖出意图"""
        intent, confidence = self.recognizer.recognize("卖出0.1个BTC")

        self.assertEqual(intent, 'place_sell_order')
        self.assertGreater(confidence, 0.8)

    def test_analyze_intent(self):
        """测试分析意图"""
        intent, confidence = self.recognizer.recognize("帮我分析一下ETH的走势")

        self.assertEqual(intent, 'analyze_trend')
        self.assertGreater(confidence, 0.8)

    def test_unknown_intent(self):
        """测试未知意图"""
        intent, confidence = self.recognizer.recognize("今天天气怎么样？")

        self.assertEqual(intent, 'unknown')
        self.assertLess(confidence, 0.5)


class TestNLPEntityExtractor(unittest.TestCase):
    """测试NLP实体提取器"""

    def setUp(self):
        from src.nlp.entity_extractor import EntityExtractor

        self.extractor = EntityExtractor()

    def test_extract_symbol(self):
        """测试交易对提取"""
        entities = self.extractor.extract("BTC现在多少钱？", 'query_price')

        self.assertIn('symbol', entities)
        self.assertEqual(entities['symbol'], 'BTCUSDT')

    def test_extract_amount(self):
        """测试金额提取"""
        entities = self.extractor.extract("用1000 USDT买入BTC", 'place_buy_order')

        self.assertIn('amount', entities)
        self.assertEqual(entities['amount'], 1000)

    def test_extract_price(self):
        """测试价格提取"""
        entities = self.extractor.extract("在70000价格卖出BTC", 'place_sell_order')

        self.assertIn('price', entities)
        self.assertEqual(entities['price'], 70000)

    def test_extract_leverage(self):
        """测试杠杆提取"""
        entities = self.extractor.extract("把BTC的杠杆调到5倍", 'set_leverage')

        self.assertIn('leverage', entities)
        self.assertEqual(entities['leverage'], 5)


class TestTechnicalIndicators(unittest.TestCase):
    """测试技术指标计算"""

    def setUp(self):
        # 创建模拟K线数据
        self.mock_klines = []
        base_price = 68000
        for i in range(100):
            self.mock_klines.append({
                'open': base_price + i * 10,
                'high': base_price + i * 10 + 50,
                'low': base_price + i * 10 - 50,
                'close': base_price + i * 10 + 20,
                'volume': 1000 + i * 10
            })

    def test_calculate_rsi(self):
        """测试RSI计算"""
        from src.analysis.indicators import TechnicalIndicators

        indicators = TechnicalIndicators()
        rsi_values = indicators.calculate_rsi(self.mock_klines, period=14)

        self.assertIsInstance(rsi_values, list)
        self.assertGreater(len(rsi_values), 0)
        self.assertTrue(all(0 <= v <= 100 for v in rsi_values))

    def test_calculate_macd(self):
        """测试MACD计算"""
        from src.analysis.indicators import TechnicalIndicators

        indicators = TechnicalIndicators()
        macd_data = indicators.calculate_macd(self.mock_klines)

        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
        self.assertIn('histogram', macd_data)
        self.assertGreater(len(macd_data['macd']), 0)

    def test_calculate_bollinger_bands(self):
        """测试布林带计算"""
        from src.analysis.indicators import TechnicalIndicators

        indicators = TechnicalIndicators()
        bb = indicators.calculate_bollinger_bands(self.mock_klines, period=20)

        self.assertIn('upper', bb)
        self.assertIn('middle', bb)
        self.assertIn('lower', bb)
        self.assertTrue(all(bb['upper'][i] >= bb['middle'][i] >= bb['lower'][i]
                           for i in range(len(bb['upper']))))

    def test_calculate_atr(self):
        """测试ATR计算"""
        from src.analysis.indicators import TechnicalIndicators

        indicators = TechnicalIndicators()
        atr_values = indicators.calculate_atr(self.mock_klines, period=14)

        self.assertIsInstance(atr_values, list)
        self.assertGreater(len(atr_values), 0)
        self.assertTrue(all(v >= 0 for v in atr_values))


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎"""

    def setUp(self):
        from src.backtest.backtest_engine import BacktestEngine

        self.BacktestEngine = BacktestEngine

        # 创建模拟K线数据
        self.mock_klines = []
        base_price = 68000
        for i in range(100):
            self.mock_klines.append({
                'open': base_price + i * 10,
                'high': base_price + i * 10 + 50,
                'low': base_price + i * 10 - 50,
                'close': base_price + i * 10 + 20,
                'volume': 1000 + i * 10,
                'close_time': 1709856000000 + i * 3600000
            })

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = self.BacktestEngine(initial_capital=10000, commission=0.001)

        self.assertEqual(engine.initial_capital, 10000)
        self.assertEqual(engine.commission, 0.001)
        self.assertEqual(engine.capital, 10000)
        self.assertEqual(engine.position, 0)

    def test_simple_strategy_backtest(self):
        """测试简单策略回测"""
        engine = self.BacktestEngine(initial_capital=10000)

        # 简单的买入持有策略
        def buy_hold_strategy(klines):
            if len(klines) == 1:
                return {'signal': 'BUY'}
            return {'signal': 'HOLD'}

        performance = engine.run_backtest(self.mock_klines, buy_hold_strategy)

        self.assertIn('total_return', performance)
        self.assertIn('total_trades', performance)
        self.assertIn('win_rate', performance)
        self.assertIn('max_drawdown', performance)
        self.assertIn('sharpe_ratio', performance)

    def test_performance_metrics(self):
        """测试绩效指标计算"""
        engine = self.BacktestEngine(initial_capital=10000)

        def simple_strategy(klines):
            if len(klines) < 10:
                return {'signal': 'HOLD'}
            if len(klines) == 10:
                return {'signal': 'BUY'}
            if len(klines) == 50:
                return {'signal': 'SELL'}
            return {'signal': 'HOLD'}

        performance = engine.run_backtest(self.mock_klines, simple_strategy)

        # 验证指标存在且合理
        self.assertIsInstance(performance['total_return'], float)
        self.assertIsInstance(performance['win_rate'], float)
        self.assertGreaterEqual(performance['win_rate'], 0)
        self.assertLessEqual(performance['win_rate'], 100)


class TestSkillsModule(unittest.TestCase):
    """测试Skills模块"""

    def test_base_skill_interface(self):
        """测试基础Skill接口"""
        from skills.base_skill import BaseSkill

        # 验证抽象方法存在
        self.assertTrue(hasattr(BaseSkill, 'execute'))

    def test_skill_registry(self):
        """测试Skill注册表"""
        from skills.base_skill import SkillRegistry

        registry = SkillRegistry()

        # 测试注册和获取
        self.assertIsInstance(registry.skills, dict)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestProxyManager))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestNLPIntentRecognizer))
    suite.addTests(loader.loadTestsFromTestCase(TestNLPEntityExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestBacktestEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSkillsModule))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
