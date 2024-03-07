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
    return [tour for tour in tours if depot.id in tour["depot_ids"]]

@register.filter
def depots_by_tour(depots, tour):
    return [depot for depot in depots if depot.id in tour["depot_ids"]]

@register.filter
def depot_index(depot, day_tours):
    for day_tour in day_tours:
        if day_tour["day"]["weekday"] == depot.weekday:
            for depot_index, day_tour_depot in enumerate(day_tour['depots']):
                if depot == day_tour_depot:
                    return depot_index + 1
    return 0

@register.filter
def get_date(weekday, days):
    return [day["date"] for day in days if day['weekday'] == weekday][0]