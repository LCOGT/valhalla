from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from mixer.backend.django import mixer


from valhalla.proposals.models import Semester
from valhalla.sciapplications.models import ScienceApplication, Call, Instrument
from valhalla.sciapplications.forms import ScienceProposalAppForm, DDTProposalAppForm, KeyProjectAppForm


class TestGetCreateSciApp(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        user = mixer.blend(User)
        self.client.force_login(user)

    def test_no_semester(self):
        response = self.client.get(
            reverse('sciapplications:create', kwargs={
                'semester': 'notasemester',
                'type': 'SCI'}
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_wrong_type(self):

        mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )

        response = self.client.get(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': 'KEY'}  # wrong type
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_form(self):
        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )

        response = self.client.get(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': call.proposal_type}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['call'].id, call.id)
        self.assertIn('ScienceProposalAppForm', str(response.context['form'].__class__))

        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.KEY_PROPOSAL
        )

        response = self.client.get(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': call.proposal_type}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['call'].id, call.id)
        self.assertIn('KeyProjectAppForm', str(response.context['form'].__class__))

        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.DDT_PROPOSAL
        )

        response = self.client.get(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': call.proposal_type}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['call'].id, call.id)
        self.assertIn('DDTProposalAppForm', str(response.context['form'].__class__))


class TestPostCreateSciApp(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)
        data = {
            'call': 1,
            'status': 'DRAFT',
            'title': 'Test Title',
            'pi': 'test@example.com',
            'coi': 'test2@example.com, test3@example.com',
            'budget_details': 'test budget value',
            'instruments': 1,
            'abstract': 'test abstract value',
            'moon': 'EITHER',
            'science_case': SimpleUploadedFile('sci', b'science_case'),
            'experimental_desgin': 'exp desgin value',
            'experimental_desgin_file': SimpleUploadedFile('exp', b'exp_file'),
            'related_programs': 'related progams value',
            'past_use': 'past use value',
            'publications': 'publications value',
            'final': SimpleUploadedFile('final', b'final content'),
            'save': 'SAVE',
            'science_justification': 'Test science justification',
            'ddt_justification': 'Test ddt justification',
            'management': 'test management',
            'relevance': 'test relevance',
            'contribution': 'test contribution',
            'attachment': SimpleUploadedFile('attachment', b'attachment content'),
        }

        timerequest_data = {
            'timerequest_set-0-id': '',
            'timerequest_set-0-telescope_class': '1m0',
            'timerequest_set-0-std_time': 30,
            'timerequest_set-0-too_time': 1,

        }

        management_data = {
            'timerequest_set-TOTAL_FORMS': 1,
            'timerequest_set-INITIAL_FORMS': 0,
            'timerequest_set-MIN_NUM_FORMS': 0,
            'timerequest_set-MAX_NUM_FORMS': 1000,
        }

        self.sci_data = {k: data[k] for k in data if k in ScienceProposalAppForm.Meta.fields}
        self.sci_data.update(timerequest_data)
        self.sci_data.update(management_data)
        self.key_data = {k: data[k] for k in data if k in KeyProjectAppForm.Meta.fields}
        self.key_data.update(timerequest_data)
        self.key_data.update(management_data)
        self.ddt_data = {k: data[k] for k in data if k in DDTProposalAppForm.Meta.fields}
        self.ddt_data.update(timerequest_data)
        self.ddt_data.update(management_data)

    def test_post_sci_form(self):
        num_apps = ScienceApplication.objects.count()
        response = self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': self.call.proposal_type}
            ),
            data=self.sci_data,
            follow=True
        )
        self.assertEqual(num_apps + 1, self.user.scienceapplication_set.count())
        self.assertContains(response, self.sci_data['title'])

    def test_post_key_form(self):
        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.KEY_PROPOSAL
        )
        mixer.blend(Instrument, call=call)
        num_apps = ScienceApplication.objects.count()
        response = self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': call.proposal_type}
            ),
            data=self.key_data,
            follow=True
        )
        self.assertEqual(num_apps + 1, self.user.scienceapplication_set.count())
        self.assertContains(response, self.sci_data['title'])

    def test_post_ddt_form(self):
        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.DDT_PROPOSAL
        )
        mixer.blend(Instrument, call=call)
        num_apps = ScienceApplication.objects.count()
        response = self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': call.proposal_type}
            ),
            data=self.ddt_data,
            follow=True
        )
        self.assertEqual(num_apps + 1, self.user.scienceapplication_set.count())
        self.assertContains(response, self.sci_data['title'])

    def test_can_save_incomplete(self):
        data = self.sci_data.copy()
        del data['abstract']
        self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': self.call.proposal_type}
            ),
            data=data,
            follow=True
        )
        self.assertEqual(self.user.scienceapplication_set.last().abstract, '')
        self.assertEqual(self.user.scienceapplication_set.last().status, ScienceApplication.DRAFT)

    def test_cannot_submit_incomplete(self):
        data = self.sci_data.copy()
        del data['abstract']
        data['status'] = 'SUBMITTED'
        response = self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': self.call.proposal_type}
            ),
            data=data,
            follow=True
        )
        self.assertFalse(self.user.scienceapplication_set.all())
        self.assertContains(response, 'Please fill out all required fields')

    def test_multiple_time_requests(self):
        data = self.sci_data.copy()
        data.update({
            'timerequest_set-1-id': '',
            'timerequest_set-1-telescope_class': '2m0',
            'timerequest_set-1-std_time': 20,
            'timerequest_set-1-too_time': 10,
            'timerequest_set-TOTAL_FORMS': 2,
        })
        self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': self.call.proposal_type}
            ),
            data=data,
            follow=True
        )
        self.assertEqual(self.user.scienceapplication_set.last().timerequest_set.count(), 2)


class TestGetUpdateSciApp(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)

    def test_can_view_draft(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:update', kwargs={'pk': app.id}))
        self.assertContains(response, app.title)

    def test_cannot_view_other_apps(self):
        other_user = mixer.blend(User)
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=other_user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:update', kwargs={'pk': app.id}))
        self.assertEqual(response.status_code, 404)


class TestPostUpdateSciApp(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)

    def can_update_draft(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )

        data = self.sci_data.copy()
        data['title'] = 'updated'
        self.client.post(
            reverse('sciapplications:create', kwargs={
                'semester': self.semester.code,
                'type': self.call.proposal_type}
            ),
            data=data,
            follow=True
        )
        self.assertEqual(ScienceApplication.objects.get(pk=app.id)['title'], data['title'])
