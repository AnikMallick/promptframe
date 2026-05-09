from abc import ABC, abstractmethod
from typing import Dict, Optional

def catch_keyerror(func):
    """
    Decorator to catch KeyError exceptions and raise a ValueError
    with a helpful message indicating the missing key.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            missing_key = e.args[0]
            raise ValueError(f"Missing key in context for template: '{missing_key}'")
    return wrapper

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