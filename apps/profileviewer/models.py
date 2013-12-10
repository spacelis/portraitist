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

DEFAULT_PARENT_KEY = ndb.Key('Version', 'geo-expertise-3',
                             app='geo-expertise')
LONG_TIME = timedelta(minutes=30)
csv.field_size_limit(500000)


def newToken(prefix=''):
    """ Return a uuid as access token.

    :returns: a uuid4()

    """
    return prefix + '-' + str(uuid4())


def secure_hash(passwd, secret):
    """ Return sha1 hashcode.

    :s: @todo
    :returns: @todo

    """
    return hashlib.sha512(passwd + secret).hexdigest()  # pylint: disable=E1101


def _k(s, kind=None):
    """ Return a key of given urlsafe key s.

    :s: A urlsafe encoded key.
    :kind: Assert the key to be the kind.
    :returns: A ndb.Key.

    """
    k = ndb.Key(urlsafe=s)
    if kind is not None and k.kind() != kind:
        raise ValueError('Given urlsafe key is not of kind: ' + kind)
    return k


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

    JS_CLASS = """ JSON.parse(atob("%s")) """

    def js_encode(self):
        """ encode for javascript. """
        d = self.as_viewdict()
        return self.JS_CLASS % (base64.b64encode(json.dumps(d)), )

    @staticmethod
    def js_decode(b64str):
        """ decode the b64str into dict object.

        :b64str: the encoded json object.
        :return: the dict

        """
        d = json.loads(base64.b64decode(b64str))
        return d

    def as_viewdict(self):
        """ Return a dict representation of current object.

        :returns: A dict object.

        """
        raise NotImplementedError


class EncodableModel(ndb.Model, Encodable):  # pylint: disable=W0223

    """ A ndb based model with encoding and syncing. """

    @classmethod
    def synced(cls, val=None, b64=False):
        """ Sync the value and return the synced one.

        :val: A string encoded json object.
        :b64: Whether the string is base64 encoded.

        """
        assert not b64, "Base64 decoding is not supported yet."
        if isinstance(val, str) and len(val):
            raw_obj = Encodable.js_decode(val)
            d = {k: v for k, v in raw_obj.iteritems() if k != '__KEY__'}
            try:
                mobj = _k(raw_obj['__KEY__']).get()
                mobj.populate(**d)  # pylint: disable=W0142
            except KeyError:
                mobj = cls(**d)  # pylint: disable=W0142
            return mobj
        raise ValueError('`val` is not a valid string.')


class TwitterAccount(ndb.Model):  # pylint: disable=R0903,R0921

    """Docstring for TwitterAccount. """

    checkins = ndb.model.JsonProperty(indexed=False, compressed=True)
    friends = ndb.model.StringProperty(indexed=False, repeated=True)
    screen_name = ndb.model.StringProperty(indexed=True)
    access_token = ndb.model.StringProperty(indexed=True)
    access_token_secret = ndb.model.StringProperty(indexed=True)
    user = ndb.model.KeyProperty(indexed=True, kind='User')

    @staticmethod
    def singIn(access_token, access_token_secret, user):
        """ Sign in with users twitter account.

        :returns: @todo

        """
        tkey = TwitterAccount(
            parent=DEFAULT_PARENT_KEY,
            access_token=access_token,
            access_token_secret=access_token_secret,
            user_account=user.key
        ).put()
        user.put()
        user.populate(twitter_account=tkey)
        return user

    @staticmethod
    def getByScreenName(screen_name):
        """ Return the account with the given screen_name.

        :returns: A TwitterAccount

        """
        try:
            return TwitterAccount.query(
                TwitterAccount.screen_name == screen_name).fetch(1)[0]
        except IndexError:
            raise KeyError

    def fetchCheckins(self):
        """ Return the checkin as a block of base64 encoded.

        :returns: @todo

        """
        raise NotImplementedError


