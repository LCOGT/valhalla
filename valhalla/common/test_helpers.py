from django.conf import settings
import responses
import json
import os

CONFIGDB_TEST_FILE = os.path.join(settings.BASE_DIR, 'valhalla/common/test_data/configdb.json')


class ConfigDBTestMixin(object):
    '''Mixin class to mock configdb calls'''
    def setUp(self):
        responses._default_mock.__enter__()
        responses.add(
            responses.GET, settings.CONFIGDB_URL + '/sites/',
            json=json.loads(open(CONFIGDB_TEST_FILE).read()), status=200
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        responses._default_mock.__exit__()
