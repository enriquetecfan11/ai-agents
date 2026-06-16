"""Registro central de skills (cargadas desde SKILL.md)."""

from __future__ import annotations

import logging
from pathlib import Path

from agents.config import SKILLS_SEARCH_PATHS
from agents.skills.base import BaseSkill
from agents.skills.loader import SkillDefinition, build_skill_catalog, discover_skills
from agents.skills.markdown_skill import MarkdownSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}
        self._definitions: dict[str, SkillDefinition] = {}

    def register(self, skill: BaseSkill, definition: SkillDefinition | None = None) -> None:
        self._skills[skill.intent_label] = skill
        if definition is not None:
            self._definitions[skill.intent_label] = definition
        elif isinstance(skill, MarkdownSkill):
            self._definitions[skill.intent_label] = skill.definition

    def get_by_intent(self, intent: str) -> BaseSkill:
        if intent not in self._skills:
            if "general" in self._skills:
                return self._skills["general"]
            raise KeyError(f"No hay skill registrada para intent '{intent}'")
        return self._skills[intent]

    def intent_descriptions(self) -> dict[str, str]:
        return {intent: skill.description for intent, skill in self._skills.items()}

    def all_skills(self) -> list[BaseSkill]:
        return list(self._skills.values())

    def definitions(self) -> list[SkillDefinition]:
        return list(self._definitions.values())

    def catalog(self) -> str:
        return build_skill_catalog(self.definitions())


def build_default_registry(search_paths: list[Path] | None = None) -> SkillRegistry:
    paths = search_paths or SKILLS_SEARCH_PATHS
    definitions = discover_skills(paths)

    if not definitions:
        logger.warning(
            "No se encontraron SKILL.md en %s. "
            "Crea skills en skills/<nombre>/SKILL.md",
            [str(p) for p in paths],
        )

    registry = SkillRegistry()
    for definition in definitions:
        registry.register(MarkdownSkill(definition), definition)
        logger.info("Skill cargada: %s (%s)", definition.name, definition.location)

    return registry
