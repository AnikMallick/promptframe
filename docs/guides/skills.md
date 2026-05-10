# Skills

Skills are reusable markdown documents that inject rich, prose-style instructions into prompts. Where YAML prompts are short and parameterised, skills are long-form — decision frameworks, best practice guides, domain knowledge, step-by-step processes.

---

## File format

A skill file is a `.md` file with a YAML frontmatter block:

```markdown title="skills/code-review/SKILL.md"
---
name: code-review
description: Use when reviewing code for quality, bugs, and security.
tags: [code, review, engineering]
version: "1.0"
---

A thorough code review checks correctness, readability, and security.

## Correctness
Check for off-by-one errors, null pointer risks, and unhandled edge cases.
Verify business logic matches the stated requirements.

## Readability
Names should be self-explanatory. Functions should do one thing.
If you need a comment to explain *what* code does, consider renaming instead.

## Security
Look for injection risks, hardcoded secrets, and improper input validation.
Never trust data from external sources without sanitising first.
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `name` | | Display name. Derived from filename if absent |
| `description` | | What this skill does / when to use it |
| `tags` | | List of strings |
| `version` | | Version string |

---

## Directory layouts

Both layouts are supported and can coexist:

=== "Folder-based (recommended)"

    ```
    skills/
      code-review/
        SKILL.md
      data-analysis/
        SKILL.md
      summarise/
        SKILL.md
    ```

    Use this when each skill might eventually have related files (examples, templates).

=== "Flat file"

    ```
    skills/
      code-review.md
      data-analysis.md
      summarise.md
    ```

    Good for simple setups. Folder-based wins if both exist for the same key.

---

## Loading skills

### Via `SkillRegistry`

```python
from promptframe import SkillRegistry

registry = SkillRegistry("skills/")

# List all skills (reads frontmatter only — fast)
registry.list()
# → [{"key": "code-review", "name": "code-review", "description": "...", "tags": [...]}]

# Load a skill by key
skill = registry.get("code-review")

# Load all at once
all_skills = registry.load_all()
# → {"code-review": Skill(...), "summarise": Skill(...)}
```

### Via `PromptRegistry`

```python
from promptframe import PromptRegistry

reg = PromptRegistry("prompts/")

# Load a single skill
skill = reg.load_skill("skills/code-review")

# Get a SkillRegistry rooted at a subdirectory
skill_reg = reg.skill_registry("skills")
```

### Direct file load

```python
from promptframe import load_skill_from_path

skill = load_skill_from_path("skills/code-review/SKILL.md")
```

---

## Working with sections

Skills are automatically parsed into sections by `##` headings:

```python
skill = registry.get("code-review")

# List all sections
list(skill.sections.keys())
# → ["Correctness", "Readability", "Security"]

# Get a specific section's content
skill.get_section("Security")
# → "Look for injection risks..."
```

---

## Rendering

```python
# Full content (default)
skill.render()

# Filter to specific sections
skill.render(sections=["Correctness", "Security"])

# Without the name heading
skill.render(include_name=False)
```

---

## Using `SkillComponent` in the builder

`SkillComponent` drops directly into `StructuredPromptBuilder`:

```python
from promptframe import (
    StructuredPromptBuilder,
    SimplePromptComponent,
    SkillComponent,
    SkillRegistry,
)

registry = SkillRegistry("skills/")
skill = registry.get("code-review")

prompt = (
    StructuredPromptBuilder()
    >> SimplePromptComponent("You are a senior software engineer.")
    >> SkillComponent(skill)                              # all sections
    >> SkillComponent(skill, sections=["Security"])       # one section only
    >> SimplePromptComponent("Review this code:\n{code}")
).build({"code": "x = input()"})
```

### Wrapping in XML tags

Many LLMs respond better when context is wrapped in semantic tags:

```python
SkillComponent(
    skill,
    sections=["Security"],
    wrapper="<skill_context>{skill}</skill_context>",
)
```

### `SkillComponent` parameters

| Parameter | Default | Description |
|---|---|---|
| `skill` | required | A loaded `Skill` instance |
| `sections` | `None` | List of section headings to include. `None` = all |
| `include_name` | `True` | Prepend `## {name}` heading |
| `wrapper` | `None` | Format string wrapping the rendered skill. Must contain `{skill}` |

---

## CLI scaffold

```bash
promptframe skill init code-review
# Creates: skills/code-review/SKILL.md

promptframe skill init data-analysis --path my_skills/
# Creates: my_skills/data-analysis/SKILL.md
```

---

!!! tip "Keep skills focused"
    A skill file works best when it covers one domain well. Prefer many small, focused skills over one large document — then use `sections=` filtering to inject only what's relevant to each prompt.
