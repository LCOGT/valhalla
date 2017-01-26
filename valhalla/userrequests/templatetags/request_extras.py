from django import template

register = template.Library()


@register.filter
def state_to_bs(value):
    state_map = {
        'PENDING': 'warning',
        'SCHEDULED': 'info',
        'COMPLETED': 'success',
        'WINDOW_EXPIRED': 'danger',
        'CANCELED': 'danger',
    }
    return state_map[value]


@register.filter
def state_to_icon(value):
    state_map = {
        'PENDING': 'refresh',
        'SCHEDULED': 'refresh',
        'COMPLETED': 'check',
        'WINDOW_EXPIRED': 'times',
        'CANCELED': 'times',
    }
    return state_map[value]


@register.filter
def request_state_count(userrequest, state):
    return userrequest.requests.filter(state=state).count()
