# PromptRegistry

**Module:** `promptframe.registry`

Environment-aware YAML prompt loader. Resolves prompt files across layered directories (environment-specific → common → base), enabling clean dev/staging/prod prompt management.

---

## `PromptRegistry`

```python
class PromptRegistry(base, environment=None, common=None)
```

### Constructor Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `base` | `str` | ✅ | Root path containing prompt YAML files |
| `environment` | `str | None` | — | Sub-folder for environment-specific overrides (e.g. `"prod"`). Files here take priority over `common` and `base`. |
| `common` | `str | None` | — | Sub-folder for shared prompts used across environments |

### File resolution order

When loading a file named `my_prompts.yaml`, the registry searches in this order and returns the first match:

1. `{base}/{environment}/my_prompts.yaml`
2. `{base}/{common}/my_prompts.yaml`
3. `{base}/my_prompts.yaml`

### Example

```python
from promptframe import PromptRegistry

reg = PromptRegistry(
    base="prompts/",
    environment="prod",
    common="shared",
)
```

---

## Methods

### `load_yml(file_name: str) -> dict`

Load a YAML file and return its raw contents as a Python dict.

Searches across environment → common → base in order and returns the first match.

```python
data = reg.load_yml("my_prompts.yaml")
```

**Raises:**
- `FileNotFoundError` — file not found in any search path
- `ValueError` — file contains invalid YAML

---

### `load_prompt(prompt_name: str) -> PromptYAML`

Load a `type: prompt` YAML file and return a typed [`PromptYAML`](./models.md#promptyaml) object.

The `.yaml` extension is added automatically if omitted.

```python
prompts = reg.load_prompt("my_prompts")

# Attribute access
text = prompts.summarize_text.format(text="...")

# Dict access
text = prompts.prompt_dict["summarize_text"].prompt
```

**Raises:**
- `FileNotFoundError` — file not found
- `ValueError` — metadata type mismatch or no prompts defined

---

### `load_model_prompt(model_prompt: str) -> PromptDataModelYAML`

Load a `type: model_prompt` YAML file and return a typed [`PromptDataModelYAML`](./models.md#promptdatamodelyaml) object.

Use `result.prompt_model_dict` to pass per-field instructions to `LLMBaseModel` methods.

```python
mp = reg.load_model_prompt("field_prompts")

MyModel.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)
```

**Raises:**
- `FileNotFoundError` — file not found
- `ValueError` — metadata type mismatch or no prompts defined

---

### `load_skill(skill_path: str) -> Skill`

Load a single skill `.md` file. Accepts either a direct path to a `.md` file or a folder that contains a `SKILL.md` file. Paths are resolved relative to `base` unless absolute.

```python
skill = reg.load_skill("skills/frontend-design")
skill = reg.load_skill("skills/frontend-design/SKILL.md")
```

**Raises:**
- `FileNotFoundError` — path does not exist or folder has no `SKILL.md`

---

### `skill_registry(skills_dir: str = "skills") -> SkillRegistry`

Return a [`SkillRegistry`](./skills.md#skillregistry) rooted at `skills_dir` (relative to `base`).

```python
sr = reg.skill_registry("skills")
skill = sr.get("frontend-design")
```

---

### `list_prompts() -> List[str]`

Return all YAML/YML file names discovered across the search directories. Files from higher-priority directories shadow duplicates in lower ones.

```python
files = reg.list_prompts()
# ["my_prompts.yaml", "shared_prompts.yaml", ...]
```

---

## Directory Layout Example

```
prompts/
├── shared/
│   └── base_instructions.yaml   # loaded by common=
├── prod/
│   └── my_prompts.yaml          # overrides base version in prod
└── my_prompts.yaml              # base fallback
```

```python
reg = PromptRegistry(base="prompts/", environment="prod", common="shared")

# In prod: loads prompts/prod/my_prompts.yaml
# In dev:  loads prompts/my_prompts.yaml
prompts = reg.load_prompt("my_prompts")
```
