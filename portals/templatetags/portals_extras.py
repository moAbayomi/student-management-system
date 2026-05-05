from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    try:
        return dictionary.get(key) or dictionary.get(str(key)) or dictionary.get(int(key))
    except (ValueError, TypeError):
        return dictionary.get(key)