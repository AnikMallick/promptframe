# StructuredPromptBuilder

**Module:** `promptframe.builder`

Fluent builder for assembling multi-part prompts from [`BasePromptComponent`](./components.md) instances. Components are joined with blank lines (`\n\n`) — the standard LLM prompt separator.

---

## `StructuredPromptBuilder`

```python
class StructuredPromptBuilder()
```

### Operators

| Operator | Description |
|---|---|
| `builder >> component` | Append a component (right-shift) |
| `builder \| component` | Append a component (pipe) |

Both operators return `self`, enabling fluent chaining.

---

## Methods

### `add(component: BasePromptComponent) -> StructuredPromptBuilder`

Append a component and return `self` for chaining.

```python
builder = StructuredPromptBuilder()
builder.add(SimplePromptComponent("You are helpful."))
builder.add(SimplePromptComponent("Answer: {question}"))
```

**Raises:** `TypeError` if `component` is not a `BasePromptComponent`.

---

### `build(context: Dict | None = None) -> str`

Render all components and join them with `\n\n`. Empty component outputs are automatically excluded.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `context` | `Dict \| None` | `None` | Variables for `{placeholder}` interpolation passed to every component |

**Returns:** Complete prompt as a single string.

```python
prompt = builder.build({"question": "What is 2+2?", "json_mode": True})
```

---

### `preview(context: Dict | None = None, *, show_index: bool = True) -> None`

Print a labelled preview of each component to stdout. Useful during development to inspect how a prompt will render.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `context` | `Dict \| None` | `None` | Render variables |
| `show_index` | `bool` | `True` | Prefix each component with its position index |

```python
builder.preview({"question": "What is 2+2?"})
# 🔍 Prompt Preview
# ========================================
# [0] SimplePromptComponent
# ------------------------------
# You are a helpful assistant.
#
# [1] SimplePromptComponent
# ------------------------------
# Answer: What is 2+2?
```

---

### `__len__() -> int`

Return the number of components currently in the builder.

```python
len(builder)  # 3
```

---

## Full Example

```python
from promptframe import StructuredPromptBuilder, PromptRegistry, SkillRegistry
from promptframe.components import (
    SimplePromptComponent,
    PromptSectionComponent,
    InputComponent,
    ConditionalPromptComponent,
    SkillComponent,
)

reg = PromptRegistry(base="prompts/", environment="prod")
prompts = reg.load_prompt("system_prompts")

skill_reg = SkillRegistry("skills/")
skill = skill_reg.get("code-review")

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent(prompts.system)
    >> SkillComponent(skill, sections=["Guidelines"])
    >> PromptSectionComponent(
            ["Be concise", "Use markdown for code"],
            header="Response rules:",
       )
    >> ConditionalPromptComponent(
            SimplePromptComponent("Return output as JSON."),
            condition_key="json_mode",
       )
    >> InputComponent()
).build({
    "json_mode": True,
    "input": "Review this function: def add(a, b): return a+b",
})

print(prompt)
```

---

## Notes

- Components that render to an empty string (e.g. a `ConditionalPromptComponent` whose condition is `False`) are silently dropped by `build()`.
- `>>` and `|` both call `add()` and are interchangeable — choose whichever reads better in your codebase.
- The builder holds no state beyond the ordered component list; the same builder can be `.build()`-ed multiple times with different contexts.
