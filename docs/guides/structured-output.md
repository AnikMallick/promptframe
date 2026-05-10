# Structured Output

The structured output system is the core feature that separates PromptFrame from a simple YAML loader. It lets you:

1. Define your output schema as a Python class (`LLMBaseModel`)
2. Store per-field instructions in a YAML file (decoupled from code)
3. Generate ready-to-use LLM prompts that describe both input and output
4. Parse the LLM response directly back into your typed Python class

---

## The core idea

```
Python class (structure)  +  YAML file (instructions)  =  LLM prompt
     Invoice                  invoice_prompts.yaml          ↓
     └── total: float    ←── model_attribute_id ──→   "Return as float..."
     └── lines: list[str]←── model_attribute_id ──→   "Return as JSON array..."
```

`model_attribute_id` is the bridge. It's defined on the Python field and matched to a `PromptDataModel` entry in your YAML file at runtime. This means you can update field instructions without touching Python code.

---

## Step 1 — Define your model

Subclass `LLMBaseModel` and annotate fields with `LLMField`:

```python
from promptframe import LLMBaseModel, LLMField

class Invoice(LLMBaseModel):
    vendor:     str        = LLMField(..., model_attribute_id="inv_vendor")
    total:      float      = LLMField(..., model_attribute_id="inv_total")
    date:       str        = LLMField(..., model_attribute_id="inv_date")
    line_items: list[str]  = LLMField(
        default_factory=list,
        model_attribute_id="inv_lines",
    )
```

`LLMField` is a drop-in replacement for Pydantic's `Field`. It accepts all standard `Field` arguments plus:

| Argument | Description |
|---|---|
| `model_attribute_id` | Key used to look up YAML instructions |
| `input_instruction` | Inline instruction (overridden by YAML if both present) |
| `output_instruction` | Inline output instruction |
| `description` | Used as fallback when no instruction is provided |

---

## Step 2 — Write the YAML instructions

```yaml title="prompts/invoice_prompts.yaml"
version: 1.0
metadata:
  type: model_prompt
  name: invoice_prompts

prompts:
  - pid: vendor_field
    model_attribute_id: inv_vendor
    output_instruction: |
      Return the vendor/supplier name as a string.

  - pid: total_field
    model_attribute_id: inv_total
    output_instruction: |
      Return the total amount as a float. Strip any currency symbols.
      "£1,234.56" → 1234.56

  - pid: date_field
    model_attribute_id: inv_date
    input_instruction: |
      The invoice date may be written in various formats.
    output_instruction: |
      Return the date as ISO 8601 string: "YYYY-MM-DD".

  - pid: lines_field
    model_attribute_id: inv_lines
    output_instruction: |
      Return a JSON array of strings. Each string is one line item.
      Example: ["Consulting 2h @ £150 = £300", "Travel = £45"]
```

---

## Step 3 — Generate schemas and call your LLM

```python
from promptframe import PromptRegistry, json_parser

registry = PromptRegistry("prompts/")
mp = registry.load_model_prompt("invoice_prompts")

# Build input instructions (tells LLM what fields mean)
input_schema = Invoice.get_input_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)

# Build output format instructions (tells LLM exactly what to return)
output_schema = Invoice.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)

# Use with any LLM
messages = [
    {"role": "system",  "content": "You are a document extraction assistant."},
    {"role": "user",    "content": input_schema + "\n\n" + invoice_text},
    {"role": "user",    "content": output_schema},
]
```

What did it create:

- input_schema: 

```json
Here is the input data schema with embedded field instructions and metadata:
<input_schema>{
"vendor": {
    "instruction": ""
},
"total": {
    "instruction": ""
},
"date": {
    "instruction": "The invoice date may be written in various formats.\n"
},
"line_items": {
    "instruction": ""
}
}</input_schema>
```

- output_schema

