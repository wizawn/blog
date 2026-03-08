"""
Skills 模块
提供标准化的 Skill 接口供 OpenClaw 调用
"""

from .base_skill import (
    BaseSkill,
    SkillRegistry,
    get_registry,
    register_skill,
    execute_skill,
    list_skills
)

__all__ = [
    'BaseSkill',
    'SkillRegistry',
    'get_registry',
    'register_skill',
    'execute_skill',
    'list_skills'
]
