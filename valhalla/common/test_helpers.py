from django.conf import settings
from unittest.mock import patch
from datetime import datetime
from django.utils import timezone
import responses
import json
import os

CONFIGDB_TEST_FILE = os.path.join(settings.BASE_DIR, 'valhalla/common/test_data/configdb.json')
FILTERWHEELS_FILE = os.path.join(settings.BASE_DIR, 'valhalla/common/test_data/filterwheels.json')


class ConfigDBTestMixin(object):
    '''Mixin class to mock configdb calls'''
    def setUp(self):
        responses._default_mock.__enter__()
        responses.add(
            responses.GET, settings.CONFIGDB_URL + '/sites/',
            json=json.loads(open(CONFIGDB_TEST_FILE).read()), status=200
        )
        responses.add(
            responses.GET, settings.CONFIGDB_URL + '/filterwheels/',
            json=json.loads(open(FILTERWHEELS_FILE).read()), status=200
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        responses._default_mock.__exit__(None, None, None)


class SetTimeMixin(object):
    def setUp(self):
        self.time_patcher = patch('valhalla.userrequests.serializers.timezone.now')
        self.mock_now = self.time_patcher.start()
        self.mock_now.return_value = datetime(2016, 9, 1, tzinfo=timezone.utc)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.time_patcher.stop()