class EmailAccount(ndb.Model):

    """ The email account registered with this site. """

    email = ndb.model.StringProperty(indexed=True)
    hashed_passwd = ndb.model.StringProperty(indexed=False)
    user = ndb.model.KeyProperty(indexed=True, kind='User')
    secret = ndb.model.StringProperty(indexed=False)

    @staticmethod
    def signUp(email, passwd, name, user):
        """ Create a new judge user.

        :email: An email address associate with this judge.
        :passwd: An password for login.
        :name: An nickname used for greeting.
        :user: A user object holding temporary sesession information.
        :returns: A newly created User entity.

        """
        assertAbsent(EmailAccount, EmailAccount.email, email)
        secret = newToken('passwd')
        ukey = user.put()
        account = EmailAccount(
            parent=DEFAULT_PARENT_KEY,
            email=email,
            hashed_passwd=secure_hash(passwd, secret),
            secret=secret,
            user=ukey).put()
        user.populate(
            email_account=account,
            name=name,
            session_token=newToken('session')
        )
        user.put()
        return user

    @staticmethod
    def login(email, passwd, user):
        """ Sign in the account.

        :email: Registered email.
        :passwd: Registered password.
        :user: A user object holds temporary session information.
        :returns: A new token.

        """
        try:
            ea = EmailAccount.query(EmailAccount.email == email)\
                .fetch(1)[0]
            if secure_hash(passwd, ea.secret) == ea.hashed_passwd:
                u = ea.user.get()
                u.inherit(user)
                u.put()
                return u
            else:
                raise ValueError('Email or password wrong.')
        except IndexError:
            raise ValueError('Email or password wrong.')


class GeoEntity(EncodableModel):  # pylint: disable=R0903,W0223

    """ A model for entities like POI, Category. """

    tfid = ndb.model.StringProperty(indexed=True)
    name = ndb.model.StringProperty(indexed=False)
    level = ndb.model.StringProperty(indexed=False)  # e.g., category, poi
    info = ndb.model.JsonProperty(indexed=False)
    url = ndb.model.StringProperty(indexed=False)

    @staticmethod
    def getByTFId(tfid):
        """ Return the entity of the given tfid.

        :tfid: @todo
        :returns: A GeoEntity

        """
        try:
            return GeoEntity.query(GeoEntity.tfid == tfid).fetch(1)[0]
        except IndexError:
            raise KeyError()


class Judgement(ndb.Model):  # pylint: disable=R0903

    """ The judgement given by judges. """

    judge = ndb.model.KeyProperty(indexed=True, kind='User')
    candidate = ndb.model.KeyProperty(indexed=True, kind='User')
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
        ts = dt.utcnow()
        for t, s in scores:
            Judgement(
                parent=DEFAULT_PARENT_KEY,
                judge=_k(judge),
                candidate=_k(candidate),
                topic=_k(t),
                score=s,
                created_at=ts,
                ipaddr=ipaddr,
                user_agent=user_agent).put()


class ExpertiseRank(EncodableModel):  # pylint: disable=R0903,W0223

    """ The ranking needed to be annotated. """

    topic_id = ndb.model.StringProperty(indexed=True)
    topic = ndb.model.KeyProperty(indexed=True, kind=GeoEntity)
    region = ndb.model.StringProperty(indexed=True)
    candidate = ndb.model.KeyProperty(indexed=True, kind=TwitterAccount)
    rank = ndb.model.IntegerProperty(indexed=False)
    rank_info = ndb.model.JsonProperty(indexed=False)  # e.g., methods, profile

    class ExpertNotExists(Http404):
        """ Exception when the expert queried does not exist"""
        pass

    @staticmethod
    def getForCandidate(k_twitter_account):
        """ Get a list of Topics by given candidates.

        :k_twitter_account: The key to a TwitterAccount.
        :returns: A list of topics

        """
        return ExpertiseRank.query(
            ExpertiseRank.candidate == k_twitter_account).fetch()

    @staticmethod
    def listCandidates():
        """ Return a list of distinct candidates. """
        return ExpertiseRank.query(projection=['candidate'], distinct=True)


