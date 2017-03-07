from __future__ import absolute_import, unicode_literals
from celery import shared_task

from valhalla.proposals.accounting import perform_accounting


@shared_task
def run_accounting():
    perform_accounting()
