---
name: python-expert
description: Best practices for production-quality Python code.
tags:
  - python
  - backend
  - engineering
version: "1.0"
---

## Code Style

Follow PEP 8. Use type hints on all public functions and class attributes.
Prefer `pathlib.Path` over `os.path`. Use f-strings, not `.format()` or `%`.

## Error Handling

Raise specific named exceptions. Never use bare `except:` clauses.
Log errors with full context using the `logging` module.

## Testing

Write tests with `pytest`. Aim for 80%+ coverage on all business logic.
Use `pytest.mark.parametrize` for table-driven tests.

## Performance

Profile before optimising. Use `cProfile` or `py-spy`.
Prefer generators over lists for large data streams.
