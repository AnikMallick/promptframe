# Fields

**Module:** `promptframe.fields`

Custom Pydantic field factory that attaches LLM-specific metadata to model fields. Use `LLMField` instead of Pydantic's `Field` on any `LLMBaseModel` subclass where you want per-field LLM instructions.

---

## `LLMField`

```python
def LLMField(
    default: Any = ...,
    *,
    description: str | None = None,
    input_instruction: str | None = None,
    output_instruction: str | None = None,
    model_attribute_id: str | None = None,
    **kwargs,
) -> Any
```

Returns a Pydantic `FieldInfo` object with extra LLM metadata stored in `json_schema_extra`.

### Arguments

| Argument | Type | Description |
|---|---|---|
| `default` | `Any` | Default value. Use `...` (Ellipsis) for required fields |
| `description` | `str \| None` | Human-readable field description (standard Pydantic) |
| `input_instruction` | `str \| None` | Instruction for the input schema; used by `get_input_instructions()` |
| `output_instruction` | `str \| None` | Instruction for the output schema; used by `get_format_instructions()` |
| `model_attribute_id` | `str \| None` | Key used to match this field with a `PromptDataModel` from a YAML model prompt file |
| `**kwargs` | | Any additional Pydantic `Field` keyword arguments |

### Instruction priority

`LLMField` metadata is overridden by YAML prompt data when both are present (see [LLMBaseModel](./llm_base_model.md#instruction-priority-summary)).

### Example

```python
from pydantic import Field
from promptframe import LLMBaseModel
from promptframe.fields import LLMField

class CustomerOutput(LLMBaseModel):
    # Fully specified with YAML binding
    name: str = LLMField(
        ...,
        description="Customer full name",
        model_attribute_id="customer_name",
        input_instruction="The raw name as it appears in the source data.",
        output_instruction="Return a cleaned, title-cased full name.",
    )

    # Standard Pydantic field — description used as fallback instruction
    score: int = Field(..., description="Risk score between 0 and 100")

    # Optional field
    notes: str | None = LLMField(None, description="Optional free-text notes")
```

---
---

# Parsers

**Module:** `promptframe.parsers`

JSON parsing utilities for LLM responses. Standalone — no inference library dependency.

---

## `json_parser(llm_response_content: str) -> Dict[str, Any]`

Parse a raw LLM string response as JSON. Handles:

- Plain JSON strings
- JSON wrapped in markdown triple-backtick fences (` ```json ... ``` `)
- Partial/incomplete JSON (missing closing braces or brackets)

```python
from promptframe.parsers import json_parser

# Plain JSON
result = json_parser('{"name": "Alice", "score": 95}')

# Markdown-fenced
result = json_parser('```json\n{"name": "Alice"}\n```')
```

**Raises:** [`OutputParsingError`](./exceptions.md#outputparsingerror) if the string cannot be parsed as JSON after all recovery attempts.

---

## `parse_json_markdown(json_string: str, *, parser=...) -> dict`

Lower-level function. Attempts a direct parse first; if that fails, searches for a ` ```json ` fence and re-attempts. Accepts a custom `parser` callable.

---

## `parse_partial_json(s: str, *, strict: bool = False) -> Any`

Parse a JSON string that may be missing closing braces or brackets. Progressively closes open structures until a valid parse is achieved. Useful for streaming LLM responses.

```python
from promptframe.parsers import parse_partial_json

parse_partial_json('{"name": "Alice", "items": [1, 2')
# {"name": "Alice", "items": [1, 2]}
```

---
---

# Exceptions

**Module:** `promptframe.exceptions`

---

## `PromptNotFoundError`

```python
class PromptNotFoundError(KeyError)
```

Raised when a prompt `pid` cannot be found in a loaded YAML file. Provides a helpful message listing available pids.

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `pid` | `str` | The pid that was not found |
| `available` | `List[str]` | All pids present in the file |

**Raised by:** `PromptYAML.__getattr__()`, `PromptDataModelYAML.__getattr__()`

```python
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

Raised when an LLM output cannot be parsed into the expected format (e.g. invalid JSON).

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
    print(e.response)   # the raw string that couldn't be parsed
    print(e.message)
```

---

## `MissingContextKeyError`

```python
class MissingContextKeyError(ValueError)
```

Raised when a required template placeholder key is absent from the render context.

**Constructor:**

```python
MissingContextKeyError(key: str)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `key` | `str` | The missing key name |

> **Note:** Most `render()` methods use the `@catch_keyerror` decorator which converts raw `KeyError` into a plain `ValueError` with a similar message. `MissingContextKeyError` is available for explicit raising in custom components.
