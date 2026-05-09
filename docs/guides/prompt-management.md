# Prompt Management

## YAML file types

promptframe supports two types of prompt YAML files, set via `metadata.type`:

| Type | Use for |
|---|---|
| `prompt` | Regular prompts — strings with optional `{placeholders}` |
| `model_prompt` | Field-level instructions bound to `LLMBaseModel` via `model_attribute_id` |

---

## Regular prompts (`type: prompt`)

```yaml title="prompts/my_prompts.yaml"
version: 1.0
metadata:
  type: prompt
  name: my_prompts
  description: General-purpose prompt collection.
  tags: [assistant, qa]
  project: my_project

prompts:
  - pid: system
    description: Base system instruction.
    prompt: You are a helpful assistant.

  - pid: summarise
    description: Summarise a piece of text.
    input_variables: [text, max_sentences]
    prompt: |
      Summarise the following in at most {max_sentences} sentences.

      Text:
      {text}
```

### Loading

```python
from promptframe import PromptRegistry

registry = PromptRegistry("prompts/")
p = registry.load_prompt("my_prompts")

# Attribute access
p.system.prompt          # → "You are a helpful assistant."
p.summarise.pid          # → "summarise"
p.summarise.input_variables  # → ["text", "max_sentences"]

# Format
p.summarise.format(text="The sky is blue.", max_sentences=1)

# Dict access
p.prompt_dict["summarise"]

# Safe get (returns None if missing)
p.get("nonexistent")     # → None
```

---

## Model prompts (`type: model_prompt`)

Model prompts store per-field instructions that get injected into `LLMBaseModel` schemas at runtime. The `model_attribute_id` is the key that binds a YAML entry to a Python field.

```yaml title="prompts/invoice_prompts.yaml"
version: 1.0
metadata:
  type: model_prompt
  name: invoice_prompts

prompts:
  - pid: total_field
    model_attribute_id: invoice_total
    description: The total amount due on the invoice.
    output_instruction: |
      Return the total as a float. If a currency symbol is present, strip it.
      Example: "£1,234.56" → 1234.56

  - pid: line_items_field
    model_attribute_id: invoice_lines
    input_instruction: |
      The line items section lists individual charges.
    output_instruction: |
      Return a JSON array of strings. Each string is one line item with
      its description and amount, e.g. ["Consulting x2h @ £150 = £300"].
```

### Loading

```python
mp = registry.load_model_prompt("invoice_prompts")

# Access by pid
mp.total_field.output_instruction

# The key dict — pass this to LLMBaseModel methods
mp.prompt_model_dict
# → {"invoice_total": PromptDataModel(...), "invoice_lines": PromptDataModel(...)}
```

See [Structured Output](structured-output.md) for how to use `prompt_model_dict` with `LLMBaseModel`.

---

## Metadata fields

| Field | Required | Description |
|---|---|---|
| `type` | ✅ | `"prompt"` or `"model_prompt"` |
| `name` | ✅ | Unique name for this collection |
| `description` | | Human-readable description |
| `tags` | | List of strings for categorisation |
| `project` | | Project name or ID |
| `version` | ✅ | Float, e.g. `1.0` |

---

## Prompt fields

=== "Regular prompt"

    | Field | Required | Description |
    |---|---|---|
    | `pid` | ✅ | Unique ID (becomes Python attribute name) |
    | `prompt` | ✅ | The prompt text. Supports `{placeholder}` interpolation |
    | `description` | | What this prompt does |
    | `input_variables` | | List of expected placeholder names (documentation only) |

=== "Model prompt"

    | Field | Required | Description |
    |---|---|---|
    | `pid` | ✅ | Unique ID |
    | `model_attribute_id` | ✅ | Links to a Python `LLMField` |
    | `input_instruction` | ⚠️ | How the LLM should interpret input (at least one of these required) |
    | `output_instruction` | ⚠️ | What the LLM should output for this field |
    | `description` | | Human-readable description |
    | `input_variables` | | List of placeholder names |

---

## Environment-aware loading

Use `environment` and `common` to load different prompts in different contexts without changing code.

```
prompts/
  prod/
    my_prompts.yaml    ← prod overrides
  shared/
    base_prompts.yaml  ← shared across envs
  my_prompts.yaml      ← fallback / dev defaults
```

```python
import os
from promptframe import PromptRegistry

registry = PromptRegistry(
    base="prompts/",
    environment=os.getenv("ENV", "dev"),   # "prod", "staging", etc.
    common="shared",
)

# Resolution order: prod/ → shared/ → prompts/
p = registry.load_prompt("my_prompts")
```

!!! info "Resolution order"
    `environment` → `common` → `base`. First match wins.
    This means you only need to override the specific file that differs between environments.

---

## Listing available files

```python
registry.list_prompts()
# → ["my_prompts.yaml", "invoice_prompts.yaml", ...]
```

---

## CLI scaffold

```bash
# Regular prompt
promptframe init regular prompts/my_prompts.yaml

# Model prompt
promptframe init model_prompt prompts/invoice_prompts.yaml

# List files in a directory
promptframe list prompts/
```
