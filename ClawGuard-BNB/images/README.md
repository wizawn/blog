# 图片说明

本目录用于存放项目演示图片。

## 需要的图片

### 1. audit_demo.png
**内容**: API安全审计输出示例
**获取方式**: ��行 `python3 clawguard.py audit` 并截图
**要点**: 
- 显示完整的审计报告
- 包含风险等级、检查项目、修复建议
- 终端背景使用深色主题

### 2. price_demo.png
**内容**: 价格查询输出
**获取方式**: 运行 `python3 clawguard.py price BTC` 并截图
**要点**:
- 显示美化的价格卡片
- 包含价格、涨跌幅、最高最低价等信息

### 3. analysis_demo.png
**内容**: 技术分析输出
**获取方式**: 运行 `python3 clawguard.py analyze BTC --interval 1h` 并截图
**要点**:
- 显示RSI、MACD、布林带等指标
- 显示综合信号

### 4. interactive_menu.png
**内容**: 交互式主菜单
**获取方式**: 运行 `python3 interactive_menu.py` 并截图
**要点**:
- 显示完整的菜单选项
- 包含Logo和菜单项

### 5. setup_wizard.png
**内容**: 配置向导界面
**获取方式**: 运行 `python3 clawguard.py setup` 并截图
**要点**:
- 显示配置向导的交互过程
- 可以是配置的某个步骤

### 6. technical_analysis.png
**内容**: 完整的技术分析输出
**获取方式**: 同 analysis_demo.png，但显示更完整的输出
**要点**:
- 显示所有指标的详细信息

### 7. grid_strategy.png（可选）
**内容**: 网格策略运行状态
**获取方式**: 运行网格策略并截图状态输出
**要点**:
- 显示网格参数、活跃订单、利润等信息

### 8. project_structure.png（可选）
**内容**: 项目结构图
**获取方式**: 使用 `tree` 命令或手动绘制
**要点**:
- 显示主要的目录和文件结构

## 截图工具推荐

### Windows
- Snipping Tool（系统自带）
- ShareX（免费，功能强大）

### macOS
- Command + Shift + 4（系统自带）
- CleanShot X（付费，功能强大）

### Linux
- gnome-screenshot
- flameshot

## 终端美化建议

为了获得更好的截图效果：

1. **终端主题**: 使用深色主题（如 Dracula、Nord）
2. **字体**: 使用等宽字体（如 Fira Code、JetBrains Mono）
3. **字体大小**: 14-16pt
4. **窗口大小**: 至少 80x24
5. **背景**: 纯色背景，避免透明度

## 图片规格

- **格式**: PNG
- **分辨率**: 至少 1920x1080
- **文件大小**: 每张图片 < 2MB
- **命名**: 使用英文小写和下划线

## 替代方案

如果暂时无法提供真实截图，可以：

1. 使用文本描述代替
2. 使用ASCII艺术图
3. 使用在线工具生成终端截图（如 carbon.now.sh）
4. 录制演示视频，从视频中截取关键帧

---

**注意**: 截图时请确保不要包含真实的API密钥或敏感信息！
