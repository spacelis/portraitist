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
from datetime import datetime as dt

from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404

from google.appengine.ext import ndb

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import EmailAccount
from apps.profileviewer.models import Session
from apps.profileviewer.models import AnnotationTask
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.util import request_property


EndPointSpec = namedtuple('EndPointSpec', ['func', 'spec',
                                           'secured', 'jsonencoded'])
_ENDPOINTS = dict()


def api_endpoint(secured=False, jsonencoded=False):
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
                                        spec=inspect.getargspec(func),
                                        secured=secured,
                                        jsonencoded=jsonencoded)
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

    :request: Django HttpRequest object.
    :name: The name of the endpoint to call.
    :returns: Json string response.

    """
    try:
        endpoint = _ENDPOINTS[name]
        if endpoint.secured:
            check_secure(request)
        kwargs = {k: request.REQUEST.get(k, None) for k in endpoint.spec.args}
    except KeyError:
        raise Http404
    ret = endpoint.func(**kwargs)  # pylint: disable=W0142
    if endpoint.jsonencoded:
        return HttpResponse(ret, mimetype="application/json")
    else:
        return HttpResponse(_j(ret), mimetype="application/json")


@api_endpoint(secured=True)
def checkins(candidate):
    """ Return all checkins for the candidate.

    :candidate: The urlsafe key to the TwitterAccount.
    :returns: All checkins from the database made by the twitter user

    """
    try:
        c = _k(candidate)
        assert c.kind == 'TwitterAccount'
        return c.get().checkins
    except AssertionError:
        return {'error': 'Please specify either a '
                'screen_name or comma separated names.'}


@api_endpoint(secured=True, jsonencoded=True)
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
import os
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


@api_endpoint(secured=True)
def list_datafiles():
    """ List the data files in data dir.

    :returns: a list of files.

    """
    return os.listdir('apps/data')


def import_entities(filename, loader):
    """ Import entities from file.

    :filename: The name of file in data.
    :loader: The function describe how the data should be loaded.
    :returns: None

    """
    path = os.path.join('apps/data', filename)

    try:
        with flexopen(path) as fin:
            for r in csv.DictReader(fin):
                loader(r)
    except IOError:
        raise Http404
    return {'import': 'succeeded'}


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
    return import_entities(filename, loader)


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
            candidate=TwitterAccount.getByScreenName(r['candidate']).key,
            rank=int(r['rank']),
            rank_info={'profile': r['profile_type'],
                       'method': r['rank_method']},).put()
    return import_entities(filename, loader)


from apps.profileviewer.models import GeoEntity


@api_endpoint(secured=True)
def import_geoentities(filename):
    """ Import geo-entities from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        GeoEntity(tfid=r['tfid'],
                  name=r['name'],
                  level=r['level'],
                  info=json.loads(r['info']),
                  url=r['url']).put()
    return import_entities(filename, loader)


@api_endpoint(secured=False)  # FIXME should be secured
def make_tasks():
    """ Make tasks based on candidates. """
    candidates = ExpertiseRank.listCandidates()
    for c in candidates:
        rankings = ExpertiseRank.getForCandidate(c.candidate)
        AnnotationTask(rankings=[r.key for r in rankings],
                       candidate=c.key).put()
    return {'make_tasks': 'succeeded'}


def partition(it, size=10):
    """ Partitioning it into groups of 10 elements.

    :it: An iterator through some elements.
    :size: The maximum size of a group.
    :yields: a group containing at most the given size of
    the elements from it.

    """
    from itertools import cycle
    from itertools import groupby
    from itertools import izip

    for _, g in groupby(izip(cycle([0] * size + [1] * size), it),
                        key=lambda x: x[0]):
        yield [x for _, x in g]


@api_endpoint(secured=False)  # FIXME should be secured
def make_taskpackages():
    """ Group tasks in to packages. """
    from apps.profileviewer.models import newToken
    for ts in partition(AnnotationTask.query().fetch(), 10):
        tkeys = [t.key for t in ts]
        TaskPackage(
            tasks=tkeys,
            progress=tkeys,
            done_by=list(),
            confirm_code=newToken('').split('-')[-1],
            assigned_at=dt(2000, 1, 1)
        ).put()
    return {'make_taskpackages': 'succeeded'}


import re
EMAILPTN = re.compile(r"^[-!#$%&'*+/0-9=?A-Z^_a-z{|}~]"
                      r"(\.?[-!#$%&'*+/0-9=?A-Z^_a-z{|}~])*"
                      r"@[a-zA-Z](-?[a-zA-Z0-9])*"
                      r"(\.[a-zA-Z](-?[a-zA-Z0-9])*)+$")


@api_endpoint()
def email_login(email, passwd, token=None):
    """ Login the user with name and passwd.

    :email: the user email.
    :passwd: the passwd.

    """
    try:
        assert EMAILPTN.match(email)
        assert len(passwd) < 50
        user = EmailAccount.login(email, passwd)
        session = Session.getOrStart(token)
        session.attach(user)
        return {'login': True}
    except ValueError:
        return {'login': False}


@api_endpoint()
def email_signUp(email, passwd, name):
    """ SignUp this user.

    :email: email address.
    :passwd: the password.

    """
    try:
        assert EMAILPTN.match(email)
        assert len(passwd) < 50
        assert len(name) < 50
        EmailAccount.signUp(email, passwd, name)
    except AssertionError:
        return {'signup': False}


@api_endpoint(secured=True)
def assert_error():
    """ Bring a debug page for console. """
    assert False
