#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data models for persistency.

File: models.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Expertise data model

"""

import csv
import hashlib
from uuid import uuid4
from datetime import timedelta
from datetime import datetime as dt
import base64
import json

from django.http import Http404
from google.appengine.ext import ndb
from google.appengine.api import memcache

DEFAULT_PARENT_KEY = ndb.Key('Version', 'geo-expertise-3', app='geo-expertise')
LONG_TIME = timedelta(minutes=30)
csv.field_size_limit(500000)


def newToken(prefix=''):
    """ Return a uuid as access token.

    :returns: a uuid4()

    """
    return prefix + str(uuid4())


def secure_hash(s):
    """ Return sha1 hashcode.

    :s: @todo
    :returns: @todo

    """
    return hashlib.sha512(s).hexdigest()  # pylint: disable=E1101


def _k(s):
    """ Return a key of given urlsafe key s.

    :s: A urlsafe encoded key.
    :returns: A ndb.Key.

    """
    return ndb.Key(urlsafe=s)


def assertAbsent(model, field, value):
    """ Assert the given value does not exists in the field of given model.

    :model: A ndb model.
    :field: the field name
    :value: A given value.
    :returns: exception or None

    """
    if len(model.query(field == value).fetch(1)) > 0:
        raise ValueError


class Encodable(object):

    """ A unified model with enhanced serierlizing methods.

    :bm_viewable: Defines the properties returned in js_encode().
    :bm_updatable: Defines the properties accepting updates for load().

    Methods:
        js_encode() will return a snippet of javascript with base64 encoded
        data.
        js_decode() will will populate a model object with a dict while keep
        non-updatable properties untouched.

    Require:
        to_dict() to be defined.

    """

    JS_CLASS = """{
        payload: JSON.parse(atob("%s")),
        get: function(name){
            return this.payload[name];
        },
        set: function(name, val){
            if(this.payload[name] !== val){
                this.payload["__CHANGED__"] = true;
                this.payload[name] = val;
            }
        }
    }"""

    def js_encode(self):
        """ encode for javascript. """
        d = self.as_dict()
        assert '__CHANGED__' not in d, '__CHANGED__ key is reserved.'
        d['__CHANGED__'] = False
        return self.JS_CLASS % (base64.b64encode(json.dumps(d)), )

    @staticmethod
    def js_decode(b64str):
        """ decode the b64str into dict object.

        :b64str: the encoded json object.
        :return: the dict, whether something changed

        """
        d = json.loads(base64.b64decode(b64str))
        if d['__CHANGED__']:
            c = True
        else:
            c = False
        del d['__CHANGED__']
        return d, c

    def as_dict(self):
        """ Return a dict representation of current object.

        :returns: A dict object.

        """
        raise NotImplementedError


class EncodableModel(ndb.Model, Encodable):

    """ A ndb based model with encoding and syncing. """

    bm_viewable = None
    bm_updatable = None

    @classmethod
    def synced(cls, val=None, b64=False):
        """ Sync the value and return the synced one.

        :val: A string encoded json object.
        :b64: Whether the string is base64 encoded.

        """
        assert not b64, "Base64 decoding is not supported yet."
        if isinstance(val, str) and len(val):
            raw_obj, changed = Encodable.js_decode(val)
            d = {k: v
                 for k, v in raw_obj.iteritems()
                 if k in cls.bm_updatable}
            try:
                mobj = _k(raw_obj['__KEY__']).get()
                if changed:  # pylint: disable=W0212
                    mobj.populate(**d)  # pylint: disable=W0142
            except KeyError:
                mobj = cls(**d)  # pylint: disable=W0142
            return mobj

    def as_dict(self):
        """ Return a dict representation of data model.

        :returns: @todo

        """
        d = self.to_dict()
        if self.key:
            d['__KEY__'] = self.key.urlsafe()
        else:
            d['__KEY__'] = None
        return {k: v for k, v in d.iteritems()
                if k in self.bm_viewable
                or k in self.bm_updatable
                or k == '__KEY__'}


class TwitterAccount(ndb.Model):  # pylint: disable=R0903,R0921

    """Docstring for TwitterAccount. """

    checkins = ndb.model.JsonProperty(indexed=False, compressed=True)
    friends = ndb.model.StringProperty(indexed=False, repeated=True)
    screen_name = ndb.model.StringProperty(indexed=True)
    access_token = ndb.model.StringProperty(indexed=True)
    access_token_secret = ndb.model.StringProperty(indexed=True)
    user = ndb.model.KeyProperty(indexed=True, kind='User')

    @staticmethod
    def singIn(access_token, access_token_secret):
        """ Sign in with users twitter account.

        :returns: @todo

        """
        pass

    @staticmethod
    def getByScreenName(screen_name):
        """ Return the account with the given screen_name.

        :returns: A TwitterAccount

        """
        try:
            return TwitterAccount.query(screen_name=screen_name).fetch(1)[0]
        except IndexError:
            raise KeyError

    def compressedCheckins(self):
        """ Return the checkin as a block of base64 encoded.

        :returns: @todo

        """
        raise NotImplementedError


class EmailAccount(ndb.Model):

    """ The email account registered with this site. """

    email = ndb.model.StringProperty(indexed=True)
    passwd = ndb.model.StringProperty(indexed=True)
    user = ndb.model.KeyProperty(indexed=True, kind='User')

    @staticmethod
    def signUp(email, passwd, name):
        """ Create a new judge user.

        :email: An email address associate with this judge.
        :passwd: An password for login.
        :name: An nickname used for greeting.
        :returns: A newly created User entity.

        """
        assertAbsent(EmailAccount, EmailAccount.email, email)
        user = User(parent=DEFAULT_PARENT_KEY,
                    name=name,
                    email_account=None,
                    twitter_account=None).put()
        account = EmailAccount(email=email,
                               passwd=secure_hash(passwd),
                               user=user).put()
        user.get().populate(email_account=account)
        return user.get()

    @staticmethod
    def login(email, passwd):
        """ Sign in the account.

        :email: Registered email.
        :passwd: Registered password.
        :returns: A new token.

        """
        try:
            user = EmailAccount.query(
                (EmailAccount.email == email),
                (EmailAccount.passwd == secure_hash(passwd))) \
                .fetch(1)[0].user.get()
            return user
        except IndexError:
            raise ValueError('User not found.')


class User(EncodableModel):

    """ A class representing users as judges or candidates."""

    # pylint: disable=E1101
    name = ndb.model.StringProperty(indexed=True)
    twitter_account = ndb.model.KeyProperty(indexed=True)
    email_account = ndb.model.KeyProperty(indexed=True)
    last_seen = ndb.model.DateTimeProperty()
    seen_instructions = ndb.model.BooleanProperty(default=False)
    done_survey = ndb.model.BooleanProperty(default=False)
    done_tasks = ndb.model.IntegerProperty(default=0)
    info = ndb.model.JsonProperty(indexed=False)
    # pylint: enable=E1101

    def addTwitterAccount(self, access_token, access_token_secret):
        """@todo: Docstring for linkTwitter.

        :access_token: The access_token from Twitter OAuth
        :access_token: The access_token_secret from Twitter OAuth
        :returns: @todo

        """
        t = TwitterAccount(
            parent=DEFAULT_PARENT_KEY,
            access_token=access_token,
            access_token_secret=access_token_secret,
            user_account=self.key
        )
        self.twitter_account = t.key


class GeoEntity(ndb.Model):  # pylint: disable=R0903

    """ A model for entities like POI, Category. """

    tfid = ndb.model.StringProperty(indexed=True)
    name = ndb.model.StringProperty(indexed=False)
    group = ndb.model.StringProperty(indexed=False)  # e.g., category, poi
    relation = ndb.model.JsonProperty(indexed=False)
    url = ndb.model.StringProperty(indexed=False)

    @staticmethod
    def getByTFId(tfid):
        """ Return the entity of the given tfid.

        :tfid: @todo
        :returns: A GeoEntity

        """
        try:
            return GeoEntity.query(tfid=tfid).fetch(1)[0]
        except IndexError:
            raise KeyError()


class Judgement(ndb.Model):  # pylint: disable=R0903

    """ The judgement given by judges. """

    judge = ndb.model.KeyProperty(indexed=True, kind=User)
    candidate = ndb.model.KeyProperty(indexed=True, kind=User)
    topic = ndb.model.KeyProperty(indexed=True, kind=GeoEntity)
    score = ndb.model.IntegerProperty(indexed=False)
    created_at = ndb.model.DateTimeProperty(indexed=False)
    ipaddr = ndb.model.StringProperty(indexed=False)
    user_agent = ndb.model.StringProperty(indexed=False)

    @staticmethod
    def add(judge, candidate, scores, ipaddr, user_agent):
        """ Add a the judgement to the database.

        :judge: The urlsafe key to the judge entity.
        :candidate: The urlsafe key to the candidate entity.
        :scores: A list of (topic_key, score).
        :ipaddr: IP address of the judge in str().
        :user_agent: The browser user agent string.
        :returns: None

        """
        for t, s in scores:
            Judgement(parent=DEFAULT_PARENT_KEY,
                      judge=_k(judge),
                      candidate=_k(candidate),
                      topic=_k(t),
                      score=s,
                      created_at=dt.utcnow(),
                      ipaddr=ipaddr,
                      user_agent=user_agent).put()


class ExpertiseRank(ndb.Model):  # pylint: disable=R0903

    """ The ranking needed to be annotated. """

    topic_id = ndb.model.StringProperty(indexed=False)
    topic = ndb.model.KeyProperty(indexed=True, kind=GeoEntity)
    region = ndb.model.StringProperty(indexed=True)
    candidate = ndb.model.KeyProperty(indexed=True, kind=TwitterAccount)
    rank = ndb.model.IntegerProperty(indexed=False)
    rank_info = ndb.model.JsonProperty(indexed=False)  # e.g., methods, profile

    class ExpertNotExists(Http404):
        """ Exception when the expert queried does not exist"""
        pass

    @staticmethod
    def getTopicsForCandidate(user):
        """ Get a list of Topics by given candidates.

        :user: The user entity.
        :returns: A list of topics

        """
        return ExpertiseRank.query(user == user.key).fetch()


class AnnotationTask(ndb.Model):  # pylint: disable=R0903

    """ A task usually contains all rankings from one canddiate. """

    rankings = ndb.model.KeyProperty(repeated=True)


class TaskPackage(ndb.Model):

    """ A package of tasks. """

    tasks = ndb.model.KeyProperty(repeated=True, kind=AnnotationTask)
    progress = ndb.model.KeyProperty(repeated=True, kind=AnnotationTask)
    done_by = ndb.model.KeyProperty(indexed=True, repeated=True, kind=User)
    confirm_code = ndb.model.StringProperty()
    assigned_at = ndb.model.DateTimeProperty(indexed=True)

    class TaskPackageNotExists(Http404):
        """ If the task_pack_id doesn't exists"""
        pass

    class NoMoreTask(Exception):
        """ If there is no more tasks to assign"""

        def __init__(self, cf_code):
            super(TaskPackage.NoMoreTask, self).__init__()
            self.cf_code = cf_code

    @staticmethod
    def getTaskPackage(safekey):
        """ Get a reference to the task package by urlsafe key.

        :key: A urlsafe key to a task package
        :returns: @todo

        """
        return _k(safekey).get()

    def nextTask(self):
        """ Return a task from the progress.

        :returns: A new task from the package.

        """
        try:
            return self.progress[0].urlsafe()
        except IndexError:
            raise TaskPackage.NoMoreTask(self.getConfirmationCode())

    def finishATask(self, task):
        """ Set the task as finished.

        :task: The task to be set as finished.
        :returns: None.

        """
        assert task == self.progress[0].urlsafe(), \
            'Do not know the task: ' + task
        del self.progress[0]
        self.put()

    def getConfirmationCode(self):
        """ Get the confirmation code.

        :task_pack_id: @todo
        :returns: @todo

        """
        return self.confirm_code


