from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def detailed_user_information(email):
    if not User.objects.filter(email=email).exists():
        return email
    else:
        u = User.objects.get(email=email)
        return '{0} {1} <{2}> ({3})'.format(u.first_name, u.last_name, u.email, u.profile.institution)
