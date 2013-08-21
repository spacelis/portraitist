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

    # pylint: disable-msg=E1101
    screen_name = ndb.StringProperty()

    expertise = ndb.JsonProperty(compressed=False)
    pois = ndb.JsonProperty(compressed=False)
    cate_timelines = ndb.JsonProperty(compressed=False)
    poi_timelines = ndb.JsonProperty(compressed=False)

    judged = ndb.BooleanProperty(indexed=True)
    judgment = ndb.JsonProperty()
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
        e = cls.query(Expert.screen_name == screen_name).fetch(1)[0]
        d = dict()
        for p in e._properties:
            d[p] = getattr(e, p)
            if p in ['pois', 'cate_timelines', 'poi_timelines']:
                d[p] = json.dumps(d[p])
        return d

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
                screen_name=row[0],
                expertise=json.loads(row[1]),
                pois=json.loads(row[2]),
                cate_timelines=json.loads(row[3]),
                poi_timelines=json.loads(row[4]),
                judged=False,
                judgment=json.loads('null')).put()
# TODO using key.urlsafe as a serialization in relating pages and judgments
