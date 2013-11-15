#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Handling HTTP API calls.

File: api.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    The api endpoints

"""

from json import dumps as _j
import inspect
from collections import namedtuple

from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404

from google.appengine.ext import ndb

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.util import request_property


EndPointSpec = namedtuple('EndPointSpec', ['func', 'spec', 'secured'])
_ENDPOINTS = dict()


def api_endpoint(secured=False):
    """ An decorator for API registry.

    Usage:
        @api_endpoint(secured=True)
        def an_api(a, b):
            # Do some stuff with a, b
            return # some stuff

    """

    def decorator(func):
        """ dummy. """
        name = func.__name__
        _ENDPOINTS[name] = EndPointSpec(func=func,
                                        spec=None,
                                        secured=secured)
        return func

    return decorator


def check_secure(req):
    """ Check whether the call is secured.

    :req: @todo
    :returns: @todo

    """
    if request_property(req, '_admin_key') != 'tu2013delft':
        raise PermissionDenied


def call_endpoint(request, name):
    """Call endpoint by name.

    :request: @todo
    :endpoint_name: @todo
    :returns: @todo

    """
    try:
        endpoint = _ENDPOINTS[name]
        if endpoint.secured:
            check_secure(request)
        if endpoint.spec is None:
            endpoint.spec = inspect.getargspec(endpoint.func)
        kwargs = {k: request.REQUEST.get(k, None) for k in endpoint.spec}
        return HttpResponse(endpoint.func(**kwargs),  # pylint: disable=W0142
                            mimetype="application/json")
    except KeyError:
        raise Http404


@api_endpoint(secured=True)
def checkins(candidate):
    """ Return all checkins for the candidate.

    :candidate: The urlsafe key to the TwitterAccount.
    :returns: All checkins from the database made by the twitter user

    """
    try:
        c = _k(candidate)
        assert c.kind == 'TwitterAccount'
        return _j(c.get().checkins)
    except AssertionError:
        return _j({'error': 'Please specify either a '
                   'screen_name or comma separated names.'})


@api_endpoint(secured=True)
def export_judgements(_):
    """ Export all judgements as json object per line.

    :returns: An iterator going over lines of json objects

    """
    def iter_judgement():
        """ An iterator over all judgements """
        for j in Judgement.query().fetch():
            yield _j({
                k: v.urlsafe()
                if isinstance(
                    Judgement._properties[k],  # pylint: disable=W0212
                    ndb.model.KeyProperty)
                else v
                for k, v in j.to_dict()
            }) + '\n'
    return iter_judgement()


# ------- Import/Export ------
import os.path
import gzip
import csv
import json


def flexopen(filename):
    """ Open file with according opener.

    :filename: @todo
    :returns: @todo

    """
    if filename.endswith('.gz'):
        return gzip.open(filename)
    else:
        return open(filename)


def import_entities(filename, loader):
    """ Import entities from file.

    :filename: The name of file in data.
    :loader: The function describe how the data should be loaded.
    :returns: None

    """
    path = os.path.join('data', filename)

    try:
        with flexopen(path) as fin:
            for r in csv.DictReader(fin):
                loader(r)
    except IOError:
        raise Http404


from apps.profileviewer.models import TwitterAccount


@api_endpoint(secured=True)
def import_candidates(filename):
    """ Import candidates from file.

    :filename: the name of file in data
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        TwitterAccount(screen_name=r['screen_name'],
                       checkins=json.loads(r['checkins'])).put()
    import_entities(filename, loader)


from apps.profileviewer.models import ExpertiseRank


@api_endpoint(secured=True)
def import_rankings(filename):
    """ Import rankings from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        ExpertiseRank(
            topic_id=r['topic_id'],
            topic=GeoEntity.getByTFId(r['associate_id']).key,
            region=r['region'],
            candidate=TwitterAccount.getByScreenName(r['screen_name']).key,
            rank=int(r['rank']),
            rank_info={'profile': r['profile_type'],
                       'method': r['rank_method']},).put()
    import_entities(filename, loader)


from apps.profileviewer.models import GeoEntity


@api_endpoint(secured=True)
def import_geoentities(filename):
    """ Import geo-entities from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        ExpertiseRank(tfid=r['id'],
                      name=r['name'],
                      group=r['type'],
                      relation=json.load(r['relation']),
                      url='').put()
    import_entities(filename, loader)


@api_endpoint(secured=True)
def assert_error():
    """ Bring a debug page for console. """
    assert False
