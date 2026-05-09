from __future__ import annotations

import json
import types as _types
from functools import lru_cache
from typing import (
    Any, Dict, List, Optional,
    Tuple, Union, cast, get_args, get_origin,
)

from pydantic import BaseModel

from .models import PromptDataModel

# You are given a structured JSON object that represents example input data for a model.

# Each key in the object corresponds to a field in the model. The purpose is to help understand the structure and meaning of each field using field-level instructions.

# For each field:
# - `"instruction"` describes the current field, and metadata of that field.
# - `"fields"` is included only if the value is a nested object or a list/dictionary of such objects.

# This format helps understand the expected structure and meaning of each field, even in nested models.

INPUT_INSTRUCTION_INTRO = """
Here is the input data schema with embedded field instructions and metadata:
<input_schema>{schema}</input_schema>
"""

JSON_FORMAT_INSTRUCTIONS = """Your response must be a valid JSON parseable object.
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
"""
JSON_FORMAT_INSTRUCTIONS_INPUT = "<format_instructions>{schema}</format_instructions>"


class LLMBaseModel(BaseModel):
    """LLMBaseModel is a base class designed to provide structured input and output instructions for language models. 
    It extends the functionality of Pydantic's BaseModel to include methods for generating and managing schema 
    instructions, handling nested structures, and integrating prompt-based metadata.
    Key Features:
    - **Input Instruction Generation**: Methods to build structured input instructions based on field metadata, 
        descriptions, and optional prompt-based data.
    - **Output Schema Cleaning**: Methods to clean and format the output schema by removing unnecessary metadata 
        and integrating prompt-based instructions.
    - **Caching for Performance**: Utilizes caching to optimize repeated calls for generating input and output 
        instructions.
    - **Support for Nested Models**: Handles nested structures and models that extend LLMBaseModel, ensuring 
        recursive generation of instructions.
    Methods:
    - `__unwrap_optional`: Unwraps `Optional` types to extract the underlying type.
    - `build_input_instruction`: Constructs input instructions for the model fields, supporting nested models 
        and prompt-based metadata.
    - `get_input_instructions`: Public interface to retrieve input instructions, either as a dictionary or a 
        formatted string.
    - `get_input_instructions_with_prompt`: Retrieves input instructions with additional prompt-based metadata.
    - `clean_output_schema`: Cleans and formats the output schema, integrating prompt-based instructions and 
        removing unnecessary metadata.
    - `get_format_instructions`: Public interface to retrieve output format instructions, either as a dictionary 
        or a formatted string.
    - `get_format_instructions_with_prompt`: Retrieves output format instructions with additional prompt-based 
        metadata.
    - `get_llm_schema`: Combines input and output instructions into a single schema.
    Attributes:
    - `INPUT_INSTRUCTION_INTRO`: A formatted string used as an introductory header for input instructions.
    - `JSON_FORMAT_INSTRUCTIONS`: A formatted string used as an introductory header for output format instructions.
    - `JSON_FORMAT_INSTRUCTIONS_INPUT`: A formatted string template for output format instructions.
    Usage:
    This class is intended to be extended by specific models that require structured input and output instructions. 
    It provides a robust framework for managing schema metadata and integrating prompt-based enhancements."""
    
    @classmethod
    def _unwrap_optional(cls, annotation: Any) -> Any:
        """Strip ``Optional[T]`` / ``Union[T, None]`` / ``T | None`` down to ``T``.

        Handles both the legacy ``typing.Union`` form and the Python 3.10+
        ``types.UnionType`` (``str | None``) form.
        """
        # typing.Optional[T] / typing.Union[T, None]
        origin = get_origin(annotation)
        if origin is Union:
            args = get_args(annotation)
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
            return annotation

        # Python 3.10+  str | None  →  types.UnionType
        if hasattr(_types, "UnionType") and isinstance(annotation, _types.UnionType):
            args = get_args(annotation)
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]

        return annotation
    
    @classmethod
    def _resolve_refs(cls, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Inline all ``$ref`` references so the schema is a flat field tree.

        This lets ``clean_output_schema`` walk by field-name paths rather than
        raw JSON-schema structural paths (``$defs``, ``properties``, etc.).
        Circular references are detected and left as an empty object to avoid
        infinite recursion.
        """
        defs = schema.get("$defs", {})

        def resolve(obj: Any, seen: frozenset = frozenset()) -> Any:
            if isinstance(obj, list):
                return [resolve(item, seen) for item in obj]
            if not isinstance(obj, dict):
                return obj

            if "$ref" in obj:
                ref_name = obj["$ref"].rsplit("/", 1)[-1]
                if ref_name in seen:
                    # Circular reference — keep any extra keys, drop the $ref
                    return {k: resolve(v, seen) for k, v in obj.items() if k != "$ref"}
                if ref_name in defs:
                    # Inline the definition and merge any extra sibling keys
                    # (e.g. model_attribute_id sits alongside $ref in Pydantic v2)
                    inlined = resolve(dict(defs[ref_name]), seen | {ref_name})
                    extras  = {k: resolve(v, seen) for k, v in obj.items() if k != "$ref"}
                    return {**inlined, **extras}
                # Unknown $ref — leave as-is
                return {k: resolve(v, seen) for k, v in obj.items()}

            return {k: resolve(v, seen) for k, v in obj.items()}

        # Resolve everything except $defs itself (no longer needed after inlining)
        return {k: resolve(v) for k, v in schema.items() if k != "$defs"}
    
    @classmethod
    def build_input_instruction(
        cls,
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str, ...]] = None,
        prefix: str = "",
    ) -> Dict[str, Any]:
        """Walk model fields and build a per-field instruction dict.

        Instructions come from (in priority order):

        1. ``input_instruction`` in the matching ``PromptDataModel`` (via
           ``model_attribute_id``).
        2. ``input_instruction`` stored directly on the ``LLMField``.
        3. The field's ``description``.

        Args:
            prompt_model_dict: ``{model_attribute_id: PromptDataModel}`` mapping.
            ignore: Dot-notation field paths to exclude, e.g. ``("vendor",
                "address.city")``.
            prefix: Internal — used for recursive nested-model calls.
        """

        def build_field(
            field_name: str,
            field_type: Any,
            field_info: Any,
            path_prefix: str,
        ) -> Optional[Dict[str, Any]]:
            full_path = f"{path_prefix}.{field_name}" if path_prefix else field_name
            if ignore and full_path in ignore:
                return None

            metadata: Dict[str, Any] = dict(field_info.json_schema_extra or {})

            # Inject instruction from YAML if available
            if prompt_model_dict:
                attr_id = metadata.get("model_attribute_id")
                if attr_id:
                    pd = prompt_model_dict.get(attr_id)
                    if isinstance(pd, PromptDataModel) and pd.input_instruction:
                        metadata["input_instruction"] = pd.input_instruction

            instruction = (
                metadata.get("input_instruction")
                or field_info.description
                or ""
            )

            field_type = cls._unwrap_optional(field_type)
            origin     = get_origin(field_type)
            args       = get_args(field_type)
            fields: Union[List[Any], Dict[str, Any], None] = None

            if isinstance(field_type, type) and issubclass(field_type, LLMBaseModel):
                fields = field_type.build_input_instruction(
                    prompt_model_dict=prompt_model_dict,
                    ignore=ignore,
                    prefix=full_path,
                )
            elif origin is list and args:
                elem = cls._unwrap_optional(args[0])
                if isinstance(elem, type) and issubclass(elem, LLMBaseModel):
                    fields = [
                        elem.build_input_instruction(
                            prompt_model_dict=prompt_model_dict,
                            ignore=ignore,
                            prefix=full_path,
                        )
                    ]
            elif (
                origin is dict
                and len(args) >= 2
                and isinstance(args[1], type)
                and issubclass(args[1], LLMBaseModel)
            ):
                fields = {
                    "<key>": args[1].build_input_instruction(
                        prompt_model_dict=prompt_model_dict,
                        ignore=ignore,
                        prefix=full_path,
                    )
                }

            return (
                {"instruction": instruction, "fields": fields}
                if fields is not None
                else {"instruction": instruction}
            )

        result: Dict[str, Any] = {}
        for field_name, field_info in cls.model_fields.items():
            entry = build_field(field_name, field_info.annotation, field_info, prefix)
            if entry is not None:
                result[field_name] = entry
        return result

    
    @classmethod
    @lru_cache(maxsize=32)
    def _get_input_instructions_cached(
        cls,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Dict[str, Any]:
        """Cached version without prompt injection (dict is not hashable)."""
        return cls.build_input_instruction(ignore=ignore)
    
    @classmethod
    def get_input_instructions(
        cls,
        get_dict: bool = False,
        force: bool = False,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Union[Dict[str, Any], str]:
        """Return input instructions without YAML prompt injection.

        Args:
            get_dict: Return raw dict instead of a formatted string.
            force: Clear the cache and rebuild.
            ignore: Dot-notation field paths to exclude, e.g. ``("vendor",)``.
        """
        if force:
            cls._get_input_instructions_cached.cache_clear()
        result = cls._get_input_instructions_cached(ignore=ignore)
        if get_dict:
            return result
        return INPUT_INSTRUCTION_INTRO.format(schema=json.dumps(result, indent=2))

    @classmethod
    def get_input_instructions_with_prompt(
        cls,
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        get_dict: bool = False,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Union[Dict[str, Any], str]:
        """Return input instructions with YAML ``input_instruction`` values injected.

        Args:
            prompt_model_dict: ``{model_attribute_id: PromptDataModel}`` mapping,
                typically from ``registry.load_model_prompt(...).prompt_model_dict``.
            get_dict: Return raw dict instead of a formatted string.
            ignore: Dot-notation field paths to exclude.
        """
        result = cls.build_input_instruction(
            prompt_model_dict=prompt_model_dict, ignore=ignore
        )
        if get_dict:
            return result
        return INPUT_INSTRUCTION_INTRO.format(schema=json.dumps(result, indent=2))
    
    
    @classmethod
    def clean_output_schema(
        cls,
        schema: Dict[str, Any],
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Dict[str, Any]:
        """Walk the Pydantic JSON schema and produce a clean output schema.

        Steps:

        1. Resolve all ``$ref`` / ``$defs`` inline so the schema is a flat
           field tree (enables consistent field-path-based ``ignore`` matching).
        2. For each field that carries a ``model_attribute_id``, inject the
           matching ``output_instruction`` (and optionally ``description``) from
           *prompt_model_dict*.
        3. Promote bare ``description`` → ``output_instruction`` when no
           explicit instruction exists.
        4. Strip internal-only keys (``input_instruction``, ``model_attribute_id``).

        ``ignore`` uses dot-notation field paths consistent with
        :meth:`build_input_instruction`, e.g. ``("vendor", "address.city")``.
        """
        # Inline $refs so we can walk by field names, not schema structure paths
        schema = cls._resolve_refs(schema)
        ignore_set = set(ignore) if ignore else set()

        def walk(obj: Any, field_path: str = "") -> Any:
            if isinstance(obj, list):
                return [walk(item, field_path) for item in obj]
            if not isinstance(obj, dict):
                return obj

            result: Dict[str, Any] = {}
            for k, v in obj.items():
                if k == "properties" and isinstance(v, dict):
                    # Each key is a field name — build field-name paths here
                    walked: Dict[str, Any] = {}
                    for fname, fschema in v.items():
                        child_path = f"{field_path}.{fname}" if field_path else fname
                        if child_path in ignore_set:
                            continue
                        walked[fname] = walk(fschema, child_path)
                    result[k] = walked
                else:
                    result[k] = walk(v, field_path)

            # Inject YAML output_instruction if this node has model_attribute_id
            if prompt_model_dict:
                attr_id = obj.get("model_attribute_id")
                if attr_id:
                    pd = prompt_model_dict.get(cast(str, attr_id))
                    if isinstance(pd, PromptDataModel):
                        if pd.output_instruction:
                            result["output_instruction"] = pd.output_instruction
                        if pd.description:
                            result["description"] = pd.description

            # Promote description → output_instruction when no explicit instruction
            if "output_instruction" in result:
                result.pop("description", None)
            elif "description" in result:
                result["output_instruction"] = result.pop("description")

            # Strip keys that are only meaningful internally
            result.pop("input_instruction", None)
            result.pop("model_attribute_id", None)

            return result

        return walk(schema)
    
    @classmethod
    @lru_cache(maxsize=32)
    def _get_format_instructions_cached(
        cls,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Dict[str, Any]:
        """Cached base schema without prompt injection."""
        schema = cls.model_json_schema()
        return cls.clean_output_schema(schema, ignore=ignore)

    @classmethod
    def get_format_instructions(
        cls,
        get_dict: bool = False,
        force: bool = False,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Union[Dict[str, Any], str]:
        """Return output format instructions without YAML prompt injection.

        Args:
            get_dict: Return raw dict instead of a formatted string.
            force: Clear the cache and rebuild.
            ignore: Dot-notation field paths to exclude.
        """
        if force:
            cls._get_format_instructions_cached.cache_clear()
        cleaned = cls._get_format_instructions_cached(ignore=ignore)
        if get_dict:
            return cleaned
        return (
            JSON_FORMAT_INSTRUCTIONS
            + "\n"
            + JSON_FORMAT_INSTRUCTIONS_INPUT.format(
                schema=json.dumps(cleaned, indent=2)  # single encode — BUG FIX
            )
        )

    @classmethod
    def get_format_instructions_with_prompt(
        cls,
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        get_dict: bool = False,
        ignore: Optional[Tuple[str, ...]] = None,
    ) -> Union[Dict[str, Any], str]:
        """Return output format instructions with YAML ``output_instruction`` injected.

        This is the primary method for structured output — it combines the
        Pydantic JSON schema with per-field instructions from your YAML file.

        Args:
            prompt_model_dict: ``{model_attribute_id: PromptDataModel}`` mapping,
                typically from ``registry.load_model_prompt(...).prompt_model_dict``.
            get_dict: Return raw dict instead of a formatted string.
            ignore: Dot-notation field paths to exclude.
        """
        schema  = cls.model_json_schema()
        cleaned = cls.clean_output_schema(
            schema, prompt_model_dict=prompt_model_dict, ignore=ignore
        )
        if get_dict:
            return cleaned
        return (
            JSON_FORMAT_INSTRUCTIONS
            + "\n"
            + JSON_FORMAT_INSTRUCTIONS_INPUT.format(
                schema=json.dumps(cleaned, indent=2)  # single encode — BUG FIX
            )
        )

    @classmethod
    def get_llm_schema(
        cls,
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        get_dict: bool = False,
    ) -> Dict[str, Any]:
        """Return both input and output schemas in one call.

        Returns:
            ``{"input": ..., "output": ...}``
        """
        return {
            "input": cls.get_input_instructions_with_prompt(
                prompt_model_dict=prompt_model_dict, get_dict=get_dict
            ),
            "output": cls.get_format_instructions_with_prompt(
                prompt_model_dict=prompt_model_dict, get_dict=get_dict
            ),
        }

    