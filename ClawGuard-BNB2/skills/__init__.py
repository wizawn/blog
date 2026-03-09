
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

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
