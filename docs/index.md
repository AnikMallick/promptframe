# PromptFrame

**LLM-agnostic prompt management** — store prompts as YAML, load them as typed Python objects, attach instructions to Pydantic models for structured output, and compose everything with a fluent builder API.

Works with any LLM — OpenAI, Anthropic, Gemini, LiteLLM, or raw HTTP. Zero inference dependency.

---

## Why PromptFrame?

Most projects start with prompt strings scattered in Python files. As the project grows this becomes painful:

- Prompts hardcoded next to business logic
- No way to update a prompt without a code deploy
- No structure around structured output — parsing is ad-hoc
- Instructions for LLM fields duplicated between code and prompts

PromptFrame solves all of this by giving prompts a **home** (YAML files), a **type** (Pydantic models), and a **bridge** (`model_attribute_id`) that connects field-level instructions in YAML to your Python data structures — without coupling your code to any specific LLM.

---

## Features

<div class="grid cards" markdown>

- :material-file-code: **YAML-first storage**

    Store prompts in structured, versionable YAML files. Use environments (`dev`/`prod`) for overrides.

- :material-type-variant: **Typed loading**

    Every prompt file loads as a Pydantic model. Access prompts as attributes: `p.system_prompt`.

- :material-format-list-bulleted: **Structured output**

    Attach instructions to Pydantic fields with `LLMField`. Generate input and output schemas for any LLM.

- :material-puzzle: **Fluent builder**

    Compose prompts from reusable components using `>>` or `|` operators.

- :material-book-open: **Skills**

    Store reusable markdown instruction documents (`SKILL.md`) and inject them into prompts by section.

- :material-monitor: **Streamlit UI**

    Browse, playground, builder, and skill editor — all in a local web UI.

</div>

---

## Install

```bash
pip install promptframe
```

With Streamlit UI:

```bash
pip install "promptframe[ui]"
```

---

## Quickstart

=== "Prompt management"

    ```yaml title="prompts/my_prompts.yaml"
    version: 1.0
    metadata:
      type: prompt
      name: my_prompts

    prompts:
      - pid: system
        prompt: You are a helpful assistant.

      - pid: summarise
        input_variables: [text, max_sentences]
        prompt: |
          Summarise the following in at most {max_sentences} sentences.
          Text: {text}
    ```

    ```python
    from promptframe import PromptRegistry

    registry = PromptRegistry("prompts/")
    p = registry.load_prompt("my_prompts")

    print(p.system.prompt)
    print(p.summarise.format(text="...", max_sentences=3))
    ```

=== "Structured output"

    ```python
    from promptframe import LLMBaseModel, LLMField, PromptRegistry

    class Invoice(LLMBaseModel):
        total:      float      = LLMField(..., model_attribute_id="invoice_total")
        line_items: list[str]  = LLMField(..., model_attribute_id="invoice_lines")

    registry = PromptRegistry("prompts/")
    mp = registry.load_model_prompt("invoice_prompts")

    # Generate schemas for your LLM call
    input_schema  = Invoice.get_input_instructions_with_prompt(mp.prompt_model_dict)
    output_schema = Invoice.get_format_instructions_with_prompt(mp.prompt_model_dict)

    # Parse LLM response back into the model
    invoice = Invoice(**json_parser(llm_response))
    ```

=== "Builder"

    ```python
    from promptframe import (
        StructuredPromptBuilder,
        SimplePromptComponent,
        PromptSectionComponent,
        SkillComponent,
    )

    prompt = (
        StructuredPromptBuilder()
        >> SimplePromptComponent(p.system)
        >> PromptSectionComponent(
               ["Be concise", "Avoid jargon"],
               header="Rules:",
           )
        >> SkillComponent(skill, sections=["Security"])
        >> SimplePromptComponent("Question: {question}")
    ).build({"question": "What is 2+2?"})
    ```

---

## Project layout

```
promptframe/
├── promptframe/
│   ├── registry.py        # PromptRegistry — YAML loader
│   ├── models.py          # PromptYAML, PromptDataModelYAML, Prompt, …
│   ├── llm_base_model.py  # LLMBaseModel — structured output
│   ├── fields.py          # LLMField — Pydantic Field with LLM metadata
│   ├── builder.py         # StructuredPromptBuilder
│   ├── skill.py           # Skill model + loader
│   ├── skill_registry.py  # SkillRegistry
│   ├── parsers.py         # json_parser, parse_json_markdown
│   ├── exceptions.py      # typed exceptions
│   ├── cli.py             # promptframe CLI
│   └── components/        # all built-in prompt components
└── docs/                  # this documentation
```
