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
from google.appengine.ext import ndb
from datetime import timedelta
from datetime import datetime as dt

DEFAULT_APP_NAME = 'geo-expertise'
MIN30 = timedelta(minutes=30)
csv.field_size_limit(500000)


def parent_key(name, appname=DEFAULT_APP_NAME):
    """@todo: Docstring for parent_key.

    :name: @todo
    :appname: @todo
    :returns: @todo

    """
    return ndb.Key(appname, name)


class Topic(ndb.Model):

    """Judgment tasks"""

    # pylint: disable-msg=E1101
    topic_id = ndb.StringProperty(indexed=True)
    topic = ndb.StringProperty()
    region = ndb.StringProperty()

    experts = ndb.JsonProperty(compressed=True, indexed=False)
    detail = ndb.JsonProperty(compressed=True, indexed=False)

    judgment_number = ndb.IntegerProperty(indexed=True)
    judgments = ndb.JsonProperty(compressed=True, indexed=False)  # [[1, 1, 1, 0, 0], [0, 1, 0, 0, 1]]
    # pylint: enable-msg=E1101

    @classmethod
    def getTopicById(cls, tid):
        """Return topic by id

        :tid: @todo
        :returns: @todo

        """
        d = cls.query(cls.topic_id == tid).fetch(1)[0]
        e = {'_key': d.key}
        e.update(d.to_dict())
        return e

    @classmethod
    def upload(cls, fstream):
        """Upload data to dbs by reading from csv_string
        :returns: @todo

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('topic'),
                topic_id=row['topic_id'],
                topic=row['topic'],
                region=row['region'],
                experts=json.loads(row['experts']),
                detail=json.loads(row['detail']),
                judgment_number=0,
                judgments=[]).put()

    @classmethod
    def update_judgment(cls, exp_id, judgment):
        """Update judgments on this topic

        :judgment: @todo
        :returns: @todo

        """
        t = ndb.Key(urlsafe=exp_id).get()
        t['judgments'].append(judgment)
        t['judgment_number'] += 1
        t.put()


class Expert(ndb.Model):

    """Candidate Expert for judging"""

    # pylint: disable-msg=E1101
    screen_name = ndb.StringProperty()

    expertise = ndb.JsonProperty(compressed=True)
    checkins = ndb.JsonProperty(compressed=True, indexed=False)

    judgment_number = ndb.IntegerProperty(indexed=True)
    judgments = ndb.JsonProperty(compressed=True)
    assigned = ndb.DateTimeProperty()
    # pylint: enable-msg=E1101

    @classmethod
    def get_by_priority(cls, limit=10):
        """Get a list of experts sorted by their priority for judging
        :returns: @todo

        """
        assert limit > 0
        return cls.query(Expert.assigned < (dt.now() - MIN30))\
                .order(Expert.assigned, Expert.judgment_number)\
                .fetch(limit)

    @classmethod
    def get_by_screen_name(cls, screen_name):
        """Return a user profile by the screen_name

        :screen_name: @todo
        :returns: @todo

        """
        d = cls.query(Expert.screen_name == screen_name)\
            .fetch(1)[0]
        e = {'exp_id': d.key.urlsafe(), '_key': d.key}
        e.update(d.to_dict())
        return e

    @classmethod
    def update_judgment(cls, exp_id, judgment):
        """Update the judgment about expert given exp_id

        :exp_id: @todo
        :judgment: @todo
        :returns: @todo

        """
        e = ndb.Key(urlsafe=exp_id).get()
        e.judgments.append(judgment)
        e.judgment_number += 1
        e.put()

    @classmethod
    def get_screen_names(cls, limit=10):
        """Return all screen_names with whether they have been judged or not
        :returns: @todo

        """
        return [e.screen_name for e in cls.get_by_priority(limit=limit)]

    @classmethod
    def upload(cls, fstream):
        """Upload data to dbs by reading from csv_string
        :returns: @todo

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('expert'),
                screen_name=row['screen_name'],
                expertise=json.loads(row['expertise']),
                checkins=json.loads(row['checkins']),
                judgment_number=0,
                judgments=[],
                assigned=dt(2013, 1, 1),
                ).put()
