"""
StructuredPromptBuilder — fluent, operator-friendly prompt assembly.

Usage::

    from promptframe import StructuredPromptBuilder, SimplePromptComponent

    prompt = (
        StructuredPromptBuilder()
        >> SimplePromptComponent("You are a helpful assistant.")
        >> SimplePromptComponent("Answer the question: {question}")
    ).build({"question": "What is 2+2?"})
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .components.base import BasePromptComponent


class StructuredPromptBuilder:
    """Assemble a list of :class:`BasePromptComponent` instances into a prompt.

    Components are joined with blank lines (``\\n\\n``) when :meth:`build` is
    called — the same separator used by most LLM prompt conventions. Unless some separator
    is specifically mentioned.

    Operators::

        builder >> component   # append a component
        builder | component    # same (pipe style)
        component | component  # returns a SequentialPromptComponent
    """

    def __init__(self, separator: str = "\n\n") -> None:
        """Initialize a StructuredPromptBuilder

        Args:
            separator (str, optional): Components are joined with with string. Defaults to ``\\n\\n``.
        """
        self.components: List[BasePromptComponent] = []
        self.separator = separator

    def add(self, component: BasePromptComponent) -> "StructuredPromptBuilder":
        """Append a component and return *self* for chaining."""
        if not isinstance(component, BasePromptComponent):
            raise TypeError(
                f"Expected a BasePromptComponent, got {type(component).__name__}"
            )
        self.components.append(component)
        return self

    def __rshift__(self, other: object) -> "StructuredPromptBuilder":
        if isinstance(other, BasePromptComponent):
            return self.add(other)
        raise TypeError(
            f"Cannot '>>' {type(other).__name__} into StructuredPromptBuilder"
        )

    def __or__(self, other: object) -> "StructuredPromptBuilder":
        if isinstance(other, BasePromptComponent):
            return self.add(other)
        raise TypeError(
            f"Cannot pipe {type(other).__name__} into StructuredPromptBuilder"
        )

    def build(self, context: Optional[Dict[str, object]] = None) -> str:
        """Render all components and join them with ``\\n\\n``.

        Args:
            context: Variables for ``{placeholder}`` interpolation.

        Returns:
            The complete prompt as a single string.
        """
        ctx = context or {}
        parts = [c.render(ctx) for c in self.components]
        # Drop empty strings (e.g. ConditionalPromptComponent that didn't fire)
        return self.separator.join(p for p in parts if p)

    def preview(
        self,
        context: Optional[Dict[str, object]] = None,
        *,
        show_index: bool = True,
    ) -> None:
        """Print a labelled preview of each component to stdout.

        Args:
            context: Variables used for rendering.
            show_index: Prefix each component with its position number.
        """
        ctx = context or {}
        print("🔍 Prompt Preview\n" + "=" * 40)
        for i, component in enumerate(self.components):
            rendered = component.render(ctx)
            label = f"[{i}] " if show_index else ""
            print(f"{label}{component.__class__.__name__}\n{'-' * 30}")
            print(rendered or "<empty>")
            print()

    def __len__(self) -> int:
        return len(self.components)

    def __repr__(self) -> str:
        return f"StructuredPromptBuilder(n_components={len(self.components)})"
