#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: models.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Expertise data model
"""

import csv
import json
from uuid import uuid4
from datetime import timedelta
from datetime import datetime as dt
from zlib import compress
from zlib import decompress
from hashlib import sha1

from google.appengine.ext import ndb

DEFAULT_APP_NAME = 'geo-expertise-2'
MIN30 = timedelta(minutes=30)
csv.field_size_limit(500000)


def parent_key(name, appname=DEFAULT_APP_NAME):
    """@todo: Docstring for parent_key.

    :name: @todo
    :appname: @todo
    :returns: @todo

    """
    return ndb.Key(appname, name)


class Judge(ndb.Model):

    """ A class representing users as judges."""

    # pylint: disable-msg=E1101
    nickname = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    judge_id = ndb.StringProperty(indexed=True)
    judgement_no = ndb.IntegerProperty(indexed=True)
    judgements = ndb.JsonProperty()
    # pylint: enable-msg=E1101

    @classmethod
    def upload(cls, fstream):
        """ Upload data to dbs by reading from a stream
        :fstream: A stream like object
        :returns: None

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('topic'),
                nickname='',
                email='',
                judge_id=row['judge_id'],
                judgement_no=int(row['judgement_no']),
                judgements=row['judgements'],
                ).put()

    @classmethod
    def newJudge(cls, email):
        """ Create a new judge user

        :email: An email address associate with this judge
        :returns: A newly created ndb judge object

        """
        return cls(parent_key=parent_key('judge'),
                   judge_id=uuid4(),
                   judgement_no=0,
                   email=email,
                   judgements=list())

    @classmethod
    def getJudgeById(cls, judge_id):
        """Return the judge object by given judge_id

        :judge_id: An string id assigned to each judge
        :returns: return the judge ndb object

        """
        judges = Judge.query(Judge.judge_id == judge_id).fetch(1)
        if not judges:
            return Judge(judge_id=judge_id,
                         judgement_no=0,
                         judgements=list())
        return judges[0]

    @classmethod
    def addJudgement(cls, judge_id, judgement):
        """@todo: Docstring for addJudgement.

        :judge_id: The id of the judge
        :judgement: A dict object holding the judgement made by the judge
        :returns: The ndb object of the judge

        """
        j = Judge.getJudgeById(judge_id)
        Expert.getExpertByScreenName(judgement['candidate'])\
            .judged_by.append(judge_id)
        j.judgements.append(judgement)
        j.judgement_no += 1
        j.put()
        return j

    @classmethod
    def statistics(cls):
        """ Return a dict object filled with statistics information

        :returns: {'judge_no', 'judgement_no'}

        """
        js = [j.judgement_no for j in
              Judge.query(projection=[Judge.judgement_no])]
        return {'judge_no': len(js),
                'j_judgement_no': sum(js)}


