# Models

**Module:** `promptframe.models`

Pydantic data models that represent the contents of loaded YAML prompt files.

---

## `Metadata`

```python
class Metadata(BaseModel)
```

Represents the `metadata` block at the top of every prompt YAML file.

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"prompt" | "model_prompt"` | ✅ | File type discriminator |
| `name` | `str` | ✅ | Human-readable name for this collection |
| `description` | `str | None` | — | Short description |
| `tags` | `List[str] | None` | — | Free-form tags |
| `project` | `str | None` | — | Project identifier |

---

## `Prompt`

```python
class Prompt(BaseModel)
```

A single prompt entry inside a `type: prompt` YAML file.

| Field | Type | Required | Description |
|---|---|---|---|
| `pid` | `str` | ✅ | Unique prompt identifier |
| `description` | `str | None` | — | What this prompt does |
| `input_variables` | `List[str] | None` | — | Named `{placeholder}` variables |
| `prompt` | `str` | ✅ | The prompt text, may contain `{placeholders}` |

### Methods

#### `format(**kwargs) -> str`

Return the prompt text with `{placeholders}` filled from keyword arguments.

```python
prompt = Prompt(pid="greet", prompt="Hello, {name}!")
prompt.format(name="Alice")  # "Hello, Alice!"
```

#### `__str__() -> str`

Returns the raw `prompt` text.

---

## `PromptDataModel`

```python
class PromptDataModel(BaseModel)
```

A single prompt entry inside a `type: model_prompt` YAML file. Used to inject per-field instructions into `LLMBaseModel` schemas.

| Field | Type | Required | Description |
|---|---|---|---|
| `pid` | `str` | ✅ | Unique prompt identifier |
| `description` | `str | None` | — | Description of this prompt's purpose |
| `input_variables` | `List[str] | None` | — | Named `{placeholder}` variables |
| `model_attribute_id` | `str` | ✅ | Key used to bind this prompt to an `LLMField` on a model |
| `input_instruction` | `str | None` | — | Instruction injected into input schemas |
| `output_instruction` | `str | None` | — | Instruction injected into output schemas |

> **Validation:** At least one of `input_instruction` or `output_instruction` must be provided, or a `ValueError` is raised.

---

## `PromptYAML`

```python
class PromptYAML(PromptYAMLBase)
```

The fully parsed representation of a `type: prompt` YAML file. Returned by `PromptRegistry.load_prompt()`.

| Field | Type | Description |
|---|---|---|
| `version` | `float` | Schema version |
| `metadata` | `Metadata` | File metadata |
| `prompts` | `List[Prompt]` | All prompts in the file |

### Properties

#### `prompt_dict -> Dict[str, Prompt]`

Cached dictionary keyed by `pid`. Built once on first access.

### Methods

#### `get(pid: str) -> Prompt | None`

Return a `Prompt` by its `pid`, or `None` if not found.

```python
p = prompts.get("summarize_text")
```

#### `__getattr__(name: str) -> Prompt`

Attribute-style access to prompts by `pid`. Raises `PromptNotFoundError` if the pid does not exist.

```python
p = prompts.summarize_text       # equivalent to prompts.get("summarize_text")
p = prompts.prompt_dict["summarize_text"]  # dict access
```

---

## `PromptDataModelYAML`

```python
class PromptDataModelYAML(PromptYAMLBase)
```

The fully parsed representation of a `type: model_prompt` YAML file. Returned by `PromptRegistry.load_model_prompt()`.

| Field | Type | Description |
|---|---|---|
| `version` | `float` | Schema version |
| `metadata` | `Metadata` | File metadata |
| `prompts` | `List[PromptDataModel]` | All model prompts in the file |

### Properties

#### `prompt_dict -> Dict[str, PromptDataModel]`

Cached dictionary keyed by `pid`.

#### `prompt_model_dict -> Dict[str, PromptDataModel]`

Cached dictionary keyed by `model_attribute_id`. This is the mapping you pass to `LLMBaseModel` methods.

```python
mp = registry.load_model_prompt("field_prompts")
MyModel.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)
```

### Methods

#### `get(pid: str) -> PromptDataModel | None`

Return a `PromptDataModel` by its `pid`, or `None` if not found.

#### `__getattr__(name: str) -> PromptDataModel`

Attribute-style access to prompts by `pid`. Raises `PromptNotFoundError` if the pid does not exist.
