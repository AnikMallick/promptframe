from __future__ import annotations

from functools import cached_property
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, model_validator

from .exceptions import PromptNotFoundError


class Metadata(BaseModel):
    type: Literal["prompt", "model_prompt"]
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None


class Prompt(BaseModel):
    pid: str
    description: Optional[str] = None
    input_variables: Optional[List[str]] = None
    prompt: str

    def format(self, **kwargs: object) -> str:
        """Return the prompt text with placeholders filled from *kwargs*."""
        return self.prompt.format(**kwargs)

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return f"Prompt(pid={self.pid!r}, prompt={self.prompt[:60]!r}...)"


class PromptDataModel(BaseModel):
    pid: str
    description: Optional[str] = None
    input_variables: Optional[List[str]] = None
    model_attribute_id: str
    input_instruction: Optional[str] = None
    output_instruction: Optional[str] = None

    @model_validator(mode="after")
    def check_instructions(self) -> PromptDataModel:
        if not self.input_instruction and not self.output_instruction:
            raise ValueError(
                "Either input_instruction or output_instruction must be provided."
            )
        return self


class PromptYAMLBase(BaseModel):
    version: float
    metadata: Metadata


class PromptYAML(PromptYAMLBase):
    prompts: List[Prompt]

    @cached_property
    def prompt_dict(self) -> Dict[str, Prompt]:
        return {p.pid: p for p in self.prompts}

    def get(self, pid: str) -> Optional[Prompt]:
        """Return a prompt by pid, or None if not found."""
        return self.prompt_dict.get(pid)

    def __getattr__(self, name: str) -> Prompt:
        # Only called when normal attribute lookup fails.
        # Allows p.my_prompt_id as sugar for p.prompt_dict["my_prompt_id"].
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.prompt_dict[name]
        except KeyError:
            raise PromptNotFoundError(name, list(self.prompt_dict)) from None

    def __repr__(self) -> str:
        pids = list(self.prompt_dict)
        return f"PromptYAML(name={self.metadata.name!r}, prompts={pids})"


class PromptDataModelYAML(PromptYAMLBase):
    prompts: List[PromptDataModel]

    @cached_property
    def prompt_dict(self) -> Dict[str, PromptDataModel]:
        return {p.pid: p for p in self.prompts}

    @cached_property
    def prompt_model_dict(self) -> Dict[str, PromptDataModel]:
        """Keyed by model_attribute_id — used to bind to LLMBaseModel fields."""
        return {p.model_attribute_id: p for p in self.prompts}

    def get(self, pid: str) -> Optional[PromptDataModel]:
        """Return a prompt by pid, or None if not found."""
        return self.prompt_dict.get(pid)

    def __getattr__(self, name: str) -> PromptDataModel:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.prompt_dict[name]
        except KeyError:
            raise PromptNotFoundError(name, list(self.prompt_dict)) from None

    def __repr__(self) -> str:
        pids = list(self.prompt_dict)
        return f"PromptDataModelYAML(name={self.metadata.name!r}, prompts={pids})"
