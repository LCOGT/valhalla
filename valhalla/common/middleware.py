import logging
from django.urls import reverse
from django.shortcuts import redirect

from valhalla.accounts.models import Profile


class RequestLogMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('valhalla_request')

    def __call__(self, request):
        response = self.get_response(request)

        try:
            username = request.user.username
            simple_interface = request.user.profile.simple_interface
        except (AttributeError, Profile.DoesNotExist):
            simple_interface = False
            username = 'anonymous'

        forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_ip:
            ip_address = forwarded_ip.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        tags = {
            'ip_address': ip_address,
            'uri': request.path,
            'status': response.status_code,
            'method': request.method,
            'user': username,
            'simple_interface': simple_interface,
        }

        if response.status_code >= 400:
            level = logging.WARN
        else:
            level = logging.INFO

        self.logger.log(level, 'ValhallaRequestLog', extra={'tags': tags})

        return response


class AcceptTermsMiddlware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and \
                not (request.user.is_staff or request.user.is_superuser or 'api' in request.path):
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=request.user, institution='', title='')

            if not profile.terms_accepted and request.path != reverse('accept-terms'):
                return redirect(reverse('accept-terms'))

        return response
