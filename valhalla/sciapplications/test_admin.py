from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mixer.backend.django import mixer


from valhalla.proposals.models import Semester
from valhalla.sciapplications.models import ScienceApplication, Call, Instrument


class TestSciAppAdmin(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.force_login(self.admin_user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            opens=timezone.now(),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)
        self.apps = mixer.cycle(3).blend(
            ScienceApplication,
            status=ScienceApplication.SUBMITTED,
            submitter=self.user,
            call=self.call,
            tac_rank=(x for x in range(3))
        )

    def test_accept(self):
        self.client.post(
            reverse('admin:sciapplications_scienceapplication_changelist'),
            data={'action': 'accept', '_selected_action': [str(app.pk) for app in self.apps]},
            follow=True
        )
        for app in self.apps:
            self.assertEqual(ScienceApplication.objects.get(pk=app.id).status, ScienceApplication.ACCEPTED)

    def test_reject(self):
        self.client.post(
            reverse('admin:sciapplications_scienceapplication_changelist'),
            data={'action': 'reject', '_selected_action': [str(app.pk) for app in self.apps]},
            follow=True
        )
        for app in self.apps:
            self.assertEqual(ScienceApplication.objects.get(pk=app.id).status, ScienceApplication.REJECTED)

    def test_port(self):
        ScienceApplication.objects.update(status=ScienceApplication.ACCEPTED)
        self.client.post(
            reverse('admin:sciapplications_scienceapplication_changelist'),
            data={'action': 'port', '_selected_action': [str(app.pk) for app in self.apps]},
            follow=True
        )
        for app in self.apps:
            self.assertEqual(ScienceApplication.objects.get(pk=app.id).status, ScienceApplication.PORTED)

    def test_port_duplicate_tac_rank(self):
        ScienceApplication.objects.update(status=ScienceApplication.ACCEPTED, tac_rank=0)
        response = self.client.post(
            reverse('admin:sciapplications_scienceapplication_changelist'),
            data={'action': 'port', '_selected_action': [str(app.pk) for app in self.apps]},
            follow=True
        )
        self.assertContains(response, 'A proposal named LCOGT{}-000 already exists.'.format(self.semester))
