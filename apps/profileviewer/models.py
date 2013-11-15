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


class BaseModel(ndb.Model):

    """ A unified model. """

    # pylint: disable-msg=E1101
    bm_version = ndb.IntegerProperty(default=0)
    # pylint: enable-msg=E1101
    bm_protected = None
    bm_keyproperties = None
    BM_KEYNAME = '__KEY__'

    def js_encode(self):
        """ encode for javascript. """
        self.__class__._ensure_keyproperties()  # pylint: disable=W0212
        d = self.to_dict()
        d = {k: d[k] for k in self._properties
             if k not in self.bm_keyproperties}
        if self.key:
            d[self.BM_KEYNAME] = self.key.urlsafe()
        return 'JSON.parse(atob("%s"))' % (base64.b64encode(json.dumps(d)), )

    @staticmethod
    def _decode(encoded):
        """ decode from the encoded. """
        return json.loads(base64.b64decode(encoded))

    @classmethod
    def _ensure_keyproperties(cls):
        """ Ensure that _keyproperties being initialized before use.

        :returns: None

        """
        if cls.bm_keyproperties is None:
            cls.bm_keyproperties = list()
            for n, p in cls._properties.iteritems():
                # pylint: disable=E1101
                if isinstance(p, ndb.model.KeyProperty):
                    cls.bm_keyproperties.append(n)
                # pylint: enable=E1101

    @classmethod
    def js_decode(cls, val=None):
        """ Sync the value and return the synced one. """
        cls._ensure_keyproperties()
        if isinstance(val, str) and len(val):
            raw_obj = cls.js_decode(val)
            mobj = _k(raw_obj[cls.BM_KEYNAME]).get()
            ver = raw_obj['bm_version']
            d = {k: v
                 for k, v in raw_obj.iteritems()
                 if k in cls._properties and
                 k not in cls.bm_keyproperties and
                 k not in cls.bm_protected}
            if mobj.bm_version < ver:  # pylint: disable-msg=W0212
                mobj.populate(**d)  # pylint: disable-msg=W0142
            return mobj


class TwitterAccount(ndb.Model):  # pylint: disable-msg=R0903,R0921

    """Docstring for TwitterAccount. """

    # pylint: disable-msg=E1101
    checkins = ndb.JsonProperty(indexed=False, compressed=True)
    friends = ndb.StringProperty(indexed=False, repeated=True)
    screen_name = ndb.StringProperty(indexed=True)
    access_token = ndb.StringProperty(indexed=True)
    access_token_secret = ndb.StringProperty(indexed=True)
    user = ndb.KeyProperty(indexed=True, kind='User')
    # pylint: enable-msg=E1101

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

    # pylint: disable-msg=E1101
    name = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    passwd = ndb.StringProperty(indexed=True)
    user = ndb.KeyProperty(indexed=True, kind='User')
    # pylint: enable-msg=E1101

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
                    last_seen=dt.utcnow(),
                    token=newToken(),
                    email_account=None,
                    twitter_account=None).put()
        account = EmailAccount(email=email,
                               name=name,
                               passwd=secure_hash(passwd),
                               user=user).put()
        user.get().populate(email_account=account)
        return user.get()

    @staticmethod
    def signIn(email, passwd):
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
            token = newToken()
            user.populate(token=token, last_seen=dt.utcnow())
            return token
        except IndexError:
            raise ValueError('User not found.')


