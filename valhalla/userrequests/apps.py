from django.apps import AppConfig


class UserrequestsConfig(AppConfig):
    name = 'userrequests'

    def ready(self):
        import valhalla.userrequests.signals.handlers
        super().ready()
