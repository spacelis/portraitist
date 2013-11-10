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

from django.http import Http404
from google.appengine.ext import ndb

DEFAULT_PARENT_KEY = 'geo-expertise-3'
LONG_TIME = timedelta(minutes=30)
csv.field_size_limit(500000)


def newToken():
    """ Return a uuid as access token.

    :returns: a uuid4()

    """
    return str(uuid4())


def secure_hash(s):
    """ Return sha1 hashcode.

    :s: @todo
    :returns: @todo

    """
    return hashlib.sha512(s).hexdigest()  # pylint: disable-msg=E1101


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


class TwitterAccount(ndb.Model):  # pylint: disable-msg=R0903

    """Docstring for TwitterAccount. """

    # pylint: disable-msg=E1101
    checkin = ndb.JsonProperty(repeated=True, index=False, compressed=True)
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
        :returns: A newly created account entity.

        """
        assertAbsent(EmailAccount, EmailAccount.email, email)
        user = User(parent=DEFAULT_PARENT_KEY,
                    last_seen=dt.utcnow(),
                    token=newToken(),
                    email_account=None,
                    twitter_account=None)
        account = EmailAccount(email=email,
                               name=name,
                               passwd=secure_hash(passwd),
                               user=user.key)
        user.populate(email_account=account).put()
        account.put()
        return user

    @staticmethod
    def signIn(email, passwd):
        """ Sign in the account.

        :email: @todo
        :passwd: @todo
        :returns: @todo

        """
        try:
            user = EmailAccount.query(
                (EmailAccount.email == email),
                (EmailAccount.passwd == secure_hash(passwd))).fetch(1)[0]
            user.token = newToken()
            user.last_seen = dt.utcnow()
        except IndexError:
            raise ValueError('User not found.')


class User(ndb.Model):

    """ A class representing users as judges or candidates."""

    # pylint: disable-msg=E1101
    twitter_account = ndb.KeyProperty(indexed=True)
    email_account = ndb.KeyProperty(indexed=True)
    last_seen = ndb.DateTimeProperty(indexed=False)
    token = ndb.StringProperty(index=True)  # UUID4
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
        if (dt.utcnow() - self.last_seen > LONG_TIME):
            raise ValueError('Long time no see.')
        self.last_seen = dt.utcnow()

    @staticmethod
    def getByToken(token):
        """ Return the user object holding the token.

        :token: @todo
        :returns: @todo

        """
        try:
            return User.query(User.token == token).fetch(1)[0]
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


class Judgement(ndb.Model):  # pylint: disable-msg=R0903

    """ The judgement given by judges. """

    # pylint: disable-msg=E1101
    judge = ndb.KeyProperty(indexed=True, kind=User)()
    candidate = ndb.KeyProperty(index=True, kind=User)
    topic = ndb.KeyProperty(indexed=True, kind=GeoEntity)
    score = ndb.IntegerProperty(indexed=False)
    created_at = ndb.DateTimeProperty(index=False)
    ipaddr = ndb.StringProperty(index=False)
    user_agent = ndb.StringProperty(index=False)
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
    user = ndb.KeyProperty(indexed=True, kind=User)
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


class TaskPackage(ndb.Model):

    """ A package of tasks. """

    # pylint: disable-msg=E1101
    tasks = ndb.KeyProperty(repeated=True)  # keys to candidates
    progress = ndb.KeyProperty(repeated=True)
    done_by = ndb.KeyProperty(indexed=True, repeated=True)
    confirm_code = ndb.StringProperty()
    assigned_at = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

    class TaskPackageNotExists(Http404):
        """ If the task_pack_id doesn't exists"""
        pass

    class NoMoreTask(Exception):
        """ If there is no more tasks to assign"""
        pass

    @staticmethod
    def getTaskPackage(safekey):
        """ Get a reference to the task package by urlsafe key.

        :key: A urlsafe key to a task package
        :returns: @todo

        """
        return _k(safekey).get()

    def getTasks(self):
        """ Return a task from the progress.

        :task_pack_id: @todo
        :returns: @todo

        """
        return self.progress[0].urlsafe()

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