class User(ndb.Model):

    """ A class representing users as judges or candidates."""

    # pylint: disable-msg=E1101
    twitter_account = ndb.KeyProperty(indexed=True)
    email_account = ndb.KeyProperty(indexed=True)
    last_seen = ndb.DateTimeProperty(indexed=False)
    token = ndb.StringProperty(indexed=True)  # UUID4
    info = ndb.JsonProperty(indexed=False)
    # pylint: enable-msg=E1101

    def getName(self):
        """ Return a name for this user.

        :returns: @todo

        """
        if self.twitter_account:
            return self.twitter_account.get().screen_name
        elif self.email_account:
            return self.email_account.get().name
        else:
            return "Unknown User"

    @staticmethod
    def default_info():
        """ Return the default info object. """
        return {
            'show_instructions': 1,
            'done_survey': 0,
            'done_tasks': 0,
            'version': 0
        }

    def getSyncedInfo(self, info=None):
        """ Return associated information of the user.

        :return: A dict() object.

        """
        if not info:
            info = User.default_info()
        if not self.info or self.info['version'] < info['version']:
            self.info = info
            self.put()
            return info
        else:
            return self.info

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

    def heartBeat(self):
        """ Make heart beat for users' session.

        :returns: None
        :throws: ValueError if the last seen is long time ago.

        """
        if self.isDead():
            raise ValueError('Long time no see.')
        self.populate(last_seen=dt.utcnow())
        if self.token is not None:
            memcache.set(key='User.' + self.token,  # pylint: disable=E1101
                         value=self,
                         time=3600)

    def isDead(self):
        """ Return whether the session is ended.

        :returns: @todo

        """
        assert self.last_seen <= dt.utcnow()
        return dt.utcnow() - self.last_seen > LONG_TIME

    @staticmethod
    def getByToken(token):
        """ Return the user object holding the token.

        :token: @todo
        :returns: @todo

        """
        try:
            user = (memcache.get('User.' + token)  # pylint: disable=E1101
                    or User.query(User.token == token).fetch(1)[0])
            user.heartBeat()
        except IndexError:
            raise ValueError('Token not found: ' + token)


class GeoEntity(ndb.Model):  # pylint: disable-msg=R0903

    """ A model for entities like POI, Category. """

    # pylint: disable-msg=E1101
    tfid = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    group = ndb.StringProperty(indexed=False)  # e.g., category, poi
    relation = ndb.JsonProperty(indexed=False)
    url = ndb.StringProperty(indexed=False)
    # pylint: enable-msg=E1101

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


class Judgement(ndb.Model):  # pylint: disable-msg=R0903

    """ The judgement given by judges. """

    # pylint: disable-msg=E1101
    judge = ndb.KeyProperty(indexed=True, kind=User)
    candidate = ndb.KeyProperty(indexed=True, kind=User)
    topic = ndb.KeyProperty(indexed=True, kind=GeoEntity)
    score = ndb.IntegerProperty(indexed=False)
    created_at = ndb.DateTimeProperty(indexed=False)
    ipaddr = ndb.StringProperty(indexed=False)
    user_agent = ndb.StringProperty(indexed=False)
    # pylint: enable-msg=E1101

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


class ExpertiseRank(ndb.Model):  # pylint: disable-msg=R0903

    """ The ranking needed to be annotated. """

    # pylint: disable-msg=E1101
    topic_id = ndb.StringProperty(indexed=False)
    topic = ndb.KeyProperty(indexed=True, kind=GeoEntity)
    region = ndb.StringProperty(indexed=True)
    candidate = ndb.KeyProperty(indexed=True, kind=TwitterAccount)
    rank = ndb.IntegerProperty(indexed=False)
    rank_info = ndb.JsonProperty(indexed=False)  # e.g., methods, profile
    # pylint: enable-msg=E1101

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

    # pylint: disable-msg=E1101
    rankings = ndb.KeyProperty(repeated=True)
    # pylint: enable-msg=E1101


class TaskPackage(ndb.Model):

    """ A package of tasks. """

    # pylint: disable-msg=E1101
    tasks = ndb.KeyProperty(repeated=True, kind=AnnotationTask)
    progress = ndb.KeyProperty(repeated=True, kind=AnnotationTask)
    done_by = ndb.KeyProperty(indexed=True, repeated=True, kind=User)
    confirm_code = ndb.StringProperty()
    assigned_at = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

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


class Session(ndb.Model):

    """ This is a class for session control. """

    # pylint: disable-msg=E1101
    user = ndb.KeyProperty(indexed=True, kind=User)
    token = ndb.StringProperty(indexed=True)
    # pylint: enable-msg=E1101

    @staticmethod
    def getOrStart(token=None):
        """ Get a session or start a new session. """
        if token:
            session = memcache.get(token)  # pylint: disable=E1101
            if isinstance(session, Session):
                return session
        token = newToken('session')
        memcache.set(key=token,  # pylint: disable=E1101
                     value=Session(user=None, token=token),
                     time=1800)
        return session

    def attach(self, user):
        """ Attach the identified user to this session.

        :user: A User object.
        :returns: self

        """
        self.user = user.key
        return self

    def isAttached(self):
        """ Return whether this session has a registered user attached.

        :returns: @todo

        """
        return self.user is not None
