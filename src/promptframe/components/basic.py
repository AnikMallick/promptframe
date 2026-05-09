"""
Built-in prompt components.

All components are LLM-agnostic — they produce plain strings and have zero
dependency on any inference library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from ..skill import Skill

from ..models import Prompt
from .base import BasePromptComponent, catch_keyerror


class SimplePromptComponent(BasePromptComponent):
    """Wrap a plain string or a :class:`~promptkit.models.Prompt` object.

    If the wrapped value contains ``{placeholder}`` slots they are filled
    from *context* when :meth:`render` is called.

    Example::

        c = SimplePromptComponent("Hello, {name}!")
        c.render({"name": "Alice"})  # "Hello, Alice!"
    """

    def __init__(self, prompt: Union[str, Prompt]) -> None:
        if not isinstance(prompt, (str, Prompt)):
            raise TypeError(
                f"SimplePromptComponent expects str or Prompt, got {type(prompt)}"
            )
        self.prompt = prompt

    @catch_keyerror
    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        if isinstance(self.prompt, Prompt):
            return self.prompt.prompt.format(**ctx) if ctx else self.prompt.prompt
        return self.prompt.format(**ctx) if ctx else self.prompt

    def __repr__(self) -> str:
        text = self.prompt.prompt if isinstance(self.prompt, Prompt) else self.prompt
        return f"SimplePromptComponent({text[:50]!r})"


class PromptSectionComponent(BasePromptComponent):
    """Render a section heading followed by one or more prompt lines.

    Args:
        requirement: The body of the section.  May be a single string / Prompt
            **or** a list of strings / Prompts (rendered as a bullet list).
        header: Optional heading text prepended before the body.

    Example::

        s = PromptSectionComponent(
            ["Be concise", "Avoid jargon"],
            header="Rules:",
        )
        # Renders as:
        # Rules:
        # - Be concise
        # - Avoid jargon
    """

    def __init__(
        self,
        requirement: Union[str, Prompt, List[str], List[Prompt]],
        header: Optional[str] = None,
    ) -> None:
        self.requirement = requirement
        self.header = header

    def _prepend_header(self, text: str) -> str:
        return f"{self.header}\n{text}" if self.header else text

    @staticmethod
    def _bullet_join(items: List[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    @catch_keyerror
    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        req = self.requirement

        if isinstance(req, Prompt):
            body = req.prompt.format(**ctx) if ctx else req.prompt
        elif isinstance(req, str):
            body = req.format(**ctx) if ctx else req
        elif isinstance(req, list):
            if all(isinstance(i, str) for i in req):
                raw = self._bullet_join(req)  # type: ignore[arg-type]
                body = raw.format(**ctx) if ctx else raw
            elif all(isinstance(i, Prompt) for i in req):
                raw = self._bullet_join([p.prompt for p in req])  # type: ignore[union-attr]
                body = raw.format(**ctx) if ctx else raw
            else:
                raise TypeError("List must contain either all str or all Prompt objects.")
        else:
            raise TypeError(f"Unsupported type for requirement: {type(req)}")

        return self._prepend_header(body)

    def __repr__(self) -> str:
        return f"PromptSectionComponent(header={self.header!r})"


class InputComponent(BasePromptComponent):
    """Emit a labelled input block (e.g. ``<input>{input}</input>``).

    This is a lightweight structural component that signals to the LLM where
    user input lives in the prompt.

    Args:
        header: Introductory line above the input block.
        template: The input wrapper template.  Must contain an ``{input}``
            placeholder if you want the value injected at render time, or can
            be a literal string.
    """

    def __init__(
        self,
        header: Optional[str] = "Input for processing is given below.",
        template: str = "<input>{input}</input>",
    ) -> None:
        self.header = header
        self.template = template

    @catch_keyerror
    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        body = self.template.format(**ctx) if ctx else self.template
        return f"{self.header}\n{body}" if self.header else body

    def __repr__(self) -> str:
        return f"InputComponent(template={self.template!r})"


class TemplatePromptComponent(BasePromptComponent):
    """Compose multiple components into a single string via a format template.

    Args:
        template: A Python format string whose placeholders are keys of
            *components*.
        components: Dict mapping placeholder names to :class:`BasePromptComponent`
            instances.

    Example::

        t = TemplatePromptComponent(
            "System: {system}\\n\\nTask: {task}",
            components={
                "system": SimplePromptComponent("You are a helpful assistant."),
                "task": SimplePromptComponent("Summarise the following: {text}"),
            },
        )
        t.render({"text": "..."})
    """

    def __init__(
        self,
        template: str,
        components: Dict[str, BasePromptComponent],
    ) -> None:
        self.template = template
        self.components = components

    @catch_keyerror
    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        filled = {key: comp.render(ctx) for key, comp in self.components.items()}
        return self.template.format(**filled)

    def __repr__(self) -> str:
        keys = list(self.components)
        return f"TemplatePromptComponent(slots={keys})"


class SequentialPromptComponent(BasePromptComponent):
    """Render a list of components in order, joined by blank lines.

    You normally create these implicitly via the ``|`` operator::

        result = SimplePromptComponent("Part A") | SimplePromptComponent("Part B")
    """

    def __init__(self, components: List[BasePromptComponent]) -> None:
        self.components = list(components)

    @catch_keyerror
    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        return "\n\n".join(c.render(ctx) for c in self.components)

    def __or__(self, other: BasePromptComponent) -> "SequentialPromptComponent":  # type: ignore[override]
        if isinstance(other, BasePromptComponent):
            return SequentialPromptComponent([*self.components, other])
        return NotImplemented

    def __repr__(self) -> str:
        return f"SequentialPromptComponent(n={len(self.components)})"


class ConditionalPromptComponent(BasePromptComponent):
    """Render *component* only when *condition_key* is truthy in *context*.

    Returns an empty string otherwise — useful for optional prompt sections.

    Example::

        c = ConditionalPromptComponent(
            component=SimplePromptComponent("Use JSON output."),
            condition_key="json_mode",
        )
        c.render({"json_mode": True})   # "Use JSON output."
        c.render({"json_mode": False})  # ""
    """

    def __init__(
        self,
        component: BasePromptComponent,
        condition_key: str,
    ) -> None:
        self.component = component
        self.condition_key = condition_key

    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        if ctx.get(self.condition_key):
            return self.component.render(ctx)
        return ""

    def __repr__(self) -> str:
        return (
            f"ConditionalPromptComponent("
            f"condition_key={self.condition_key!r}, "
            f"component={self.component!r})"
        )

class SkillComponent(BasePromptComponent):
    """Inject a :class:`~promptkit.Skill` (markdown skill file) into a prompt.

    Args:
        skill: A loaded :class:`~promptkit.Skill` instance.
        sections: If provided, only render these section headings from the skill.
        include_name: Prepend the skill name as a heading (default: True).
        wrapper: Optional format string wrapping the rendered skill.
            Must contain ``{skill}`` placeholder. Useful for XML-style tagging::

                wrapper="<skill>{skill}</skill>"

    Example::

        registry = SkillRegistry("skills/")
        skill    = registry.get("frontend-design")

        prompt = (
            StructuredPromptBuilder()
            >> SimplePromptComponent("You are a frontend expert.")
            >> SkillComponent(skill, sections=["Design Thinking"])
            >> SimplePromptComponent("Build: {task}")
        ).build({"task": "a login page"})
    """

    def __init__(
        self,
        skill: "Skill",  # type: ignore[name-defined]  # noqa: F821
        sections: Optional[List[str]] = None,
        *,
        include_name: bool = True,
        wrapper: Optional[str] = None,
    ) -> None:
        self.skill = skill
        self.sections = sections
        self.include_name = include_name
        self.wrapper = wrapper

    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        rendered = self.skill.render(
            sections=self.sections,
            include_name=self.include_name,
        )
        if self.wrapper:
            rendered = self.wrapper.format(skill=rendered)
        return rendered

    def __repr__(self) -> str:
        return (
            f"SkillComponent(skill={self.skill.name!r}, "
            f"sections={self.sections})"
        )
