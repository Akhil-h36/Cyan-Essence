from django import template
import re

register = template.Library()

@register.filter
def remove_page_param(query_string):
    """Remove page parameter from query string"""
    return re.sub(r'&?page=\d+', '', query_string)

@register.filter(name='get_range')
def get_range(value):
    """
    Filter - returns a list containing range made from given value
    Usage (in template):
    {% for i in totalPages|get_range %}
      {{ i }}
    {% endfor %}
    """
    return range(1, int(value) + 1)