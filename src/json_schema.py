"""
json_schema.py — JSON Schema for 20 Newsgroups structured extraction.

Extraction task
---------------
From a 20 Newsgroups post fragment (alt.atheism / sci.electronics /
soc.religion.christian) extract seven structured fields.

Fields
------
category          : required enum — which newsgroup
persons           : required array[string] — person names
organizations     : required array[string] — org names
locations         : required array[string] — place / GPE names
dates             : required array[string] — date strings verbatim
has_question      : required boolean — post contains a question?
sentiment         : required enum ["positive","negative","neutral","mixed"]
"""

EXTRACTION_SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "NewsGroupExtractionSchema",
    "description": "Structured extraction output for 20 Newsgroups post fragments",
    "type": "object",
    "required": [
        "category",
        "persons",
        "organizations",
        "locations",
        "dates",
        "has_question",
        "sentiment",
    ],
    "properties": {
        "category": {
            "type": "string",
            "enum": ["sci.electronics", "soc.religion.christian", "alt.atheism"],
            "description": "Newsgroup category the text belongs to",
        },
        "persons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Person names mentioned (empty [] if none)",
        },
        "organizations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Organization names mentioned (empty [] if none)",
        },
        "locations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Location / GPE names mentioned (empty [] if none)",
        },
        "dates": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Date strings found verbatim in text (empty [] if none)",
        },
        "has_question": {
            "type": "boolean",
            "description": "True if the post contains a question, false otherwise",
        },
        "sentiment": {
            "type": "string",
            "enum": ["positive", "negative", "neutral", "mixed"],
            "description": "Overall sentiment / tone of the post",
        },
    },
    "additionalProperties": False,
}


def get_schema() -> dict:
    """Return the extraction schema dict."""
    return EXTRACTION_SCHEMA
