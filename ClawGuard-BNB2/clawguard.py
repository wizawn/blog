#!/usr/bin/env python3
"""
ClawGuard 主命令行接口
提供简单易用的命令行工具
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.utils.health_check import run_health_check, print_system_info
from src.utils.setup_wizard import run_setup_wizard
from src.utils.ui import UI, print_success, print_error, print_info, print_warning
from src.utils.output_formatter import OutputFormatter

logger = get_logger("cli")


def cmd_setup(args):
    """运行配置向导"""
    run_setup_wizard()


def cmd_health(args):
    """运行健康检查"""
    results = run_health_check(verbose=args.verbose)

    if args.info:
        print_system_info()

    # 返回退出码
    return 0 if not results["failed"] else 1


def cmd_audit(args):
    """运行API安全审计"""
    try:
        from src.security.api_auditor import APISecurityAuditor
        from src.config.config_manager import ConfigManager

        print("\n🔍 正在运行API安全审计...\n")

        # 获取API凭证
        config = ConfigManager()
        creds = config.get_api_credentials()

        if not creds or not creds.get('api_key'):
            print("❌ 未配置API密钥")
            print("💡 请先运行: clawguard setup")
            return 1

        # 创建审计器
        auditor = APISecurityAuditor(
            api_key=creds['api_key'],
            api_secret=creds['api_secret'],
            testnet=creds.get('testnet', False)
        )

        # 运行审计
        report = auditor.run_full_audit()

        return 0

    except Exception as e:
        logger.error(f"审计失败: {e}", exc_info=True)
        print(f"\n❌ 审计失败: {str(e)}")
        return 1


def cmd_price(args):
    """查询价格"""
    try:
        from src.api.binance_client import BinanceClient

        symbol = args.symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        client = BinanceClient()
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))

        if not formatter.json_mode:
            print_info(f"正在查询 {symbol} 价格...")

        ticker = client.get_ticker_price(symbol)

        if formatter.json_mode:
            # JSON 输出
            data = formatter.format_price(symbol, ticker)
            formatter.output(data)
        else:
            # 使用美化的价格卡片
            UI.print_price_card(
                symbol=symbol,
                price=float(ticker.get('price', 0)),
                change=float(ticker.get('priceChangePercent', 0)),
                high=float(ticker.get('highPrice', 0)),
                low=float(ticker.get('lowPrice', 0)),
                volume=float(ticker.get('volume', 0))
            )

        return 0

    except Exception as e:
        logger.error(f"查询价格失败: {e}", exc_info=True)
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))
        if formatter.json_mode:
            formatter.output(None, str(e))
        else:
            print_error(f"查询失败: {str(e)}")
        return 1


def cmd_account(args):
    """查询账户信息"""
    try:
        from src.api.binance_client import BinanceClient

        client = BinanceClient()
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))

        if not formatter.json_mode:
            print("\n⏳ 正在查询账户信息...\n")

        account = client.get_account_info()

        if formatter.json_mode:
            # JSON 输出
            data = formatter.format_account(account)
            formatter.output(data)
        else:
            # 人类可读输出
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("💼 账户信息")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            # 计算总权益
            balances = account.get('balances', [])
            total_usdt = 0

            print("\n持仓资产:")
            for balance in balances:
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                total = free + locked

                if total > 0.01:  # 只显示大于0.01的资产
                    asset = balance.get('asset', 'N/A')
                    print(f"  {asset}: {total:.8f} (可用: {free:.8f}, 冻结: {locked:.8f})")

                    if asset == 'USDT':
                        total_usdt = total

            if total_usdt > 0:
                print(f"\n💰 USDT权益: ${total_usdt:.2f}")

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return 0

    except Exception as e:
        logger.error(f"查询账户失败: {e}", exc_info=True)
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))
        if formatter.json_mode:
            formatter.output(None, str(e))
        else:
            print(f"\n❌ 查询失败: {str(e)}")
        return 1


def cmd_logs(args):
    """查看日志"""
    from src.utils.logger import get_log_stats, clean_old_logs

    if args.clean:
        print(f"\n⏳ 正在清理 {args.days} 天前的日志...\n")
        cleaned = clean_old_logs(args.days)

        if cleaned:
            print(f"✅ 已清理 {len(cleaned)} 个日志文件:")
            for log_file in cleaned:
                print(f"  • {log_file}")
        else:
            print("✅ 没有需要清理的日志文件")

        print()
        return 0

    # 显示日志统计
    print("\n📊 日志统计信息\n")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    stats = get_log_stats()

    if not stats:
        print("暂无日志文件")
    else:
        for name, info in stats.items():
            print(f"\n📄 {name}")
            print(f"  大小: {info['size_mb']} MB")
            print(f"  最后修改: {info['modified']}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    log_dir = Path.home() / ".clawguard" / "logs"
    print(f"\n💡 日志目录: {log_dir}")
    print(f"💡 清理旧日志: clawguard logs --clean --days 30\n")

    return 0


def cmd_config(args):
    """配置管理"""
    from src.config.config_manager import ConfigManager

    config = ConfigManager()

    if args.show:
        # 显示配置
        print("\n⚙️  当前配置\n")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        creds = config.get_api_credentials()

        if creds and creds.get('api_key'):
            api_key = creds['api_key']
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"API Key: {masked_key}")
            print(f"环境: {'测试网' if creds.get('testnet') else '主网'}")
        else:
            print("未配置API密钥")

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    elif args.reset:
        # 重置配置
        skip_confirm = getattr(args, 'yes', False)
        if skip_confirm or input("\n⚠️  确认重置所有配置? (yes/no): ").lower() == 'yes':
            config_dir = Path.home() / ".clawguard" / "config"
            if config_dir.exists():
                import shutil
                shutil.rmtree(config_dir)
                print("✅ 配置已重置")
                print("💡 请运行 'clawguard setup' 重新配置\n")
            else:
                print("✅ 配置目录不存在，无需重置\n")
        else:
            print("❌ 已取消\n")

    return 0


def cmd_monitor(args):
    """价格监控"""
    try:
        from src.streaming.websocket_client import create_price_monitor
        from datetime import datetime

        symbol = args.symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        print(f"\n🔍 启动价格监控: {symbol}")
        print(f"告警条件: {args.condition} ${args.threshold:.2f}")
        print("按 Ctrl+C 停止监控\n")

        def on_price(data):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{data['symbol']}: ${data['price']:.2f} "
                  f"({data['change_percent']:+.2f}%)")

        def on_alert(symbol, price, threshold):
            print(f"\n🚨 告警触发！")
            print(f"   {symbol} 价格: ${price:.2f}")
            print(f"   阈值: ${threshold:.2f}\n")

        monitor = create_price_monitor(testnet=False)
        monitor.add_alert(symbol, args.condition, args.threshold, on_alert)
        monitor.start()

        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n监控已停止")
        return 0
    except Exception as e:
        logger.error(f"价格监控失败: {e}", exc_info=True)
        print(f"\n❌ 监控失败: {str(e)}")
        return 1


def cmd_analyze(args):
    """技术分析"""
    try:
        from src.analysis.indicators import create_indicators

        symbol = args.symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        indicators = create_indicators()
        indicators.print_analysis(symbol, args.interval)

        return 0

    except Exception as e:
        logger.error(f"技术分析失败: {e}", exc_info=True)
        print(f"\n❌ 分析失败: {str(e)}")
        return 1


def cmd_report(args):
    """交易报告"""
    try:
        from src.analysis.trade_analyzer import create_analyzer

        symbol = args.symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        analyzer = create_analyzer()

        if args.save:
            report_file, metrics_file = analyzer.save_report(symbol, args.days)
            print(f"\n✅ 报告已保存:")
            print(f"  文本报告: {report_file}")
            print(f"  数据文件: {metrics_file}\n")
        else:
            report = analyzer.generate_report(symbol, args.days)
            print(report)

        return 0

    except Exception as e:
        logger.error(f"生成报告失败: {e}", exc_info=True)
        print(f"\n❌ 报告生成失败: {str(e)}")
        return 1


def cmd_grid(args):
    """网格交易"""
    try:
        from src.strategies.grid_strategy import create_grid_strategy

        symbol = args.symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        if args.action == 'create':
            strategy = create_grid_strategy(
                symbol=symbol,
                lower_price=args.lower,
                upper_price=args.upper,
                grid_count=args.grids,
                investment=args.amount
            )

            strategy.print_status()

            skip_confirm = getattr(args, 'yes', False)
            if skip_confirm or input("\n确认启动网格策略? (yes/no): ").lower() == 'yes':
                print("\n启动网格策略...")
                strategy.start()
            else:
                print("\n已取消")

        return 0

    except Exception as e:
        logger.error(f"网格交易失败: {e}", exc_info=True)
        print(f"\n❌ 操作失败: {str(e)}")
        return 1


def cmd_version(args):
    """显示版本信息"""
    print("\n" + "="*60)
    print("ClawGuard - 币安安全交易助手")
    print("="*60)
    print("\n版本: v2.1.0")
    print("作者: ClawSec")
    print("项目: https://github.com/wizawn/lobsterguard")
    print("\n核心特性:")
    print("  ✅ API安全审计 (12项检查)")
    print("  ✅ 智能风控引擎 (三层防护)")
    print("  ✅ WebSocket实时行情")
    print("  ✅ 价格监控告警")
    print("  ✅ 技术指标分析 (RSI, MACD, 布林带)")
    print("  ✅ 交易历史分析")
    print("  ✅ 网格交易策略")
    print("  ✅ 合约交易支持")
    print("  ✅ HTTP API 服务器")
    print("  ✅ Skills 模块")
    print("  ✅ NLP 命令解析")
    print("="*60 + "\n")

    return 0


def cmd_futures(args):
    """合约交易命令"""
    try:
        from src.api.binance_futures_client import BinanceFuturesClient
        from src.risk.futures_risk_control import FuturesRiskControl

        client = BinanceFuturesClient()
        risk_control = FuturesRiskControl()
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))

        if args.action == 'account':
            # 查询合约账户
            account = client.get_account_info()

            if formatter.json_mode:
                formatter.output({
                    'total_balance': float(account.get('totalWalletBalance', 0)),
                    'available_balance': float(account.get('availableBalance', 0)),
                    'total_unrealized_pnl': float(account.get('totalUnrealizedProfit', 0))
                })
            else:
                print("\n💼 合约账户信息")
                print("=" * 40)
                print(f"总权益: ${float(account.get('totalWalletBalance', 0)):,.2f}")
                print(f"可用余额: ${float(account.get('availableBalance', 0)):,.2f}")
                print(f"未实现盈亏: ${float(account.get('totalUnrealizedProfit', 0)):,.2f}")
                print("=" * 40 + "\n")

        elif args.action == 'position':
            # 查询持仓
            positions = client.get_position_risk(args.symbol if hasattr(args, 'symbol') else None)

            active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

            if formatter.json_mode:
                formatter.output([{
                    'symbol': p['symbol'],
                    'position_amt': float(p.get('positionAmt', 0)),
                    'entry_price': float(p.get('entryPrice', 0)),
                    'mark_price': float(p.get('markPrice', 0)),
                    'unrealized_pnl': float(p.get('unRealizedProfit', 0)),
                    'leverage': int(p.get('leverage', 1)),
                    'liquidation_price': float(p.get('liquidationPrice', 0))
                } for p in active_positions])
            else:
                if not active_positions:
                    print("\n📊 暂无持仓\n")
                else:
                    print("\n📊 当前持仓")
                    print("=" * 60)
                    for p in active_positions:
                        print(f"\n交易对: {p['symbol']}")
                        print(f"数量: {float(p.get('positionAmt', 0))}")
                        print(f"入场价: ${float(p.get('entryPrice', 0)):,.2f}")
                        print(f"标记价: ${float(p.get('markPrice', 0)):,.2f}")
                        print(f"未实现盈亏: ${float(p.get('unRealizedProfit', 0)):,.2f}")
                        print(f"杠杆: {int(p.get('leverage', 1))}x")
                        print(f"强平价: ${float(p.get('liquidationPrice', 0)):,.2f}")
                    print("=" * 60 + "\n")

        elif args.action == 'leverage':
            # 设置杠杆
            symbol = args.symbol.upper()
            if not symbol.endswith('USDT'):
                symbol += 'USDT'

            leverage = args.leverage

            # 风控检查
            passed, error = risk_control.check_leverage(symbol, leverage)
            if not passed:
                if formatter.json_mode:
                    formatter.output(None, error)
                else:
                    print(f"\n❌ {error}\n")
                return 1

            result = client.change_leverage(symbol, leverage)

            if formatter.json_mode:
                formatter.output({
                    'symbol': result.get('symbol'),
                    'leverage': result.get('leverage')
                })
            else:
                print(f"\n✅ 杠杆已设置")
                print(f"交易对: {result.get('symbol')}")
                print(f"杠杆: {result.get('leverage')}x\n")

        elif args.action == 'funding':
            # 查询资金费率
            symbol = args.symbol.upper()
            if not symbol.endswith('USDT'):
                symbol += 'USDT'

            funding_rates = client.get_funding_rate(symbol, limit=5)

            if formatter.json_mode:
                formatter.output([{
                    'funding_time': r.get('fundingTime'),
                    'funding_rate': float(r.get('fundingRate', 0))
                } for r in funding_rates])
            else:
                print(f"\n💰 {symbol} 资金费率历史")
                print("=" * 40)
                for r in funding_rates:
                    rate = float(r.get('fundingRate', 0))
                    print(f"费率: {rate*100:.4f}%")
                print("=" * 40 + "\n")

        elif args.action == 'risk':
            # 风险摘要
            summary = risk_control.get_risk_summary()

            if 'error' in summary:
                if formatter.json_mode:
                    formatter.output(None, summary['error'])
                else:
                    print(f"\n❌ {summary['error']}\n")
                return 1

            if formatter.json_mode:
                formatter.output(summary)
            else:
                print("\n⚠️ 风险摘要")
                print("=" * 40)
                print(f"总权益: ${summary['total_balance']:,.2f}")
                print(f"持仓价值: ${summary['total_position_value']:,.2f}")
                print(f"持仓比例: {summary['position_ratio']*100:.2f}%")
                print(f"风险等级: {summary['risk_level']}")
                print("=" * 40 + "\n")

        return 0

    except Exception as e:
        logger.error(f"合约操作失败: {e}", exc_info=True)
        formatter = OutputFormatter(json_mode=getattr(args, 'json', False))
        if formatter.json_mode:
            formatter.output(None, str(e))
        else:
            print(f"\n❌ 操作失败: {str(e)}\n")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog='clawguard',
        description='ClawGuard - 币安安全交易助手',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  clawguard setup              # 运行配置向导
  clawguard health             # 系统健康检查
  clawguard audit              # API安全审计
  clawguard price BTC --json   # 查询BTC价格(JSON格式)
  clawguard account --json     # 查询账户信息(JSON格式)
  clawguard logs               # 查看日志统计
  clawguard config --show      # 显示当前配置

更多信息: https://github.com/wizawn/lobsterguard
        """
    )

    parser.add_argument('-v', '--version', action='store_true', help='显示版本信息')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出(用于AI集成)')
    parser.add_argument('-y', '--yes', action='store_true', help='跳过确认提示')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # setup 命令
    parser_setup = subparsers.add_parser('setup', help='运行配置向导')
    parser_setup.set_defaults(func=cmd_setup)

    # health 命令
    parser_health = subparsers.add_parser('health', help='系统健康检查')
    parser_health.add_argument('--verbose', action='store_true', help='显示详细信息')
    parser_health.add_argument('--info', action='store_true', help='显示系统信息')
    parser_health.set_defaults(func=cmd_health)

    # audit 命令
    parser_audit = subparsers.add_parser('audit', help='API安全审计')
    parser_audit.set_defaults(func=cmd_audit)

    # price 命令
    parser_price = subparsers.add_parser('price', help='查询价格')
    parser_price.add_argument('symbol', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_price.set_defaults(func=cmd_price)

    # account 命令
    parser_account = subparsers.add_parser('account', help='查询账户信息')
    parser_account.set_defaults(func=cmd_account)

    # logs 命令
    parser_logs = subparsers.add_parser('logs', help='日志管理')
    parser_logs.add_argument('--clean', action='store_true', help='清理旧日志')
    parser_logs.add_argument('--days', type=int, default=30, help='保留天数 (默认: 30)')
    parser_logs.set_defaults(func=cmd_logs)

    # config 命令
    parser_config = subparsers.add_parser('config', help='配置管理')
    parser_config.add_argument('--show', action='store_true', help='显示当前配置')
    parser_config.add_argument('--reset', action='store_true', help='重置配置')
    parser_config.set_defaults(func=cmd_config)

    # version 命令
    parser_version = subparsers.add_parser('version', help='显示版本信息')
    parser_version.set_defaults(func=cmd_version)

    # monitor 命令
    parser_monitor = subparsers.add_parser('monitor', help='价格监控告警')
    parser_monitor.add_argument('symbol', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_monitor.add_argument('--condition', choices=['above', 'below', 'change_percent'],
                               default='above', help='告警条件')
    parser_monitor.add_argument('--threshold', type=float, required=True, help='告警阈值')
    parser_monitor.set_defaults(func=cmd_monitor)

    # analyze 命令
    parser_analyze = subparsers.add_parser('analyze', help='技术指标分析')
    parser_analyze.add_argument('symbol', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_analyze.add_argument('--interval', default='1h',
                               choices=['1m', '5m', '15m', '1h', '4h', '1d'],
                               help='时间间隔 (默认: 1h)')
    parser_analyze.set_defaults(func=cmd_analyze)

    # report 命令
    parser_report = subparsers.add_parser('report', help='交易报告')
    parser_report.add_argument('symbol', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_report.add_argument('--days', type=int, default=30, help='统计天数 (默认: 30)')
    parser_report.add_argument('--save', action='store_true', help='保存报告到文件')
    parser_report.set_defaults(func=cmd_report)

    # grid 命令
    parser_grid = subparsers.add_parser('grid', help='网格交易策略')
    parser_grid.add_argument('action', choices=['create', 'start', 'stop', 'status'],
                            help='操作类型')
    parser_grid.add_argument('symbol', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_grid.add_argument('--lower', type=float, help='网格下限价格')
    parser_grid.add_argument('--upper', type=float, help='网格上限价格')
    parser_grid.add_argument('--grids', type=int, default=10, help='网格数量 (默认: 10)')
    parser_grid.add_argument('--amount', type=float, help='投资金额 (USDT)')
    parser_grid.set_defaults(func=cmd_grid)

    # futures 命令
    parser_futures = subparsers.add_parser('futures', help='合约交易')
    parser_futures.add_argument('action',
                               choices=['account', 'position', 'leverage', 'funding', 'risk'],
                               help='操作类型')
    parser_futures.add_argument('symbol', nargs='?', help='交易对符号 (如: BTC, BTCUSDT)')
    parser_futures.add_argument('leverage', nargs='?', type=int, help='杠杆倍数 (1-125)')
    parser_futures.set_defaults(func=cmd_futures)

    # 解析参数
    args = parser.parse_args()

    # 处理版本参数
    if args.version:
        return cmd_version(args)

    # 如果没有命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    # 执行命令
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        return 1
    except Exception as e:
        logger.error(f"命令执行失败: {e}", exc_info=True)
        print(f"\n❌ 错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
