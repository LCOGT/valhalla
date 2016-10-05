from django.contrib.sites.shortcuts import get_current_site
from registration.backends.default.views import RegistrationView
from registration.signals import user_registered
from registration.models import RegistrationProfile

from valhalla.accounts.forms import CustomRegistrationForm
from valhalla.accounts.models import Profile
from valhalla.proposals.models import ProposalInvite


class CustomRegistrationView(RegistrationView):
    """
    Custom registration view in order to create and populate the profile object
    """
    form_class = CustomRegistrationForm

    def get_initial(self):
        return {'ptoken': self.request.GET.get('ptoken')}

    def register(self, form):
        site = get_current_site(self.request)

        new_user_instance = form.save()

        ptoken = form.cleaned_data.get('ptoken')
        if ptoken and ProposalInvite.objects.filter(token=ptoken, used=None).exists():
            proposal_invite = ProposalInvite.objects.get(token=ptoken)
            proposal_invite.accept(new_user_instance)

        Profile.objects.create(
            user=new_user_instance,
            title=form.cleaned_data['title'],
            institution=form.cleaned_data['institution']
        )

        new_user = RegistrationProfile.objects.create_inactive_user(
            new_user=new_user_instance,
            site=site,
            send_email=self.SEND_ACTIVATION_EMAIL,
            request=self.request,
        )

        user_registered.send(
            sender=self.__class__,
            user=new_user,
            request=self.request
        )
        return new_user
