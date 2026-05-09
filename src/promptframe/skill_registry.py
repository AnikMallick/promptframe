"""
SkillRegistry — discover and load skills from a directory tree.

Mirrors :class:`~promptkit.PromptRegistry` but for ``.md`` skill files.

Supported layouts (both can coexist)::

    # Folder-based (preferred)
    skills/
      frontend-design/
        SKILL.md
      data-analysis/
        SKILL.md

    # Flat file
    skills/
      frontend-design.md
      data-analysis.md

Usage::

    from promptkit import SkillRegistry

    registry = SkillRegistry("skills/")
    skill = registry.get("frontend-design")

    registry.list()
    # [{"key": "frontend-design", "name": "...", "description": "...", "tags": [...]}]
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import frontmatter

from .skill import Skill, load_skill_from_path


class SkillRegistry:
    """Discover and load skills from a directory tree.

    Args:
        base: Root directory to scan for skill files.

    Attributes:
        base: Absolute path to the root directory.
    """

    _SKILL_FILENAME = "SKILL.md"

    def __init__(self, base: str) -> None:
        self.base = os.path.abspath(base)
        self._cache: Dict[str, Skill] = {}

    # Discovery

    def _discover(self) -> Dict[str, str]:
        """Return ``{skill_key: absolute_path}`` for every skill found."""
        found: Dict[str, str] = {}

        if not os.path.isdir(self.base):
            return found

        for entry in sorted(os.scandir(self.base), key=lambda e: e.name):
            # Folder-based: skills/frontend-design/SKILL.md
            if entry.is_dir():
                candidate = os.path.join(entry.path, self._SKILL_FILENAME)
                if os.path.isfile(candidate):
                    found[entry.name] = candidate

            # Flat file: skills/frontend-design.md
            elif entry.is_file() and entry.name.endswith(".md"):
                key = os.path.splitext(entry.name)[0]
                if key not in found:   # folder-based wins ties
                    found[key] = entry.path

        return found

    # Public API

    def get(self, key: str, *, force_reload: bool = False) -> Skill:
        """Load a skill by its directory/file key.

        Args:
            key: The folder name or file stem (e.g. ``"frontend-design"``).
            force_reload: Bypass the in-memory cache and re-read from disk.

        Raises:
            KeyError: If no skill with that key exists in the registry.
        """
        if key in self._cache and not force_reload:
            return self._cache[key]

        index = self._discover()
        if key not in index:
            available = sorted(index)
            raise KeyError(
                f"Skill '{key}' not found in '{self.base}'. "
                f"Available: {available}"
            )

        skill = load_skill_from_path(index[key])
        self._cache[key] = skill
        return skill

    def load_all(self, *, force_reload: bool = False) -> Dict[str, Skill]:
        """Load every skill in the registry.

        Returns:
            ``{key: Skill}`` dict for all discovered skills.
        """
        for key, path in self._discover().items():
            if key not in self._cache or force_reload:
                self._cache[key] = load_skill_from_path(path)
        return dict(self._cache)

    def list(self) -> List[Dict[str, Any]]:
        """Return a lightweight summary of all skills without loading content.

        Reads only frontmatter for uncached skills — fast even with many files.

        Returns:
            List of ``{"key", "name", "description", "tags"}`` dicts.
        """
        summaries = []
        for key, path in self._discover().items():
            if key in self._cache:
                s = self._cache[key]
                summaries.append({
                    "key": key,
                    "name": s.name,
                    "description": s.description,
                    "tags": s.tags,
                })
            else:
                try:
                    post = frontmatter.load(path)
                    meta = post.metadata
                    summaries.append({
                        "key": key,
                        "name": meta.get("name", key),
                        "description": meta.get("description"),
                        "tags": meta.get("tags", []),
                    })
                except Exception:
                    summaries.append({
                        "key": key,
                        "name": key,
                        "description": None,
                        "tags": [],
                    })
        return summaries

    def __repr__(self) -> str:
        n = len(self._discover())
        return f"SkillRegistry(base={self.base!r}, n_skills={n})"
