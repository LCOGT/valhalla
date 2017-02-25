from django.apps import AppConfig


class UserrequestsConfig(AppConfig):
    name = 'valhalla.userrequests'

    def ready(self):
        import valhalla.userrequests.signals.handlers  # noqa
        super().ready()
