from django.apps import AppConfig


class ProposalsConfig(AppConfig):
    name = 'valhalla.proposals'

    def ready(self):
        import valhalla.proposals.signals.handlers  # noqa
        super().ready()