class Session(Encodable):

    """ This is a class for session control. """

    def __init__(self):
        """ Init a session.

        :token: @todo
        :returns: @todo

        """
        self.user = None
        self.token = newToken('session')
        self.last_seen = dt.utcnow()

    @staticmethod
    def getOrStart(token=None):
        """ Get a session or start a new session. """
        if token:
            session = memcache.get(token)  # pylint: disable=E1101
            if isinstance(session, Session):
                return session
        session = Session()
        memcache.set(key=session.token,  # pylint: disable=E1101
                     value=session,
                     time=1800)
        return session

    def attach(self, user):
        """ Attach the identified user to this session.

        :user: A User object.
        :returns: self

        """
        self.user = user.key
        memcache.set(key=self.token,  # pylint: disable=E1101
                     value=self,
                     time=1800)
        return self

    def isAttached(self):
        """ Return whether this session has a registered user attached.

        :returns: @todo

        """
        return self.user is not None

    def heartBeat(self):
        """ Make heart beat for users' session.

        :returns: None
        :throws: ValueError if the last seen is long time ago.

        """
        if self.isDead():
            raise ValueError('Long time no see.')
        self.last_seen = dt.utcnow()
        if self.token is not None:
            memcache.set(key=self.token,  # pylint: disable=E1101
                         value=self,
                         time=3600)

    def isDead(self):
        """ Return whether the session is ended.

        :returns: @todo

        """
        assert self.last_seen <= dt.utcnow()
        return dt.utcnow() - self.last_seen > LONG_TIME

    def as_dict(self):
        """ Return a dict object representing the data.

        :returns: @todo

        """
        return {
            'token': self.token,
            'isAttached': self.isAttached()
        }
