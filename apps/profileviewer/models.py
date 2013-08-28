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

DEFAULT_APP_NAME = 'geo-expertise'
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

    experts = ndb.JsonProperty(compressed=False, indexed=False)
    detail = ndb.JsonProperty(compressed=False, indexed=False)

    judgment_number = ndb.IntegerProperty(indexed=True)
    judgments = ndb.JsonProperty()  # [[1, 1, 1, 0, 0], [0, 1, 0, 0, 1]]
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

    expertise = ndb.JsonProperty(compressed=False)
    checkins = ndb.JsonProperty(compressed=True, indexed=False)

    judged = ndb.BooleanProperty(indexed=True)
    judgments = ndb.JsonProperty()
    # pylint: enable-msg=E1101

    @classmethod
    def get_one_unjudged(cls):
        """Get one unjudged
        :returns: @todo

        """
        return cls.query(judged=False).sort(-cls.screen_name).fetch(1)[0]

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
        e['judgments'].append(judgment)
        e.populate(judged=True)
        e.put()

    @classmethod
    def get_all_screen_names(cls):
        """Return all screen_names with whether they have been judged or not
        :returns: @todo

        """
        return [{'screen_name': e.screen_name, 'judged': e.judged}
                for e in cls.query()]

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
                judged=False,
                judgments=[]).put()
