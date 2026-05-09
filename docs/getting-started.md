# Getting Started

## Installation

```bash
pip install promptframe
```

For the Streamlit UI:

```bash
pip install "promptframe[ui]"
```

**Requirements:** Python 3.11+

---

## Your first prompt file

Use the CLI to scaffold a new YAML file:

```bash
promptframe init regular prompts/my_prompts.yaml
```

Or create it manually:

```yaml title="prompts/my_prompts.yaml"
version: 1.0
metadata:
  type: prompt
  name: my_prompts
  description: My first prompt collection.

prompts:
  - pid: system
    description: System prompt for the assistant.
    prompt: You are a helpful, concise assistant.

  - pid: answer_question
    description: Answer a user question.
    input_variables: [question]
    prompt: |
      Answer the following question clearly and concisely.

      Question: {question}
```

!!! tip "pid naming"
    `pid` (prompt ID) must be unique within a file. Use snake_case —
    it becomes the attribute name on the loaded model.

---

## Loading prompts

```python
from promptframe import PromptRegistry

registry = PromptRegistry("prompts/")
p = registry.load_prompt("my_prompts")
```

`p` is a Pydantic model. Each prompt is accessible as an attribute:

```python
# Attribute access
print(p.system.prompt)
# → "You are a helpful, concise assistant."

# Format with variables
rendered = p.answer_question.format(question="What is 2+2?")

# Dict access (useful when pid is dynamic)
rendered = p.prompt_dict["answer_question"].format(question="What is 2+2?")
```

---

## Using with an LLM

promptframe is LLM-agnostic — it builds strings, nothing more. Here's the pattern with any client:

=== "OpenAI"

    ```python
    from openai import OpenAI
    from promptframe import PromptRegistry

    registry = PromptRegistry("prompts/")
    p = registry.load_prompt("my_prompts")

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",  "content": p.system.prompt},
            {"role": "user",    "content": p.answer_question.format(question="What is 2+2?")},
        ],
    )
    ```

=== "Anthropic"

    ```python
    import anthropic
    from promptframe import PromptRegistry

    registry = PromptRegistry("prompts/")
    p = registry.load_prompt("my_prompts")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        system=p.system.prompt,
        messages=[{"role": "user", "content": p.answer_question.format(question="What is 2+2?")}],
        max_tokens=1024,
    )
    ```

=== "LiteLLM"

    ```python
    import litellm
    from promptframe import PromptRegistry

    registry = PromptRegistry("prompts/")
    p = registry.load_prompt("my_prompts")

    response = litellm.completion(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": p.system.prompt},
            {"role": "user",   "content": p.answer_question.format(question="What is 2+2?")},
        ],
    )
    ```

---

## Next steps

<div class="grid cards" markdown>

- [:material-file-document: **Prompt Management**](guides/prompt-management.md)

    Full YAML schema, environments, model prompts.

- [:material-format-list-bulleted: **Structured Output**](guides/structured-output.md)

    `LLMBaseModel`, `LLMField`, schema generation.

- [:material-book-open: **Skills**](guides/skills.md)

    Reusable markdown instruction documents.

- [:material-puzzle: **Prompt Builder**](guides/builder.md)

    Composing prompts from components.

</div>
