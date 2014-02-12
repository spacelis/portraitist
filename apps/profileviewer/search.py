#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" This module is responsible for search.

File: search.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:


"""


from google.appengine.api import search
from google.appengine.ext import ndb

INDEX = search.Index('EXPSEARCH')


class IndexEntry(ndb.Model):

    """ The model for storing index. """



    def __init__(self):
        """@todo: to be defined1. """
        ndb.Model.__init__(self)




def build_index(user, checkins):
    """ Build index for user with checkins.

    :user: @todo
    :checkins: @todo
    :returns: @todo

    """
    pass


def search_index(query):
    """ Search index with the query.

    :query: @todo
    :returns: @todo

    """
    pass
