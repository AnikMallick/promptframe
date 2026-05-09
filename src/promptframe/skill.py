"""
Skill support — markdown files with YAML frontmatter.

A skill is a reusable, prose-style instruction document.  Unlike YAML prompts
(which are short, parameterised strings), skills are rich markdown documents —
best practices, step-by-step guides, decision frameworks — that get injected
verbatim into a prompt as context.

File conventions supported::

    # Folder-based (preferred — mirrors the /mnt/skills/public/ pattern)
    skills/
      frontend-design/
        SKILL.md
      data-analysis/
        SKILL.md

    # Flat-file
    skills/
      frontend-design.md
      data-analysis.md

Frontmatter schema::

    ---
    name: frontend-design
    description: When to use this skill (shown in SkillRegistry listings).
    tags: [frontend, react, css]
    version: "1.0"
    ---
    ## actual skill content here...

Only ``name`` is required.  Everything else is optional.
"""

from __future__ import annotations

import os
import re
from functools import cached_property
from typing import Any, Dict, List, Optional

import frontmatter


# ---------------------------------------------------------------------------
# Skill model
# ---------------------------------------------------------------------------


class Skill:
    """A loaded skill — frontmatter metadata + markdown body.

    Attributes:
        name: The skill name (from frontmatter, or derived from file name).
        description: What this skill does / when to use it.
        tags: Optional list of tags.
        version: Optional version string.
        content: The raw markdown body — the actual instruction text.
        source_path: Absolute path to the source file.
        extra: Any additional frontmatter keys not listed above.
    """

    def __init__(
        self,
        name: str,
        content: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        version: Optional[str] = None,
        source_path: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.content = content
        self.description = description
        self.tags = tags or []
        self.version = version
        self.source_path = source_path
        self.extra = extra or {}

    @cached_property
    def sections(self) -> Dict[str, str]:
        """Parse top-level markdown ``##`` headings into a dict.

        Allows you to extract just one section of a large skill file::

            skill.sections["Design Thinking"]
            skill.sections["Frontend Aesthetics Guidelines"]
        """
        result: Dict[str, str] = {}
        current_heading: Optional[str] = None
        current_lines: List[str] = []

        for line in self.content.splitlines():
            heading_match = re.match(r"^#{1,3}\s+(.+)", line)
            if heading_match:
                if current_heading is not None:
                    result[current_heading] = "\n".join(current_lines).strip()
                current_heading = heading_match.group(1).strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_heading is not None:
            result[current_heading] = "\n".join(current_lines).strip()
        elif current_lines:
            # Content before the first heading
            result["__preamble__"] = "\n".join(current_lines).strip()

        return result

    def get_section(self, heading: str) -> Optional[str]:
        """Return the content of a specific section, or None if not found."""
        return self.sections.get(heading)

    def render(
        self,
        sections: Optional[List[str]] = None,
        *,
        include_name: bool = True,
    ) -> str:
        """Render the skill to a string for injection into a prompt.

        Args:
            sections: If provided, only include these section headings.
                      Order is preserved as given.
            include_name: Prepend ``## {name}`` heading when True (default).

        Returns:
            The rendered skill content as a plain string.
        """
        if sections:
            parts = []
            for heading in sections:
                body = self.get_section(heading)
                if body:
                    parts.append(f"## {heading}\n{body}")
            body = "\n\n".join(parts)
        else:
            body = self.content

        if include_name:
            return f"## {self.name}\n\n{body}"
        return body

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return (
            f"Skill(name={self.name!r}, "
            f"tags={self.tags}, "
            f"sections={list(self.sections)})"
        )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_skill_from_path(path: str) -> Skill:
    """Parse a single ``.md`` skill file and return a :class:`Skill`.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skill file not found: {path}")

    try:
        post = frontmatter.load(path)
    except Exception as exc:
        raise ValueError(f"Failed to parse skill file '{path}': {exc}") from exc

    meta = dict(post.metadata)
    content = post.content.strip()

    # Derive name from filename if not in frontmatter
    name: str = meta.pop("name", None) or os.path.splitext(
        os.path.basename(path)
    )[0].replace("-", " ").replace("_", " ").title()

    return Skill(
        name=name,
        content=content,
        description=meta.pop("description", None),
        tags=meta.pop("tags", None),
        version=str(meta.pop("version", "")) or None,
        source_path=os.path.abspath(path),
        extra=meta,  # anything else in frontmatter
    )
