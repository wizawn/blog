# 交易模式使用指南

## 📋 三种交易模式

ClawGuard-BNB 支持三种交易模式，让用户可以安全地学习、测试和实盘交易。

---

## 🎯 模式对比

| 特性 | 模拟盘 (Paper) | 测试网 (Testnet) | 实盘 (Live) |
|-----|---------------|-----------------|------------|
| **风险等级** | 无风险 | 低风险 | 高风险 |
| **需要API密钥** | ❌ 否 | ✅ 是（测试网） | ✅ 是（主网） |
| **使用真实资金** | ❌ 否 | ❌ 否 | ✅ 是 |
| **价格数据** | 模拟波动 | 真实测试网 | 真实主网 |
| **交易执行** | 本地模拟 | 测试网API | 主网API |
| **适用场景** | 学习、策略测试 | API集成验证 | 真实交易 |
| **可重置** | ✅ 是 | ❌ 否 | ❌ 否 |

---

## 🚀 快速开始

### 查看当前模式

```bash
# 查看当前交易模式
python3 clawguard.py mode

# 或使用 JSON 输出
python3 clawguard.py mode --json
```

### 切换模式

```bash
# 交互式切换
python3 clawguard.py mode --switch

# 直接切换到模拟盘
python3 clawguard.py mode --set paper

# 切换到测试网
python3 clawguard.py mode --set testnet

# 切换到实盘（需要确认）
python3 clawguard.py mode --set live
```

---

## 📖 模式详解

### 1. 模拟盘模式 (Paper Trading)

**特点**:
- ✅ 完全本地模拟，无需API密钥
- ✅ 模拟真实的价格波动
- ✅ 完整的账户和持仓管理
- ✅ 交易历史记录
- ✅ 可随时重置
- ✅ 零风险学习环境

**适用场景**:
- 🎓 学习量化交易
- 🧪 测试交易策略
- 📊 验证技术指标
- 🎯 练习下单操作

**使用方法**:

```bash
# 切换到模拟盘
python3 clawguard.py mode --set paper

# 查询价格（模拟）
python3 clawguard.py price BTC --json

# 查询账户（模拟）
python3 clawguard.py account --json

# 下单（模拟）
python3 clawguard.py order BTCUSDT BUY MARKET 0.01 --json --yes

# 查看模拟盘统计
python3 clawguard.py paper-stats --json

# 重置模拟盘
python3 clawguard.py paper-reset --yes
```

**Python API**:

```python
from src.trading import get_paper_trading_engine

# 获取模拟交易引擎
engine = get_paper_trading_engine(initial_balance=10000)

# 查询价格
ticker = engine.get_ticker_price('BTCUSDT')
print(f"BTC价格: ${ticker['price']}")

# 下单
order = engine.place_market_order('BTCUSDT', 'BUY', 0.01)
print(f"订单ID: {order['orderId']}")

# 查看统计
stats = engine.get_statistics()
print(f"总盈亏: ${stats['total_pnl']:.2f}")

# 重置
engine.reset()
```

---

### 2. 测试网模式 (Testnet)

**特点**:
- ✅ 币安官方测试网络
- ✅ 需要测试网API密钥
- ✅ 真实的API交互
- ✅ 使用测试币（无价值）
- ✅ 验证策略和集成
- ✅ 无真实资金风险

**适用场景**:
- 🔌 验证API集成
- 🧪 测试完整交易流程
- 📡 测试网络连接
- 🔧 调试程序

**获取测试网API密钥**:

1. 访问币安测试网: https://testnet.binance.vision/
2. 注册账号
3. 生成API密钥
4. 配置到系统

**使用方法**:

```bash
# 设置测试网API密钥
export BINANCE_API_KEY="your_testnet_key"
export BINANCE_API_SECRET="your_testnet_secret"

# 切换到测试网
python3 clawguard.py mode --set testnet

# 使用方式与实盘相同
python3 clawguard.py price BTC --json
python3 clawguard.py account --json
```

---

### 3. 实盘模式 (Live Trading)

**特点**:
- ⚠️ 真实交易环境
- ⚠️ 需要主网API密钥
- ⚠️ 使用真实资金
- ✅ 完整的交易功能
- ✅ 实时市场数据
- ⚠️ 高风险，请谨慎

**适用场景**:
- 💰 真实交易
- 📈 量化策略实盘
- 🎯 专业交易

**安全建议**:

1. ⚠️ **从小资金开始** - 不要投入超过承受能力的资金
2. ⚠️ **设置止损** - 始终设置止损保护
3. ⚠️ **API权限** - 不要给API密钥提现权限
4. ⚠️ **IP白名单** - 启用IP白名单限制
5. ⚠️ **定期检查** - 定期检查持仓和订单

