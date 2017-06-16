from django.dispatch import receiver
from django.db.models.signals import pre_save
from valhalla.proposals.models import TimeAllocation


@receiver(pre_save, sender=TimeAllocation)
def set_default_ipp_time(sender, instance, *args, **kwargs):
    ''' Sets default IPP values if none are given at creation'''
    if not instance.id:
        if not instance.ipp_limit:
            instance.ipp_limit = instance.std_allocation / 10
        if not instance.ipp_time_available:
            instance.ipp_time_available = instance.std_allocation / 20
