# Prompt Components

**Module:** `promptframe.components`

Composable building blocks for assembling LLM prompts. All components extend `BasePromptComponent` and produce plain strings — no inference library dependency.

Use components with [`StructuredPromptBuilder`](./builder.md) or call `.render()` directly.

---

## `BasePromptComponent`

```python
class BasePromptComponent(ABC)
```

Abstract base class for all components. Subclasses must implement:

### `render(context: Dict | None = None) -> str`

Render the component to a string. `context` is a dict of `{placeholder: value}` pairs used to fill `{placeholder}` slots in templates.

---

## `SimplePromptComponent`

```python
class SimplePromptComponent(prompt: str | Prompt)
```

Wraps a plain string or a [`Prompt`](./models.md#prompt) object. Placeholders in the text are filled from `context` at render time.

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `prompt` | `str \| Prompt` | The prompt text or `Prompt` object |

**Example:**

```python
from promptframe.components import SimplePromptComponent

c = SimplePromptComponent("Hello, {name}! Today is {day}.")
c.render({"name": "Alice", "day": "Monday"})
# "Hello, Alice! Today is Monday."

# Also accepts a Prompt object
c = SimplePromptComponent(prompts.greet)
c.render({"name": "Alice"})
```

---

## `PromptSectionComponent`

```python
class PromptSectionComponent(requirement, header=None)
```

Renders a section heading followed by a body. The body can be a single string/`Prompt` or a list (rendered as a bullet list).

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `requirement` | `str \| Prompt \| List[str] \| List[Prompt]` | Section body content |
| `header` | `str \| None` | Optional heading prepended before the body |

**Example:**

```python
from promptframe.components import PromptSectionComponent

s = PromptSectionComponent(
    ["Be concise", "Avoid jargon", "Use simple language"],
    header="Rules:",
)
print(s.render())
# Rules:
# - Be concise
# - Avoid jargon
# - Use simple language

# Single string body
s = PromptSectionComponent("Always respond in English.", header="Language:")
```

> **Note:** Lists must be homogeneous — either all `str` or all `Prompt` objects.

---

## `InputComponent`

```python
class InputComponent(header=None, template="<input>{input}</input>")
```

Renders a labelled input block signalling to the LLM where user input is located.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `header` | `str \| None` | `"Input for processing is given below."` | Intro line above the input block |
| `template` | `str` | `"<input>{input}</input>"` | Wrapper template; must contain `{input}` if you want the value injected |

**Example:**

```python
from promptframe.components import InputComponent

c = InputComponent()
c.render({"input": "What is the capital of France?"})
# Input for processing is given below.
# <input>What is the capital of France?</input>

# Custom template
c = InputComponent(
    header="User query:",
    template="<query>{input}</query>",
)
```

---

## `TemplatePromptComponent`

```python
class TemplatePromptComponent(template: str, components: Dict[str, BasePromptComponent])
```

Composes multiple components into a single string via a Python format template. Each placeholder in the template maps to a named component that is rendered and substituted.

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `template` | `str` | Format string whose placeholders are keys of `components` |
| `components` | `Dict[str, BasePromptComponent]` | Mapping from placeholder name to component |

**Example:**

```python
from promptframe.components import TemplatePromptComponent, SimplePromptComponent

t = TemplatePromptComponent(
    template="System: {system}\n\nTask: {task}",
    components={
        "system": SimplePromptComponent("You are a helpful assistant."),
        "task":   SimplePromptComponent("Summarise the following: {text}"),
    },
)
print(t.render({"text": "The quick brown fox..."}))
# System: You are a helpful assistant.
#
# Task: Summarise the following: The quick brown fox...
```

---

## `SequentialPromptComponent`

```python
class SequentialPromptComponent(components: List[BasePromptComponent])
```

Renders a list of components in order, joined by blank lines (`\n\n`). Typically created implicitly via the `|` operator between components.

**Example:**

```python
from promptframe.components import SimplePromptComponent

combined = (
    SimplePromptComponent("Part A")
    | SimplePromptComponent("Part B")
    | SimplePromptComponent("Part C")
)
print(combined.render())
# Part A
#
# Part B
#
# Part C
```

### Operators

| Operator | Description |
|---|---|
| `component \| component` | Returns a `SequentialPromptComponent` joining both |
| `SequentialPromptComponent \| component` | Appends to the existing sequence |

---

## `ConditionalPromptComponent`

```python
class ConditionalPromptComponent(component: BasePromptComponent, condition_key: str)
```

Renders `component` only when `condition_key` is truthy in the context. Returns an empty string otherwise. Useful for optional prompt sections.

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `component` | `BasePromptComponent` | The component to render conditionally |
| `condition_key` | `str` | Key looked up in the render context |

**Example:**

```python
from promptframe.components import ConditionalPromptComponent, SimplePromptComponent

c = ConditionalPromptComponent(
    component=SimplePromptComponent("Respond in JSON format only."),
    condition_key="json_mode",
)

c.render({"json_mode": True})   # "Respond in JSON format only."
c.render({"json_mode": False})  # ""
c.render({})                    # ""
```

---

## `SkillComponent`

```python
class SkillComponent(skill, sections=None, *, include_name=True, wrapper=None)
```

Injects a [`Skill`](./skills.md#skill) (markdown instruction document) into a prompt.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `skill` | `Skill` | — | A loaded `Skill` instance |
| `sections` | `List[str] \| None` | `None` | If provided, only render these section headings |
| `include_name` | `bool` | `True` | Prepend the skill name as a `##` heading |
| `wrapper` | `str \| None` | `None` | Optional format string wrapping the output; must contain `{skill}` |

**Example:**

```python
from promptframe import SkillRegistry
from promptframe.components import SkillComponent, SimplePromptComponent
from promptframe import StructuredPromptBuilder

registry = SkillRegistry("skills/")
skill = registry.get("frontend-design")

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a frontend expert.")
    >> SkillComponent(skill, sections=["Guidelines"])
    >> SimplePromptComponent("Build: {task}")
).build({"task": "a login page"})

# With XML wrapper
SkillComponent(skill, wrapper="<skill>\n{skill}\n</skill>")
```

---

## Error Handling

All `render()` methods decorated with `@catch_keyerror` will raise `ValueError` (with a helpful message) if a required placeholder key is missing from the context, instead of the raw `KeyError`.

```python
c = SimplePromptComponent("Hello, {name}!")
c.render({})  # ValueError: Missing key in context for template: 'name'
```
