"""
JSON parsing utilities — standalone, no inference-library dependency.

Adapted from the LangChain project (MIT License):
https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/utils/json.py
"""

from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Callable, Dict

from .exceptions import OutputParsingError

# Low-level helpers

def _replace_new_line(match: re.Match[str]) -> str:
    value = match.group(2)
    value = re.sub(r"\n", r"\\n", value)
    value = re.sub(r"\r", r"\\r", value)
    value = re.sub(r"\t", r"\\t", value)
    value = re.sub(r'(?<!\\)"', r"\"", value)
    return match.group(1) + value + match.group(3)


def _custom_parser(s: str) -> str:
    if isinstance(s, (bytes, bytearray)):
        s = s.decode()
    return re.sub(
        r'("action_input"\:\s*")(.*?)(")',
        _replace_new_line,
        s,
        flags=re.DOTALL,
    )


def parse_partial_json(s: str, *, strict: bool = False) -> Any:
    """Parse a JSON string that may be missing closing braces/brackets.

    Attempts a full parse first, then progressively closes open structures
    until a valid parse is achieved.

    Returns:
        Parsed Python object, or raises :class:`json.JSONDecodeError` if
        nothing works.
    """
    try:
        return json.loads(s, strict=strict)
    except JSONDecodeError:
        pass

    new_chars: list[str] = []
    stack: list[str] = []
    is_inside_string = False
    escaped = False

    for char in s:
        new_char = char
        if is_inside_string:
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                new_char = "\\n"
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        elif char == '"':
            is_inside_string = True
            escaped = False
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in {"}", "]"}:
            if stack and stack[-1] == char:
                stack.pop()
            else:
                return None
        new_chars.append(new_char)

    if is_inside_string:
        if escaped:
            new_chars.pop()
        new_chars.append('"')

    stack.reverse()
    while new_chars:
        try:
            return json.loads("".join(new_chars + stack), strict=strict)
        except JSONDecodeError:
            new_chars.pop()

    return json.loads(s, strict=strict)


_json_markdown_re = re.compile(r"```(json)?(.*)", re.DOTALL)
_json_strip_chars = " \n\r\t`"


def parse_json_markdown(
    json_string: str,
    *,
    parser: Callable[[str], Any] = parse_partial_json,
) -> dict:
    """Extract and parse a JSON object from a Markdown-fenced string.

    Handles both plain JSON and triple-backtick fenced blocks.
    """
    try:
        return _parse_json(json_string, parser=parser)
    except JSONDecodeError:
        match = _json_markdown_re.search(json_string)
        json_str = json_string if match is None else match.group(2)
    return _parse_json(json_str, parser=parser)


def _parse_json(
    json_str: str,
    *,
    parser: Callable[[str], Any] = parse_partial_json,
) -> dict:
    json_str = json_str.strip(_json_strip_chars)
    json_str = _custom_parser(json_str)
    return parser(json_str)

# Public parsers

def json_parser(llm_response_content: str) -> Dict[str, Any]:
    """Parse a raw LLM string response as JSON.

    Args:
        llm_response_content: The string to parse.

    Returns:
        Parsed dict.

    Raises:
        OutputParsingError: If the string cannot be parsed as JSON.
    """
    text = llm_response_content.strip()
    try:
        return parse_json_markdown(text)
    except JSONDecodeError as exc:
        raise OutputParsingError(response=text) from exc
