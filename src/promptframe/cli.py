"""
promptframe CLI

Professional CLI for managing YAML-based prompts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
import difflib

from .registry import PromptRegistry
from .skill_registry import SkillRegistry
from .skill import load_skill_from_path


console = Console()

CLI_NAME = "promptframe"
CLI_DESCRIPTION = "LLM-agnostic prompt management toolkit"

# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------

_REGULAR_TEMPLATE = """\
version: 1.0

metadata:
  type: prompt
  name: {name}
  description: Describe this prompt collection here.
  tags: []
  project: my_project

prompts:
  - pid: summarize_text
    description: Summarize a block of text.

    input_variables:
      - text

    prompt: |
      Summarize the following text:

      {{text}}

  - pid: classify_topic
    description: Classify content into a topic.

    input_variables:
      - content

    prompt: |
      Classify the following content into a topic category:

      {{content}}
"""

_MODEL_PROMPT_TEMPLATE = """\
version: 1.0

metadata:
  type: model_prompt
  name: {name}
  description: Describe this model prompt collection here.
  tags: []
  project: my_project

prompts:
  - pid: clean_name
    description: Clean and normalize a name field.

    model_attribute_id: customer_name

    input_variables:
      - raw_name

    input_instruction: |
      The input contains {{raw_name}}.

    output_instruction: |
      Return a cleaned human-readable name.
"""
_SKILL_TEMPLATE = """\
---
name: {name}
description: Describe when this skill should be used.
tags:
  - example
version: "1.0"
---

# Overview

Describe the purpose of this skill.

## Guidelines

- Add instructions here
- Add best practices here

## Examples

