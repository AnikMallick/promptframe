# Environments

`PromptRegistry` supports environment-aware file resolution out of the box. This lets you maintain different prompt versions for different deployment contexts without changing any Python code.

---

## How it works

When you configure `environment` and `common`, the registry searches three locations in order:

```
1. base/{environment}/{file}   ← highest priority
2. base/{common}/{file}
3. base/{file}                 ← fallback
```

The first file found wins.

---

## Setup

```
prompts/
  prod/
    extraction.yaml    ← production-tuned prompts
  staging/
    extraction.yaml    ← staging overrides
  shared/
    system.yaml        ← shared across all envs
  extraction.yaml      ← dev defaults / fallback
```

```python
import os
from promptframe import PromptRegistry

registry = PromptRegistry(
    base="prompts/",
    environment=os.getenv("ENV", "dev"),  # "prod", "staging", "dev"
    common="shared",
)
```

---

## Common patterns

### Only override what differs

You don't need a copy of every file in every environment folder. If `prod/extraction.yaml` exists it wins; if not, `prompts/extraction.yaml` is used as the fallback.

```python
# This resolves to prod/extraction.yaml in production,
# prompts/extraction.yaml in dev
p = registry.load_prompt("extraction")
```

### Shared prompts

Put prompts that are identical across all environments in `common/`. They'll be found as long as no environment-specific override exists:

```python
# Always loads shared/system.yaml (no env-specific version)
p = registry.load_prompt("system")
```

### Per-environment tone / verbosity

A common use case — production prompts are tighter and more directive, dev prompts have more debug context:

```yaml title="prompts/extraction.yaml (dev)"
prompts:
  - pid: extract_invoice
    prompt: |
      Extract invoice fields. Return as JSON.
      DEBUG: log any ambiguous fields to "debug_notes".
      Invoice text: {text}
```

```yaml title="prompts/prod/extraction.yaml"
prompts:
  - pid: extract_invoice
    prompt: |
      Extract invoice fields. Return as JSON.
      Invoice text: {text}
```

---

## Listing files

`list_prompts()` respects the same resolution order and deduplicates:

```python
registry.list_prompts()
# Returns each filename once, from the highest-priority location that has it
```
