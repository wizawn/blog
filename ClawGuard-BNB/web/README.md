# ClawGuard-BNB Web 管理界面

## 📋 概述

ClawGuard-BNB Web 管理界面提供可视化的交易管理、策略监控和系统配置功能。

## 🎯 功能特性

### 1. 仪表盘
- 账户总览（总资产、今日盈亏、持仓数量）
- 实时价格监控
- 运行中的策略状态
- 最近订单记录

### 2. 交易管理
- 现货交易（市价单、限价单）
- 合约交易（开仓、平仓、杠杆调整）
- 账户余额查看
- 持仓管理
- 订单管理（查看、取消）

### 3. 策略管理
- 策略列表查看
- 创建新策略（网格、均线交叉等）
- 启动/停止策略
- 策略绩效监控
- 策略删除

### 4. 市场分析
- K线图表（支持多时间周期）
- 技术指标（RSI、MACD、布林带、均线）
- 综合分析信号
- 市场深度

### 5. 风险管理
- 风控配置（单笔限额、每日亏损、持仓比例）
- 风控统计
- 风控告警历史

### 6. 系统设置
- 交易模式切换（模拟盘/测试网/实盘）
- 代理配置（HTTP/HTTPS/SOCKS5）
- NLP 自然语言测试
- 系统信息查看

## 🚀 快速开始

### 方式1: 生产模式（推荐）

```bash
# 1. 安装 Python 依赖
pip install flask flask-cors flask-socketio

# 2. 安装 Node.js 依赖并构建前端
cd web/frontend
npm install
npm run build

# 3. 启动服务器
cd ..
python3 start_web.py
```

访问: http://localhost:8080

### 方式2: 开发模式（前端热重载）

```bash
# 1. 安装依赖
pip install flask flask-cors flask-socketio
cd web/frontend && npm install && cd ..

# 2. 启动开发服务器
python3 start_web.py --dev
```

- 前端: http://localhost:3000
- 后端: http://localhost:8080

### 方式3: 一键启动

```bash
# 构建并启动
python3 web/start_web.py --build

# 或使用自定义端口
python3 web/start_web.py --port 9000
```

## 📁 项目结构

```
web/
├── backend/                    # 后端服务器
│   ├── app.py                  # Flask 应用
│   ├── routes/                 # API 路由
│   │   ├── dashboard.py        # 仪表盘
│   │   ├── trading.py          # 交易
│   │   ├── strategy.py         # 策略
│   │   ├── analysis.py         # 分析
│   │   ├── risk.py             # 风控
│   │   └── settings.py         # 设置
│   └── websocket/              # WebSocket
│       └── realtime.py         # 实时推送
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/              # 页面
│   │   │   ├── Dashboard.vue
│   │   │   ├── Trading.vue
│   │   │   ├── Strategy.vue
│   │   │   ├── Analysis.vue
│   │   │   ├── Risk.vue
│   │   │   └── Settings.vue
│   │   ├── components/         # 组件
│   │   │   ├── PriceCard.vue
│   │   │   ├── OrderForm.vue
│   │   │   ├── KLineChart.vue
│   │   │   └── PositionTable.vue
│   │   ├── api/                # API 客户端
│   │   ├── router/             # 路由
│   │   └── store/              # 状态管理
│   ├── package.json
│   └── vite.config.js
│
├── start_web.py                # 启动脚本
└── README.md                   # 本文档
```

## 🔌 API 端点

### 仪表盘
- `GET /api/dashboard/overview` - 获取概览
- `GET /api/dashboard/prices` - 获取价格列表
- `GET /api/dashboard/strategies` - 获取策略状态
- `GET /api/dashboard/system-status` - 获取系统状态

### 交易
- `POST /api/trading/spot/order` - 下现货订单
- `GET /api/trading/spot/orders` - 获取现货订单
- `DELETE /api/trading/spot/order/:id` - 取消订单
- `POST /api/trading/futures/order` - 下合约订单
- `GET /api/trading/futures/positions` - 获取持仓
- `POST /api/trading/futures/leverage` - 设置杠杆

