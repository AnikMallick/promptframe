"""
PromptFrame — LLM-agnostic prompt management with structured output support.

Two usage paths:

**Plain prompt management** (no structured output)::

    from promptframe import PromptRegistry, StructuredPromptBuilder, SimplePromptComponent

    reg = PromptRegistry("prompts/")
    p   = reg.load_prompt("my_prompts")

    result = (
        StructuredPromptBuilder()
        >> SimplePromptComponent(p.system)
        >> SimplePromptComponent("Answer: {question}")
    ).build({"question": "What is 2+2?"})

**Structured output** (LLM-agnostic, decoupled prompts)::

    from promptframe import PromptRegistry, LLMBaseModel, LLMField

    class Invoice(LLMBaseModel):
        total:      float      = LLMField(..., model_attribute_id="invoice_total")
        line_items: list[str]  = LLMField(..., model_attribute_id="invoice_lines")

    reg = PromptRegistry("prompts/")
    mp  = reg.load_model_prompt("invoice_prompts")

    input_schema  = Invoice.get_input_instructions_with_prompt(mp.prompt_model_dict)
    output_schema = Invoice.get_format_instructions_with_prompt(mp.prompt_model_dict)

    # After calling your LLM:
    invoice = Invoice(**json_parser(llm_response))
"""

from .builder import StructuredPromptBuilder
from .components import (
    BasePromptComponent,
    ConditionalPromptComponent,
    InputComponent,
    PromptSectionComponent,
    SequentialPromptComponent,
    SimplePromptComponent,
    SkillComponent,
    TemplatePromptComponent,
)
from .exceptions import MissingContextKeyError, OutputParsingError, PromptNotFoundError
from .fields import LLMField
from .registry import PromptRegistry
from .llm_base_model import LLMBaseModel
from .models import (
    Metadata,
    Prompt,
    PromptDataModel,
    PromptDataModelYAML,
    PromptYAML,
    PromptYAMLBase,
)
from .parsers import json_parser, parse_json_markdown, parse_partial_json
from .skill import Skill, load_skill_from_path
from .skill_registry import SkillRegistry

__version__ = "0.1.0"

__all__ = [
    # Structured output — core value prop
    "LLMBaseModel",
    "LLMField",
    # Prompt hub
    "PromptRegistry",
    # Builder
    "StructuredPromptBuilder",
    # Components
    "BasePromptComponent",
    "SimplePromptComponent",
    "PromptSectionComponent",
    "InputComponent",
    "TemplatePromptComponent",
    "SequentialPromptComponent",
    "ConditionalPromptComponent",
    "SkillComponent",
    # Skills
    "Skill",
    "SkillRegistry",
    "load_skill_from_path",
    # Models
    "Prompt",
    "PromptDataModel",
    "PromptYAML",
    "PromptDataModelYAML",
    "PromptYAMLBase",
    "Metadata",
    # Parsers
    "json_parser",
    "parse_json_markdown",
    "parse_partial_json",
    # Exceptions
    "PromptNotFoundError",
    "OutputParsingError",
    "MissingContextKeyError",
]