```json
Your response must be a valid JSON parseable object.
This ensures the output can be reliably parsed and used in downstream processes.

Example of a JSON Schema is shown below:
{
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "profile": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["name", "skills"]
        }
      },
      "required": ["id", "profile"]
    }
  },
  "required": ["user"]
}

Valid output:
{
  "user": {
    "id": 123,
    "profile": {
      "name": "Alice",
      "skills": ["Python", "FastAPI"]
    }
  }
}

Your response should be STRICLY formated using this schema:

<format_instructions>{
  "properties": {
    "vendor": {
      "title": "Vendor",
      "type": "string",
      "output_instruction": "Return the vendor/supplier name as a string.\n"
    },
    "total": {
      "title": "Total",
      "type": "number",
      "output_instruction": "Return the total amount as a float. Strip any currency symbols.\n\"\u00a31,234.56\" \u2192 1234.56\n"
    },
    "date": {
      "title": "Date",
      "type": "string",
      "output_instruction": "Return the date as ISO 8601 string: \"YYYY-MM-DD\".\n"
    },
    "line_items": {
      "items": {
        "type": "string"
      },
      "title": "Line Items",
      "type": "array",
      "output_instruction": "Return a JSON array of strings. Each string is one line item.\nExample: [\"Consulting 2h @ \u00a3150 = \u00a3300\", \"Travel = \u00a345\"]"
    }
  },
  "required": [
    "vendor",
    "total",
    "date"
  ],
  "title": "Invoice",
  "type": "object"
}</format_instructions>
```

---

## Step 4 — Parse the response

```python
llm_response = "..."  # raw string from your LLM

# json_parser handles markdown-fenced JSON, partial JSON, etc.
invoice = Invoice(**json_parser(llm_response))

print(invoice.vendor)      # "Acme Corp"
print(invoice.total)       # 1234.56
print(invoice.line_items)  # ["Consulting 2h @ £150 = £300"]
```

---

## Schema methods reference

### `get_format_instructions_with_prompt`

Generates output format instructions combining the Pydantic JSON schema with YAML `output_instruction` values.

```python
# Returns a formatted string ready to paste into a prompt
schema_str = Invoice.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)

# Returns a dict instead
schema_dict = Invoice.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict,
    get_dict=True,
)

# Exclude fields
schema_str = Invoice.get_format_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict,
    ignore=("date",),
)
```

### `get_input_instructions_with_prompt`

Generates input schema instructions with YAML `input_instruction` values injected.

```python
input_str = Invoice.get_input_instructions_with_prompt(
    prompt_model_dict=mp.prompt_model_dict
)
```

### `get_llm_schema`

Returns both input and output schemas in one call.

```python
schemas = Invoice.get_llm_schema(prompt_model_dict=mp.prompt_model_dict)
schemas["input"]   # input instructions
schemas["output"]  # output format instructions
```

### Without YAML (inline instructions only)

If you define instructions directly on `LLMField`, you can call the non-`_with_prompt` variants:

```python
class SimpleModel(LLMBaseModel):
    name: str = LLMField(
        ...,
        output_instruction="Return the full name as a string."
    )

schema = SimpleModel.get_format_instructions()
```

---

## Nested models

Nested `LLMBaseModel` subclasses are walked recursively:

```python
class Address(LLMBaseModel):
    street: str  = LLMField(..., model_attribute_id="addr_street")
    city:   str  = LLMField(..., model_attribute_id="addr_city")

class Person(LLMBaseModel):
    name:    str     = LLMField(..., model_attribute_id="person_name")
    address: Address = LLMField(..., model_attribute_id="person_address")
```

Both `Person` and `Address` model_attribute_ids can be matched from the same `prompt_model_dict`.

---

!!! tip "Caching"
    Schema generation is cached per class when called without `prompt_model_dict`.
    Pass `force=True` to bust the cache after a code change:
    ```python
    Invoice.get_format_instructions(force=True)
    ```
