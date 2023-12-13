from django import template

register = template.Library()


@register.filter
def get_attr(value, arg):
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    if hasattr(value, 'get'):
        return value.get(arg)
    return ''

@register.filter
def tours_by_depot(tours, depot):
    return [
        tour
        for tour in tours
        if depot.id in tour['depot_ids']
    ]