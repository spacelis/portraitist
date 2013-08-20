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
from StringIO import StringIO
from google.appengine.ext import ndb

DEFAULT_APP_NAME = 'geo-expertise'


def parent_key(name, appname=DEFAULT_APP_NAME):
    """@todo: Docstring for parent_key.

    :name: @todo
    :appname: @todo
    :returns: @todo

    """
    return ndb.Key(appname, name)


class Expert(ndb.Model):

    """Candidate Expert for judging"""

    uid = ndb.StringProperty()
    screen_name = ndb.StringProperty()
    expertise = ndb.StringProperty()
    pois = ndb.JsonProperty(compressed=False)
    cate_timelines = ndb.JsonProperty(compressed=False)
    poi_timelines = ndb.JsonProperty(compressed=False)

    judged = ndb.BooleanProperty(indexed=True)
    judgment = ndb.JsonProperty()

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
        return cls.query(screen_name=screen_name).fetch(1)[0]

    @classmethod
    def get_all_screen_names(cls):
        """Return all screen_names with whether they have been judged or not
        :returns: @todo

        """
        return [{'screen_name': e.screen_name, 'judged': e.judged}
                for e in cls.query()]

    @classmethod
    def upload(cls, csv_string):
        """Upload data to dbs by reading from csv_string
        :returns: @todo

        """
        csv_in = StringIO(csv_string)
        for row in csv.reader(csv_in):
            cls(parent=parent_key('judgment'),
                uid=row[0],
                screen_name=row[1],
                expertise=row[2],
                pois=json.loads(row[3]),
                cate_timelines=json.loads(row[4]),
                poi_timelines=json.loads(row[5]),
                judged=False,
                judgment=json.loads('null')).put()
# TODO using key.urlsafe as a serialization in relating pages and judgments
