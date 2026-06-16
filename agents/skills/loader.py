"""Descubrimiento y parseo de Agent Skills (formato agentskills.io)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agents.config import ROOT_DIR, SKILLS_SEARCH_PATHS

logger = logging.getLogger(__name__)

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "chroma_db", "documentos"}


@dataclass
class SkillDefinition:
    """Skill descubierta: metadata (tier 1) + instrucciones (tier 2)."""

    name: str
    description: str
    location: Path
    body: str
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def base_dir(self) -> Path:
        return self.location.parent

    def list_resources(self) -> list[str]:
        """Lista archivos en scripts/, references/ y assets/ (tier 3)."""
        resources: list[str] = []
        for subdir in ("scripts", "references", "assets"):
            folder = self.base_dir / subdir
            if not folder.is_dir():
                continue
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    resources.append(str(path.relative_to(self.base_dir)).replace("\\", "/"))
        return resources

    def catalog_entry(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "location": str(self.location),
        }


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw.strip()

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", raw, re.DOTALL)
    if not match:
        return {}, raw.strip()

    yaml_block, body = match.group(1), match.group(2).strip()
    try:
        frontmatter = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        wrapped = re.sub(
            r"^(description:\s*)(.+)$",
            r'\1"\2"',
            yaml_block,
            count=1,
            flags=re.MULTILINE,
        )
        frontmatter = yaml.safe_load(wrapped) or {}

    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, body


def _normalize_metadata(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items()}


def _parse_allowed_tools(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [t for t in value.split() if t]
    if isinstance(value, list):
        return [str(t) for t in value]
    return []


def parse_skill_md(path: Path) -> SkillDefinition | None:
    """Parsea un SKILL.md según la especificación Agent Skills."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("No se pudo leer %s: %s", path, exc)
        return None

    frontmatter, body = _parse_frontmatter(raw)
    name = str(frontmatter.get("name", "")).strip()
    description = str(frontmatter.get("description", "")).strip()
    warnings: list[str] = []

    if not description:
        logger.error("Skill sin description, omitida: %s", path)
        return None

    if not name:
        name = path.parent.name
        warnings.append("name ausente; usando nombre del directorio")

    dir_name = path.parent.name
    if name != dir_name:
        warnings.append(f"name '{name}' no coincide con directorio '{dir_name}'")

    if len(name) > 64:
        warnings.append("name supera 64 caracteres")

    allowed_raw = frontmatter.get("allowed-tools") or frontmatter.get("allowed_tools")
    metadata = _normalize_metadata(frontmatter.get("metadata"))
    tools_from_meta = _parse_allowed_tools(metadata.get("tools"))
    allowed_tools = _parse_allowed_tools(allowed_raw) or tools_from_meta

    for warning in warnings:
        logger.warning("Skill %s: %s", name, warning)

    return SkillDefinition(
        name=name,
        description=description,
        location=path.resolve(),
        body=body,
        license=frontmatter.get("license"),
        compatibility=frontmatter.get("compatibility"),
        metadata=metadata,
        allowed_tools=allowed_tools,
        warnings=warnings,
    )


def discover_skills(search_paths: list[Path] | None = None) -> list[SkillDefinition]:
    """Descubre skills en subdirectorios que contengan SKILL.md."""
    paths = search_paths or SKILLS_SEARCH_PATHS
    found: dict[str, SkillDefinition] = {}

    for base in paths:
        if not base.is_dir():
            continue
        for skill_md in base.rglob("SKILL.md"):
            if any(part in _SKIP_DIRS for part in skill_md.parts):
                continue
            definition = parse_skill_md(skill_md)
            if definition is None:
                continue
            if definition.name in found:
                logger.warning(
                    "Skill '%s' duplicada; prevalece %s sobre %s",
                    definition.name,
                    definition.location,
                    found[definition.name].location,
                )
            found[definition.name] = definition

    return list(found.values())


def build_skill_catalog(definitions: list[SkillDefinition]) -> str:
    """Tier 1: catálogo name+description para el router (progressive disclosure)."""
    if not definitions:
        return ""
    lines = ["<available_skills>"]
    for skill in definitions:
        lines.append("  <skill>")
        lines.append(f"    <name>{skill.name}</name>")
        lines.append(f"    <description>{skill.description}</description>")
        lines.append(f"    <location>{skill.location}</location>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)
