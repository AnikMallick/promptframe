# LLMBaseModel

**Module:** `promptframe.llm_base_model`

A Pydantic `BaseModel` extension that generates structured input and output schema instructions for LLMs. Extend this class instead of `BaseModel` when you want your model's schema to drive LLM prompts.

---

## Overview

`LLMBaseModel` adds methods to:

- Generate **input instructions** — tell the LLM what each input field means.
- Generate **output format instructions** — tell the LLM exactly how to structure its JSON response.
- Inject per-field instructions from YAML [`model_prompt`](./models.md#promptdatamodelyaml) files.
- Handle **nested models**, `List[Model]`, and `Dict[str, Model]` recursively.
- Cache schemas for performance.

---

## Class Definition

```python
class LLMBaseModel(pydantic.BaseModel)
```

### Usage

```python
from promptframe import LLMBaseModel
from promptframe.fields import LLMField
from pydantic import Field

class CustomerOutput(LLMBaseModel):
    name: str = LLMField(
        ...,
        description="Customer full name",
        model_attribute_id="customer_name",
        output_instruction="Return a cleaned, title-cased full name.",
    )
    score: int = Field(..., description="Risk score between 0 and 100")
    notes: str | None = Field(None, description="Optional free-text notes")

# Without YAML injection
instructions = CustomerOutput.get_format_instructions()

# With YAML injection
mp = registry.load_model_prompt("field_prompts")
instructions = CustomerOutput.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)
```

---

## Class Methods

### `build_input_instruction(...) -> Dict[str, Any]`

```python
@classmethod
def build_input_instruction(
    cls,
    prompt_model_dict: Dict[str, PromptDataModel] | None = None,
    ignore: Tuple[str, ...] | None = None,
    prefix: str = "",
) -> Dict[str, Any]
```

Walk model fields and build a per-field instruction dictionary. Used internally and by the `get_input_instructions*` methods.

Instruction priority for each field:

1. `input_instruction` from a matching `PromptDataModel` in `prompt_model_dict` (matched via `model_attribute_id`)
2. `input_instruction` set directly on the `LLMField`
3. The field's `description`

Handles nested `LLMBaseModel`, `List[LLMBaseModel]`, and `Dict[str, LLMBaseModel]` recursively.

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `prompt_model_dict` | `Dict[str, PromptDataModel] \| None` | Mapping of `model_attribute_id → PromptDataModel` |
| `ignore` | `Tuple[str, ...] \| None` | Dot-notation field paths to exclude, e.g. `("vendor", "address.city")` |
| `prefix` | `str` | Internal — used during recursive nested model calls |

**Returns:** `Dict[str, Any]` — each key is a field name, each value is `{"instruction": str}` or `{"instruction": str, "fields": ...}` for nested models.

---

### `get_input_instructions(...) -> Dict | str`

```python
@classmethod
def get_input_instructions(
    cls,
    get_dict: bool = False,
    force: bool = False,
    ignore: Tuple[str, ...] | None = None,
) -> Dict[str, Any] | str
```

Return input instructions **without** YAML prompt injection. Results are cached.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `get_dict` | `bool` | `False` | Return raw dict instead of a formatted string |
| `force` | `bool` | `False` | Clear the cache and rebuild |
| `ignore` | `Tuple[str, ...] \| None` | `None` | Field paths to exclude |

**Returns:** Formatted string (default) or raw dict.

---

### `get_input_instructions_with_prompt(...) -> Dict | str`

```python
@classmethod
def get_input_instructions_with_prompt(
    cls,
    prompt_model_dict: Dict[str, PromptDataModel] | None = None,
    get_dict: bool = False,
    ignore: Tuple[str, ...] | None = None,
) -> Dict[str, Any] | str
```

Return input instructions **with** YAML `input_instruction` values injected. Not cached (depends on runtime `prompt_model_dict`).

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `prompt_model_dict` | `Dict[str, PromptDataModel] \| None` | From `registry.load_model_prompt(...).prompt_model_dict` |
| `get_dict` | `bool` | Return raw dict instead of formatted string |
| `ignore` | `Tuple[str, ...] \| None` | Field paths to exclude |

---

### `get_format_instructions(...) -> Dict | str`

```python
@classmethod
def get_format_instructions(
    cls,
    get_dict: bool = False,
    force: bool = False,
    ignore: Tuple[str, ...] | None = None,
) -> Dict[str, Any] | str
```

Return output format instructions **without** YAML prompt injection. The output schema is derived from the Pydantic JSON schema with internal metadata keys stripped. Results are cached.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `get_dict` | `bool` | `False` | Return raw dict instead of formatted string |
| `force` | `bool` | `False` | Clear the cache and rebuild |
| `ignore` | `Tuple[str, ...] \| None` | `None` | Field paths to exclude |

```python
instructions = CustomerOutput.get_format_instructions()
# Returns a string beginning with JSON format preamble + schema
```

---

### `get_format_instructions_with_prompt(...) -> Dict | str`

```python
@classmethod
def get_format_instructions_with_prompt(
    cls,
    prompt_model_dict: Dict[str, PromptDataModel] | None = None,
    get_dict: bool = False,
    ignore: Tuple[str, ...] | None = None,
) -> Dict[str, Any] | str
```

**Primary method for structured LLM output.** Combines the Pydantic JSON schema with per-field `output_instruction` values from your YAML model prompt file.

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `prompt_model_dict` | `Dict[str, PromptDataModel] \| None` | From `registry.load_model_prompt(...).prompt_model_dict` |
| `get_dict` | `bool` | Return raw dict instead of formatted string |
| `ignore` | `Tuple[str, ...] \| None` | Field paths to exclude |

```python
mp = registry.load_model_prompt("field_prompts")

instructions = CustomerOutput.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict,
)
```

---

### `get_llm_schema(...) -> Dict[str, Any]`

```python
@classmethod
def get_llm_schema(
    cls,
    prompt_model_dict: Dict[str, PromptDataModel] | None = None,
    get_dict: bool = False,
) -> Dict[str, Any]
```

Return both input and output schemas in a single call.

**Returns:**

```python
{
    "input": <input instructions>,
    "output": <output format instructions>,
}
```

---

### `clean_output_schema(...) -> Dict[str, Any]`

```python
@classmethod
def clean_output_schema(
    cls,
    schema: Dict[str, Any],
    prompt_model_dict: Dict[str, PromptDataModel] | None = None,
    ignore: Tuple[str, ...] | None = None,
) -> Dict[str, Any]
```

Low-level method that transforms a raw Pydantic JSON schema into a clean output schema suitable for LLM instructions. Steps performed:

1. Resolve all `$ref` / `$defs` inline.
2. Inject `output_instruction` (and optionally `description`) from `prompt_model_dict` for fields with a matching `model_attribute_id`.
3. Promote bare `description` → `output_instruction` when no explicit instruction exists.
4. Strip internal-only keys (`input_instruction`, `model_attribute_id`).

You generally don't need to call this directly — use `get_format_instructions_with_prompt` instead.

---

## Instruction Priority Summary

| Source | Input | Output |
|---|---|---|
| `prompt_model_dict` (YAML) | `input_instruction` | `output_instruction` |
| `LLMField` on the model | `input_instruction` | `output_instruction` |
| Pydantic `description` | fallback | fallback (promoted) |

---

## Nested Model Example

```python
class Address(LLMBaseModel):
    city: str = Field(..., description="City name")
    zip_code: str = Field(..., description="Postal code")

class CustomerOutput(LLMBaseModel):
    name: str = LLMField(..., model_attribute_id="customer_name")
    address: Address  # nested model — instructions generated recursively

# Exclude a nested field
instructions = CustomerOutput.get_format_instructions(
    ignore=("address.zip_code",)
)
```
