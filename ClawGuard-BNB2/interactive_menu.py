#!/usr/bin/env python3
"""
交互式主菜单
提供友好的交互式界面
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.ui import UI, Colors
from src.utils.logger import get_logger

logger = get_logger("menu")


class InteractiveMenu:
    """交互式菜单系统"""

    def __init__(self):
        """初始化菜单"""
        self.running = True

    def show_main_menu(self):
        """显示主菜单"""
        UI.clear_screen()
        UI.print_logo()

        options = [
            "🔧 系统配置",
            "🏥 健康检查",
            "🔒 API安全审计",
            "💰 价格查询",
            "💼 账户信息",
            "🔍 实时监控",
            "📊 技术分析",
            "📈 交易报告",
            "🎯 网格策略",
            "📝 日志管理",
            "⚙️  配置管理",
            "❌ 退出"
        ]

        choice = UI.print_menu("ClawGuard 主菜单", options)

        # 执行对应功能
        menu_actions = [
            self.menu_setup,
            self.menu_health,
            self.menu_audit,
            self.menu_price,
            self.menu_account,
            self.menu_monitor,
            self.menu_analyze,
            self.menu_report,
            self.menu_grid,
            self.menu_logs,
            self.menu_config,
            self.menu_exit
        ]

        if 0 <= choice < len(menu_actions):
            menu_actions[choice]()

    def menu_setup(self):
        """配置向导"""
        UI.print_header("系统配置")

        if UI.confirm("是否运行配置向导?"):
            from src.utils.setup_wizard import run_setup_wizard
            run_setup_wizard()

        self.pause()

    def menu_health(self):
        """健康检查"""
        UI.print_header("系统健康检查")

        from src.utils.health_check import run_health_check, print_system_info

        # 显示系统信息
        if UI.confirm("是否显示系统信息?", default=False):
            print_system_info()

        # 运行健康检查
        verbose = UI.confirm("是否显示详细信息?", default=False)
        results = run_health_check(verbose=verbose)

        self.pause()

    def menu_audit(self):
        """API安全审计"""
        UI.print_header("API安全审计")

        try:
            from src.security.api_auditor import APISecurityAuditor
            from src.config.config_manager import ConfigManager

            # 获取API凭证
            config = ConfigManager()
            creds = config.get_api_credentials()

            if not creds or not creds.get('api_key'):
                UI.print_error("未配置API密钥")
                UI.print_info("请先运行系统配置")
                self.pause()
                return

            UI.print_info("正在运行API安全审计...")

            # 创建审计器
            auditor = APISecurityAuditor(
                api_key=creds['api_key'],
                api_secret=creds['api_secret'],
                testnet=creds.get('testnet', False)
            )

            # 运行审计
            report = auditor.run_full_audit()

        except Exception as e:
            UI.print_error(f"审计失败: {str(e)}")
            logger.error(f"审计失败: {e}", exc_info=True)

        self.pause()

    def menu_price(self):
        """价格查询"""
        UI.print_header("价格查询")

        symbol = UI.input_text("请输入交易对（如 BTC, ETH）", "BTC")
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        try:
            from src.api.binance_client import BinanceClient

            client = BinanceClient()
            UI.print_info(f"正在查询 {symbol} 价格...")

            ticker = client.get_ticker_price(symbol)

            # 使用美化的价格卡片
            UI.print_price_card(
                symbol=symbol,
                price=float(ticker.get('price', 0)),
                change=float(ticker.get('priceChangePercent', 0)),
                high=float(ticker.get('highPrice', 0)),
                low=float(ticker.get('lowPrice', 0)),
                volume=float(ticker.get('volume', 0))
            )

        except Exception as e:
            UI.print_error(f"查询失败: {str(e)}")
            logger.error(f"查询价格失败: {e}", exc_info=True)

        self.pause()

    def menu_account(self):
        """账户信息"""
        UI.print_header("账户信息")

        try:
            from src.api.binance_client import BinanceClient

            client = BinanceClient()
            UI.print_info("正在查询账户信息...")

            account = client.get_account_info()

            # 显示账户信息
            balances = account.get('balances', [])

            # 筛选有余额的资产
            active_balances = []
            for balance in balances:
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                total = free + locked

                if total > 0.01:
                    active_balances.append([
                        balance.get('asset', 'N/A'),
                        f"{total:.8f}",
                        f"{free:.8f}",
                        f"{locked:.8f}"
                    ])

            if active_balances:
                UI.print_table(
                    headers=["资产", "总量", "可用", "冻结"],
                    rows=active_balances
                )
            else:
                UI.print_warning("账户暂无资产")

        except Exception as e:
            UI.print_error(f"查询失败: {str(e)}")
            logger.error(f"查询账户失败: {e}", exc_info=True)

        self.pause()

    def menu_monitor(self):
        """实时监控"""
        UI.print_header("实时价格监控")

        symbol = UI.input_text("请输入交易对（如 BTC）", "BTC")
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        # 选择告警条件
        conditions = ["价格高于", "价格低于", "涨跌幅超过"]
        UI.print_section("选择告警条件")
        for i, cond in enumerate(conditions, 1):
            print(f"  {i}. {cond}")

        cond_choice = UI.input_text("请选择 [1-3]", "1")
        condition_map = {
            "1": "above",
            "2": "below",
            "3": "change_percent"
        }
        condition = condition_map.get(cond_choice, "above")

        threshold = float(UI.input_text("请输入阈值", "70000"))

        UI.print_info(f"启动监控: {symbol} {condition} {threshold}")
        UI.print_warning("按 Ctrl+C 停止监控")

        try:
            from src.streaming.websocket_client import create_price_monitor
            from datetime import datetime

            def on_alert(symbol, price, threshold):
                UI.print_warning(f"告警触发！{symbol} 价格: ${price:.2f}, 阈值: ${threshold:.2f}")

            monitor = create_price_monitor(testnet=False)
            monitor.add_alert(symbol, condition, threshold, on_alert)
            monitor.start()

            import time
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            UI.print_info("监控已停止")
        except Exception as e:
            UI.print_error(f"监控失败: {str(e)}")
            logger.error(f"监控失败: {e}", exc_info=True)

        self.pause()

    def menu_analyze(self):
        """技术分析"""
        UI.print_header("技术指标分析")

        symbol = UI.input_text("请输入交易对（如 BTC）", "BTC")
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
        UI.print_section("选择时间间隔")
        for i, interval in enumerate(intervals, 1):
            print(f"  {i}. {interval}")

        interval_choice = UI.input_text("请选择 [1-6]", "4")
        interval = intervals[int(interval_choice) - 1] if interval_choice.isdigit() else "1h"

        try:
            from src.analysis.indicators import create_indicators

            UI.print_info(f"正在分析 {symbol} ({interval})...")

            indicators = create_indicators()
            indicators.print_analysis(symbol, interval)

        except Exception as e:
            UI.print_error(f"分析失败: {str(e)}")
            logger.error(f"技术分析失败: {e}", exc_info=True)

        self.pause()

    def menu_report(self):
        """交易报告"""
        UI.print_header("交易历史报告")

        symbol = UI.input_text("请输入交易对（如 BTC）", "BTC")
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        days = int(UI.input_text("统计天数", "30"))
        save = UI.confirm("是否保存报告到文件?", default=False)

        try:
            from src.analysis.trade_analyzer import create_analyzer

            UI.print_info(f"正在生成 {symbol} 的 {days} 天交易报告...")

            analyzer = create_analyzer()

            if save:
                report_file, metrics_file = analyzer.save_report(symbol, days)
                UI.print_success(f"报告已保存:")
                UI.print_info(f"  文本报告: {report_file}")
                UI.print_info(f"  数据文件: {metrics_file}")
            else:
                report = analyzer.generate_report(symbol, days)
                print(report)

        except Exception as e:
            UI.print_error(f"生成报告失败: {str(e)}")
            logger.error(f"生成报告失败: {e}", exc_info=True)

        self.pause()

    def menu_grid(self):
        """网格策略"""
        UI.print_header("网格交易策略")

        UI.print_warning("网格交易存在风险，请谨慎操作！")
        UI.print_info("建议先在测试网测试")

        if not UI.confirm("是否继续?"):
            return

        symbol = UI.input_text("请输入交易对（如 BTC）", "BTC")
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        lower = float(UI.input_text("网格下限价格", "65000"))
        upper = float(UI.input_text("网格上限价格", "70000"))
        grids = int(UI.input_text("网格数量", "10"))
        amount = float(UI.input_text("投资金额（USDT）", "1000"))

        try:
            from src.strategies.grid_strategy import create_grid_strategy

            strategy = create_grid_strategy(
                symbol=symbol,
                lower_price=lower,
                upper_price=upper,
                grid_count=grids,
                investment=amount
            )

            strategy.print_status()

            if UI.confirm("确认启动网格策略?"):
                UI.print_info("启动网格策略...")
                strategy.start()
            else:
                UI.print_info("已取消")

        except Exception as e:
            UI.print_error(f"网格策略失败: {str(e)}")
            logger.error(f"网格策略失败: {e}", exc_info=True)

        self.pause()

    def menu_logs(self):
        """日志管理"""
        UI.print_header("日志管理")

        options = [
            "查看日志统计",
            "清理旧日志",
            "返回主菜单"
        ]

        choice = UI.print_menu("日志管理", options)

        if choice == 0:
            # 查看日志统计
            from src.utils.logger import get_log_stats

            stats = get_log_stats()

            if stats:
                rows = []
                for name, info in stats.items():
                    rows.append([
                        name,
                        f"{info['size_mb']} MB",
                        info['modified']
                    ])

                UI.print_table(
                    headers=["日志文件", "大小", "最后修改"],
                    rows=rows
                )
            else:
                UI.print_warning("暂无日志文件")

        elif choice == 1:
            # 清理旧日志
            days = int(UI.input_text("保留天数", "30"))

            if UI.confirm(f"确认清理 {days} 天前的日志?"):
                from src.utils.logger import clean_old_logs

                cleaned = clean_old_logs(days)

                if cleaned:
                    UI.print_success(f"已清理 {len(cleaned)} 个日志文件")
                    for log_file in cleaned:
                        UI.print_info(f"  • {log_file}")
                else:
                    UI.print_info("没有需要清理的日志文件")

        self.pause()

    def menu_config(self):
        """配置管理"""
        UI.print_header("配置管理")

        options = [
            "显示当前配置",
            "重置配置",
            "返回主菜单"
        ]

        choice = UI.print_menu("配置管理", options)

        if choice == 0:
            # 显示配置
            from src.config.config_manager import ConfigManager

            config = ConfigManager()
            creds = config.get_api_credentials()

            if creds and creds.get('api_key'):
                api_key = creds['api_key']
                masked_key = api_key[:8] + "..." + api_key[-4:]

                UI.print_section("当前配置")
                UI.print_key_value("API Key", masked_key)
                UI.print_key_value("环境", "测试网" if creds.get('testnet') else "主网")
            else:
                UI.print_warning("未配置API密钥")

        elif choice == 1:
            # 重置配置
            if UI.confirm("确认重置所有配置?", default=False):
                config_dir = Path.home() / ".clawguard" / "config"
                if config_dir.exists():
                    import shutil
                    shutil.rmtree(config_dir)
                    UI.print_success("配置已重置")
                    UI.print_info("请运行系统配置重新配置")
                else:
                    UI.print_info("配置目录不存在，无需重置")

        self.pause()

    def menu_exit(self):
        """退出"""
        UI.print_header("退出")

        if UI.confirm("确认退出?"):
            UI.print_success("感谢使用 ClawGuard！")
            self.running = False
            sys.exit(0)

    def pause(self):
        """暂停等待用户"""
        print()
        input(f"{Colors.DIM}按 Enter 键继续...{Colors.RESET}")

    def run(self):
        """运行菜单"""
        while self.running:
            try:
                self.show_main_menu()
            except KeyboardInterrupt:
                print("\n")
                if UI.confirm("确认退出?"):
                    UI.print_success("感谢使用 ClawGuard！")
                    break
            except Exception as e:
                UI.print_error(f"发生错误: {str(e)}")
                logger.error(f"菜单错误: {e}", exc_info=True)
                self.pause()


def main():
    """主函数"""
    menu = InteractiveMenu()
    menu.run()


if __name__ == "__main__":
    main()
