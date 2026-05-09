from typing import Optional


class PromptNotFoundError(KeyError):
    """Raised when a prompt ID cannot be found in a loaded YAML file."""

    def __init__(self, pid: str, available: Optional[list[str]] = None) -> None:
        self.pid = pid
        self.available = available or []
        hint = f" Available: {self.available}" if self.available else ""
        super().__init__(f"Prompt '{pid}' not found.{hint}")


class OutputParsingError(Exception):
    """Raised when an LLM output cannot be parsed into the expected format."""

    def __init__(
        self,
        message: str = "Failed to parse the LLM response output.",
        response: Optional[str] = None,
    ) -> None:
        self.message = message
        self.response = response
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        if self.response:
            return f"{self.message}\nResponse:\n{self.response}"
        return self.message


class MissingContextKeyError(ValueError):
    """Raised when a required template key is absent from the render context."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            f"Missing key in context for template: '{key}'. "
            "Pass it via the context dict when calling .render() or .build()."
        )
