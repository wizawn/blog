# ClawGuard-BNB 交易策略文档

## 概述

ClawGuard-BNB 提供多种量化交易策略，适用于不同的市场环境和风险偏好。所有策略都经过回测验证，并配备完善的风控系统。

---

## 策略列表

| 策略名称 | 类型 | 适用市场 | 风险等级 | 推荐资金 |
|---------|------|---------|---------|---------|
| 网格交易 | 套利 | 震荡市 | 低-中 | $1000+ |
| 合约网格 | 套利 | 震荡市 | 中-高 | $500+ |
| 均线交叉 | 趋势跟踪 | 趋势市 | 中 | $2000+ |
| 突破策略 | 趋势跟踪 | 趋势市 | 中-高 | $2000+ |
| 资金费率套利 | 套利 | 任何 | 低 | $5000+ |

---

## 1. 网格交易策略 (Grid Trading)

### 策略原理

在价格区间内设置多个买卖网格，当价格下跌时自动买入，上涨时自动卖出，通过频繁的低买高卖获取利润。

### 适用场景

- ✅ 震荡行情（横盘整理）
- ✅ 波动率适中（5-15%）
- ✅ 有明确的支撑和阻力位
- ❌ 单边趋势市场
- ❌ 极端波动市场

### 参数说明

```python
symbol: str          # 交易对，如 'BTCUSDT'
lower_price: float   # 网格下限（支撑位）
upper_price: float   # 网格上限（阻力位）
grid_count: int      # 网格数量（建议10-20）
investment: float    # 投资金额
```

### 使用示例

```bash
# CLI方式
python3 clawguard.py grid create BTCUSDT \
  --lower 65000 \
  --upper 70000 \
  --grids 10 \
  --amount 1000

# 查看网格状态
python3 clawguard.py grid status

# 停止网格
python3 clawguard.py grid stop
```

```python
# Python API方式
from src.strategies.grid_strategy import GridStrategy

strategy = GridStrategy(
    symbol='BTCUSDT',
    lower_price=65000,
    upper_price=70000,
    grid_count=10,
    investment=1000
)

# 启动策略
result = strategy.start()
print(result)

# 查看表现
performance = strategy.get_performance()
print(f"已成交订单: {performance['filled_orders']}")
print(f"未实现盈亏: ${performance['unrealized_pnl']:.2f}")
```

### 风险控制

- **止损**: 价格跌破下限5%自动停止
- **止盈**: 总盈利达到20%可考虑退出
- **仓位**: 建议不超过总资金的30%

### 收益预期

- **年化收益**: 15-40%（取决于波动率）
- **胜率**: 85-95%
- **最大回撤**: 10-20%

### 优化建议

1. **动态调整**: 根据市场波动调整网格间距
2. **多币种**: 分散到3-5个币种降低风险
3. **定期重置**: 每月重新评估价格区间

---

## 2. 合约网格策略 (Futures Grid)

### 策略原理

在合约市场使用杠杆进行网格交易，通过做多和做空双向获利。

### 适用场景

- ✅ 震荡行情
- ✅ 有杠杆需求
- ✅ 资金利用率要求高
- ❌ 单边暴涨暴跌
- ❌ 新手交易者

### 参数说明

```python
symbol: str          # 交易对
lower_price: float   # 网格下限
upper_price: float   # 网格上限
grid_count: int      # 网格数量
investment: float    # 投资金额
leverage: int        # 杠杆倍数（1-5倍）
```

### 使用示例

```python
from src.strategies.futures_grid_strategy import FuturesGridStrategy

strategy = FuturesGridStrategy(
    symbol='BTCUSDT',
    lower_price=65000,
    upper_price=70000,
    grid_count=10,
    investment=1000,
    leverage=3  # 3倍杠杆
)

# 启动策略
result = strategy.start()

# 查看持仓
positions = strategy.get_performance()
print(f"未实现盈亏: ${positions['unrealized_pnl']:.2f}")
```

### 风险控制

- **最大杠杆**: 5倍（系统限制）
- **强平保护**: 距离强平价10%时自动减仓
- **资金费率**: 超过0.01%时暂停开仓
- **止损**: 亏损达到本金20%自动平仓

### 收益预期

- **年化收益**: 30-80%（3倍杠杆）
- **胜率**: 80-90%
- **最大回撤**: 15-30%

### 注��事项

⚠️ **高风险警告**: 合约交易风险极高，可能导致爆仓，请谨慎使用！

---

## 3. 均线交叉策略 (MA Crossover)

### 策略原理

使用快速移动平均线和慢速移动平均线的交叉作为买卖信号：
- **金叉** (快线上穿慢线): 买入信号
- **死叉** (快线下穿慢线): 卖出信号

