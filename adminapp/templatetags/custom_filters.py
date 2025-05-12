from django import template

register = template.Library()

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