class AnnotationTask(ndb.Model):  # pylint: disable=R0903

    """ A task usually contains all rankings from one candidate. """

    rankings = ndb.model.KeyProperty(repeated=True, kind=ExpertiseRank)
    candidate = ndb.model.KeyProperty(indexed=True, kind=TwitterAccount)

    def as_viewdict(self):
        """ Return a dict object of the task.

        :returns: @todo

        """
        return {'rankings': [r.get() for r in self.rankings],
                'candidate': self.candidate.get()}

    @staticmethod
    def getByKey(key):
        """ Return the task indexed with the key.

        :key: @todo
        :returns: @todo

        """
        return ndb.Key(urlsafe=key).get()


class TaskPackage(ndb.Model):

    """ A package of tasks. """

    tasks = ndb.model.KeyProperty(repeated=True, kind=AnnotationTask)
    progress = ndb.model.KeyProperty(repeated=True, kind=AnnotationTask)
    done_by = ndb.model.KeyProperty(indexed=True, repeated=True, kind='User')
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

    def reset(self):
        """ Reset the progress of current task package. """
        self.progress = self.tasks
        self.put()


class User(EncodableModel):

    """ A class representing users as judges or candidates."""

    name = ndb.model.StringProperty(indexed=True)
    twitter_account = ndb.model.KeyProperty(indexed=True)
    email_account = ndb.model.KeyProperty(indexed=True)
    last_seen = ndb.model.DateTimeProperty()
    finished_tasks = ndb.model.IntegerProperty(indexed=False)
    show_instructions = ndb.model.BooleanProperty(indexed=False)
    task_package = ndb.model.KeyProperty(indexed=False)
    session_token = ndb.model.StringProperty(indexed=True)

    def addTwitterAccount(self, twitter_account):
        """ Linking a twitter account to this user.

        :returns: @todo

        """
        self.twitter_account = twitter_account.key

    def as_viewdict(self):
        """ Return a dict object encapsulate the information of this user.
        :returns: @todo

        """
        return {
            'name': self.name,
            'session_token': self.session_token,
            'finished_tasks': self.finished_tasks,
            'show_instructions': self.show_instructions,
            'is_known_user': self.isKnownUser(),
            'task_package': None if self.task_package is None
            else self.task_package.urlsafe(),
        }

    @staticmethod
    def unit():
        """ Return an empty user object. """
        return User(
            parent=DEFAULT_PARENT_KEY,
            name='Unkown User',
            finished_tasks=0,
            session_token=newToken('session'),
            show_instructions=True,
            last_seen=dt.utcnow()
        )

    @staticmethod
    def getOrCreate(token=None):
        """ Get a session or start a new session. """
        if token:
            u = memcache.get(token)  # pylint: disable=E1101
            if isinstance(u, User):
                return u
        u = User.unit()
        u.cache()
        return u

    def cache(self):
        """ Make self available in cache. """
        memcache.set(key=self.session_token,  # pylint: disable=E1101
                     value=self,
                     time=1800)
        return self

    def reset_token(self):
        """ Assign a new session token to this user. """
        self.populate(session_token=newToken('session'))
        self.put()
        self.cache()

    def assign(self, task_package):
        """ Assign a task package for this session.

        :task_package: TaskPackage object as ndb.Model
        :returns: self

        """
        self.task_package = task_package
        return self

    def touch(self):
        """ Make heart beat for a user's session.

        Updating the last_seen checkin point.
        Updating values in memcache.

        :returns: None
        :throws: ValueError if the last seen is long time ago.

        """
        if self.isDead():
            raise ValueError('Long time no see.')
        self.last_seen = dt.utcnow()
        if self.session_token is not None:
            memcache.set(key=self.session_token,  # pylint: disable=E1101
                         value=self,
                         time=3600)
        self.put()

    def isDead(self):
        """ Return whether the session is ended.

        :returns: True if this session is timeout

        """
        assert self.last_seen <= dt.utcnow()
        isdead = dt.utcnow() - self.last_seen > LONG_TIME
        return isdead

    def inherit(self, user):
        """ Inherit the property of other user.

        :user: @todo
        :returns: @todo

        """
        self.finished_tasks += user.finished_tasks
        self.show_instructions |= user.show_instructions

    def isKnownUser(self):
        """ Whether this user is known (not temporary user)self.
        :returns: @todo

        """
        return self.key.integer_id() is not None
