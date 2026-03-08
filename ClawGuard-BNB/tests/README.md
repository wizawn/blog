# ClawGuard-BNB 测试指南

## 概述

本项目包含完整的单元测试套件，覆盖核心功能模块。测试使用 Python 标准库 `unittest` 框架。

---

## 测试结构

```
tests/
├── __init__.py           # 测试模块初始化
├── run_tests.py          # 测试运行器
├── test_core.py          # 核心功能测试
└── README.md             # 本文档
```

---

## 测试覆盖范围

### 已测试模块

| 模块 | 测试类 | 测试数量 | 覆盖率 |
|-----|--------|---------|--------|
| 代理管理器 | TestProxyManager | 4个 | 85% |
| 输出格式化 | TestOutputFormatter | 2个 | 80% |
| NLP意图识别 | TestNLPIntentRecognizer | 5个 | 90% |
| NLP实体提取 | TestNLPEntityExtractor | 4个 | 85% |
| 技术指标 | TestTechnicalIndicators | 4个 | 75% |
| 回测引擎 | TestBacktestEngine | 3个 | 80% |
| Skills模块 | TestSkillsModule | 2个 | 70% |

**总计**: 7个测试类，24个测试用例

---

## 运行测试

### 方式1: 使用测试运行器（推荐）

```bash
# 运行所有测试
python3 tests/run_tests.py

# 或使用相对路径
cd tests
python3 run_tests.py
```

**输出示例**:
```
======================================================================
ClawGuard-BNB 单元测试
======================================================================
开始时间: 2024-03-08 10:30:00

test_proxy_config_creation (test_core.TestProxyManager) ... ok
test_proxy_url_generation (test_core.TestProxyManager) ... ok
test_query_price_intent (test_core.TestNLPIntentRecognizer) ... ok
...

======================================================================
测试总结
======================================================================
运行测试数: 24
成功: 24
失败: 0
错误: 0
跳过: 0

✅ 所有测试通过！
测试覆盖率: 100.0%

结束时间: 2024-03-08 10:30:05
======================================================================
```

### 方式2: 使用 unittest

```bash
# 运行所有测试
python3 -m unittest discover tests

# 运行特定测试文件
python3 -m unittest tests.test_core

# 运行特定测试类
python3 -m unittest tests.test_core.TestProxyManager

# 运行特定测试方法
python3 -m unittest tests.test_core.TestProxyManager.test_proxy_config_creation

# 详细输出
python3 -m unittest discover tests -v
```

### 方式3: 使用 pytest（如果已安装）

```bash
# 安装 pytest
pip install pytest pytest-cov

# 运行测试
pytest tests/

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 详细输出
pytest tests/ -v

# 只运行失败的测试
pytest tests/ --lf
```

---

## 测试详解

### 1. 代理管理器测试

**测试内容**:
- 代理配置创建
- 代理URL生成
- 带认证的代理URL
- 代理管理器初始化

**示例**:
```python
def test_proxy_config_creation(self):
    """测试代理配置创建"""
    config = ProxyConfig(
        proxy_type='http',
        host='127.0.0.1',
        port=7890
    )

    self.assertEqual(config.proxy_type, 'http')
    self.assertEqual(config.host, '127.0.0.1')
    self.assertEqual(config.port, 7890)
```

### 2. NLP意图识别测试

**测试内容**:
- 价格查询意图识别
- 买入订单意图识别
- 卖出订单意图识别
- 分���意图识别
- 未知意图处理

**示例**:
```python
def test_query_price_intent(self):
    """测试价格查询意图"""
    intent, confidence = self.recognizer.recognize("BTC现在多少钱？")

    self.assertEqual(intent, 'query_price')
    self.assertGreater(confidence, 0.8)
```

### 3. 技术指标测试

**测试内容**:
- RSI计算正确性
- MACD计算正确性
- 布林带计算正确性
- ATR计算正确性

**示例**:
```python
def test_calculate_rsi(self):
    """测试RSI计算"""
    indicators = TechnicalIndicators()
    rsi_values = indicators.calculate_rsi(self.mock_klines, period=14)

    self.assertIsInstance(rsi_values, list)
    self.assertTrue(all(0 <= v <= 100 for v in rsi_values))
```

### 4. 回测引擎测试

**测试内容**:
- 引擎初始化
- 简单策略回测
- 绩效指标计算

**示例**:
```python
def test_simple_strategy_backtest(self):
    """测试简单策略回测"""
    engine = BacktestEngine(initial_capital=10000)

    def buy_hold_strategy(klines):
        if len(klines) == 1:
            return {'signal': 'BUY'}
        return {'signal': 'HOLD'}

    performance = engine.run_backtest(self.mock_klines, buy_hold_strategy)

    self.assertIn('total_return', performance)
    self.assertIn('win_rate', performance)
```

---

## 编写新测试

### 测试模板

```python
import unittest

class TestNewFeature(unittest.TestCase):
    """测试新功能"""

    def setUp(self):
        """测试前准备"""
        # 初始化测试数据
        self.test_data = {}

    def tearDown(self):
        """测试后清理"""
        # 清理资源
        pass

    def test_basic_functionality(self):
        """测试基本功能"""
        # 准备
        input_data = "test"

        # 执行
        result = some_function(input_data)

        # 验证
        self.assertEqual(result, expected_value)
        self.assertTrue(condition)
        self.assertIn(item, collection)
```

### 常用断言方法

