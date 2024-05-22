from django import template
from juntagrico.entity.subs import Subscription

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

@register.filter
def by_weekday(queryset_or_sub, weekday_id):
    # case 1: single subscription object is passed
    if isinstance(queryset_or_sub, Subscription):
        return queryset_or_sub if queryset_or_sub.depot.weekday == weekday_id else None
    # case 2: queryset of subscriptions or depots is passed
    if queryset_or_sub.model == Subscription:
        return queryset_or_sub.filter(depot__weekday=weekday_id)
    return queryset_or_sub.filter(weekday=weekday_id)
