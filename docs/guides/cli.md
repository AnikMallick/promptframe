# CLI Reference

PromptFrame ships with a command-line tool for managing prompts and skills without writing Python. It uses [Rich](https://github.com/Textualize/rich) for formatted, colourised output.

```bash
promptframe --help
```

Commands are split into two groups — **prompt commands** (top-level) and **skill subcommands** (under `skill`).

---

## Prompt commands

### `init` — scaffold a prompt file

Create a new YAML prompt file from a template.

```bash
promptframe init <template> <output>
```

| Argument | Description |
|---|---|
| `template` | `regular` or `model` |
| `output` | Destination file path |
| `-f, --force` | Overwrite if the file already exists |

=== "Regular prompt"

    ```bash
    promptframe init regular prompts/my_prompts.yaml
    ```

    Generates a `type: prompt` file with two example prompts.

=== "Model prompt"

    ```bash
    promptframe init model prompts/invoice_prompts.yaml
    ```

    Generates a `type: model_prompt` file with an example field instruction.

---

### `list` — list prompt files

List all YAML prompt files in a directory.

```bash
promptframe list [path]
```

`path` defaults to `.` (current directory).

```bash
promptframe list prompts/
```

---

### `inspect` — inspect a prompt file

Show metadata and a summary of all prompts in a file.

```bash
promptframe inspect <file>
```

```bash
promptframe inspect prompts/invoice_prompts.yaml
```

Prints a metadata table (version, type, name, project, prompt count) followed by a table of all prompt IDs and their descriptions.

---

### `render` — render a single prompt

Print a specific prompt's text to the terminal with syntax highlighting.

```bash
promptframe render <file> <pid>
```

```bash
promptframe render prompts/my_prompts.yaml summarise_text
```

Renders `output_instruction` for model prompts when no `prompt` field is present.

---

### `validate` — validate prompt files

Check all YAML files in a directory for required fields (`version`, `metadata`, `prompts`, and `pid` on each prompt).

```bash
promptframe validate <path>
```

```bash
promptframe validate prompts/
```

Prints `VALID` or `INVALID` per file, then a summary panel showing passed/failed counts.

---

### `lint` — lint prompt files

Check for quality issues beyond structural validity. Currently flags prompts that are missing a `description`.

```bash
promptframe lint <path>
```

```bash
promptframe lint prompts/
```

!!! tip
    Run `validate` first (structure), then `lint` (quality). They serve different purposes.

---

### `diff` — compare two prompt files

Show which prompts were added, removed, or modified between two versions of a prompt file. Modified prompts get a unified diff.

```bash
promptframe diff <old> <new>
```

```bash
promptframe diff prompts/v1/invoice.yaml prompts/v2/invoice.yaml
```

Useful when reviewing changes before a deploy or when auditing prompt history in git.

---

### `export` — export a prompt file

Export a YAML prompt file to another format.

```bash
promptframe export <file> [--format json] [-o output]
```

| Argument | Description |
|---|---|
| `file` | Path to the YAML prompt file |
| `--format` | Output format. Currently `json` only (default: `json`) |
| `-o, --output` | Write to a file instead of printing to stdout |

```bash
# Print JSON to terminal
promptframe export prompts/invoice.yaml

# Write to a file
promptframe export prompts/invoice.yaml -o invoice.json
```

---

### `scaffold` — scaffold an environment directory structure

Create a standard `dev / test / prod / common` folder structure for environment-aware prompt management.

```bash
promptframe scaffold [path] [--example] [-f, --force]
```

| Argument | Default | Description |
|---|---|---|
| `path` | `prompts` | Base directory to scaffold into |
| `--example` | off | Create an example prompt file in `common/` |
| `-f, --force` | off | Allow scaffolding into a non-empty directory |

```bash
# Default: creates prompts/dev, prompts/test, prompts/prod, prompts/common
promptframe scaffold

# Custom path with an example file
promptframe scaffold my_prompts/ --example
```

Resulting structure:

```
my_prompts/
  common/
    example_prompt.yaml   ← only if --example
  dev/
  test/
  prod/
```

Each folder gets a `.gitkeep` so it's tracked by git even when empty. See [Environments](environments.md) for how to load from this structure.

---

### `version` — show version

```bash
promptframe version
```

---

## Skill commands

All skill commands live under the `skill` subcommand:

```bash
promptframe skill <command> [args]
```

---

### `skill init` — create a new skill

Create a `SKILL.md` template inside a named folder.

```bash
promptframe skill init <name> [--path skills] [-f, --force]
```

| Argument | Default | Description |
|---|---|---|
| `name` | required | Skill folder name (e.g. `code-review`) |
| `--path` | `skills` | Parent directory to create the skill folder inside |
| `-f, --force` | off | Overwrite if `SKILL.md` already exists |

```bash
promptframe skill init code-review
# Creates: skills/code-review/SKILL.md

promptframe skill init data-analysis --path my_skills/
# Creates: my_skills/data-analysis/SKILL.md
```

---

### `skill list` — list skills

Show all skills in a directory in a formatted table (key, name, description, tags).

```bash
promptframe skill list [path]
```

`path` defaults to `skills`.

```bash
promptframe skill list
promptframe skill list my_skills/
```

---

### `skill inspect` — inspect a skill

Show metadata and section headings for a single skill.

```bash
promptframe skill inspect <key> [--path skills]
```

```bash
promptframe skill inspect code-review
promptframe skill inspect code-review --path my_skills/
```

Prints a metadata table (name, description, version, tags, source path) followed by a table of all section headings.

---

### `skill render` — render a skill

Print a skill's content to the terminal with syntax highlighting.

```bash
promptframe skill render <key> [--path skills] [--section HEADING] [--no-name]
```

| Argument | Default | Description |
|---|---|---|
| `key` | required | Skill key (folder name or file stem) |
| `--path` | `skills` | Skills directory |
| `--section` | all | Section heading to include. Repeatable |
| `--no-name` | off | Omit the skill name heading |

```bash
# Render full skill
promptframe skill render code-review

# Render one section
promptframe skill render code-review --section Security

# Render multiple sections
promptframe skill render code-review --section Security --section Correctness

# Without the name heading
promptframe skill render code-review --no-name
```

---

### `skill validate` — validate skills

Check all skill files in a directory for required content (name present, non-empty content).

```bash
promptframe skill validate [path]
```

`path` defaults to `skills`.

```bash
promptframe skill validate
promptframe skill validate my_skills/
```

Prints `VALID` or `INVALID` per file with a summary panel.

---

### `skill lint` — lint skills

Check skill files for quality issues — flags skills missing a `description` or `tags`.

```bash
promptframe skill lint [path]
```

```bash
promptframe skill lint
```

---

### `skill diff` — compare two skill files

Show a unified diff between two `SKILL.md` files.

```bash
promptframe skill diff <old> <new>
```

```bash
promptframe skill diff skills/code-review/SKILL.md new_skills/code-review/SKILL.md
```

---

### `skill search` — search skills

Search across skill keys, names, descriptions, and tags.

```bash
promptframe skill search <query> [--path skills]
```

```bash
promptframe skill search security
promptframe skill search "code review" --path my_skills/
```

Returns a table of matching skills. Matching is case-insensitive substring search across all metadata fields.

---

## Typical workflows

**Starting a new project:**

```bash
# Scaffold environment folders
promptframe scaffold prompts/ --example

# Add your first prompt file
promptframe init regular prompts/common/my_prompts.yaml

# Validate everything is correct
promptframe validate prompts/

# Lint for quality
promptframe lint prompts/
```

**Working with skills:**

```bash
# Create a skill
promptframe skill init code-review

# Edit skills/code-review/SKILL.md in your editor

# Check it's valid
promptframe skill validate

# Preview a section before using it in a prompt
promptframe skill render code-review --section Security
```

**Reviewing changes before a deploy:**

```bash
# Compare prompts between branches/versions
promptframe diff prompts/v1/extraction.yaml prompts/v2/extraction.yaml

# Compare a skill
promptframe skill diff skills/old/code-review/SKILL.md skills/new/code-review/SKILL.md
```