### 适用场景

- ✅ 趋势明显的市场
- ✅ 中长期持仓
- ✅ 波动率较低
- ❌ 震荡市场（频繁假信号）
- ❌ 短线交易

### 参数说明

```python
symbol: str          # 交易对
fast_period: int     # 快线周期（默认10）
slow_period: int     # 慢线周期（默认30）
interval: str        # 时间间隔（1h, 4h, 1d）
```

### 使用示例

```python
from src.strategies.ma_crossover_strategy import MACrossoverStrategy

strategy = MACrossoverStrategy(
    symbol='BTCUSDT',
    fast_period=10,
    slow_period=30,
    interval='1h'
)

# 生成信号
signal = strategy.generate_signal()
print(f"信号: {signal['signal']}")
print(f"原因: {signal['reason']}")

# 如果有信号，执行交易
if signal['signal'] == 'BUY':
    result = strategy.execute_signal(signal, quantity=0.001)
    print(result)
```

### 回测示例

```python
from src.backtest.backtest_engine import BacktestEngine
from src.analysis.indicators import TechnicalIndicators

# 创建回测引擎
engine = BacktestEngine(initial_capital=10000)

# 获取历史数据
indicators = TechnicalIndicators()
klines = indicators.get_klines('BTCUSDT', '1h', limit=500)

# 定义策略函数
def ma_strategy(historical_klines):
    if len(historical_klines) < 30:
        return {'signal': 'HOLD'}

    closes = [k['close'] for k in historical_klines]
    fast_ma = sum(closes[-10:]) / 10
    slow_ma = sum(closes[-30:]) / 30

    if fast_ma > slow_ma:
        return {'signal': 'BUY'}
    elif fast_ma < slow_ma:
        return {'signal': 'SELL'}
    return {'signal': 'HOLD'}

# 运行回测
performance = engine.run_backtest(klines, ma_strategy)
engine.print_report(performance)
```

### 风险控制

- **止损**: 亏损3%自动止损
- **止盈**: 盈利10%部分止盈
- **持仓时间**: 最长持仓7天

### 收益预期

- **年化收益**: 20-50%
- **胜率**: 55-65%
- **最大回撤**: 15-25%

### 优化建议

1. **参数优化**: 根据不同币种调整周期
2. **过滤器**: 添加成交量或RSI过滤假信号
3. **多时间框架**: 结合日线和小时线确认趋势

---

## 4. 突破策略 (Breakout Strategy)

### 策略原理

识别关键的支撑和阻力位，当价格突破这些位置时进场：
- **向上突破阻力位**: 买入
- **向下突破支撑位**: 卖出

### 适用场景

- ✅ 盘整后的突破
- ✅ 趋势启动阶段
- ✅ 波动率扩大
- ❌ 假突破频繁的市场
- ❌ 极端波动

### 参数说明

```python
symbol: str                  # 交易对
lookback_period: int         # 回看周期（默认20）
breakout_threshold: float    # 突破阈值（默认2%）
interval: str                # 时间间隔
```

### 使用示例

```python
from src.strategies.breakout_strategy import BreakoutStrategy

strategy = BreakoutStrategy(
    symbol='BTCUSDT',
    lookback_period=20,
    breakout_threshold=0.02,  # 2%
    interval='1h'
)

# 生成信号
signal = strategy.generate_signal()
print(f"当前价格: ${signal['current_price']:.2f}")
print(f"支撑位: ${signal['support']:.2f}")
print(f"阻力位: ${signal['resistance']:.2f}")
print(f"信号: {signal['signal']}")

# 执行交易
if signal['signal'] in ['BUY', 'SELL']:
    result = strategy.execute_signal(signal, quantity=0.001)
    print(result)
```

### 风险控制

- **止损**: 突破失败回到区间内立即止损
- **止盈**: 盈利5%止盈
- **假突破过滤**: 需要突破2%以上才确认

### 收益预期

- **年化收益**: 25-60%
- **胜率**: 50-60%
- **最大回撤**: 20-30%

### 优化建议

1. **成交量确认**: 突破伴随放量更可靠
2. **回踩确认**: 等待回踩支撑/阻力后再进场
3. **多重时间框架**: 日线突破 + 小时线确认

---

## 5. 资金费率套利 (Funding Rate Arbitrage)

### 策略原理

利用合约市场的资金费率机制，在资金费率较高时做空，较低时做多，赚取资金费。

### 适用场景

- ✅ 任何市场环境
- ✅ 低风险套利
- ✅ 大资金量
- ❌ 小资金（手续费占比高）

