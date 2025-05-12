from django import template
import json

register = template.Library()

@register.filter
def parse_json(json_string):
    """
    Parse a JSON string into a Python dictionary
    Usage: {{ json_string|parse_json }}
    """
    try:
        return json.loads(json_string)
    except (ValueError, TypeError):
        return {}