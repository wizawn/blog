#!/usr/bin/env python3
"""
Skills 基类
定义标准化的 Skill 接口
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import json
import logging

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Skills 基类"""

    def __init__(self):
        """初始化 Skill"""
        self.name = ""
        self.version = "1.0.0"
        self.description = ""
        self.actions = []

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Skill 动作

        Args:
            action: 动作名称
            params: 参数字典

        Returns:
            执行结果字典
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取 Skill 元数据

        Returns:
            元数据字典
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'actions': self.actions
        }

    def validate_params(self, params: Dict[str, Any], required: list) -> tuple[bool, Optional[str]]:
        """
        验证参数

        Args:
            params: 参数字典
            required: 必需参数列表

        Returns:
            (是否有效, 错误信息)
        """
        for param in required:
            if param not in params:
                return False, f"缺少必需参数: {param}"

        return True, None

    def success_response(self, data: Any) -> Dict[str, Any]:
        """
        构建成功响应

        Args:
            data: 响应数据

        Returns:
            响应字典
        """
        return {
            'success': True,
            'data': data
        }

    def error_response(self, error: str) -> Dict[str, Any]:
        """
        构建错误响应

        Args:
            error: 错误信息

        Returns:
            响应字典
        """
        return {
            'success': False,
            'error': error
        }

    def log_action(self, action: str, params: Dict[str, Any], result: Dict[str, Any]):
        """
        记录动作日志

        Args:
            action: 动作名称
            params: 参数
            result: 结果
        """
        logger.info(f"[{self.name}] Action: {action}, Success: {result.get('success', False)}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} version={self.version}>"


class SkillRegistry:
    """Skill 注册表"""

    def __init__(self):
        """初始化注册表"""
        self.skills = {}

    def register(self, skill: BaseSkill):
        """
        注册 Skill

        Args:
            skill: Skill 实例
        """
        self.skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name}")

    def get(self, name: str) -> Optional[BaseSkill]:
        """
        获取 Skill

        Args:
            name: Skill 名称

        Returns:
            Skill 实例或 None
        """
        return self.skills.get(name)

    def list_skills(self) -> list:
        """
        列出所有 Skills

        Returns:
            Skill 元数据列表
        """
        return [skill.get_metadata() for skill in self.skills.values()]

    def execute(self, skill_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Skill 动作

        Args:
            skill_name: Skill 名称
            action: 动作名称
            params: 参数

        Returns:
            执行结果
        """
        skill = self.get(skill_name)
        if not skill:
            return {
                'success': False,
                'error': f"Skill not found: {skill_name}"
            }

        try:
            result = skill.execute(action, params)
            skill.log_action(action, params, result)
            return result
        except Exception as e:
            logger.error(f"Skill execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# 全局注册表
_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """获取全局注册表"""
    return _registry


def register_skill(skill: BaseSkill):
    """注册 Skill 到全局注册表"""
    _registry.register(skill)


def execute_skill(skill_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行 Skill 动作"""
    return _registry.execute(skill_name, action, params)


def list_skills() -> list:
    """列出所有 Skills"""
    return _registry.list_skills()
