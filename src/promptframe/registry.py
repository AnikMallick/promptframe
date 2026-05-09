"""
PromptRegistry — environment-aware YAML prompt loader.

Usage::

    reg = PromptRegistry(base="prompts/", environment="prod", common="shared")

    # Regular prompts
    p = reg.load_prompt("my_prompts")
    print(p.system.format(name="Alice"))   # attribute access via __getattr__
    print(p.prompt_dict["system"].prompt)  # dict access

    # Model prompts (bind to LLMBaseModel fields via model_attribute_id)
    mp = reg.load_model_prompt("field_prompts")
    schema = MyModel.get_format_instructions_with_prompt(
        prompt_model_dict=mp.prompt_model_dict
    )
"""

from __future__ import annotations

import glob
import os
from typing import List, Optional

import yaml

from .models import (
    Metadata,
    Prompt,
    PromptDataModel,
    PromptDataModelYAML,
    PromptYAML,
    PromptYAMLBase,
)
from .skill import Skill, load_skill_from_path
from .skill_registry import SkillRegistry


class PromptRegistry:
    """Load structured YAML prompt files into typed, attribute-accessible models.

    Args:
        base: Root path that contains prompt YAML files.
        environment: Sub-folder for environment-specific overrides (e.g. ``"prod"``).
            Files here take priority over *common* and *base*.
        common: Sub-folder for shared prompts used across environments.
    """

    def __init__(
        self,
        base: str,
        environment: Optional[str] = None,
        common: Optional[str] = None,
    ) -> None:
        self.base = base
        self.env = environment
        self.common = common
        
    # Internal helpers

    def _ensure_yaml_ext(self, name: str, ext: str = ".yaml") -> str:
        if name.endswith((".yaml", ".yml")):
            return name
        return f"{name}{ext}"

    def _get_path_candidates(self, file_name: str) -> List[str]:
        paths: List[str] = []
        if self.env:
            paths.append(os.path.join(self.base, self.env, file_name))
        if self.common:
            paths.append(os.path.join(self.base, self.common, file_name))
        paths.append(os.path.join(self.base, file_name))
        return paths

    # Public API

    def load_yml(self, file_name: str) -> dict:
        """Load a YAML file and return its contents as a plain dict.

        Searches *environment*, *common*, then *base* in that order and
        returns the first match.

        Raises:
            FileNotFoundError: If the file cannot be found in any candidate path.
            ValueError: If the file contains invalid YAML syntax.
        """
        paths = self._get_path_candidates(file_name)
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        return yaml.safe_load(fh)
                except yaml.YAMLError as exc:
                    raise ValueError(f"Invalid YAML in '{path}': {exc}") from exc
        raise FileNotFoundError(
            f"Prompt file '{file_name}' not found. Searched: {paths}"
        )

    def load_prompt(self, prompt_name: str) -> PromptYAML:
        """Load a ``type: prompt`` YAML file.

        Returns a :class:`~promptkit.models.PromptYAML` whose prompts are
        accessible as attributes (``result.my_prompt``) or via
        ``result.prompt_dict["my_prompt"]``.

        Raises:
            ValueError: On missing/invalid metadata or empty prompts list.
            FileNotFoundError: If the file does not exist.
        """
        data = self.load_yml(self._ensure_yaml_ext(prompt_name))
        self._validate_metadata(data, expected_type="prompt")
        return PromptYAML(**data)

    def load_model_prompt(self, model_prompt: str) -> PromptDataModelYAML:
        """Load a ``type: model_prompt`` YAML file.

        Returns a :class:`~promptkit.models.PromptDataModelYAML`.
        Use ``result.prompt_model_dict`` to get a ``{model_attribute_id: PromptDataModel}``
        mapping suitable for passing to
        ``LLMBaseModel.get_format_instructions_with_prompt()``.

        Raises:
            ValueError: On missing/invalid metadata or empty prompts list.
            FileNotFoundError: If the file does not exist.
        """
        data = self.load_yml(self._ensure_yaml_ext(model_prompt))
        self._validate_metadata(data, expected_type="model_prompt")
        return PromptDataModelYAML(**data)


    def load_skill(self, skill_path: str) -> "Skill":
        """Load a single skill .md file by path (relative to base or absolute).

        Pass either a direct path to a ``.md`` file, or a folder name that
        contains a ``SKILL.md`` file::

            skill = hub.load_skill("skills/frontend-design")
            skill = hub.load_skill("skills/frontend-design/SKILL.md")
        """
        if not os.path.isabs(skill_path):
            skill_path = os.path.join(self.base, skill_path)
        if os.path.isdir(skill_path):
            candidate = os.path.join(skill_path, "SKILL.md")
            if os.path.isfile(candidate):
                skill_path = candidate
            else:
                raise FileNotFoundError(
                    f"Directory '{skill_path}' has no SKILL.md"
                )
        return load_skill_from_path(skill_path)

    def skill_registry(self, skills_dir: str = "skills") -> "SkillRegistry":
        """Return a SkillRegistry rooted at *skills_dir* (relative to base)."""
        path = (
            skills_dir if os.path.isabs(skills_dir)
            else os.path.join(self.base, skills_dir)
        )
        return SkillRegistry(path)

    def list_prompts(self) -> List[str]:
        """Return all YAML/YML file names found across search directories.

        Files from higher-priority directories shadow duplicates in lower ones.
        """
        seen: set[str] = set()
        results: List[str] = []
        search_dirs: List[str] = []
        if self.env:
            search_dirs.append(os.path.join(self.base, self.env))
        if self.common:
            search_dirs.append(os.path.join(self.base, self.common))
        search_dirs.append(self.base)

        for dir_path in search_dirs:
            if not os.path.isdir(dir_path):
                continue
            for file_path in sorted(
                glob.glob(os.path.join(dir_path, "*.yml"))
                + glob.glob(os.path.join(dir_path, "*.yaml"))
            ):
                name = os.path.basename(file_path)
                if name not in seen:
                    results.append(name)
                    seen.add(name)

        return results

    # Private helpers

    @staticmethod
    def _validate_metadata(data: dict, expected_type: str) -> None:
        metadata = data.get("metadata") or {}
        if not metadata:
            raise ValueError("'metadata' section is missing from the prompt file.")
        actual_type = metadata.get("type")
        if actual_type != expected_type:
            raise ValueError(
                f"Expected metadata.type='{expected_type}', got '{actual_type}'."
            )
        if not data.get("prompts"):
            raise ValueError("No prompts defined in the file.")
