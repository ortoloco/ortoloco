from django import template

register = template.Library()


@register.filter
def get_attr(value, arg):
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'get'):
        return value.get(arg)
    else:
        ''
