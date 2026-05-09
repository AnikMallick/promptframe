# Exceptions

**Module:** `promptframe.exceptions`

---

## `PromptNotFoundError`

```python
class PromptNotFoundError(KeyError)
```

Raised when a prompt `pid` cannot be found in a loaded YAML file. Includes a helpful message listing all available pids.

**Constructor:**

```python
PromptNotFoundError(pid: str, available: List[str] | None = None)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `pid` | `str` | The pid that was not found |
| `available` | `List[str]` | All pids present in the file |

**Raised by:** `PromptYAML.__getattr__()`, `PromptDataModelYAML.__getattr__()`

```python
from promptframe.exceptions import PromptNotFoundError

try:
    prompt = prompts.nonexistent_prompt
except PromptNotFoundError as e:
    print(e.pid)        # "nonexistent_prompt"
    print(e.available)  # ["summarize_text", "classify_topic"]
```

---

## `OutputParsingError`

```python
class OutputParsingError(Exception)
```

Raised when an LLM output cannot be parsed into the expected format (e.g. malformed JSON).

**Constructor:**

```python
OutputParsingError(
    message: str = "Failed to parse the LLM response output.",
    response: str | None = None,
)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error description |
| `response` | `str \| None` | The raw LLM response string that failed to parse |

**Raised by:** `json_parser()`

```python
from promptframe.parsers import json_parser
from promptframe.exceptions import OutputParsingError

try:
    result = json_parser(llm_output)
except OutputParsingError as e:
    print(e.message)    # "Failed to parse the LLM response output."
    print(e.response)   # the raw string that couldn't be parsed
```

---

## `MissingContextKeyError`

```python
class MissingContextKeyError(ValueError)
```

Raised when a required `{placeholder}` key is absent from the render context passed to a component or builder.

**Constructor:**

```python
MissingContextKeyError(key: str)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `key` | `str` | The missing placeholder key name |

**Note:** Most `render()` methods use the `@catch_keyerror` decorator, which converts raw `KeyError` into a plain `ValueError` with a similar message. `MissingContextKeyError` is available for explicit use in custom components.

```python
from promptframe.exceptions import MissingContextKeyError

class MyComponent(BasePromptComponent):
    def render(self, context=None):
        ctx = context or {}
        if "required_key" not in ctx:
            raise MissingContextKeyError("required_key")
        return ctx["required_key"]
```
