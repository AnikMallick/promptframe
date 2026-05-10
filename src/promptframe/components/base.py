from abc import ABC, abstractmethod
import re
from typing import Dict, List, Optional, Self

def safe_format(template: str, **kwargs) -> str:
    """Format *template* with *kwargs*, leaving unresolved placeholders intact.

    Unlike ``str.format(**kwargs)``, this never raises ``KeyError`` and never
    misinterprets JSON-style braces (e.g. ``{"field": "value"}``) as template
    slots. Only ``{keys}`` that exist in *kwargs* are substituted; everything
    else is left exactly as written.

    Example::

        safe_format('Hello {name}! Schema: {"field": 1}', name="Alice")
        # 'Hello Alice! Schema: {"field": 1}'
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1).strip()
        return str(kwargs[key]) if key in kwargs else match.group(0)

    return re.sub(r'\{([^{}]*)\}', _replace, template)

class BasePromptComponent(ABC):
    """
    Abstract base class for all prompt components.
    """

    @abstractmethod
    def render(self, context: Optional[Dict] = None) -> str:
        """
        Renders the prompt using the provided context.
        Args:
            context (Optional[Dict]): A dictionary containing the context variables 
                to be used for rendering the prompt. Defaults to None.
        Returns:
            str: The rendered prompt as a string.
        """

        pass
    
    def __or__(self, other: Self) -> "SequentialPromptComponent":  # type: ignore[override]
        if isinstance(Self, SequentialPromptComponent):
            if isinstance(other, SequentialPromptComponent):
                return SequentialPromptComponent([*self.components, *other.components])
            else:
                return SequentialPromptComponent([*self.components, other])
        elif isinstance(other, SequentialPromptComponent):
            return SequentialPromptComponent([self, *other.components])
        elif not isinstance(other, SequentialPromptComponent):
            return SequentialPromptComponent([self, other])
        return NotImplemented



class SequentialPromptComponent(BasePromptComponent):
    """Render a list of components in order, joined by blank lines: ``\\n\\n``.
    """

    def __init__(self, components: List[BasePromptComponent]) -> None:
        self.components = list(components)

    def render(self, context: Optional[Dict[str, object]] = None) -> str:
        ctx = context or {}
        return "\n\n".join(c.render(ctx) for c in self.components)
    
    def __repr__(self) -> str:
        return f"SequentialPromptComponent(n={len(self.components)})"
    