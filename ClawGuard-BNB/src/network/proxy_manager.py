#!/usr/bin/env python3
"""
代理管理器 - 支持 HTTP/HTTPS/SOCKS5 代理
提供代理池、自动轮转、健康检查等功能
"""

import time
import requests
from typing import Optional, Dict, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ProxyConfig:
    """代理配置类"""

    def __init__(self, proxy_type: str, host: str, port: int,
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化代理配置

        Args:
            proxy_type: 代理类型 (http, https, socks5)
            host: 代理主机
            port: 代理端口
            username: 用户名（可选）
            password: 密码（可选）
        """
        self.proxy_type = proxy_type.lower()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.last_check = 0
        self.is_healthy = True
        self.failure_count = 0

    def get_url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, str]:
        """转换为requests库使用的代理字典"""
        proxy_url = self.get_url()
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def __repr__(self) -> str:
        return f"ProxyConfig({self.proxy_type}://{self.host}:{self.port})"


class ProxyManager:
    """代理管理器"""

    def __init__(self, config_dict: Optional[Dict] = None):
        """
        初始化代理管理器

        Args:
            config_dict: 代理配置字典
        """
        self.enabled = False
        self.current_proxy: Optional[ProxyConfig] = None
        self.proxy_pool: List[ProxyConfig] = []
        self.pool_enabled = False
        self.failover_enabled = True
        self.retry_count = 3
        self.timeout = 10
        self.current_pool_index = 0

        if config_dict:
            self.load_config(config_dict)

    def load_config(self, config: Dict):
        """
        从配置字典加载代理设置

        Args:
            config: 代理配置字典
        """
        self.enabled = config.get('enabled', False)

        if not self.enabled:
            return

        # 加载主代理
        proxy_type = config.get('type', 'http')
        host = config.get('host')
        port = config.get('port')
        username = config.get('username')
        password = config.get('password')

        if host and port:
            self.current_proxy = ProxyConfig(proxy_type, host, port, username, password)
            logger.info(f"已加载代理配置: {self.current_proxy}")

        # 加载代理池
        pool_config = config.get('pool', {})
        self.pool_enabled = pool_config.get('enabled', False)

        if self.pool_enabled:
            proxies = pool_config.get('proxies', [])
            for proxy_dict in proxies:
                proxy = ProxyConfig(
                    proxy_dict.get('type', 'http'),
                    proxy_dict['host'],
                    proxy_dict['port'],
                    proxy_dict.get('username'),
                    proxy_dict.get('password')
                )
                self.proxy_pool.append(proxy)
            logger.info(f"已加载代理池: {len(self.proxy_pool)} 个代理")

        # 加载故障转移配置
        failover_config = config.get('failover', {})
        self.failover_enabled = failover_config.get('enabled', True)
        self.retry_count = failover_config.get('retry_count', 3)
        self.timeout = failover_config.get('timeout', 10)

    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """
        获取当前代理配置（用于requests）

        Returns:
            代理字典或None
        """
        if not self.enabled or not self.current_proxy:
            return None

        return self.current_proxy.to_dict()

    def get_proxy_url(self) -> Optional[str]:
        """
        获取当前代理URL

        Returns:
            代理URL或None
        """
        if not self.enabled or not self.current_proxy:
            return None

        return self.current_proxy.get_url()

    def test_proxy(self, proxy: Optional[ProxyConfig] = None,
                   test_url: str = "https://api.binance.com/api/v3/ping") -> bool:
        """
        测试代理连接

        Args:
            proxy: 要测试的代理（默认为当前代理）
            test_url: 测试URL

        Returns:
            是否连接成功
        """
        if not self.enabled:
            return True

        proxy_to_test = proxy or self.current_proxy
        if not proxy_to_test:
            return False

        try:
            logger.info(f"测试代理连接: {proxy_to_test}")
            response = requests.get(
                test_url,
                proxies=proxy_to_test.to_dict(),
                timeout=self.timeout,
                verify=True
            )

            success = response.status_code == 200
            proxy_to_test.is_healthy = success
            proxy_to_test.last_check = time.time()

            if success:
                proxy_to_test.failure_count = 0
                logger.info(f"✅ 代理连接成功: {proxy_to_test}")
            else:
                proxy_to_test.failure_count += 1
                logger.warning(f"❌ 代理连接失败: {proxy_to_test} (状态码: {response.status_code})")

            return success

        except Exception as e:
            proxy_to_test.is_healthy = False
            proxy_to_test.failure_count += 1
            proxy_to_test.last_check = time.time()
            logger.error(f"❌ 代理连接失败: {proxy_to_test} - {str(e)}")
            return False

    def rotate_proxy(self) -> bool:
        """
        轮转到下一个代理（从代理池）

        Returns:
            是否成功轮转
        """
        if not self.pool_enabled or not self.proxy_pool:
            return False

        # 尝试所有代理
        for _ in range(len(self.proxy_pool)):
            self.current_pool_index = (self.current_pool_index + 1) % len(self.proxy_pool)
            next_proxy = self.proxy_pool[self.current_pool_index]

            # 测试代理
            if self.test_proxy(next_proxy):
                self.current_proxy = next_proxy
                logger.info(f"✅ 已切换到代理: {self.current_proxy}")
                return True

        logger.error("❌ 代理池中没有可用的代理")
        return False

    def handle_proxy_failure(self) -> bool:
        """
        处理代理失败（尝试故障转移）

        Returns:
            是否成功恢复
        """
        if not self.failover_enabled:
            return False

        logger.warning("检测到代理失败，尝试故障转移...")

        # 如果启用了代理池，尝试轮转
        if self.pool_enabled and self.proxy_pool:
            return self.rotate_proxy()

        # 否则重新测试当前代理
        return self.test_proxy()

    def get_proxy_status(self) -> Dict:
        """
        获取代理状态信息

        Returns:
            状态字典
        """
        if not self.enabled:
            return {
                'enabled': False,
                'message': '代理未启用'
            }

        status = {
            'enabled': True,
            'current_proxy': str(self.current_proxy) if self.current_proxy else None,
            'is_healthy': self.current_proxy.is_healthy if self.current_proxy else False,
            'failure_count': self.current_proxy.failure_count if self.current_proxy else 0,
            'pool_enabled': self.pool_enabled,
            'pool_size': len(self.proxy_pool),
            'failover_enabled': self.failover_enabled
        }

        return status


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 示例配置
    config = {
        'enabled': True,
        'type': 'http',
        'host': '127.0.0.1',
        'port': 7890,
        'username': None,
        'password': None,
        'pool': {
            'enabled': False,
            'proxies': []
        },
        'failover': {
            'enabled': True,
            'retry_count': 3,
            'timeout': 10
        }
    }

    # 创建代理管理器
    proxy_manager = ProxyManager(config)

    # 测试代理
    print("\n测试代理连接...")
    success = proxy_manager.test_proxy()
    print(f"测试结果: {'成功' if success else '失败'}")

    # 获取状态
    print("\n代理状态:")
    status = proxy_manager.get_proxy_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
