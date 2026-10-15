"""Strict JSON schemas for model responses."""

LABEL_SCHEMA = {
    "type": "string",
    "enum": ["entailment", "neutral", "contradiction"],
}

TASK_A_SCHEMA = {
    "type": "object",
    "properties": {
        "label": LABEL_SCHEMA,
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["page", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["label", "evidence"],
    "additionalProperties": False,
    "anyOf": [
        {
            "properties": {
                "label": {"type": "string", "enum": ["neutral"]},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer"},
                            "text": {"type": "string"},
                        },
                        "required": ["page", "text"],
                        "additionalProperties": False,
                    },
                    "maxItems": 0,
                },
            },
            "required": ["label", "evidence"],
            "additionalProperties": False,
        },
        {
            "properties": {
                "label": {
                    "type": "string",
                    "enum": ["entailment", "contradiction"],
                },
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer"},
                            "text": {"type": "string", "maxLength": 4500},
                        },
                        "required": ["page", "text"],
                        "additionalProperties": False,
                    },
                    "minItems": 1,
                    "maxItems": 4,
                },
            },
            "required": ["label", "evidence"],
            "additionalProperties": False,
        },
    ],
}

TASK_B_SCHEMA = {
    "type": "object",
    "properties": {
        "label": LABEL_SCHEMA,
        "evidence": {"type": "null"},
    },
    "required": ["label", "evidence"],
    "additionalProperties": False,
}


def response_format(schema: dict, name: str) -> dict:
    """Build the OpenAI-compatible Structured Outputs configuration."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema,
        },
    }
