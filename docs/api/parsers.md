# Parsers

**Module:** `promptframe.parsers`

JSON parsing utilities for LLM responses. Standalone — no inference library dependency. Adapted from [LangChain](https://github.com/langchain-ai/langchain) (MIT License).

---

## `json_parser(llm_response_content: str) -> Dict[str, Any]`

Parse a raw LLM string response as JSON. The primary parser for production use.

Handles:
- Plain JSON strings
- JSON wrapped in markdown triple-backtick fences (` ```json ... ``` `)
- Partial/incomplete JSON (missing closing braces or brackets)
- Strings with leading/trailing whitespace

```python
from promptframe.parsers import json_parser

# Plain JSON
result = json_parser('{"name": "Alice", "score": 95}')

# Markdown-fenced
result = json_parser('```json\n{"name": "Alice"}\n```')
```

**Raises:** [`OutputParsingError`](./exceptions.md#outputparsingerror) if the string cannot be parsed as JSON after all recovery attempts.

---

## `parse_json_markdown(json_string: str, *, parser=parse_partial_json) -> dict`

Lower-level function that attempts a direct parse first; if that fails, searches for a ` ```json ` fence block and re-attempts parsing. Accepts a custom `parser` callable for advanced use cases.

---

## `parse_partial_json(s: str, *, strict: bool = False) -> Any`

Parse a JSON string that may be missing closing braces or brackets. Progressively closes open structures until a valid parse is achieved. Useful for handling truncated or streaming LLM responses.

```python
from promptframe.parsers import parse_partial_json

parse_partial_json('{"name": "Alice", "items": [1, 2')
# {"name": "Alice", "items": [1, 2]}

parse_partial_json('{"status": "ok"')
# {"status": "ok"}
```

**Returns:** Parsed Python object, or raises `json.JSONDecodeError` if nothing works.
