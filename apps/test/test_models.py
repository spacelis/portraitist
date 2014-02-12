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
        self.assertNotEqual('a', M.secure_hash('a', ''))
        self.assertNotEqual(M.secure_hash('b', ''), M.secure_hash('a', ''))
        self.assertEquals(M.secure_hash('a', ''), M.secure_hash('a', ''))


class TestKeyNoParentSpeed(unittest.TestCase):

    """ Test the speed regarding the key length. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

        class AClass(M.EncodableModel):
            akey = ndb.model.KeyProperty(indexed=True)
            name = ndb.model.StringProperty(indexed=True)

        for _ in range(10000):
            akey = AClass(name="nothing").put()

        self.akey = akey
        memcache.Client().flush_all()

    def tearDown(self):
        self.testbed.deactivate()

    def test_noparent_key(self):
        """ test_noparent_key. """
        x = self.akey.get()


class TestKeyParentSpeed(unittest.TestCase):

    """ Test the speed regarding the key length. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='testbed')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        parentkey = ndb.Key('test', 'parenting', app='testbed')

        class AClass(M.EncodableModel):
            akey = ndb.model.KeyProperty(indexed=True)
            name = ndb.model.StringProperty(indexed=True)

        for _ in range(10000):
            akey = AClass(parent=parentkey, name="nothing").put()

        self.akey = akey
        memcache.Client().flush_all()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parent_key(self):
        """ test_noparent_key. """
        import cProfile
        cProfile.runctx("self.akey.get()", locals(), globals(),
                        filename="ParentKeyGet.profile")


class TestBaseModel(unittest.TestCase):

    """ TestBaseModel. """

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='geo-expertise')
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

        class AClass(M.EncodableModel):
            akey = ndb.model.KeyProperty(indexed=True)
            name = ndb.model.StringProperty(indexed=True)
            gender = ndb.model.StringProperty(indexed=False)
            address = ndb.model.JsonProperty(indexed=False)

            def as_viewdict(self):
                """ dummy as dict function """
                return {
                    'name': self.name,
                    'gender': self.gender,
                }

        self.aclass = AClass

    def tearDown(self):
        self.testbed.deactivate()

    def test_NDB_async_features(self):
        """ test_NDB_async_features """
        A = self.aclass
        A(name='test').put()
        fa = M.fetch_one_async(A.query())
        self.assertEqual(fa.get_result().to_dict(), {'akey': None,
                                                     'name': 'test',
                                                     'gender': None,
                                                     'address': None})

    def test_NDB_todict(self):
        """ test ndb.Model.to_dict(). """
        A = self.aclass
        a = A()
        a.put()
        self.assertEqual(a.to_dict(), {'akey': None,
                                       'name': None,
                                       'gender': None,
                                       'address': None})

    def test_NDB_todict2(self):
        """ test ndb.Model.to_dict() for json. """
        A = self.aclass
        a = A(address={'line1': 'Juniusstraat'})
        self.assertEqual(a.to_dict(), {'akey': None,
                                       'name': None,
                                       'gender': None,
                                       'address': {'line1': 'Juniusstraat'}})

    def test_NDB_key(self):
        """ test_NDB_key. """
        with self.assertRaises(TypeError):
            ndb.Key(urlsafe='a')

    def test_BaseModel_encode(self):
        """ test_BaseModel. """
        A = self.aclass
        a = A()
        import subprocess
        out = subprocess.check_output(
            ['node', '-e', 'atob=require("atob");\
             process.stdout.write(JSON.stringify(%s))'
             % (a.js_encode(), )])
        obj = json.loads(out)
        self.assertEqual(obj, {u'gender': None,
                               u'name': None})

    def test_BaseModel_encode2(self):
        """ test_BaseModel. """
        A = self.aclass
        a = A()
        self.assertTrue(isinstance(A.akey, ndb.model.KeyProperty))
        import subprocess
        out = subprocess.check_output(
            ['node', '-e', """atob=require("atob");
             var x = %s;
             x.name = "Swyer";
             process.stdout.write(JSON.stringify(x))"""
             % (a.js_encode(), )])
        obj = json.loads(out)
        self.assertEqual(obj, {u'gender': None,
                               u'name': 'Swyer'})

    def test_BaseModel_synced(self):
        """ test_jsdecode. """
        import base64
        A = self.aclass
        datapack = base64.b64encode(
            json.dumps({u'gender': 'male',
                        u'name': 'Jack Shaphard'}))
        a = A.synced(datapack)
        self.assertEqual(a.name, 'Jack Shaphard')
        self.assertIsNone(a.key)

    def test_BaseModel_synced2(self):
        """ test_BaseModel_load2. """
        import base64
        A = self.aclass
        a = A(name='Jack Shaphard',
              gender='male').put()
        obj = {'name': 'Kate',
               'gender': 'female',
               '__KEY__': a.urlsafe()}
        a = A.synced(base64.b64encode(json.dumps(obj)))
        self.assertEqual(a.name, 'Kate')
        self.assertEqual(a.gender, 'female')
        self.assertIsNotNone(a.key)
        b = A.query().fetch()[0]
        self.assertEqual(b.name, 'Kate')
        self.assertEqual(a.gender, 'female')


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
        g = M.GeoEntity(tfid='a', name='c', level='a', url='h')
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
        f = M.GeoEntity(tfid='a', name='c', level='s', url='h')
        memcache.set(key='a', value=f)
        memcache.set(key='b', value=f)
        g = memcache.get('a')
        g.name = 'xxx'
        self.assertNotEqual(memcache.get('a').name, 'xxx')

    def test_keykind(self):
        """ test_keykind. """
        g = M.GeoEntity(tfid='a', name='c', level='a', info={}, url='h')
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
        u = M.EmailAccount.signUp('spacelis@gmail.com', 'abc12345',
                                  'Sapce Li', M.User.unit())
        a = M.EmailAccount.query().fetch()[0]
        self.assertEquals(u.key, a.user)
        self.assertEquals(u.email_account.get().email, a.email)
        self.assertEqual(len(M.EmailAccount.query().fetch()), 1)
        self.assertEqual(len(M.User.query().fetch()), 1)
        self.assertIsNone(u.twitter_account)
        self.assertNotEquals(u.email_account.get().hashed_passwd, 'abc12345')
        self.assertEquals(M.EmailAccount.login('spacelis@gmail.com',
                                               'abc12345', M.User.unit()).key,
                          u.key)

    def test_EmailAccount(self):
        """ test EmailAccount. """
        u = M.EmailAccount.signUp('spacelis@gmail.com', 'abc12345',
                                  'Sapce Li', M.User.unit())
        self.assertTrue(M.EmailAccount.contains(email='spacelis@gmail.com'))
        self.assertFalse(M.EmailAccount.contains(email='Space Lis'))

    def test_heartBeat(self):
        """ test_heartBeat(). """
        from datetime import datetime as dt
        from datetime import timedelta
        from time import sleep
        u = M.EmailAccount.signUp('spacelis@gmail.com', 'abc12345',
                                  'Sapce Li', M.User.unit())
        s = M.User.getOrCreate(None)
        sleep(1)
        self.assertLessEqual(s.last_seen, dt.utcnow())
        self.assertGreaterEqual(s.last_seen,
                                dt.utcnow() - timedelta(seconds=2))