### 参数说明

```python
symbol: str              # 交易对
funding_threshold: float # 资金费率阈值（默认0.01%）
hedge_ratio: float       # 对冲比例（默认1.0）
```

### 使用示例

```python
from src.strategies.funding_rate_arbitrage import FundingRateArbitrage

strategy = FundingRateArbitrage(
    symbol='BTCUSDT',
    funding_threshold=0.01,
    hedge_ratio=1.0
)

# 检查套利机会
opportunity = strategy.check_opportunity()
if opportunity['should_trade']:
    print(f"资金费率: {opportunity['funding_rate']:.4f}%")
    print(f"预期收益: ${opportunity['expected_profit']:.2f}")

    # 执行套利
    result = strategy.execute()
    print(result)
```

### 风险控制

- **对冲**: 现货和合约1:1对冲
- **资金费率监控**: 实时监控费率变化
- **自动平仓**: 费率反转时自动平仓

### 收益预期

- **年化收益**: 10-30%（低风险）
- **胜率**: 95%+
- **最大回撤**: <5%

---

## 策略对比

| 策略 | 收益 | 风险 | 胜率 | 适合人群 |
|-----|------|------|------|---------|
| 网格交易 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | 新手-中级 |
| 合约网格 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中级-高级 |
| 均线交叉 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 新手-中级 |
| 突破策略 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 中级-高级 |
| 资金费率套利 | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 中级-高级 |

---

## 策略组合建议

### 保守型组合
- 50% 网格交易
- 30% 资金费率套利
- 20% 现金储备

**预期年化**: 15-25%
**风险等级**: 低

### 平衡型组合
- 40% 网格交易
- 30% 均线交叉
- 20% 突破策略
- 10% 现金储备

**预期年化**: 25-40%
**风险等级**: 中

### 激进型组合
- 30% 合约网格
- 30% 突破策略
- 30% 均线交叉
- 10% 资金费率套利

**预期年化**: 40-80%
**风险等级**: 高

---

## 回测工具使用

### 基础回测

```python
from src.backtest.backtest_engine import BacktestEngine

# 创建引擎
engine = BacktestEngine(
    initial_capital=10000,
    commission=0.001  # 0.1% 手续费
)

# 定义策略
def my_strategy(klines):
    # 策略逻辑
    return {'signal': 'BUY'}  # 或 'SELL', 'HOLD'

# 运行回测
performance = engine.run_backtest(klines, my_strategy)

# 查看结果
print(f"总收益率: {performance['total_return']:.2f}%")
print(f"胜率: {performance['win_rate']:.2f}%")
print(f"最大回撤: {performance['max_drawdown']:.2f}%")
print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
```

### 策略对比

```python
# 回测多个策略
strategies = {
    'MA交叉': ma_crossover_strategy,
    '突破': breakout_strategy,
    '网格': grid_strategy
}

results = {}
for name, strategy in strategies.items():
    engine = BacktestEngine(initial_capital=10000)
    performance = engine.run_backtest(klines, strategy)
    results[name] = performance

# 对比结果
for name, perf in results.items():
    print(f"\n{name}:")
    print(f"  收益率: {perf['total_return']:.2f}%")
    print(f"  夏普比率: {perf['sharpe_ratio']:.2f}")
```

---

## 风险提示

⚠️ **重要提示**:

1. **历史表现不代表未来**: 回测结果仅供参考
2. **市场风险**: 加密货币市场波动极大
3. **杠杆风险**: 合约交易可能导致爆仓
4. **技术风险**: 系统故障、网络问题等
5. **资金管理**: 不要投入超过承受能力的资金

**建议**:
- 从小资金开始测试
- 使用测试网练习
- 设置严格的止损
- 分散投资多个策略
- 定期评估和调整

---

## 常见问题

### Q: 哪个策略最适合新手？
A: 网格交易策略，风险较低，胜率高，容易理解。

### Q: 如何选择策略参数？
A: 先使用默认参数，然后通过回测优化，最后小资金实盘验证。

### Q: 策略失效怎么办？
A: 定期回测，如果连续亏损超过3次，暂停策略重新评估。

### Q: 可以同时运行多个策略吗？
A: 可以，建议不同策略分配不同的资金，避免相互干扰。

### Q: 需要多少资金才能开始？
A: 建议至少$1000，太少的资金手续费占比过高。

---

## 更新日志

### v3.0.0 (2024-03)
- ✅ 新增5种交易策略
- ✅ 完整的回测框架
- ✅ 风控系统集成
- ✅ 策略组合建议

---

## 支持

如有问题，请提交 Issue 或查看完整文档。
