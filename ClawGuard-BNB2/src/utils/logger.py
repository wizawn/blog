#!/usr/bin/env python3
"""
ClawGuard 日志系统
提供统一的日志管理，支持文件轮转、多级别日志、彩色输出
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


class ClawGuardLogger:
    """ClawGuard 日志管理器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.log_dir = Path.home() / ".clawguard" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 主日志文件
        self.main_log_file = self.log_dir / "clawguard.log"
        # 错误日志文件
        self.error_log_file = self.log_dir / "error.log"
        # 交易日志文件
        self.trade_log_file = self.log_dir / "trades.log"
        # 审计日志文件
        self.audit_log_file = self.log_dir / "audit.log"

        self.loggers = {}

    def get_logger(
        self,
        name: str = "clawguard",
        level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True
    ) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称
            level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件

        Returns:
            配置好的日志记录器
        """
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # 清除已有的处理器
        logger.handlers.clear()

        # 日志格式
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # 文件处理器（自动轮转）
        if file_output:
            file_handler = RotatingFileHandler(
                self.main_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # 错误日志单独记录
            error_handler = RotatingFileHandler(
                self.error_log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=3,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)

        self.loggers[name] = logger
        return logger

    def get_trade_logger(self) -> logging.Logger:
        """获取交易专用日志记录器"""
        if "trade" in self.loggers:
            return self.loggers["trade"]

        logger = logging.getLogger("clawguard.trade")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        handler = RotatingFileHandler(
            self.trade_log_file,
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.loggers["trade"] = logger
        return logger

    def get_audit_logger(self) -> logging.Logger:
        """获取审计专用日志记录器"""
        if "audit" in self.loggers:
            return self.loggers["audit"]

        logger = logging.getLogger("clawguard.audit")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        handler = RotatingFileHandler(
            self.audit_log_file,
            maxBytes=20 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.loggers["audit"] = logger
        return logger

    def log_trade(
        self,
        order_id: str,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        status: str,
        pnl: Optional[float] = None
    ):
        """
        记录交易日志

        Args:
            order_id: 订单ID
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            price: 价格
            status: 状态
            pnl: 盈亏
        """
        trade_logger = self.get_trade_logger()

        pnl_str = f", PnL: {pnl:+.2f} USDT" if pnl is not None else ""

        trade_logger.info(
            f"Order: {order_id} | {symbol} | {side} | "
            f"Amount: {amount} | Price: {price} | Status: {status}{pnl_str}"
        )

    def log_audit(self, event_type: str, details: str, risk_level: str = "INFO"):
        """
        记录审计日志

        Args:
            event_type: 事件类型
            details: 详细信息
            risk_level: 风险级别
        """
        audit_logger = self.get_audit_logger()
        audit_logger.info(f"[{risk_level}] {event_type} - {details}")

    def get_log_stats(self) -> dict:
        """获取日志统计信息"""
        stats = {}

        for log_file in [self.main_log_file, self.error_log_file,
                         self.trade_log_file, self.audit_log_file]:
            if log_file.exists():
                size_mb = log_file.stat().st_size / (1024 * 1024)
                stats[log_file.name] = {
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }

        return stats

    def clean_old_logs(self, days: int = 30):
        """
        清理旧日志文件

        Args:
            days: 保留天数
        """
        import time
        cutoff_time = time.time() - (days * 86400)

        cleaned = []
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned.append(log_file.name)

        return cleaned


# 全局日志管理器实例
_logger_manager = ClawGuardLogger()


def get_logger(name: str = "clawguard", level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器（便捷函数）

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        日志记录器
    """
    return _logger_manager.get_logger(name, level)


def log_trade(order_id: str, symbol: str, side: str, amount: float,
              price: float, status: str, pnl: Optional[float] = None):
    """记录交易日志（便捷函数）"""
    _logger_manager.log_trade(order_id, symbol, side, amount, price, status, pnl)


def log_audit(event_type: str, details: str, risk_level: str = "INFO"):
    """记录审计日志（便捷函数）"""
    _logger_manager.log_audit(event_type, details, risk_level)


def get_log_stats() -> dict:
    """获取日志统计信息（便捷函数）"""
    return _logger_manager.get_log_stats()


def clean_old_logs(days: int = 30) -> list:
    """清理旧日志（便捷函数）"""
    return _logger_manager.clean_old_logs(days)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger("test", logging.DEBUG)

    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误")

    # 测试交易日志
    log_trade("12345", "BTCUSDT", "BUY", 0.001, 68000, "FILLED", 50.5)

    # 测试审计日志
    log_audit("API_KEY_CHECK", "API密钥权限检查通过", "INFO")
    log_audit("SUSPICIOUS_LOGIN", "检测到异地登录", "WARNING")

    # 显示日志统计
    print("\n日志统计:")
    for name, info in get_log_stats().items():
        print(f"  {name}: {info['size_mb']} MB, 最后修改: {info['modified']}")