### 策略
- `GET /api/strategy/list` - 获取策略列表
- `POST /api/strategy/create` - 创建策略
- `GET /api/strategy/:id` - 获取策略详情
- `POST /api/strategy/:id/start` - 启动策略
- `POST /api/strategy/:id/stop` - 停止策略
- `DELETE /api/strategy/:id` - 删除策略

### 分析
- `GET /api/analysis/klines` - 获取K线数据
- `GET /api/analysis/indicators` - 获取技术指标
- `GET /api/analysis/summary` - 获取分析摘要

### 风控
- `GET /api/risk/config` - 获取风控配置
- `POST /api/risk/config` - 更新风控配置
- `GET /api/risk/stats` - 获取风控统计
- `GET /api/risk/alerts` - 获取风控告警

### 设置
- `GET /api/settings/trading-mode` - 获取交易模式
- `POST /api/settings/trading-mode` - 设置交易模式
- `GET /api/settings/proxy` - 获取代理配置
- `POST /api/settings/proxy` - 更新代理配置
- `POST /api/settings/nlp/parse` - NLP 解析

## 🔧 配置

### 后端配置

编辑 `~/.clawguard/config.yaml`:

```yaml
api:
  host: 0.0.0.0
  port: 8080
  debug: false
  cors_enabled: true
```

### 前端配置

编辑 `web/frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8080
```

## 🌐 WebSocket 实时推送

### 连接

```javascript
import io from 'socket.io-client'

const socket = io('http://localhost:8080')

socket.on('connect', () => {
  console.log('已连接')
})
```

### 订阅价格

```javascript
socket.emit('subscribe_price', {
  symbols: ['BTCUSDT', 'ETHUSDT']
})

socket.on('price_update', (data) => {
  console.log('价格更新:', data.prices)
})
```

### 订阅账户

```javascript
socket.emit('subscribe_account')

socket.on('account_update', (data) => {
  console.log('账户更新:', data.account)
})
```

## 📱 界面截图

### 仪表盘
- 显示账户总资产、今日盈亏
- 实时价格卡片
- 运行中的策略列表
- 最近订单记录

### 交易页面
- 现货/合约交易切换
- 下单表单（市价/限价）
- 账户余额表格
- 当前订单列表

### 策略页面
- 策略列表（名称、类型、盈亏、状态）
- 创建策略对话框
- 启动/停止/删除操作

### 分析页面
- K线图表（ECharts）
- 技术指标卡片
- 综合分析信号

## 🔐 安全建议

1. **生产环境**
   - 修改 Flask SECRET_KEY
   - 启用 HTTPS
   - 配置防火墙规则
   - 使用反向代理（Nginx）

2. **API 密钥**
   - 不要在前端暴露 API 密钥
   - 所有敏感操作通过后端处理

3. **CORS 配置**
   - 生产环境限制允许的域名
   - 不要使用 `*` 通配符

## 🐛 故障排除

### 前端无法连接后端

检查：
1. 后端是否正常运行
2. 端口是否被占用
3. 防火墙设置
4. CORS 配置

### WebSocket 连接失败

检查：
1. 后端 SocketIO 是否启动
2. 浏览器是否支持 WebSocket
3. 代理服务器配置

### K线图不显示

检查：
1. ECharts 是否正确加载
2. API 是否返回数据
3. 浏览器控制台错误

## 📚 技术栈

### 后端
- Flask 2.3+ - Web 框架
- Flask-SocketIO 5.3+ - WebSocket 支持
- Flask-CORS 4.0+ - CORS 支持

### 前端
- Vue.js 3.3+ - 前端框架
- Element Plus 2.4+ - UI 组件库
- ECharts 5.4+ - 图表库
- Axios 1.5+ - HTTP 客户端
- Socket.IO Client 4.7+ - WebSocket 客户端
- Vite 4.4+ - 构建工具

## 🎉 总结

ClawGuard-BNB Web 管理界面提供了完整的可视化交易管理功能，支持：

- ✅ 实时数据监控
- ✅ 现货和合约交易
- ✅ 策略管理
- ✅ 技术分析
- ✅ 风险控制
- ✅ 系统配置

**立即开始**: `python3 web/start_web.py`
