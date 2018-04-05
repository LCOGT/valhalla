from django import template

register = template.Library()


@register.simple_tag
def time_requested_by_tag(tag, semester):
    return tag.time_requested_for_semester(semester)
