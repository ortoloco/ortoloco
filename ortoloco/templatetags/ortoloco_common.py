from django import template
from juntagrico.entity.subs import Subscription
from ortoloco.util.news import get_news_posts
from django.utils.safestring import mark_safe
import datetime

register = template.Library()


@register.filter
def get_attr(value, arg):
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    if hasattr(value, 'get'):
        return value.get(arg)
    return ''

@register.filter
def depots_by_tour(depots, tour):
    return [depot for depot in depots if depot.tour_id == tour.id]

@register.filter
def depot_index(depot, depots):
    tour_depots = depots_by_tour(depots, depot.tour)
    for depot_index, day_tour_depot in enumerate(tour_depots):
        if depot == day_tour_depot:
            return depot_index + 1
    return 0

@register.filter
def get_date(weekday):
    # weekday: Monday is 1 and Sunday is 7
    # datetime.weekday(): Monday is 0 and Sunday is 6
    days = weekday - datetime.date.today().weekday() + 6
    return datetime.date.today() + datetime.timedelta(days=days)

@register.filter
def by_weekday(queryset_or_sub, weekday_id):
    # case 1: single subscription object is passed
    if isinstance(queryset_or_sub, Subscription):
        return queryset_or_sub if queryset_or_sub.depot.weekday == weekday_id else None
    # case 2: queryset of subscriptions or depots is passed
    if queryset_or_sub.model == Subscription:
        return queryset_or_sub.filter(depot__weekday=weekday_id)
    return queryset_or_sub.filter(weekday=weekday_id)

@register.simple_tag
def newstb():
    return mark_safe(get_news_posts(11))
