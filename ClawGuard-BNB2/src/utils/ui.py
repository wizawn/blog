#!/usr/bin/env python3
"""
UI/UX 美化工具
提供彩色输出、表格、进度条、ASCII艺术等
"""

import sys
from typing import List, Dict, Optional
from datetime import datetime


class Colors:
    """ANSI颜色代码"""
    # 基础颜色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # 样式
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'

    # 重置
    RESET = '\033[0m'


class UI:
    """UI工具类"""

    @staticmethod
    def print_logo():
        """打印ASCII Logo"""
        logo = f"""
{Colors.CYAN}{Colors.BOLD}
   _____ _               _____                     _
  / ____| |             / ____|                   | |
 | |    | | __ ___      | |  __ _   _  __ _ _ __ __| |
 | |    | |/ _` \\ \\ /\\ / / | |_ | | | |/ _` | '__/ _` |
 | |____| | (_| |\\ V  V /| |__| | |_| | (_| | | | (_| |
  \\_____|_|\\__,_| \\_/\\_/  \\_____|\\__,_|\\__,_|_|  \\__,_|

{Colors.RESET}{Colors.BRIGHT_CYAN}        币安安全交易助手 v2.1.0{Colors.RESET}
{Colors.DIM}        让币安交易更安全、更智能、更高效{Colors.RESET}
"""
        print(logo)

    @staticmethod
    def print_header(text: str, width: int = 60):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*width}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(width)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*width}{Colors.RESET}\n")

    @staticmethod
    def print_section(text: str, width: int = 60):
        """打印章节"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*width}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'─'*width}{Colors.RESET}\n")

    @staticmethod
    def print_success(text: str):
        """打印成功信息"""
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

    @staticmethod
    def print_error(text: str):
        """打印错误信息"""
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")

    @staticmethod
    def print_warning(text: str):
        """打印警告信息"""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

    @staticmethod
    def print_info(text: str):
        """打印信息"""
        print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

    @staticmethod
    def print_table(headers: List[str], rows: List[List[str]],
                   col_widths: Optional[List[int]] = None):
        """
        打印表格

        Args:
            headers: 表头
            rows: 数据行
            col_widths: 列宽（可选）
        """
        if not col_widths:
            # 自动计算列宽
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 打印表头
        header_line = "│ " + " │ ".join(
            f"{h:<{w}}" for h, w in zip(headers, col_widths)
        ) + " │"

        separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        top_border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        bottom_border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

        print(f"\n{Colors.CYAN}{top_border}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{header_line}{Colors.RESET}")
        print(f"{Colors.CYAN}{separator}{Colors.RESET}")

        # 打印数据行
        for row in rows:
            row_line = "│ " + " │ ".join(
                f"{str(cell):<{w}}" for cell, w in zip(row, col_widths)
            ) + " │"
            print(f"{Colors.WHITE}{row_line}{Colors.RESET}")

        print(f"{Colors.CYAN}{bottom_border}{Colors.RESET}\n")

    @staticmethod
    def print_progress_bar(current: int, total: int, prefix: str = "",
                          suffix: str = "", length: int = 50):
        """
        打印进度条

        Args:
            current: 当前进度
            total: 总数
            prefix: 前缀文本
            suffix: 后缀文本
            length: 进度条长度
        """
        percent = current / total
        filled = int(length * percent)
        bar = "█" * filled + "░" * (length - filled)

        print(f"\r{prefix} {Colors.CYAN}[{bar}]{Colors.RESET} "
              f"{Colors.BOLD}{percent*100:.1f}%{Colors.RESET} {suffix}",
              end="", flush=True)

        if current == total:
            print()

    @staticmethod
    def print_box(text: str, width: int = 60, color: str = Colors.CYAN):
        """打印文本框"""
        lines = text.split('\n')

        print(f"\n{color}┌{'─' * (width - 2)}┐{Colors.RESET}")
        for line in lines:
            padding = width - len(line) - 4
            print(f"{color}│{Colors.RESET} {line}{' ' * padding} {color}│{Colors.RESET}")
        print(f"{color}└{'─' * (width - 2)}┘{Colors.RESET}\n")

    @staticmethod
    def print_menu(title: str, options: List[str]) -> int:
        """
        打印交互式菜单

        Args:
            title: 菜单标题
            options: 选项列表

        Returns:
            用户选择的索引
        """
        UI.print_header(title)

        for i, option in enumerate(options, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {option}")

        print()

        while True:
            try:
                choice = input(f"{Colors.BOLD}请选择 [1-{len(options)}]: {Colors.RESET}")
                choice_num = int(choice)

                if 1 <= choice_num <= len(options):
                    return choice_num - 1
                else:
                    UI.print_error(f"请输入 1-{len(options)} 之间的数字")
            except ValueError:
                UI.print_error("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n")
                sys.exit(0)

    @staticmethod
    def print_key_value(key: str, value: str, key_width: int = 20):
        """打印键值对"""
        print(f"{Colors.CYAN}{key:<{key_width}}{Colors.RESET}: {Colors.WHITE}{value}{Colors.RESET}")

    @staticmethod
    def print_status(status: str, message: str):
        """
        打印状态信息

        Args:
            status: 状态（success, error, warning, info, loading）
            message: 消息
        """
        icons = {
            'success': f"{Colors.GREEN}✅",
            'error': f"{Colors.RED}❌",
            'warning': f"{Colors.YELLOW}⚠️ ",
            'info': f"{Colors.CYAN}ℹ️ ",
            'loading': f"{Colors.BLUE}⏳"
        }

        icon = icons.get(status, "")
        print(f"{icon} {message}{Colors.RESET}")

    @staticmethod
    def print_price_card(symbol: str, price: float, change: float,
                        high: float, low: float, volume: float):
        """打印价格卡片"""
        change_color = Colors.GREEN if change >= 0 else Colors.RED
        change_arrow = "↗" if change >= 0 else "↘"

        print(f"\n{Colors.CYAN}┌{'─' * 58}┐{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BOLD}{symbol}{Colors.RESET}"
              f"{' ' * (57 - len(symbol))}{Colors.CYAN}│{Colors.RESET}")
        print(f"{Colors.CYAN}├{'─' * 58}┤{Colors.RESET}")

        print(f"{Colors.CYAN}│{Colors.RESET} "
              f"{Colors.BOLD}💰 价格:{Colors.RESET} "
              f"{Colors.BRIGHT_WHITE}${price:,.2f}{Colors.RESET}"
              f"{' ' * (48 - len(f'${price:,.2f}'))}"
              f"{Colors.CYAN}│{Colors.RESET}")

        print(f"{Colors.CYAN}│{Colors.RESET} "
              f"{Colors.BOLD}📈 24h涨跌:{Colors.RESET} "
              f"{change_color}{change:+.2f}% {change_arrow}{Colors.RESET}"
              f"{' ' * (42 - len(f'{change:+.2f}%'))}"
              f"{Colors.CYAN}│{Colors.RESET}")

        print(f"{Colors.CYAN}│{Colors.RESET} "
              f"{Colors.BOLD}📊 24h最高:{Colors.RESET} ${high:,.2f}"
              f"{' ' * (44 - len(f'${high:,.2f}'))}"
              f"{Colors.CYAN}│{Colors.RESET}")

        print(f"{Colors.CYAN}│{Colors.RESET} "
              f"{Colors.BOLD}📉 24h最低:{Colors.RESET} ${low:,.2f}"
              f"{' ' * (44 - len(f'${low:,.2f}'))}"
              f"{Colors.CYAN}│{Colors.RESET}")

        print(f"{Colors.CYAN}│{Colors.RESET} "
              f"{Colors.BOLD}📦 24h成交量:{Colors.RESET} {volume:,.2f}"
              f"{' ' * (41 - len(f'{volume:,.2f}'))}"
              f"{Colors.CYAN}│{Colors.RESET}")

        print(f"{Colors.CYAN}└{'─' * 58}┘{Colors.RESET}\n")

    @staticmethod
    def print_spinner(message: str = "加载中"):
        """打印旋转加载动画"""
        import time
        import itertools

        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])

        for _ in range(20):
            sys.stdout.write(f"\r{Colors.CYAN}{next(spinner)}{Colors.RESET} {message}...")
            sys.stdout.flush()
            time.sleep(0.1)

        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
        sys.stdout.flush()

    @staticmethod
    def confirm(message: str, default: bool = True) -> bool:
        """
        确认对话框

        Args:
            message: 提示信息
            default: 默认值

        Returns:
            用户确认结果
        """
        default_str = "Y/n" if default else "y/N"
        choice = input(f"{Colors.YELLOW}❓ {message} [{default_str}]: {Colors.RESET}").strip().lower()

        if not choice:
            return default

        return choice in ['y', 'yes', '是']

    @staticmethod
    def input_text(prompt: str, default: str = "") -> str:
        """
        文本输入

        Args:
            prompt: 提示信息
            default: 默认值

        Returns:
            用户输入
        """
        if default:
            prompt = f"{prompt} [{default}]"

        value = input(f"{Colors.CYAN}📝 {prompt}: {Colors.RESET}").strip()
        return value if value else default

    @staticmethod
    def clear_screen():
        """清屏"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')


