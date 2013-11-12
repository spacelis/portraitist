#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Testing datastore models.

File: test_models.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    Testing basic operations on data models.

"""

import unittest
from google.appengine.ext import testbed
from google.appengine.api import memcache
from collections import Counter

import apps.profileviewer.models as M
# pylint: disable-msg=R0904


class TestModelUtils(unittest.TestCase):

    """ Testing newToken, secure_hash. """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_newToken(self):
        """ test_newToken. """
        self.assertSequenceEqual(
            [i for _, i in
             Counter(M.newToken() for _ in range(1000)).iteritems()],
            [1 for _ in range(1000)]
        )

    def test_secure_hash(self):
        """ test_secure_hash. """
        self.assertNotEqual('a', M.secure_hash('a'))
        self.assertNotEqual(M.secure_hash('b'), M.secure_hash('a'))
        self.assertEquals(M.secure_hash('a'), M.secure_hash('a'))


class TestModels(unittest.TestCase):

    """models tests."""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='geo-expertise')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_populate(self):
        """ test_basis. """
        g = M.GeoEntity(tfid='a', name='c', group='a', relation='s', url='h')
        g.put()
        g.populate(tfid='b')
        self.assertEqual(M.GeoEntity.query().fetch()[0].tfid, 'b')

    def test_memcache(self):
        """ test_basis. """
        self.assertIsNone(memcache.get('something'))
        memcache.set(key='something', value=1)
        self.assertIsNotNone(memcache.get('something'))

    def test_EmailAccount(self):
        """ test EmailAccount. """
        u = M.EmailAccount.signUp('spacelis@gmail.com', 'abc12345', 'Sapce Li')
        a = M.EmailAccount.query().fetch()[0]
        self.assertEquals(u.key, a.user)
        self.assertEquals(u.email_account.get().email, a.email)
        self.assertEqual(len(M.EmailAccount.query().fetch()), 1)
        self.assertEqual(len(M.User.query().fetch()), 1)
        self.assertIsNotNone(u.token)
        self.assertIsNone(u.twitter_account)
        self.assertNotEquals(u.email_account.get().passwd, 'abc12345')
        self.assertEquals(u.email_account.get().passwd,
                          M.secure_hash('abc12345'))

    def test_heartBeat(self):
        """ test_heartBeat(). """
        from datetime import datetime as dt
        from datetime import timedelta
        from time import sleep
        u = M.EmailAccount.signUp('spacelis@gmail.com', 'abc12345', 'Sapce Li')
        u.heartBeat()
        sleep(1)
        self.assertLessEqual(u.last_seen, dt.utcnow())
        self.assertGreaterEqual(u.last_seen,
                                dt.utcnow() - timedelta(seconds=2))
