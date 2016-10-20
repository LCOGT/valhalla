from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib import messages

from valhalla.accounts.forms import UserForm


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, _('Profile successfully updated.'))
        return reverse('index')