# 便捷函数
def print_logo():
    """打印Logo"""
    UI.print_logo()


def print_header(text: str):
    """打印标题"""
    UI.print_header(text)


def print_success(text: str):
    """打印成功信息"""
    UI.print_success(text)


def print_error(text: str):
    """打印错误信息"""
    UI.print_error(text)


def print_warning(text: str):
    """打印警告信息"""
    UI.print_warning(text)


def print_info(text: str):
    """打印信息"""
    UI.print_info(text)


def print_table(headers: List[str], rows: List[List[str]]):
    """打印表格"""
    UI.print_table(headers, rows)


def confirm(message: str, default: bool = True) -> bool:
    """确认对话框"""
    return UI.confirm(message, default)


if __name__ == "__main__":
    # 测试UI组件
    UI.print_logo()

    UI.print_header("测试标题")

    UI.print_success("操作成功")
    UI.print_error("操作失败")
    UI.print_warning("警告信息")
    UI.print_info("提示信息")

    # 测试表格
    headers = ["名称", "价格", "涨跌幅"]
    rows = [
        ["BTC", "$68,234.50", "+2.34%"],
        ["ETH", "$3,456.78", "+1.89%"],
        ["BNB", "$612.34", "+3.12%"]
    ]
    UI.print_table(headers, rows)

    # 测试进度条
    import time
    for i in range(101):
        UI.print_progress_bar(i, 100, prefix="下载中", suffix="完成")
        time.sleep(0.02)

    # 测试价格卡片
    UI.print_price_card("BTCUSDT", 68234.50, 2.34, 69100.00, 66500.00, 28456.78)

    # 测试确认对话框
    if UI.confirm("是否继续"):
        print("用户选择继续")