class Topic(ndb.Model):

    """Judgment tasks"""
    ZCATE_TOPIC = 'A topic about a top-level category.'
    CATE_TOPIC = 'A topic about a lower-level category.'
    POI_TOPIC = 'A topic about a specific place.'

    # pylint: disable-msg=E1101
    topic_id = ndb.StringProperty(indexed=True)
    topic = ndb.StringProperty()
    region = ndb.StringProperty()
    topic_type = ndb.ComputedProperty(
        lambda self: Topic.ZCATE_TOPIC if 'zcate' in self.topic_id
        else (Topic.CATE_TOPIC if 'cate' in self.topic_id
              else Topic.POI_TOPIC))

    experts = ndb.JsonProperty()
    related_to = ndb.JsonProperty()

    assigned = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

    @classmethod
    def getTopicById(cls, topic_id):
        """ Return topic by topic_id

        :topic_id: A given topic_id, e.g. "poi-0001", "zcate-0009"
        :returns: A dict object representing a Topic

        """
        t = cls.query(cls.topic_id == topic_id).fetch(1)[0]
        return {'topic_id': t.topic_id,
                'topic': t.topic,
                'region': t.region,
                'topic_type': t.topic_type,
                'related_to': t.related_to}

    @classmethod
    def upload(cls, fstream):
        """ Upload data to dbs by reading from a stream
        :fstream: A stream like object
        :returns: None

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('topic'),
                topic_id=row['topic_id'],
                topic=row['topic'],
                region=row['region'],
                experts=json.loads(row['experts']),
                related_to=json.loads(row['related_to']),
                ).put()


class Expert(ndb.Model):

    """Candidate Expert for judging"""

    # pylint: disable-msg=E1101
    screen_name = ndb.StringProperty(indexed=True)
    hash_id = ndb.ComputedProperty(
        lambda self: sha1(self.screen_name).hexdigest())

    topics = ndb.JsonProperty()
    checkins_store = ndb.BlobProperty()
    judged_by = ndb.StringProperty(repeated=True)
    judged_no = ndb.ComputedProperty(lambda self: len(self.judged_by))

    assigned = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

    @classmethod
    def getExpertsByPriority(cls, limit=10):
        """ Get a list of experts sorted by their priority for judging

        :returns: A list of experts

        """
        assert limit > 0
        return cls.query(Expert.assigned < (dt.now() - MIN30))\
            .order(Expert.assigned, Expert.judged_no)\
            .fetch(limit)

    @classmethod
    def getExpertInfoByHashId(cls, hash_id):
        """ Return a dict object holding basic information about the expert

        :screen_name: The screen_name of the expert
        :returns: A dict {'screen_name': str, 'topics': [topic_id: str]}

        """
        topics = cls.getExpertByHashId(hash_id).topics
        return {'hash_id': hash_id,
                'topics': topics}

    @classmethod
    def getExpertByHashId(cls, hash_id):
        """ Return a ndb object of the given expert

        :screen_name: The screen_name
        :returns: A ndb object of the expert

        """
        return cls.query(Expert.hash_id == hash_id).fetch(1)[0]

    @classmethod
    def getExpertInfoByScreenName(cls, screen_name):
        """ Return a dict object holding basic information about the expert

        :screen_name: The screen_name of the expert
        :returns: A dict {'screen_name': str, 'topics': [topic_id: str]}

        """
        e = cls.query(Expert.screen_name == screen_name).fetch(1)[0]
        return {'screen_name': e.screen_name,
                'topics': e.topics}

    @classmethod
    def getExpertByScreenName(cls, screen_name):
        """ Return a ndb object of the given expert

        :screen_name: The screen_name
        :returns: A ndb object of the expert

        """
        return cls.query(Expert.screen_name == screen_name).fetch(1)[0]

    @classmethod
    def getScreenNames(cls, limit=10):
        """ Return a list of screen_names ordered by their priority for judging

        :returns: [screen_name: str]

        """
        return [e.screen_name for e in cls.getExpertsByPriority(limit=limit)]

    @staticmethod
    def getCheckinsInJson(expert):
        """ Get the checkin profile for given user and return a json string

        :returns: checkins: json

        """
        return decompress(expert.checkins_store)

    @classmethod
    def getTask(cls):
        """ Get only one from the ordered screen_names by priority for judging

        :returns: screen_name

        """
        e = cls.getExpertsByPriority(1)[0]
        e.assigned = dt.now()
        e.put()
        return e.hash_id

    @classmethod
    def getJudgedExperts(cls):
        """ Return all judged experts
        :returns: [expert: Expert]

        """
        es = cls.query(Expert.judged_no > 0).fetch()
        return es

    @classmethod
    def upload(cls, fstream):
        """Upload data to dbs by reading from csv file stream
        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('expert'),
                screen_name=row['screen_name'],
                topics=json.loads(row['topics']),
                checkins_store=compress(row['checkins']),
                assigned=dt(2013, 1, 1),
                ).put()

    @classmethod
    def statistics(cls):
        """ Return a set of statistics

        :returns: {'judged_experts': int, 'expert_no': int,
                   'judgement_no': int}

        """
        es = [e.judged_no for e in
              Expert.query(projection=[Expert.judged_no]).fetch()]
        return {'judged_experts': len([e for e in es if e > 0]),
                'expert_no': len(es),
                'e_judgement_no': sum(es)}
