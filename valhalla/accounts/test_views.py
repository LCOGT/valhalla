from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import auth
from mixer.backend.django import mixer

from valhalla.accounts.models import Profile
from valhalla.proposals.models import ProposalInvite, Membership


class TestIndex(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='doge',
            password='sopassword',
            email='doge@dog.com'
        )

    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Observation Portal')

    def test_login_fails(self):
        self.client.post(
            reverse('auth_login'),
            {'username': 'doge', 'password': 'wrongpass'},
        )
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated())

    def test_login(self):
        self.client.post(
            reverse('auth_login'),
            {'username': 'doge', 'password': 'sopassword'},
        )
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())

    def test_login_with_email(self):
        self.client.post(
            reverse('auth_login'),
            {'username': 'doge@dog.com', 'password': 'sopassword'},
        )
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())


class TestRegistration(TestCase):
    def setUp(self):
        self.reg_data = {
            'first_name': 'Bobby',
            'last_name': 'Shaftoe',
            'institution': 'US Army',
            'title': 'Jarhead',
            'email': 'bshaftoe@army.gov',
            'username': 'bshaftoe',
            'password1': 'imnotcrazy',
            'password2': 'imnotcrazy',
            'tos': True,
        }

    def test_registration(self):
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('registration_register'), self.reg_data, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'check your email')

        user = User.objects.get(username=self.reg_data['username'])
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.title, self.reg_data['title'])
        self.assertEqual(user.profile.institution, self.reg_data['institution'])

    def test_registration_with_invite(self):
        invitation = mixer.blend(ProposalInvite, email=self.reg_data['email'], membership=None, used=None)
        response = self.client.post(reverse('registration_register'), self.reg_data, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'check your email')
        invitation = ProposalInvite.objects.get(pk=invitation.id)
        self.assertTrue(invitation.used)
        self.assertTrue(Membership.objects.filter(user__username=self.reg_data['username']).exists())

    def test_registration_with_multiple_invites(self):
        invitations = mixer.cycle(2).blend(ProposalInvite, email=self.reg_data['email'], membership=None, used=None)
        self.client.post(reverse('registration_register'), self.reg_data, follow=True)
        invitation = ProposalInvite.objects.get(pk=invitations[0].id)
        self.assertTrue(invitation.used)
        self.assertTrue(Membership.objects.filter(user__username=self.reg_data['username']).exists())
        invitation = ProposalInvite.objects.get(pk=invitations[1].id)
        self.assertTrue(invitation.used)
        self.assertTrue(Membership.objects.filter(user__username=self.reg_data['username']).exists())


class TestProfile(TestCase):
    def setUp(self):
        self.profile = mixer.blend(Profile, notifications_enabled=True)
        self.data = {
            'first_name': self.profile.user.first_name,
            'last_name': self.profile.user.last_name,
            'email': self.profile.user.email,
            'username': self.profile.user.username,
            'institution': self.profile.institution,
            'title': self.profile.title,
            'notifications_enabled': self.profile.notifications_enabled
        }
        self.client.force_login(self.profile.user)

    def test_update(self):
        good_data = self.data.copy()
        good_data['email'] = 'hi@lco.global'
        response = self.client.post(reverse('profile'), good_data, follow=True)
        self.assertContains(response, 'Profile successfully updated')
        self.assertEqual(Profile.objects.get(pk=self.profile.id).user.email, 'hi@lco.global')

    def test_unique_email(self):
        mixer.blend(User, email='first@example.com')
        bad_data = self.data.copy()
        bad_data['email'] = 'first@example.com'
        response = self.client.post(reverse('profile'), bad_data, follow=True)
        self.assertContains(response, 'User with this email already exists')
        self.assertNotEqual(Profile.objects.get(pk=self.profile.id).user.email, 'first@example.com')

    def test_required(self):
        bad_data = self.data.copy()
        del bad_data['username']
        response = self.client.post(reverse('profile'), bad_data, follow=True)
        self.assertContains(response, 'This field is required')
        self.assertTrue(Profile.objects.get(pk=self.profile.id).user.username)

    def test_api_call(self):
        response = self.client.get(reverse('api:profile'))
        self.assertEqual(response.json()['username'], self.profile.user.username)
