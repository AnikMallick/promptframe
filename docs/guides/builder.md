# Prompt Builder

`StructuredPromptBuilder` composes multiple prompt components into a single string, joining them with blank lines (`\n\n`).

---

## Basic usage

```python
from promptframe import (
    StructuredPromptBuilder,
    SimplePromptComponent,
)

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a helpful assistant.")
    >> SimplePromptComponent("Answer this question: {question}")
).build({"question": "What is 2+2?"})
```

### Operators

Both `>>` and `|` append a component. Use whichever feels right for your style:

```python
# >> style
builder = StructuredPromptBuilder()
builder >> SimplePromptComponent("Part A")
builder >> SimplePromptComponent("Part B")

# | style (same result)
builder = StructuredPromptBuilder()
builder | SimplePromptComponent("Part A")
builder | SimplePromptComponent("Part B")

# Chained
prompt = (
    StructuredPromptBuilder()
    >> comp_a
    >> comp_b
    >> comp_c
).build()
```

### Component pipe shorthand

Two components can be combined directly without a builder:

```python
combined = SimplePromptComponent("Part A") | SimplePromptComponent("Part B")
# → SequentialPromptComponent(["Part A", "Part B"])
combined.render()
# → "Part A\n\nPart B"
```

---

## Components

### `SimplePromptComponent`

Wraps a plain string or a `Prompt` object:

```python
SimplePromptComponent("You are a helpful assistant.")
SimplePromptComponent(p.system)   # Prompt object from PromptRegistry
SimplePromptComponent("Hello, {name}!").render({"name": "Alice"})
```

### `PromptSectionComponent`

A heading followed by a body or bullet list:

```python
# Single body
PromptSectionComponent("Be concise.", header="Rule:")

# Bullet list
PromptSectionComponent(
    ["Be concise", "Avoid jargon", "Use plain language"],
    header="Rules:",
)
# Renders as:
# Rules:
# - Be concise
# - Avoid jargon
# - Use plain language
```

### `InputComponent`

A labelled input block for telling the LLM where user input lives:

```python
InputComponent()
# Renders as:
# Input for processing is given below.
# <input>{input}</input>

# Custom template
InputComponent(
    header="The document to analyse:",
    template="<document>{input}</document>",
)
```

### `ConditionalPromptComponent`

Renders only when a context key is truthy:

```python
ConditionalPromptComponent(
    component=SimplePromptComponent("Return your answer as JSON."),
    condition_key="json_mode",
)

builder.build({"json_mode": True})   # included
builder.build({"json_mode": False})  # empty string, dropped from output
```

### `SkillComponent`

Injects a skill document. See the [Skills guide](skills.md) for full details.

```python
SkillComponent(skill)
SkillComponent(skill, sections=["Security"])
SkillComponent(skill, wrapper="<context>{skill}</context>")
```

### `TemplatePromptComponent`

Compose multiple components via a format string:

```python
TemplatePromptComponent(
    "System: {system}\n\nTask: {task}",
    components={
        "system": SimplePromptComponent("You are a helpful assistant."),
        "task":   SimplePromptComponent("Summarise: {text}"),
    },
)
```

### `SequentialPromptComponent`

Joins a list of components with blank lines. Usually created by the `|` operator:

```python
seq = SimplePromptComponent("A") | SimplePromptComponent("B")
# equivalent to:
SequentialPromptComponent([SimplePromptComponent("A"), SimplePromptComponent("B")])
```

---

## Building

```python
# No context (no placeholders)
result = builder.build()

# With context
result = builder.build({"question": "What is 2+2?", "json_mode": True})
```

Empty components (`ConditionalPromptComponent` that didn't fire) are automatically dropped — no extra blank lines.

---

## Preview

Print a labelled breakdown to stdout during development:

```python
builder.preview({"question": "test"})

# Output:
# 🔍 Prompt Preview
# ════════════════════════════════════════
# [0] SimplePromptComponent
# ──────────────────────────────────────
# You are a helpful assistant.
#
# [1] SimplePromptComponent
# ──────────────────────────────────────
# Answer this question: test
```

---

## Custom components

Subclass `BasePromptComponent` to build your own:

```python
from promptframe import BasePromptComponent
from typing import Dict, Optional

class DateStampComponent(BasePromptComponent):
    def render(self, context: Optional[Dict] = None) -> str:
        from datetime import date
        return f"Today's date: {date.today().isoformat()}"

builder >> DateStampComponent()
```
