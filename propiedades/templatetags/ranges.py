from django import template
register = template.Library()

@register.simple_tag
def num_range(a, b):
    return range(int(a), int(b)+1)
