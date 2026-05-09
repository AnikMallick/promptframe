# CLI Reference

**Entry point:** `promptframe`

The `promptframe` CLI provides tools for creating, inspecting, validating, and managing YAML prompt files and markdown skill files.

---

## Global Options

```
promptframe --version    Show version and exit
promptframe --help       Show help
```

---

## Prompt Commands

### `init` — Create a prompt template

```
promptframe init <template> <output> [--force]
```

| Argument | Description |
|---|---|
| `template` | Template type: `regular` (type: prompt) or `model` (type: model_prompt) |
| `output` | Output file path (e.g. `prompts/my_prompts.yaml`) |
| `-f, --force` | Overwrite if the file already exists |

**Example:**

```bash
promptframe init regular prompts/my_prompts.yaml
promptframe init model prompts/field_prompts.yaml --force
```

---

### `list` — List prompt files

```
promptframe list [path]
```

| Argument | Default | Description |
|---|---|---|
| `path` | `.` | Directory to search for YAML/YML files |

```bash
promptframe list prompts/
```

---

### `validate` — Validate YAML prompt files

```
promptframe validate <path>
```

Checks all `.yaml` and `.yml` files under `path` for required keys (`version`, `metadata`, `prompts`) and that every prompt has a `pid`.

```bash
promptframe validate prompts/
```

Output includes a summary of how many files passed and failed.

---

### `inspect` — Inspect a prompt file

```
promptframe inspect <file>
```

Displays metadata (version, type, name, project, prompt count) and a table of all prompts with their descriptions.

```bash
promptframe inspect prompts/my_prompts.yaml
```

---

### `render` — Render a specific prompt

```
promptframe render <file> <pid>
```

Render a single prompt by its `pid`. If the prompt contains `{placeholders}`, you will be prompted for their values interactively.

```bash
promptframe render prompts/my_prompts.yaml summarize_text
```

---

### `lint` — Lint prompt files

```
promptframe lint <path>
```

Runs structural and best-practice checks on all YAML files under `path`, reporting warnings and errors.

```bash
promptframe lint prompts/
```

---

### `export` — Export a prompt file

```
promptframe export <file> [--format json] [-o output]
```

| Argument | Default | Description |
|---|---|---|
| `file` | — | Path to the YAML prompt file |
| `--format` | `json` | Export format (currently `json`) |
| `-o, --output` | stdout | Output file path |

```bash
promptframe export prompts/my_prompts.yaml --format json -o output.json
```

---

### `diff` — Compare two prompt files

```
promptframe diff <old> <new>
```

Show a side-by-side diff of two prompt YAML files.

```bash
promptframe diff prompts/v1.yaml prompts/v2.yaml
```

---

### `scaffold` — Scaffold a prompt directory structure

```
promptframe scaffold [path] [--example] [--force]
```

Creates a standard directory layout with `dev/`, `test/`, `prod/`, and `common/` sub-folders.

| Argument | Default | Description |
|---|---|---|
| `path` | `prompts` | Base directory to create |
| `--example` | — | Also create an example prompt file in `common/` |
| `-f, --force` | — | Allow scaffolding into a non-empty directory |

```bash
promptframe scaffold prompts/ --example
```

**Generated structure:**

```
prompts/
├── common/
│   └── .gitkeep
├── dev/
│   └── .gitkeep
├── test/
│   └── .gitkeep
└── prod/
    └── .gitkeep
```

---

## Skill Commands

All skill subcommands are under `promptframe skill`.

### `skill init` — Create a new skill

```
promptframe skill init <name> [--path skills] [--force]
```

| Argument | Default | Description |
|---|---|---|
| `name` | — | Skill name (used as directory/file name) |
| `--path` | `skills` | Base directory for skills |
| `-f, --force` | — | Overwrite existing skill |

```bash
promptframe skill init frontend-design --path skills/
```

---

### `skill list` — List available skills

```
promptframe skill list [path]
```

| Argument | Default | Description |
|---|---|---|
| `path` | `skills` | Directory to scan |

```bash
promptframe skill list skills/
```

---

### `skill inspect` — Inspect a skill

```
promptframe skill inspect <key> [--path skills]
```

Display metadata (name, description, tags, version, sections) for a skill.

```bash
promptframe skill inspect frontend-design --path skills/
```

---

### `skill render` — Render a skill

```
promptframe skill render <key> [--path skills] [--section HEADING] [--no-name]
```

| Argument | Default | Description |
|---|---|---|
| `key` | — | Skill key (directory or file stem) |
| `--path` | `skills` | Skills directory |
| `--section` | — | Render only this section (repeatable for multiple sections) |
| `--no-name` | — | Omit the skill name heading |

```bash
promptframe skill render frontend-design --section Guidelines --section Examples
```

---

### `skill validate` — Validate skills

```
promptframe skill validate [path]
```

Check all skill files under `path` for valid frontmatter and required fields.

```bash
promptframe skill validate skills/
```

---

### `skill lint` — Lint skills

```
promptframe skill lint [path]
```

Run best-practice checks on all skill files.

```bash
promptframe skill lint skills/
```

---

### `skill diff` — Diff two skills

```
promptframe skill diff <old> <new>
```

Show a diff between two skill files.

```bash
promptframe skill diff skills/v1/frontend-design.md skills/v2/frontend-design.md
```

---

### `skill search` — Search skills

```
promptframe skill search <query> [--path skills]
```

Search skill names, descriptions, and tags for a keyword.

```bash
promptframe skill search react --path skills/
```
