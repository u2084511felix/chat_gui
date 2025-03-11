from utils.models.openai_config import Generate, TextModels, create_generator_module
import json
import os
import inspect


def get_caller_script_dir():
    stack = inspect.stack()

    for frame in reversed(stack):
        caller_file = frame.filename
        if "modules.py" not in caller_file:
            return os.path.dirname(os.path.abspath(caller_file))

    return os.getcwd()


def save_json_file(data, file_name):
    """Saves JSON in the same directory as the script that originally called modules.py."""
    caller_dir = get_caller_script_dir()
    os.makedirs(caller_dir, exist_ok=True)
    file_path = os.path.join(caller_dir, file_name)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"File saved to: {file_path}")


async def legacy_structured_output(prompt, schema):
    system_message = "Supply the function variables for the given function according to the instruction."

    LegacyStructuredOutput = Generate()
    new_schema = json.loads(schema)

    function_name = new_schema.get("name")
    LegacyStructuredOutput.tool_choice = {
        "type": "function", "function": {"name": function_name}}

    LegacyStructuredOutput.tools = [
        {
            "type": "function",
            "function": new_schema
        }
    ]

    legacy_structured_output = await LegacyStructuredOutput.function_call_legacy_structured_output(system_message, prompt)

    legacy_structured_output = legacy_structured_output[0].function.arguments
    output_json = json.loads(legacy_structured_output)
    save_json_file(output_json, "finaloutput.json")
    return legacy_structured_output


async def generate_legacy_structured_output_schema(json_object):

    transforn_prompt = "Transform this JSON object: " + str(json_object)
    SchemaGenerator = Generate()

    sys_msg = f"""Generate a JSON schema for the given instruction converting from an existing data outline, using the function."""

    SchemaGenerator.tools = [
        {
            "type": "function",
            "function": {
                "name": "Tool_Schema",
                "description": "Schema for generating tool schemas. Do not use $ref in the schema. Use the 'type' and 'properties' fields to define the schema.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"
                        },
                        "description": {
                            "type": "string"
                        },
                        "parameters": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string"
                                        },
                                        "properties": {
                                            "type": "object",
                                            "enum": [],
                                            "additionalProperties": False
                                        },
                                        "required": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["type", "properties", "required"],
                                    "additionalProperties": False
                                }
                            ]
                        }
                    },
                    "required": ["name", "description", "parameters"]
                }
            }
        }
    ]

    SchemaGenerator.tool_choice = {
        "type": "function", "function": {"name": "Tool_Schema"}}

    generated_schema = await SchemaGenerator.function_call_legacy_structured_output(sys_msg, transforn_prompt)

    generated_schema = generated_schema[0].function.arguments
    output_json = json.loads(generated_schema)
    save_json_file(output_json, "schema_output.json")

    return generated_schema


async def generate_structured_output_schema(json_object):

    transforn_prompt = "Transform this JSON object: " + str(json_object)
    SchemaGenerator = Generate()

    sys_msg = f"""Generate a JSON schema for the given instruction converting from an existing data outline, using the function."""

    SchemaGenerator.tools = [
        {
            "type": "function",
            "function": {
                "name": "Tool_Schema",
                "description": "Schema for generating schemas from a draft json model. The first 'name' parameter, should relate to the content model, and the 'description' parameter should describe the purpose of the content model. The 'schema' parameter should produce named objects that define a valid schema for the content model. Each parameter in the content model should be under a named object in the 'schema' parameter. All name properties must be single word which matches the pattern: '^[a-zA-Z0-9_-]+$'. The 'schema' object should output schema objects with a maximum nesting level of 5. Any objects inside of named schema objects should contain a required array listing all required elements in the object and 'additionalProperties' = 'false'. Likewise any arrays in named schema objects",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"
                        },
                        "description": {
                            "type": "string"
                        },
                        "schema": {
                            "type": "object",
                            "description": "schema object containing named schema objects that define each property the content model schema. Maximum nesting of 5 for each named schema object",
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string"
                                        },
                                        "properties": {
                                            "oneOf": [
                                                {
                                                    "name": {
                                                        "decription": "The named schema object for one element of the content model. Maximum nesting of 5.",
                                                        "type": "object",
                                                        "oneOf": [
                                                            {
                                                                "type": "object",
                                                                "properties": {
                                                                    "description": {
                                                                        "type": "string",
                                                                        "description": "the description of the named schema object"
                                                                    },
                                                                    "type": {
                                                                        "description": "the type of an element in a named schmea object",
                                                                        "type": "string",
                                                                        "enum": ["string", "number", "boolean", "integer", "object", "array"]
                                                                    },
                                                                    "properties": {
                                                                        "type": "object",
                                                                        "enum": [],
                                                                        "additionalProperties": False
                                                                    },
                                                                    "required": {
                                                                        "type": "array",
                                                                        "items": {
                                                                            "type": "string"
                                                                        }
                                                                    }
                                                                },
                                                                "required": ["description", "type"],
                                                                "additionalProperties": False
                                                            }
                                                        ],
                                                    }
                                                }
                                            ]
                                        },
                                        "required": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["type", "properties", "required"],
                                    "additionalProperties": False
                                }

                            ]
                        }

                    },
                    "required": ["name", "description", "schema"]
                }
            }
        }
    ]

    SchemaGenerator.tool_choice = {
        "type": "function", "function": {"name": "Tool_Schema"}}

    generated_schema = await SchemaGenerator.function_call_legacy_structured_output(sys_msg, transforn_prompt)

    generated_schema = generated_schema[0].function.arguments
    output_json = json.loads(generated_schema)
    save_json_file(output_json, "schema_output.json")

    return generated_schema


async def structured_outputs_generator(transforn_prompt, schema):

    module = create_generator_module(max_tokens=2000)
    sys_msg = f"""Generate a JSON schema for the given content model."""

    response = await module.structured_output(sys_msg, transforn_prompt, schema)
    return response
