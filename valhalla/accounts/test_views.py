from django.test import TestCase
from django.core.urlresolvers import reverse


class TestIndex(TestCase):
    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Observation Portal')
