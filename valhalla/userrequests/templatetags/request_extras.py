from django import template

register = template.Library()


@register.filter
def state_to_bs(value):
    state_map = {
        'PENDING': 'warning',
        'SCHEDULED': '',
        'COMPLETED': 'success',
        'WINDOW_EXPIRED': 'danger',
        'CANCELED': 'danger',
    }
    return state_map[value]
