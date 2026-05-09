from typing import Any, Union
from pydantic import Field
from pydantic.fields import FieldInfo


def LLMField(
    default: Any = ...,
    *,
    description: Union[str, None] = None,
    input_instruction: Union[str, None] = None,
    output_instruction: Union[str, None] = None,
    model_attribute_id: Union[str, None] = None,
    **kwargs
) -> Any:
    """
    Custom Field for LLM metadata
    
    Args:
        default: Default value for the field.
        description: Description of the field.
        input_instruction: Input instruction for the field.
        output_instruction: Output instruction for the field.
        model_attribute_id: Model attribute ID for the field, this will be used to bind prompts from prompt hub - prompt data.
        **kwargs: Additional keyword arguments for Field.
    """
    metadata = {
        "input_instruction": input_instruction,
        "output_instruction": output_instruction,
        "model_attribute_id": model_attribute_id,
    }
    # Merge with user-provided json_schema_extra if needed
    if "json_schema_extra" in kwargs:
        kwargs["json_schema_extra"].update({k: v for k, v in metadata.items() if v is not None})
    else:
        kwargs["json_schema_extra"] = {k: v for k, v in metadata.items() if v is not None}

    return Field(default, description=description, **kwargs)
