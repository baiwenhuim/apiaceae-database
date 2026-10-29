from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    if isinstance(value, str):
        return value.split(key)
    return []

@register.filter
def get_item(value, key):
    # Ensure value is a dictionary and key is treated as a string
    if isinstance(value, dict):
        return value.get(str(key), '')
    return ''

@register.filter(name='or_logic') # Avoid naming it 'or' as it's a reserved keyword
def or_logic(value1, value2):
    return bool(value1) or bool(value2)