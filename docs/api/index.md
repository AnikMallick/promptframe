# promptframe — API Reference

**promptframe** is an LLM-agnostic prompt management toolkit. It provides typed YAML prompt loading, composable prompt components, structured output schema generation, skill (markdown instruction) injection, and a CLI for day-to-day prompt operations.

---

## Modules

| Module | Description |
|---|---|
| [Models](./models.md) | Pydantic data models for prompts and YAML files |
| [PromptRegistry](./registry.md) | Load and resolve YAML prompt files |
| [LLMBaseModel](./llm_base_model.md) | Structured input/output schema generation for LLMs |
| [Prompt Components](./components.md) | Composable building blocks for prompt assembly |
| [StructuredPromptBuilder](./builder.md) | Fluent builder for assembling multi-part prompts |
| [Skills](./skills.md) | Markdown skill files — loading, rendering, and registry |
| [Fields](./fields.md) | `LLMField` — custom Pydantic field with LLM metadata |
| [Parsers](./parsers.md) | JSON parsing utilities for LLM responses |
| [Exceptions](./exceptions.md) | Library-specific exception classes |
| [CLI](./cli.md) | `promptframe` command-line interface |

---

## Quick Start

### 1. Loading and using prompts

```python
from promptframe import PromptRegistry

reg = PromptRegistry(base="prompts/", environment="prod", common="shared")

# Load a prompt YAML file
prompts = reg.load_prompt("my_prompts")

# Access by attribute or dict
system_prompt = prompts.system_prompt          # attribute access
system_prompt = prompts.prompt_dict["system_prompt"]  # dict access

# Render with variables
text = system_prompt.format(name="Alice", topic="Python")
```

### 2. Assembling prompts with the builder

```python
from promptframe import StructuredPromptBuilder
from promptframe.components import SimplePromptComponent, PromptSectionComponent

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a helpful assistant.")
    >> PromptSectionComponent(["Be concise", "Avoid jargon"], header="Rules:")
    >> SimplePromptComponent("Answer: {question}")
).build({"question": "What is 2+2?"})
```

### 3. Structured output with LLMBaseModel

```python
from pydantic import Field
from promptframe import LLMBaseModel
from promptframe.fields import LLMField

class MyOutput(LLMBaseModel):
    name: str = LLMField(..., description="Customer full name", model_attribute_id="customer_name")
    score: int = Field(..., description="Risk score 0-100")

# Get JSON schema instructions for the LLM
instructions = MyOutput.get_format_instructions()
```

### 4. Using skills

```python
from promptframe import SkillRegistry, StructuredPromptBuilder
from promptframe.components import SimplePromptComponent, SkillComponent

registry = SkillRegistry("skills/")
skill = registry.get("frontend-design")

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a frontend expert.")
    >> SkillComponent(skill)
    >> SimplePromptComponent("Task: {task}")
).build({"task": "Build a login page"})
```

---

## YAML File Formats

### `type: prompt`

```yaml
version: 1.0

metadata:
  type: prompt
  name: my_prompts
  description: General prompt collection
  tags: [nlp, summarization]
  project: my_project

prompts:
  - pid: summarize_text
    description: Summarize a block of text.
    input_variables:
      - text
    prompt: |
      Summarize the following text:
      {text}
```

### `type: model_prompt`

```yaml
version: 1.0

metadata:
  type: model_prompt
  name: field_prompts
  description: Per-field LLM instructions

prompts:
  - pid: clean_name
    description: Clean and normalize a name field.
    model_attribute_id: customer_name
    input_instruction: |
      The input contains {raw_name}.
    output_instruction: |
      Return a cleaned human-readable name.
```

### Skill file (`.md` with YAML frontmatter)

```markdown
---
name: frontend-design
description: When to use this skill.
tags: [frontend, react, css]
version: "1.0"
---

## Guidelines

- Use semantic HTML
- Prefer CSS variables for theming
```
