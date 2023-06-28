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
@register.filter
def by_tour(queryset_depots, tour_id):
    # quick and dirty assignment depot_ids to tours, defined here and in depot_list.py
    tour_depots = [[6],
                   [20, 13, 14, 3],
                   [8, 12, 11, 2, 16],
                   [17],
                   [7, 15, 9, 10],
                   [5, 18, 19]]
    depot_ids = tour_depots[tour_id]
    return queryset_depots.filter(id__in=depot_ids)
