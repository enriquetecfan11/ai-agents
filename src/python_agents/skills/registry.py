"""Registro central de skills disponibles."""

from __future__ import annotations

from src.python_agents.skills.base import BaseSkill
from src.python_agents.skills.implementations import ExampleSkill, GeneralSkill, RagSkill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.intent_label] = skill

    def get_by_intent(self, intent: str) -> BaseSkill:
        if intent not in self._skills:
            return self._skills["general"]
        return self._skills[intent]

    def intent_descriptions(self) -> dict[str, str]:
        return {intent: skill.description for intent, skill in self._skills.items()}

    def all_skills(self) -> list[BaseSkill]:
        return list(self._skills.values())


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(RagSkill())
    registry.register(ExampleSkill())
    registry.register(GeneralSkill())
    return registry
