from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from mixer.backend.django import mixer
from PyPDF2 import PdfFileMerger
from weasyprint import HTML
from unittest.mock import MagicMock


from valhalla.proposals.models import Semester
from valhalla.sciapplications.models import ScienceApplication, Call, Instrument
from valhalla.sciapplications.forms import ScienceProposalAppForm, DDTProposalAppForm, KeyProjectAppForm


class TestGetCreateSciApp(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        user = mixer.blend(User)
        self.client.force_login(user)

    def test_no_call(self):
        response = self.client.get(
            reverse('sciapplications:create', kwargs={'call': 66})
        )
        self.assertEqual(response.status_code, 404)

    def test_get_form(self):
        call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            proposal_type=Call.SCI_PROPOSAL
        )

        response = self.client.get(
            reverse('sciapplications:create', kwargs={'call': call.id})
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
            reverse('sciapplications:create', kwargs={'call': call.id})
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
            reverse('sciapplications:create', kwargs={'call': call.id})
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
            'status': 'SUBMITTED',
            'title': 'Test Title',
            'pi': 'test@example.com',
            'coi': 'test2@example.com, test3@example.com',
            'budget_details': 'test budget value',
            'instruments': 1,
            'abstract': 'test abstract value',
            'moon': 'EITHER',
            'science_case': 'science case',
            'science_case_file': SimpleUploadedFile('sci.pdf', b'science_case'),
            'experimental_design': 'exp desgin value',
            'experimental_design_file': SimpleUploadedFile('exp.PDF', b'exp_file'),
            'related_programs': 'related progams value',
            'past_use': 'past use value',
            'publications': 'publications value',
            'save': 'SAVE',
            'science_justification': 'Test science justification',
            'ddt_justification': 'Test ddt justification',
            'management': 'test management',
            'relevance': 'test relevance',
            'contribution': 'test contribution',
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
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
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
            reverse('sciapplications:create', kwargs={'call': call.id}),
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
            reverse('sciapplications:create', kwargs={'call': call.id}),
            data=self.ddt_data,
            follow=True
        )
        self.assertEqual(num_apps + 1, self.user.scienceapplication_set.count())
        self.assertContains(response, self.sci_data['title'])

    def test_can_save_incomplete(self):
        data = self.sci_data.copy()
        data['status'] = 'DRAFT'
        del data['abstract']
        self.client.post(
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertEqual(self.user.scienceapplication_set.last().abstract, '')
        self.assertEqual(self.user.scienceapplication_set.last().status, ScienceApplication.DRAFT)

    def test_cannot_submit_incomplete(self):
        data = self.sci_data.copy()
        del data['abstract']
        response = self.client.post(
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertFalse(self.user.scienceapplication_set.all())
        self.assertContains(response, 'There was an error with your submission')

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
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertEqual(self.user.scienceapplication_set.last().timerequest_set.count(), 2)

    def test_cannot_post_own_email(self):
        data = self.sci_data.copy()
        data['pi'] = self.user.email
        response = self.client.post(
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertContains(response, 'There was an error with your submission')
        self.assertContains(response, 'if you are the PI')

    def test_can_leave_out_email(self):
        data = self.sci_data.copy()
        del data['pi']
        del data['coi']
        response = self.client.post(
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.scienceapplication_set.last().pi, '')
        self.assertEqual(self.user.scienceapplication_set.last().coi, '')

    def test_cannot_upload_silly_files(self):
        data = self.sci_data.copy()
        data['science_case_file'] = SimpleUploadedFile('notpdf.png', b'apngfile')
        response = self.client.post(
            reverse('sciapplications:create', kwargs={'call': self.call.id}),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'We can only accept PDF files')


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

    def test_cannot_edit_submitted(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.SUBMITTED,
            submitter=self.user,
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

    def test_can_update_draft(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )

        data = {
            'call': 1,
            'title': 'updates',
            'status': 'DRAFT',
            'timerequest_set-TOTAL_FORMS': 0,
            'timerequest_set-INITIAL_FORMS': 0,
            'timerequest_set-MIN_NUM_FORMS': 0,
            'timerequest_set-MAX_NUM_FORMS': 1000,

        }
        self.client.post(
            reverse('sciapplications:update', kwargs={'pk': app.id}),
            data=data,
            follow=True
        )
        self.assertEqual(ScienceApplication.objects.get(pk=app.id).title, data['title'])


class TestSciAppIndex(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            opens=timezone.now(),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)

    def test_unauthorized(self):
        self.client.logout()
        response = self.client.get(reverse('sciapplications:index'))
        self.assertEqual(response.status_code, 302)

    def test_index_no_applications(self):
        response = self.client.get(reverse('sciapplications:index'))
        self.assertContains(response, 'You have not started any proposals')

    def test_index(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:index'))
        self.assertContains(response, self.call.eligibility_short)
        self.assertContains(response, app.title)


class TestSciAppDetail(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            opens=timezone.now(),
            proposal_type=Call.SCI_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)

    def test_can_view_details(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:detail', kwargs={'pk': app.id}))
        self.assertContains(response, app.title)

    def test_cannot_view_others_details(self):
        other_user = mixer.blend(User)
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=other_user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:detail', kwargs={'pk': app.id}))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_details(self):
        staff_user = mixer.blend(User, is_staff=True)
        self.client.force_login(staff_user)
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:detail', kwargs={'pk': app.id}))
        self.assertContains(response, app.title)

    def test_pdf_view(self):
        # Just test the view here, actual pdf rendering is slow and loud
        PdfFileMerger.merge = MagicMock
        HTML.write_pdf = MagicMock
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:pdf', kwargs={'pk': app.id}))
        self.assertTrue(PdfFileMerger.merge.called)
        self.assertTrue(HTML.write_pdf.called)
        self.assertEqual(response.status_code, 200)

    def test_bad_characters(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call,
            abstract='A string with bad \u0008 characters'
        )
        response = self.client.get(reverse('sciapplications:pdf', kwargs={'pk': app.id}), follow=True)
        self.assertContains(response, 'There was an error generating your pdf')

    def test_staff_can_view_pdf(self):
        PdfFileMerger.merge = MagicMock
        HTML.write_pdf = MagicMock
        staff_user = mixer.blend(User, is_staff=True)
        self.client.force_login(staff_user)
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.get(reverse('sciapplications:pdf', kwargs={'pk': app.id}))
        self.assertTrue(PdfFileMerger.merge.called)
        self.assertTrue(HTML.write_pdf.called)
        self.assertEqual(response.status_code, 200)


class TestSciAppDelete(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            deadline=timezone.now() + timedelta(days=7),
            opens=timezone.now(),
            proposal_type=Call.DDT_PROPOSAL
        )
        mixer.blend(Instrument, call=self.call)

    def test_can_delete_draft(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=self.user,
            call=self.call
        )
        response = self.client.post(
            reverse('sciapplications:delete', kwargs={'pk': app.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, app.title)
        self.assertFalse(ScienceApplication.objects.filter(pk=app.id).exists())

    def test_cannot_delete_non_draft(self):
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.SUBMITTED,
            submitter=self.user,
            call=self.call
        )
        response = self.client.post(
            reverse('sciapplications:delete', kwargs={'pk': app.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ScienceApplication.objects.filter(pk=app.id).exists())

    def test_cannot_delete_others(self):
        other_user = mixer.blend(User)
        app = mixer.blend(
            ScienceApplication,
            status=ScienceApplication.DRAFT,
            submitter=other_user,
            call=self.call
        )
        response = self.client.post(
            reverse('sciapplications:delete', kwargs={'pk': app.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ScienceApplication.objects.filter(pk=app.id).exists())
