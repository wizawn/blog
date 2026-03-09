#!/usr/bin/env python3
"""
K线数据缓存管理器
提高数据访问性能
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)


class KlineCache:
    """K线数据缓存"""

    def __init__(self, ttl: int = 60):
        """
        初始化缓存

        Args:
            ttl: 缓存过期时间（秒）
        """
        self.ttl = ttl
        self.cache: Dict[str, Tuple[List, float]] = {}
        self.lock = Lock()

    def get(self, symbol: str, interval: str, limit: int) -> Optional[List]:
        """
        获取缓存的K线数据

        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 数量限制

        Returns:
            K线数据或None
        """
        key = f"{symbol}:{interval}:{limit}"

        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]

                # 检查是否过期
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"缓存命中: {key}")
                    return data
                else:
                    # 过期，删除
                    del self.cache[key]
                    logger.debug(f"缓存过期: {key}")

        return None

    def set(self, symbol: str, interval: str, limit: int, data: List):
        """
        设置缓存

        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 数量限制
            data: K线数据
        """
        key = f"{symbol}:{interval}:{limit}"

        with self.lock:
            self.cache[key] = (data, time.time())
            logger.debug(f"缓存已设置: {key}")

    def clear(self, symbol: Optional[str] = None):
        """
        清除缓存

        Args:
            symbol: 交易对（可选，不指定则清除所有）
        """
        with self.lock:
            if symbol:
                # 清除特定交易对的缓存
                keys_to_delete = [k for k in self.cache.keys() if k.startswith(f"{symbol}:")]
                for key in keys_to_delete:
                    del self.cache[key]
                logger.debug(f"已清除 {symbol} 的缓存")
            else:
                # 清除所有缓存
                self.cache.clear()
                logger.debug("已清除所有缓存")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self.lock:
            total = len(self.cache)
            expired = 0
            current_time = time.time()

            for data, timestamp in self.cache.values():
                if current_time - timestamp >= self.ttl:
                    expired += 1

            return {
                'total': total,
                'active': total - expired,
                'expired': expired,
                'ttl': self.ttl
            }


# 全局缓存实例
_kline_cache = None
_cache_lock = Lock()


def get_kline_cache(ttl: int = 60) -> KlineCache:
    """
    获取K线缓存单例

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        K线缓存实例
    """
    global _kline_cache

    if _kline_cache is None:
        with _cache_lock:
            if _kline_cache is None:
                _kline_cache = KlineCache(ttl)

    return _kline_cache
