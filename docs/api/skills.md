# Skills

**Modules:** `promptframe.skill`, `promptframe.skill_registry`

Skills are rich markdown instruction documents — best practices, decision frameworks, step-by-step guides — that get injected verbatim into prompts as context. Unlike short parameterised YAML prompts, skills are human-authored prose meant to guide LLM behavior across many tasks.

---

## File Conventions

Skills are `.md` files with optional YAML frontmatter. Two layouts are supported and can coexist:

### Folder-based (preferred)

```
skills/
  frontend-design/
    SKILL.md
  data-analysis/
    SKILL.md
```

### Flat-file

```
skills/
  frontend-design.md
  data-analysis.md
```

### Frontmatter schema

```markdown
---
name: frontend-design          # required; derived from filename if omitted
description: When to use this skill.
tags:
  - frontend
  - react
version: "1.0"
---

## Overview

Skill content here...
```

Only `name` is required. Everything else is optional.

---

## `Skill`

```python
class Skill
```

A loaded skill — frontmatter metadata plus the markdown body.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | Skill name (from frontmatter or derived from filename) |
| `description` | `str \| None` | What this skill does / when to use it |
| `tags` | `List[str]` | Optional tags (empty list if not set) |
| `version` | `str \| None` | Version string |
| `content` | `str` | Raw markdown body |
| `source_path` | `str \| None` | Absolute path to the source file |
| `extra` | `Dict[str, Any]` | Any additional frontmatter keys not listed above |

### Properties

#### `sections -> Dict[str, str]`

Cached dictionary of top-level `#`, `##`, and `###` headings mapped to their content. Lets you extract individual sections of a large skill file.

```python
skill.sections
# {"Overview": "...", "Guidelines": "...", "Examples": "..."}

skill.sections["Guidelines"]
# "- Use semantic HTML\n- Prefer CSS variables..."
```

### Methods

#### `get_section(heading: str) -> str | None`

Return the content of a specific section, or `None` if not found.

```python
body = skill.get_section("Guidelines")
```

---

#### `render(sections=None, *, include_name=True) -> str`

Render the skill to a string for injection into a prompt.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `sections` | `List[str] \| None` | `None` | If provided, only include these section headings (in the given order) |
| `include_name` | `bool` | `True` | Prepend `## {name}` heading |

**Returns:** Rendered skill content as a plain string.

```python
# Full content
skill.render()

# Only specific sections
skill.render(sections=["Guidelines", "Examples"])

# Without the name heading
skill.render(include_name=False)
```

#### `__str__() -> str`

Returns the raw `content` markdown body.

---

## `load_skill_from_path(path: str) -> Skill`

**Module:** `promptframe.skill`

Parse a single `.md` skill file and return a `Skill` instance.

```python
from promptframe.skill import load_skill_from_path

skill = load_skill_from_path("skills/frontend-design/SKILL.md")
```

**Raises:**
- `FileNotFoundError` — path does not exist
- `ValueError` — file cannot be parsed

---

## `SkillRegistry`

```python
class SkillRegistry(base: str)
```

Discover and load skills from a directory tree. Supports both folder-based and flat-file layouts simultaneously. Skills are cached in memory after the first load.

### Constructor

| Argument | Type | Description |
|---|---|---|
| `base` | `str` | Root directory to scan for skill files (stored as absolute path) |

```python
from promptframe import SkillRegistry

registry = SkillRegistry("skills/")
```

---

### Methods

#### `get(key: str, *, force_reload: bool = False) -> Skill`

Load a skill by its directory name or file stem (e.g. `"frontend-design"`). Returns from cache on subsequent calls unless `force_reload=True`.

```python
skill = registry.get("frontend-design")
skill = registry.get("data-analysis", force_reload=True)
```

**Raises:** `KeyError` if no skill with that key exists, with a list of available keys in the message.

---

#### `load_all(*, force_reload: bool = False) -> Dict[str, Skill]`

Load every discovered skill into the cache and return them all.

```python
all_skills = registry.load_all()
# {"frontend-design": Skill(...), "data-analysis": Skill(...)}
```

---

#### `list() -> List[Dict[str, Any]]`

Return a lightweight summary of all skills without loading full content. Reads only frontmatter for uncached skills — fast even with many files.

**Returns:** List of dicts with keys `key`, `name`, `description`, `tags`.

```python
registry.list()
# [
#   {"key": "frontend-design", "name": "Frontend Design", "description": "...", "tags": ["frontend"]},
#   {"key": "data-analysis",   "name": "Data Analysis",   "description": "...", "tags": ["data"]},
# ]
```

---

## Using Skills in Prompts

Skills are injected via [`SkillComponent`](./components.md#skillcomponent):

```python
from promptframe import SkillRegistry, StructuredPromptBuilder
from promptframe.components import SimplePromptComponent, SkillComponent

registry = SkillRegistry("skills/")
skill = registry.get("frontend-design")

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a frontend expert.")
    >> SkillComponent(skill, sections=["Guidelines"])
    >> SimplePromptComponent("Task: {task}")
).build({"task": "Build a login page"})
```

Skills can also be loaded via `PromptRegistry`:

```python
from promptframe import PromptRegistry

reg = PromptRegistry(base="prompts/")
skill = reg.load_skill("skills/frontend-design")
sr = reg.skill_registry("skills")
```
