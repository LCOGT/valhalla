from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import auth
from mixer.backend.django import mixer

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
