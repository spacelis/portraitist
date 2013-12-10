#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Testing API module.

File: test_api.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    Testing API Module.

"""

import json
import unittest
import mock
from mock import Mock
from StringIO import StringIO

from google.appengine.ext import testbed
from django.http import HttpRequest


class ContextualStringIO(StringIO):

    """ A context StringIO. """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


# pylint: disable=R0904
@mock.patch('apps.profileviewer.api.flexopen',)
class TestImportAPI(unittest.TestCase):

    """ TestImportAPI. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='geo-expertise')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_importEntity(self, mock_flexopen):
        """ test_importEntity. """
        mock_flexopen.return_value = ContextualStringIO(
            'screen_name,checkins\nspaceli,"{""a"": 1}"')

        def loader(r):
            """ test_loader. """
            self.assertEqual(r['screen_name'], 'spaceli')
            self.assertEqual(json.loads(r['checkins']), {'a': 1})

        from apps.profileviewer.api import import_entities
        import_entities('', loader)

    def test_import_candidates(self, mock_flexopen):
        """test_import_candidates."""
        mock_flexopen.return_value = ContextualStringIO(
            'screen_name,checkins\nspaceli,"{""a"": 1}"')

        from apps.profileviewer.api import import_candidates
        from apps.profileviewer.models import TwitterAccount

        import_candidates('')
        self.assertEqual(len(TwitterAccount.query().fetch()), 1)


class TestUtilFunctions(unittest.TestCase):

    """ Test general util functions. """

    def test_partition(self):
        """ test_partition. """
        from apps.profileviewer.api import partition
        self.assertEqual([list(g) for g in partition(range(11), 7)],
                         [[0, 1, 2, 3, 4, 5, 6],
                          [7, 8, 9, 10]])
