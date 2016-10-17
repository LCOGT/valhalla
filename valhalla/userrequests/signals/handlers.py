from django.dispatch import receiver
from django.db.models.signals import pre_save
from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.state_changes import on_request_state_change, on_userrequest_state_change


@receiver(pre_save, sender=UserRequest)
def cb_userrequest_pre_save(sender, instance, *args, **kwargs):
    # instance has the new data, query the model for the current data
    if instance.id:
        # This is an update to the model
        current_data = UserRequest.objects.get(pk=instance.pk)
        on_userrequest_state_change(current_data, instance)


@receiver(pre_save, sender=Request)
def cb_request_pre_save(sender, instance, *args, **kwargs):
    # instance has the new data, query the model for the current data
    if instance.id:
        # This is an update to the model
        current_data = Request.objects.get(pk=instance.pk)
        on_request_state_change(current_data, instance)
