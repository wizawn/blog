"""
Web 管理 Skill
允许 OpenClaw 通过 Skills 接口管理 Web 界面
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import subprocess
import threading
import requests


class WebManagementSkill:
    """Web 管理 Skill"""

    def __init__(self):
        self.name = "web_management"
        self.version = "1.0.0"
        self.description = "管理 Web 管理界面"
        self.web_process = None

    def execute(self, action: str, params: Dict = None) -> Dict[str, Any]:
        """
        执行 Skill 动作

        Args:
            action: 动作名称
            params: 参数

        Returns:
            执行结果
        """
        if action == "start":
            return self._start_web()
        elif action == "stop":
            return self._stop_web()
        elif action == "status":
            return self._check_status()
        else:
            return {
                "success": False,
                "error": f"未知动作: {action}"
            }

    def _start_web(self) -> Dict[str, Any]:
        """启动 Web 界面"""
        try:
            # 检查是否已经运行
            if self._is_running():
                return {
                    "success": True,
                    "message": "Web 界面已在运行",
                    "url": "http://localhost:8080"
                }

            # 启动 Web 服务器
            web_dir = Path(__file__).parent.parent.parent / 'web'

            def run_web():
                subprocess.run([
                    sys.executable,
                    str(web_dir / 'backend' / 'app.py'),
                    '--host', '0.0.0.0',
                    '--port', '8080'
                ])

            thread = threading.Thread(target=run_web, daemon=True)
            thread.start()

            # 等待启动
            import time
            time.sleep(2)

            if self._is_running():
                return {
                    "success": True,
                    "message": "Web 界面已启动",
                    "url": "http://localhost:8080"
                }
            else:
                return {
                    "success": False,
                    "error": "Web 界面启动失败"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _stop_web(self) -> Dict[str, Any]:
        """停止 Web 界面"""
        # Web 服务器在后台线程运行，无法直接停止
        # 需要重启整个进程
        return {
            "success": False,
            "error": "Web 界面需要重启进程才能停止"
        }

    def _check_status(self) -> Dict[str, Any]:
        """检查 Web 界面状态"""
        if self._is_running():
            return {
                "success": True,
                "status": "running",
                "url": "http://localhost:8080"
            }
        else:
            return {
                "success": True,
                "status": "stopped"
            }

    def _is_running(self) -> bool:
        """检查 Web 界面是否运行"""
        try:
            response = requests.get('http://localhost:8080/health', timeout=2)
            return response.status_code == 200
        except:
            return False


# 导出函数供外部调用
def execute_skill(action: str, params: Dict = None) -> Dict[str, Any]:
    """执行 Web 管理 Skill"""
    skill = WebManagementSkill()
    return skill.execute(action, params)
