from typing import Any, Callable, Dict, List, Set, Tuple, Union, cast, get_args, get_origin, Optional
from functools import lru_cache, wraps
import json
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
    def __unwrap_optional(cls, annotation: Any) -> Any:
        """
        Unwraps `Optional[...]` types (which are actually `Union[T, None]`).
        Returns the type without `None` if it's an Optional type, otherwise returns the original type.
        
        Args:
            annotation (Any): The type annotation to be unwrapped.
        
        Returns:
            Any: The unwrapped type annotation.
        """
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # Check if it's a Union and contains `None` as one of the types.
        if origin is Union and len(args) == 2 and type(None) in args:
            return next(arg for arg in args if arg is not type(None))
        
        return annotation
    
    @classmethod
    def build_input_instruction(
        cls,
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str]] = None,
        prefix: str = "") -> Dict[str, Any]:
        
        def build_instruction(field_name: str, field_type, field_info, path_prefix: str) -> Optional[Dict[str, Any]]:
            full_path = f"{path_prefix}.{field_name}" if path_prefix else field_name
            if ignore and full_path in ignore:
                return None  # Skip this field
            
            metadata = (field_info.json_schema_extra or {})
            if prompt_model_dict: # there is model dict or prompt dict
                model_attribute_id = metadata.get("model_attribute_id")
                if model_attribute_id and prompt_model_dict.get(model_attribute_id) and isinstance(prompt_model_dict[model_attribute_id], PromptDataModel):
                    prompt_data = prompt_model_dict.get(model_attribute_id)
                    if isinstance(prompt_data, PromptDataModel) and prompt_data.input_instruction:
                        metadata["input_instruction"] = prompt_data.input_instruction # updating input instruction from prompt data
            instruction = metadata.get("input_instruction") or field_info.description or ""
            
            # Unwrap optional types here
            field_type = cls.__unwrap_optional(field_type)
            
            # Handle nested structures
            origin = get_origin(field_type)
            args = get_args(field_type)

            fields: Union[List[Dict[str,Any]], Dict[str,Any], None] = None

            if isinstance(field_type, type) and issubclass(field_type, LLMBaseModel):
                fields = (field_type.build_input_instruction(prompt_model_dict=prompt_model_dict, ignore=ignore, prefix=full_path) if field_type 
                            else None)

            elif origin is list and args:
                elem_type = cls.__unwrap_optional(args[0])
                if isinstance(elem_type, type) and issubclass(elem_type, LLMBaseModel):
                    fields = [elem_type.build_input_instruction(prompt_model_dict=prompt_model_dict, ignore=ignore, prefix=full_path)]

            elif origin is dict and args and issubclass(args[1], LLMBaseModel):
                fields ={"<key>": args[1].build_input_instruction(prompt_model_dict=prompt_model_dict, ignore=ignore, prefix=full_path)}
            if fields is None:
                return {
                    "instruction": instruction,
                }
            return {
                "instruction": instruction,
                "fields": fields,
            }

        result = {}
        for field_name, field_info in cls.model_fields.items():
            # value = getattr(self, field_name, None)
            field_type = field_info.annotation
            _insert = build_instruction(field_name, field_type, field_info, prefix)
            if _insert:
                result[field_name] = _insert
        return result

    @classmethod
    @lru_cache(maxsize=32)
    def _get_input_instructions(
        cls, get_dict: bool = False, 
        force: bool = False,
        ignore: Optional[Tuple[str]] = None) -> Union[Dict[str, Any], str]:
        """
        Returns a structured instruction schema for the input model.

        This method generates a schema that provides instructions for each field in the input model, 
        helping to understand how to structure or validate the input data. It uses the model's field-level 
        metadata and descriptions to construct the instructions.

        If `get_dict=True`, the result is returned as a raw dictionary representation.
        If `get_dict=False`, the result is returned as a formatted string with an introductory header.

        The result is cached for performance. If `force=True`, the cache is cleared and the instructions 
        are rebuilt.

        Args:
            get_dict (bool): If True, returns the raw dictionary representation of the input schema.
                             If False, returns a formatted string with an introductory header.
            force (bool): If True, forces the cache to be cleared and rebuilds the input instructions.

        Returns:
            Union[Dict[str, Any], str]: The structured input schema, either as a dictionary or a string 
                                        (formatted with an introduction).
        """
        if force:
            # Force a rebuild by clearing the cache
            cls._get_input_instructions.cache_clear()
        result = cls.build_input_instruction(ignore=ignore)
        if get_dict:
            return result
        return INPUT_INSTRUCTION_INTRO.format(schema = json.dumps(result, indent=2))
    
    @classmethod
    def get_input_instructions(cls, get_dict: bool = False, force: bool = False,
                               ignore: Optional[Tuple[str]] = None) -> Union[Dict[str, Any], str]:
        """
        Retrieves input instructions for the class, either as a dictionary or a string.
        Args:
            get_dict (bool, optional): If True, returns the instructions as a dictionary.
                                        Defaults to False, which returns the instructions as a string.
            force (bool, optional): If True, forces the generation of instructions even if cached.
                                    Defaults to False.
            ignore (Optional[Tuple[str]], optional): A Tuple of keys to ignore when generating instructions.
                                                    Defaults to None.
        Returns:
            Union[Dict[str, Any], str]: The input instructions, either as a dictionary or a string.
        """
        # _ignore: Optional[frozenset[str]] = frozenset(ignore) if ignore else None
        return cls._get_input_instructions(get_dict=get_dict, force=force, ignore=ignore)

    @classmethod
    def get_input_instructions_with_prompt(
        cls, get_dict: bool = False, 
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str]] = None) -> Union[Dict[str, Any], str]:
        """
        Generates input instructions with an optional prompt and returns them either as a dictionary 
        or a formatted string.
        Args:
            get_dict (bool, optional): If True, returns the result as a dictionary. 
                Defaults to False.
            prompt_model_dict (Optional[Dict[str, PromptDataModel]], optional): A dictionary 
                mapping strings to `PromptDataModel` instances, used to build the input instructions. 
                Defaults to None.
            ignore (Optional[Tuple[str]], optional): A Tuple of keys to ignore when building the input 
                instructions. Defaults to None.
        Returns:
            Union[Dict[str, Any], str]: The input instructions, either as a dictionary if `get_dict` 
            is True, or as a formatted string otherwise.
        """
        result = cls.build_input_instruction(prompt_model_dict=prompt_model_dict, ignore=ignore)
        if get_dict:
            return result
        return INPUT_INSTRUCTION_INTRO.format(schema = json.dumps(result, indent=2))
    
    
    @classmethod
    def clean_output_schema(
        cls,
        schema: Dict[str, Any],
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str]] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        def walk(
            obj: Union[Dict[str, Any], List[Any]],
            path_prefix: str = "",
            prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None
        ) -> Union[Dict[str, Any], List[Any]]:
            if isinstance(obj, dict):
                result : Dict[str, Any] = {}
                for k, v in obj.items():
                    full_path = f"{path_prefix}.{k}" if path_prefix else k
                    if ignore and full_path in ignore:
                        continue
                    result [k] = walk(v, path_prefix=full_path, prompt_model_dict=prompt_model_dict)

                if prompt_model_dict and isinstance(prompt_model_dict, dict):
                    model_attribute_id = cast(str, obj.get("model_attribute_id"))
                    if model_attribute_id and prompt_model_dict.get(model_attribute_id) and isinstance(prompt_model_dict[model_attribute_id], PromptDataModel):
                        prompt_data = prompt_model_dict.get(model_attribute_id)
                        if isinstance(prompt_data, PromptDataModel):
                            if prompt_data.output_instruction: 
                                result["output_instruction"] = prompt_data.output_instruction
                            if prompt_data.description:
                                result["description"] = prompt_data.description

                if "output_instruction" in result:
                    result.pop("description", None)
                elif "description" in result:
                    result["output_instruction"] = result.pop("description")

                result.pop("input_instruction", None)
                result.pop("model_attribute_id", None)
                
                return result

            elif isinstance(obj, list):
                return [
                    walk(item, path_prefix=path_prefix, prompt_model_dict=prompt_model_dict)
                    for item in obj
                ]
            return obj

        return walk(schema, path_prefix="", prompt_model_dict=prompt_model_dict)

    @classmethod
    @lru_cache(maxsize=32)
    def _get_format_instructions(cls, get_dict: bool = False, force: bool = False,
                                 ignore: Optional[Tuple[str]] = None,
                                 prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None) -> Union[Dict[str, Any], List[Any], str]:
        """
        Returns a formatted schema that represents the structure and instructions for the output model.

        This method processes the model's JSON schema, cleans it (removes unnecessary metadata), 
        and formats it into a structured output that can be used for understanding how to format 
        the model's outputs.

        If `get_dict=True`, the result is returned as a raw dictionary representation.
        If `get_dict=False`, the result is returned as a string with an introductory header.

        The result is cached for better performance on subsequent calls. If `force=True`, the cache is 
        cleared and the output schema is rebuilt.

        Args:
            get_dict (bool): If True, the method returns a dictionary representation of the schema. 
                             If False, the schema is returned as a formatted string with a header.
            force (bool): If True, forces the cache to be cleared and rebuilds the format instructions.

        Returns:
            Union[Dict[str, Any], str]: The formatted output schema, either as a dictionary or a string.
        """
        if force:
        # Force a rebuild by clearing the cache
            cls._get_format_instructions.cache_clear()
        schema = cls.model_json_schema()
        cleaned_schema = cls.clean_output_schema(schema, prompt_model_dict=prompt_model_dict, ignore=ignore)
        if get_dict:
            return cleaned_schema
        result = json.dumps(cleaned_schema, indent=2)
        result = JSON_FORMAT_INSTRUCTIONS + "\n" +JSON_FORMAT_INSTRUCTIONS_INPUT.format(schema = json.dumps(result, indent=2))
        return result

    @classmethod
    def get_format_instructions(cls, get_dict: bool = False, force: bool = False,
                                ignore: Optional[Tuple[str]] = None) -> Union[Dict[str, Any], List[Any], str]:
        """
        Retrieves format instructions for the class.
        Args:
            get_dict (bool, optional): If True, returns the instructions as a dictionary. 
                                        Defaults to False.
            force (bool, optional): If True, forces the generation of format instructions 
                                    even if they are cached. Defaults to False.
            ignore (Optional[Tuple[str]], optional): A Tuple of keys to ignore when generating 
                                                    the format instructions. Defaults to None.
        Returns:
            Union[Dict[str, Any], List[Any], str]: The format instructions, which can be 
                                                    returned as a dictionary, a list, or a string.
        """
        return cls._get_format_instructions(get_dict=get_dict, force=force, ignore=ignore)

    @classmethod
    def get_format_instructions_with_prompt(
        cls, get_dict: bool = False, 
        prompt_model_dict: Optional[Dict[str, PromptDataModel]] = None,
        ignore: Optional[Tuple[str]] = None) -> Union[Dict[str, Any], List[Any], str]:
        """
        Generates format instructions based on the model's JSON schema, with options to customize the output.

        Args:
            get_dict (bool, optional): If True, returns the cleaned schema as a dictionary. 
                                       Defaults to False.
            prompt_model_dict (Optional[Dict[str, PromptDataModel]], optional): A dictionary mapping 
                prompt model names to their respective `PromptDataModel` instances. Used to customize 
                the schema cleaning process. Defaults to None.
            ignore (Optional[Tuple[str]], optional): A Tuple of keys to ignore during schema cleaning. 
                                                   Defaults to None.

        Returns:
            Union[Dict[str, Any], List[Any], str]: The cleaned schema in one of the following formats:
                - A dictionary, if `get_dict` is True.
                - A JSON-formatted string with additional format instructions, if `get_dict` is False.
        """
        schema = cls.model_json_schema()
        cleaned_schema = cls.clean_output_schema(schema, prompt_model_dict=prompt_model_dict, ignore=ignore)
        if get_dict:
            return cleaned_schema
        result = json.dumps(cleaned_schema, indent=2)
        result = JSON_FORMAT_INSTRUCTIONS + "\n" +JSON_FORMAT_INSTRUCTIONS_INPUT.format(schema = json.dumps(result, indent=2))
        return result

    @classmethod
    def get_llm_schema(cls, get_dict: bool = False) -> Dict[str, Any]:
        """
        Retrieve the schema for the language model (LLM), including input and output instructions.

        Args:
            get_dict (bool, optional): If True, the instructions will be returned as dictionaries.
                                       Defaults to False.

        Returns:
            Dict[str, Any]: A dictionary containing the input and output schema for the LLM.
                            The "input" key maps to the input instructions, and the "output" key
                            maps to the output format instructions.
        """
        return {
            "input": cls.get_input_instructions(get_dict=get_dict),
            "output": cls.get_format_instructions(get_dict=get_dict),
        }

    