**使用方法**:

```bash
# 设置主网API密钥
export BINANCE_API_KEY="your_mainnet_key"
export BINANCE_API_SECRET="your_mainnet_secret"

# 切换到实盘（需要确认）
python3 clawguard.py mode --set live

# 使用方式与测试网相同
python3 clawguard.py price BTC --json
python3 clawguard.py account --json
```

---

## 🔧 配置方式

### 方式1: 环境变量（推荐）

```bash
# 设置交易模式
export TRADING_MODE="paper"  # paper, testnet, live

# 设置API密钥（测试网/实盘需要）
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
```

### 方式2: 配置文件

编辑 `~/.clawguard/config.yaml`:

```yaml
trading:
  mode: paper  # paper, testnet, live

binance:
  use_testnet: true  # testnet模式时为true
```

### 方式3: CLI命令

```bash
# 使用CLI命令切换
python3 clawguard.py mode --set paper
```

---

## 📊 模拟盘功能

### 查看统计信息

```bash
python3 clawguard.py paper-stats --json
```

**输出示例**:
```json
{
  "initial_balance": 10000.0,
  "current_balance": 9850.5,
  "total_value": 10234.8,
  "total_pnl": 234.8,
  "pnl_percent": 2.35,
  "total_trades": 15,
  "buy_trades": 8,
  "sell_trades": 7,
  "positions_count": 2
}
```

### 重置模拟盘

```bash
# 重置到初始状态
python3 clawguard.py paper-reset --yes
```

⚠️ **注意**: 重置会清空所有交易历史和持仓！

---

## 🎓 推荐学习路径

### 第1阶段: 模拟盘学习（1-2周）

1. **熟悉基础操作**
   - 查询价格
   - 查询账户
   - 下单交易

2. **学习技术分析**
   - 使用技术指标
   - 理解交易信号

3. **测试交易策略**
   - 网格交易
   - 均线交叉
   - 突破策略

4. **验证盈利能力**
   - 持续盈利
   - 控制回撤
   - 提高胜率

### 第2阶段: 测试网验证（3-7天）

1. **API集成测试**
   - 验证API连接
   - 测试订单执行
   - 检查错误处理

2. **完整流程测试**
   - 完整交易流程
   - 异常情况处理
   - 网络问题应对

### 第3阶段: 实盘交易（谨慎）

1. **小资金开始**
   - 从小额开始
   - 逐步增加
   - 控制风险

2. **严格风控**
   - 设置止损
   - 控制仓位
   - 分散投资

3. **持续优化**
   - 记录交易
   - 分析总结
   - 改进策略

---

## 🔍 常见问题

### Q: 模拟盘的价格准确吗？

A: 模拟盘使用基础价格加上随机波动（±0.5%），适合学习和测试，但不完全等同于真实市场。

### Q: 测试网和实盘有什么区别？

A: 测试网使用测试币（无价值），实盘使用真实资金。API使用方式完全相同。

### Q: 如何获取测试网API密钥？

A: 访问 https://testnet.binance.vision/ 注册并生成。

### Q: 模拟盘数据会保存吗？

A: 是的，模拟盘数据保存在 `~/.clawguard/paper_trading.json`。

### Q: 可以同时使用多个模式吗？

A: 不可以，同一时间只能使用一种模式。

### Q: 切换模式会丢失数据吗？

A: 模拟盘数据会保留，测试网和实盘数据在币安服务器上。

---

## 🚨 风险提示

### 模拟盘

- ✅ 无风险
- ⚠️ 模拟价格可能与真实市场有差异
- ⚠️ 不考虑滑点和流动性

### 测试网

- ✅ 低风险（测试币无价值）
- ⚠️ 测试网可能不稳定
- ⚠️ 测试币可能被重置

### 实盘

- ⚠️ **高风险**
- ⚠️ **可能损失全部资金**
- ⚠️ **市场波动剧烈**
- ⚠️ **杠杆交易风险极高**

**重要提示**:
- 只投入你能承受损失的资金
- 始终设置止损
- 不要使用杠杆（除非你完全理解风险）
- 定期检查持仓和风险

---

## 📚 相关文档

- [快速入门](OPENCLAW_QUICKSTART.md)
- [API文档](docs/API.md)
- [策略文档](docs/STRATEGIES.md)
- [风险管理](docs/RISK_MANAGEMENT.md)

---

<div align="center">

**安全第一，谨慎交易**

从模拟盘开始 → 测试网验证 → 小额实盘 → 逐步增加

</div>