Provide examples.
"""

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def find_skill_files(base: Path) -> list[Path]:
    files = []

    for path in base.rglob("SKILL.md"):
        files.append(path)

    for path in base.rglob("*.md"):
        if path.name != "SKILL.md":
            files.append(path)

    return files

def load_prompt_map(path: Path) -> dict:
    data = load_yaml(path)

    prompts = {}

    for prompt in data.get("prompts", []):
        pid = prompt.get("pid")
        if pid:
            prompts[pid] = prompt

    return prompts

def success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def warning(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def find_yaml_files(base: Path) -> list[Path]:
    return list(base.rglob("*.yaml")) + list(base.rglob("*.yml"))


# -------------------------------------------------------------------
# init
# -------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    template_map = {
        "regular": _REGULAR_TEMPLATE,
        "model": _MODEL_PROMPT_TEMPLATE,
    }

    output = Path(args.output)

    if output.exists() and not args.force:
        error(f"File already exists: {output}")
        console.print("Use [cyan]--force[/cyan] to overwrite.")
        sys.exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    template = template_map[args.template]
    content = template.format(name=output.stem)

    output.write_text(content, encoding="utf-8")

    success(f"Created {args.template} template")
    console.print(f"[dim]{output}[/dim]")


# -------------------------------------------------------------------
# list
# -------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    registry = PromptRegistry(base=args.path)
    files = registry.list_prompts()

    if not files:
        warning("No prompt files found.")
        return

    table = Table(
        title="Prompt Files",
        box=box.ROUNDED,
    )

    table.add_column("File", style="cyan")

    for file in files:
        table.add_row(file)

    console.print(table)


# -------------------------------------------------------------------
# validate
# -------------------------------------------------------------------


def validate_prompt_file(path: Path) -> list[str]:
    errors = []

    try:
        data = load_yaml(path)

        if "version" not in data:
            errors.append("Missing 'version'")

        if "metadata" not in data:
            errors.append("Missing 'metadata'")

        if "prompts" not in data:
            errors.append("Missing 'prompts'")

        prompts = data.get("prompts", [])

        for idx, prompt in enumerate(prompts):
            if "pid" not in prompt:
                errors.append(f"Prompt #{idx} missing 'pid'")

    except Exception as e:
        errors.append(str(e))

    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    base = Path(args.path)

    files = find_yaml_files(base)

    if not files:
        warning("No YAML files found.")
        return

    passed = 0
    failed = 0

    for file in files:
        errors = validate_prompt_file(file)

        if errors:
            failed += 1
            console.print(f"\n[bold red]INVALID[/bold red] {file}")

            for err in errors:
                console.print(f"  • {err}")

        else:
            passed += 1
            console.print(f"[green]VALID[/green] {file}")

    console.print()
    console.print(
        Panel.fit(
            f"[green]{passed} passed[/green]\n"
            f"[red]{failed} failed[/red]",
            title="Validation Summary",
        )
    )


# -------------------------------------------------------------------
# inspect
# -------------------------------------------------------------------


def cmd_inspect(args: argparse.Namespace) -> None:
    path = Path(args.file)

    if not path.exists():
        error(f"File not found: {path}")
        sys.exit(1)

    data = load_yaml(path)

    metadata = data.get("metadata", {})
    prompts = data.get("prompts", [])

    table = Table(
        title=f"Prompt File: {path.name}",
        box=box.ROUNDED,
    )

    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Version", str(data.get("version")))
    table.add_row("Type", str(metadata.get("type")))
    table.add_row("Name", str(metadata.get("name")))
    table.add_row("Project", str(metadata.get("project")))
    table.add_row("Prompt Count", str(len(prompts)))

    console.print(table)

    prompt_table = Table(
        title="Prompts",
        box=box.MINIMAL,
    )

    prompt_table.add_column("PID", style="green")
    prompt_table.add_column("Description")

    for prompt in prompts:
        prompt_table.add_row(
            prompt.get("pid", ""),
            prompt.get("description", ""),
        )

    console.print(prompt_table)


# -------------------------------------------------------------------
# render
# -------------------------------------------------------------------


def cmd_render(args: argparse.Namespace) -> None:
    path = Path(args.file)
    pid = args.pid

    data = load_yaml(path)

    prompts = data.get("prompts", [])

    target = None

    for prompt in prompts:
        if prompt.get("pid") == pid:
            target = prompt
            break

    if target is None:
        error(f"Prompt '{pid}' not found.")
        sys.exit(1)

    content = (
        target.get("prompt")
        or target.get("output_instruction")
        or "No renderable content."
    )

    syntax = Syntax(
        content,
        "markdown",
        theme="monokai",
        line_numbers=True,
    )

    console.print(
        Panel(
            syntax,
            title=f"Rendered Prompt: {pid}",
            border_style="cyan",
        )
    )


# -------------------------------------------------------------------
# lint
# -------------------------------------------------------------------


def cmd_lint(args: argparse.Namespace) -> None:
    base = Path(args.path)

    files = find_yaml_files(base)

    if not files:
        warning("No YAML files found.")
        return

    issues = 0

    for file in files:
        data = load_yaml(file)

        prompts = data.get("prompts", [])

        for prompt in prompts:
            desc = prompt.get("description")

            if not desc:
                issues += 1
                console.print(
                    f"[yellow]LINT[/yellow] {file} -> "
                    f"Prompt '{prompt.get('pid')}' missing description"
                )

    if issues == 0:
        success("No lint issues found.")


# -------------------------------------------------------------------
# export
# -------------------------------------------------------------------


def cmd_export(args: argparse.Namespace) -> None:
    path = Path(args.file)

    data = load_yaml(path)

    if args.format == "json":
        output = json.dumps(data, indent=2)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            success(f"Exported JSON to {args.output}")
        else:
            console.print_json(output)


# -------------------------------------------------------------------
# version
# -------------------------------------------------------------------


def cmd_version(args: argparse.Namespace) -> None:
    try:
        from . import __version__
    except ImportError:
        __version__ = "0.1.0"

    console.print(f"[bold cyan]{CLI_NAME}[/bold cyan] v{__version__}")


# -------------------------------------------------------------------
# diff
# -------------------------------------------------------------------

def cmd_diff(args: argparse.Namespace) -> None:
    old_file = Path(args.old)
    new_file = Path(args.new)

    old_prompts = load_prompt_map(old_file)
    new_prompts = load_prompt_map(new_file)

    old_keys = set(old_prompts)
    new_keys = set(new_prompts)

    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys

    table = Table(title="Prompt Differences")

    table.add_column("Type")
    table.add_column("Prompt ID")

    for pid in sorted(added):
        table.add_row("[green]ADDED[/green]", pid)

    for pid in sorted(removed):
        table.add_row("[red]REMOVED[/red]", pid)

    modified = []

    for pid in sorted(common):
        old_prompt = old_prompts[pid]
        new_prompt = new_prompts[pid]

        if old_prompt != new_prompt:
            modified.append(pid)
            table.add_row("[yellow]MODIFIED[/yellow]", pid)

    console.print(table)

    # detailed diff

    for pid in modified:
        console.rule(f"[cyan]{pid}")

        old_text = yaml.dump(
            old_prompts[pid],
            sort_keys=False,
        ).splitlines()

        new_text = yaml.dump(
            new_prompts[pid],
            sort_keys=False,
        ).splitlines()

        diff = difflib.unified_diff(
            old_text,
            new_text,
            fromfile="old",
            tofile="new",
            lineterm="",
        )

        diff_text = "\n".join(diff)

        console.print(
            Syntax(
                diff_text,
                "diff",
                theme="monokai",
                line_numbers=False,
            )
        )
# -------------------------------------------------------------------
# skill init
# -------------------------------------------------------------------


def cmd_skill_init(args: argparse.Namespace) -> None:
    name = args.name

    skill_dir = Path(args.path) / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists() and not args.force:
        error(f"Skill already exists: {skill_file}")
        console.print("Use [cyan]--force[/cyan] to overwrite.")
        sys.exit(1)

    content = _SKILL_TEMPLATE.format(name=name)

    skill_file.write_text(content, encoding="utf-8")

    success(f"Created skill '{name}'")
    console.print(f"[dim]{skill_file}[/dim]")


# -------------------------------------------------------------------
# skill list
# -------------------------------------------------------------------


def cmd_skill_list(args: argparse.Namespace) -> None:
    registry = SkillRegistry(args.path)

    skills = registry.list()

    if not skills:
        warning("No skills found.")
        return

    table = Table(
        title="Skills",
        box=box.ROUNDED,
    )

    table.add_column("Key", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Tags", style="yellow")

    for skill in skills:
        table.add_row(
            skill["key"],
            skill.get("name", ""),
            skill.get("description", "") or "",
            ", ".join(skill.get("tags", [])),
        )

    console.print(table)


# -------------------------------------------------------------------
# skill inspect
# -------------------------------------------------------------------


def cmd_skill_inspect(args: argparse.Namespace) -> None:
    registry = SkillRegistry(args.path)

    try:
        skill = registry.get(args.key)
    except KeyError as e:
        error(str(e))
        sys.exit(1)

    table = Table(
        title=f"Skill: {skill.name}",
        box=box.ROUNDED,
    )

    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Name", skill.name)
    table.add_row("Description", skill.description or "")
    table.add_row("Version", skill.version or "")
    table.add_row("Tags", ", ".join(skill.tags))
    table.add_row("Source", skill.source_path or "")

    console.print(table)

    sections_table = Table(
        title="Sections",
        box=box.MINIMAL,
    )

    sections_table.add_column("Heading", style="green")

    for section in skill.sections.keys():
        sections_table.add_row(section)

    console.print(sections_table)


# -------------------------------------------------------------------
# skill render
# -------------------------------------------------------------------


def cmd_skill_render(args: argparse.Namespace) -> None:
    registry = SkillRegistry(args.path)

    try:
        skill = registry.get(args.key)
    except KeyError as e:
        error(str(e))
        sys.exit(1)

    content = skill.render(
        sections=args.sections,
        include_name=not args.no_name,
    )

    syntax = Syntax(
        content,
        "markdown",
        theme="monokai",
        line_numbers=True,
    )

    console.print(
        Panel(
            syntax,
            title=f"Skill Render: {skill.name}",
            border_style="cyan",
        )
    )


# -------------------------------------------------------------------
# skill validate
# -------------------------------------------------------------------


def validate_skill_file(path: Path) -> list[str]:
    errors = []

    try:
        skill = load_skill_from_path(str(path))

        if not skill.name:
            errors.append("Missing name")

        if not skill.content.strip():
            errors.append("Empty skill content")

    except Exception as e:
        errors.append(str(e))

    return errors


def cmd_skill_validate(args: argparse.Namespace) -> None:
    base = Path(args.path)

    files = find_skill_files(base)

    if not files:
        warning("No skill files found.")
        return

    passed = 0
    failed = 0

    for file in files:
        errors = validate_skill_file(file)

        if errors:
            failed += 1

            console.print(f"\n[bold red]INVALID[/bold red] {file}")

            for err in errors:
                console.print(f"  • {err}")

        else:
            passed += 1
            console.print(f"[green]VALID[/green] {file}")

    console.print()

    console.print(
        Panel.fit(
            f"[green]{passed} passed[/green]\n"
            f"[red]{failed} failed[/red]",
            title="Skill Validation Summary",
        )
    )


# -------------------------------------------------------------------
# skill lint
# -------------------------------------------------------------------


def cmd_skill_lint(args: argparse.Namespace) -> None:
    base = Path(args.path)

    files = find_skill_files(base)

    if not files:
        warning("No skill files found.")
        return

    issues = 0

    for file in files:
        try:
            skill = load_skill_from_path(str(file))

            if not skill.description:
                issues += 1

                console.print(
                    f"[yellow]LINT[/yellow] "
                    f"{file} -> missing description"
                )

            if not skill.tags:
                issues += 1

                console.print(
                    f"[yellow]LINT[/yellow] "
                    f"{file} -> missing tags"
                )

        except Exception as e:
            issues += 1

            console.print(
                f"[red]ERROR[/red] {file} -> {e}"
            )

    if issues == 0:
        success("No lint issues found.")


# -------------------------------------------------------------------
# skill diff
# -------------------------------------------------------------------


def cmd_skill_diff(args: argparse.Namespace) -> None:
    old_file = Path(args.old)
    new_file = Path(args.new)

    old_text = old_file.read_text(encoding="utf-8").splitlines()
    new_text = new_file.read_text(encoding="utf-8").splitlines()

    diff = difflib.unified_diff(
        old_text,
        new_text,
        fromfile=str(old_file),
        tofile=str(new_file),
        lineterm="",
    )

    diff_text = "\n".join(diff)

    console.print(
        Syntax(
            diff_text,
            "diff",
            theme="monokai",
            line_numbers=False,
        )
    )


# -------------------------------------------------------------------
# skill search
# -------------------------------------------------------------------


def cmd_skill_search(args: argparse.Namespace) -> None:
    query = args.query.lower()

    registry = SkillRegistry(args.path)

    skills = registry.list()

    matches = []

    for skill in skills:
        haystack = " ".join(
            [
                skill.get("key", ""),
                skill.get("name", ""),
                skill.get("description", "") or "",
                " ".join(skill.get("tags", [])),
            ]
        ).lower()

        if query in haystack:
            matches.append(skill)

    if not matches:
        warning(f"No skills found for '{args.query}'")
        return

    table = Table(
        title=f"Skill Search: {args.query}",
        box=box.ROUNDED,
    )

    table.add_column("Key", style="cyan")
    table.add_column("Description")
    table.add_column("Tags", style="yellow")

    for skill in matches:
        table.add_row(
            skill["key"],
            skill.get("description", "") or "",
            ", ".join(skill.get("tags", [])),
        )

    console.print(table)

# -------------------------------------------------------------------
# Environment Scaffold Template
# -------------------------------------------------------------------

_ENV_STRUCTURE = [
    "common",
    "dev",
    "test",
    "prod",
]


# -------------------------------------------------------------------
# scaffold
# -------------------------------------------------------------------


def cmd_scaffold(args: argparse.Namespace) -> None:
    base = Path(args.path)

    if base.exists() and any(base.iterdir()) and not args.force:
        error(
            f"Directory '{base}' is not empty."
        )

        console.print(
            "Use [cyan]--force[/cyan] to scaffold anyway."
        )

        sys.exit(1)

    base.mkdir(parents=True, exist_ok=True)

    created = []

    for folder in _ENV_STRUCTURE:
        env_dir = base / folder

        env_dir.mkdir(parents=True, exist_ok=True)

        created.append(env_dir)

        # create .gitkeep
        gitkeep = env_dir / ".gitkeep"

        if not gitkeep.exists():
            gitkeep.touch()

    # Optional example prompt

    if args.example:
        example_file = base / "common" / "example_prompt.yaml"

        content = _REGULAR_TEMPLATE.format(
            name="example_prompt"
        )

        example_file.write_text(
            content,
            encoding="utf-8",
        )

        created.append(example_file)

    success("Prompt environment scaffold created")

    table = Table(
        title="Created Structure",
        box=box.ROUNDED,
    )

    table.add_column("Path", style="cyan")

    for item in created:
        table.add_row(str(item))

    console.print(table)

# -------------------------------------------------------------------
# parser
# -------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description=CLI_DESCRIPTION,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="promptframe 0.1.0",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # init

    p_init = sub.add_parser("init", help="Create prompt template")
    p_init.add_argument(
        "template",
        choices=["regular", "model"],
    )
    p_init.add_argument("output")
    p_init.add_argument(
        "-f",
        "--force",
        action="store_true",
    )
    p_init.set_defaults(func=cmd_init)

    # list

    p_list = sub.add_parser("list", help="List prompt files")
    p_list.add_argument("path", nargs="?", default=".")
    p_list.set_defaults(func=cmd_list)

    # validate

    p_validate = sub.add_parser(
        "validate",
        help="Validate YAML prompt files",
    )
    p_validate.add_argument("path")
    p_validate.set_defaults(func=cmd_validate)

    # inspect

    p_inspect = sub.add_parser(
        "inspect",
        help="Inspect prompt file",
    )
    p_inspect.add_argument("file")
    p_inspect.set_defaults(func=cmd_inspect)

    # render

    p_render = sub.add_parser(
        "render",
        help="Render a specific prompt",
    )
    p_render.add_argument("file")
    p_render.add_argument("pid")
    p_render.set_defaults(func=cmd_render)

    # lint

    p_lint = sub.add_parser(
        "lint",
        help="Lint prompt files",
    )
    p_lint.add_argument("path")
    p_lint.set_defaults(func=cmd_lint)

    # export

    p_export = sub.add_parser(
        "export",
        help="Export prompt file",
    )

    p_export.add_argument("file")

    p_export.add_argument(
        "--format",
        choices=["json"],
        default="json",
    )

    p_export.add_argument(
        "-o",
        "--output",
    )

    p_export.set_defaults(func=cmd_export)

    # version

    p_version = sub.add_parser(
        "version",
        help="Show version",
    )
    p_version.set_defaults(func=cmd_version)
    
    # diff
    p_diff = sub.add_parser(
        "diff",
        help="Compare two prompt files",
    )

    p_diff.add_argument("old")
    p_diff.add_argument("new")

    p_diff.set_defaults(func=cmd_diff)
    
    
    # ---------------------------------------------------------------
    # skill
    # ---------------------------------------------------------------

    p_skill = sub.add_parser(
        "skill",
        help="Skill management commands",
    )

    skill_sub = p_skill.add_subparsers(
        dest="skill_command",
        required=True,
    )

    # skill init

    p_skill_init = skill_sub.add_parser(
        "init",
        help="Create a new skill",
    )

    p_skill_init.add_argument("name")

    p_skill_init.add_argument(
        "--path",
        default="skills",
    )

    p_skill_init.add_argument(
        "-f",
        "--force",
        action="store_true",
    )

    p_skill_init.set_defaults(func=cmd_skill_init)

    # skill list

    p_skill_list = skill_sub.add_parser(
        "list",
        help="List skills",
    )

    p_skill_list.add_argument(
        "path",
        nargs="?",
        default="skills",
    )

    p_skill_list.set_defaults(func=cmd_skill_list)

    # skill inspect

    p_skill_inspect = skill_sub.add_parser(
        "inspect",
        help="Inspect a skill",
    )

    p_skill_inspect.add_argument("key")

    p_skill_inspect.add_argument(
        "--path",
        default="skills",
    )

    p_skill_inspect.set_defaults(func=cmd_skill_inspect)

    # skill render

    p_skill_render = skill_sub.add_parser(
        "render",
        help="Render a skill",
    )

    p_skill_render.add_argument("key")

    p_skill_render.add_argument(
        "--path",
        default="skills",
    )

    p_skill_render.add_argument(
        "--section",
        dest="sections",
        action="append",
    )

    p_skill_render.add_argument(
        "--no-name",
        action="store_true",
    )

    p_skill_render.set_defaults(func=cmd_skill_render)

    # skill validate

    p_skill_validate = skill_sub.add_parser(
        "validate",
        help="Validate skills",
    )

    p_skill_validate.add_argument(
        "path",
        nargs="?",
        default="skills",
    )

    p_skill_validate.set_defaults(func=cmd_skill_validate)

    # skill lint

    p_skill_lint = skill_sub.add_parser(
        "lint",
        help="Lint skills",
    )

    p_skill_lint.add_argument(
        "path",
        nargs="?",
        default="skills",
    )

    p_skill_lint.set_defaults(func=cmd_skill_lint)

    # skill diff

    p_skill_diff = skill_sub.add_parser(
        "diff",
        help="Diff two skills",
    )

    p_skill_diff.add_argument("old")
    p_skill_diff.add_argument("new")

    p_skill_diff.set_defaults(func=cmd_skill_diff)

    # skill search

    p_skill_search = skill_sub.add_parser(
        "search",
        help="Search skills",
    )

    p_skill_search.add_argument("query")

    p_skill_search.add_argument(
        "--path",
        default="skills",
    )

    p_skill_search.set_defaults(func=cmd_skill_search)
    
    
    # ---------------------------------------------------------------
    # scaffold
    # ---------------------------------------------------------------

    p_scaffold = sub.add_parser(
        "scaffold",
        help="Scaffold prompt environment folders",
        description=(
            "Create a standard prompt directory structure "
            "with dev/test/prod/common environments."
        ),
    )

    p_scaffold.add_argument(
        "path",
        nargs="?",
        default="prompts",
        help="Base scaffold directory.",
    )

    p_scaffold.add_argument(
        "--example",
        action="store_true",
        help="Create an example prompt file.",
    )

    p_scaffold.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Allow scaffolding into non-empty directories.",
    )

    p_scaffold.set_defaults(func=cmd_scaffold)

    return parser


# -------------------------------------------------------------------
# main
# -------------------------------------------------------------------


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()