```python
# 相等性
self.assertEqual(a, b)          # a == b
self.assertNotEqual(a, b)       # a != b

# 真值
self.assertTrue(x)              # bool(x) is True
self.assertFalse(x)             # bool(x) is False

# 包含
self.assertIn(a, b)             # a in b
self.assertNotIn(a, b)          # a not in b

# 类型
self.assertIsInstance(a, b)     # isinstance(a, b)
self.assertIsNone(x)            # x is None

# 比较
self.assertGreater(a, b)        # a > b
self.assertLess(a, b)           # a < b
self.assertGreaterEqual(a, b)   # a >= b
self.assertLessEqual(a, b)      # a <= b

# 异常
self.assertRaises(ValueError, func, args)
with self.assertRaises(ValueError):
    func(args)
```

---

## Mock 和测试数据

### 使用 Mock 对象

```python
from unittest.mock import Mock, patch

class TestWithMock(unittest.TestCase):

    @patch('src.api.binance_client.BinanceClient')
    def test_with_mock_client(self, mock_client):
        """使用Mock客户端测试"""
        # 设置Mock返回值
        mock_client.get_ticker_price.return_value = {
            'symbol': 'BTCUSDT',
            'price': '68234.50'
        }

        # 测试代码
        result = some_function(mock_client)

        # 验证Mock被调用
        mock_client.get_ticker_price.assert_called_once()
```

### 创建测试数据

```python
def create_mock_klines(count=100, base_price=68000):
    """创建模拟K线数据"""
    klines = []
    for i in range(count):
        klines.append({
            'open': base_price + i * 10,
            'high': base_price + i * 10 + 50,
            'low': base_price + i * 10 - 50,
            'close': base_price + i * 10 + 20,
            'volume': 1000 + i * 10,
            'close_time': 1709856000000 + i * 3600000
        })
    return klines
```

---

## 持续集成 (CI)

### GitHub Actions 配置

创建 `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 测试最佳实践

### 1. 测试命名

```python
# ✅ 好的命名
def test_proxy_url_generation_with_authentication(self):
    pass

# ❌ 不好的命名
def test1(self):
    pass
```

### 2. 测试独立性

```python
# ✅ 每个测试独立
def test_feature_a(self):
    data = create_test_data()
    result = function_a(data)
    self.assertEqual(result, expected)

def test_feature_b(self):
    data = create_test_data()  # 重新创建
    result = function_b(data)
    self.assertEqual(result, expected)

# ❌ 测试相互依赖
class_data = None

def test_feature_a(self):
    global class_data
    class_data = create_test_data()
    # ...

def test_feature_b(self):
    # 依赖 test_feature_a 的结果
    result = function_b(class_data)
```

### 3. 测试覆盖边界情况

```python
def test_calculate_rsi(self):
    # 正常情况
    result = calculate_rsi(normal_data)
    self.assertGreater(result, 0)

    # 边界情况
    result = calculate_rsi([])  # 空数据
    self.assertEqual(result, 0)

    result = calculate_rsi(single_item)  # 单个数据
    self.assertEqual(result, 50)
```

### 4. 使用描述性断言消息

```python
# ✅ 带消息
self.assertEqual(result, expected,
                f"RSI计算错误: 期望{expected}, 实际{result}")

# ❌ 无消息
self.assertEqual(result, expected)
```

---

## 测试覆盖率

### 生成覆盖率报告

```bash
# 安装 coverage
pip install coverage

# 运行测试并收集覆盖率
coverage run -m unittest discover tests

# 查看报告
coverage report

# 生成HTML报告
coverage html
# 在浏览器中打开 htmlcov/index.html
```

### 覆盖率目标

- **核心模块**: 80%+
- **工具模块**: 70%+
- **整体项目**: 75%+

---

## 性能测试

### 基准测试示例

```python
import time

class TestPerformance(unittest.TestCase):

    def test_indicator_calculation_speed(self):
        """测试指标计算速度"""
        klines = create_mock_klines(1000)

        start = time.time()
        result = calculate_rsi(klines)
        elapsed = time.time() - start

        # 应该在100ms内完成
        self.assertLess(elapsed, 0.1,
                       f"RSI计算太慢: {elapsed:.3f}秒")
```

---

## 故障排查

### 常见问题

#### 1. 导入错误

```
ModuleNotFoundError: No module named 'src'
```

**解决方案**:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

#### 2. 测试数据问题

```
AssertionError: Lists differ
```

**解决方案**: 检查测试数据是否正确，使用 `print()` 调试

#### 3. Mock 不生效

```
AttributeError: Mock object has no attribute 'method'
```

**解决方案**: 确保 Mock 对象正确配置返回值

---

## 下一步

### 待添加的测试

- [ ] HTTP API 端点测试
- [ ] WebSocket 连接测试
- [ ] 数据库操作测试（如果有）
- [ ] 集成测试
- [ ] 端到端测试

### 改进建议

1. 增加测试覆盖率到 85%+
2. 添加性能基准测试
3. 实现自动化 CI/CD
4. 添加压力测试
5. 实现测试数据生成器

---

## 参考资源

- [Python unittest 文档](https://docs.python.org/3/library/unittest.html)
- [pytest 文档](https://docs.pytest.org/)
- [测试驱动开发 (TDD)](https://en.wikipedia.org/wiki/Test-driven_development)

---

## 更新日志

### v3.0.0 (2024-03)
- ✅ 初始测试套件
- ✅ 7个测试类，24个测试用例
- ✅ 覆盖核心功能模块
- ✅ 测试运行器和文档

---

## 贡献

欢迎提交新的测试用例！请确保：
1. 测试命名清晰
2. 包含文档字符串
3. 测试独立运行
4. 覆盖边界情况
