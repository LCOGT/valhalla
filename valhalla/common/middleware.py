import logging

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

        tags = {
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
