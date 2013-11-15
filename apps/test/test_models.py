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
import json
from google.appengine.ext import testbed
from google.appengine.api import memcache
from google.appengine.ext import ndb
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


class TestBaseModel(unittest.TestCase):

    """ TestBaseModel. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='geo-expertise')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

        class AClass(M.BaseModel):
            akey = ndb.model.KeyProperty(indexed=True)
            name = ndb.model.StringProperty(indexed=True)
            gender = ndb.model.StringProperty(indexed=False)

            bm_updatable = ['name']
            bm_viewable = ['gender']

        self.aclass = AClass

    def tearDown(self):
        self.testbed.deactivate()

    def test_BaseModel_encode(self):
        """ test_BaseModel. """
        A = self.aclass
        a = A()
        self.assertTrue(isinstance(A.akey, ndb.model.KeyProperty))
        self.assertEqual(a.bm_version, 0)
        import subprocess
        out = subprocess.check_output(
            ['node', '-e', 'atob=require("atob");\
             process.stdout.write(JSON.stringify(%s))'
             % (a.js_encode(), )])
        obj = json.loads(out)
        self.assertEqual(obj, {u'bm_version': 0,
                               u'gender': None,
                               u'name': None})

    def test_BaseModel_load(self):
        """ test_jsdecode. """
        A = self.aclass
        datapack = json.dumps({u'bm_version': 0,
                               u'gender': 'male',
                               u'name': 'Jack Shaphard'})
        a = A.load(datapack)
        self.assertEqual(a.name, 'Jack Shaphard')
        self.assertIsNone(a.key)

    def test_BaseModel_load2(self):
        """ test_BaseModel_load2. """
        A = self.aclass
        a = A(name='Jack Shaphard',
              gender='male').put()
        obj = {'name': 'Swyer',
               'gender': 'female',
               'bm_version': 1,
               '__KEY__': a.urlsafe()}
        a = A.load(json.dumps(obj))
        self.assertEqual(a.name, 'Swyer')
        self.assertEqual(a.gender, 'male')
        self.assertIsNotNone(a.key)
        b = A.query().fetch()[0]
        self.assertEqual(b.name, 'Swyer')
        self.assertEqual(a.gender, 'male')


class TestNDB(unittest.TestCase):

    """ Test NDB Feature. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='geo-expertise')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_name(self):
        pass

    def test_inheritance(self):
        """ test_inheritance. """
        class A(ndb.Model):
            version = ndb.IntegerProperty()

        class B(A):
            name = ndb.StringProperty()
            gender = ndb.StringProperty()

        b = B(name='Jack Shaphard', gender='mail', version=100)
        b.put()
        self.assertEquals(B.query().fetch()[0].version, 100)
        self.assertIsNotNone(b.key)
        self.assertIsNone(B().key)

    def test_populate(self):
        """ test_populate. """
        g = M.GeoEntity(tfid='a', name='c', group='a', relation='s', url='h')
        g.put()
        g.populate(tfid='b')
        self.assertEqual(M.GeoEntity.query().fetch()[0].tfid, 'b')

    def test_memcache(self):
        """ test_memcache. """
        self.assertIsNone(memcache.get('something'))
        memcache.set(key='something', value=1)
        self.assertIsNotNone(memcache.get('something'))

    def test_memcache2(self):
        """ test_memcache2. """
        f = M.GeoEntity(tfid='a', name='c', group='a', relation='s', url='h')
        memcache.set(key='a', value=f)
        memcache.set(key='b', value=f)
        g = memcache.get('a')
        g.name = 'xxx'
        self.assertNotEqual(memcache.get('a').name, 'xxx')

    def test_keykind(self):
        """ test_keykind. """
        g = M.GeoEntity(tfid='a', name='c', group='a', relation='s', url='h')
        self.assertEquals(g.put().kind(), 'GeoEntity')


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
