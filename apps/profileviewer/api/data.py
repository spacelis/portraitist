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
from datetime import datetime as dt

from django.http import Http404
from django.http import HttpResponse

from google.appengine.ext import ndb

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import AnnotationTask
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.util import throttle_map
from apps.profileviewer.api import APIRegistry


_REG = APIRegistry()


def call_endpoint(request, name):
    """Call endpoint by name.

    :request: Django HttpRequest object.
    :name: The name of the endpoint to call.
    :returns: Json string response.

    """
    return _REG.call_endpoint(request, name)


@_REG.api_endpoint(secured=False)
def checkins(candidate):
    """ Return all checkins for the candidate.

    :candidate: The urlsafe key to the TwitterAccount.
    :returns: All checkins from the database made by the twitter user

    """
    try:
        c = _k(candidate)
        assert c.kind() == 'TwitterAccount'
        return c.get().checkins
    except AssertionError:
        return {'error': 'Please specify a valid key to'
                'a twiter account.'}


@_REG.api_endpoint(secured=True, tojson=False)
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
    return HttpResponse(iter_judgement(), mimetype='application/json')


# ------- Import/Export ------
import os
import os.path
import gzip
import csv
import json

csv.field_size_limit(1000000)


def flexopen(filename):
    """ Open file with according opener.

    :filename: @todo
    :returns: @todo

    """
    if filename.endswith('.gz'):
        return gzip.open(filename)
    else:
        return open(filename)


@_REG.api_endpoint(secured=True)
def list_datafiles():
    """ List the data files in data dir.

    :returns: a list of files.

    """
    return os.listdir('apps/data')


def import_entities(filename, loader, pool=20):
    """ Import entities from file.

    :filename: The name of file in data.
    :loader: The function describe how the data should be loaded.
    :returns: None

    """
    path = os.path.join('apps/data', filename)

    @ndb.tasklet
    def async_loader(r):
        """ Async loader. """
        ndb.Return(loader(r))

    try:
        with flexopen(path) as fin:
            throttle_map(csv.DictReader(fin), async_loader, pool)
    except IOError:
        raise Http404
    return {'import': 'succeeded'}


from apps.profileviewer.models import TwitterAccount


@_REG.api_endpoint(secured=True)
def import_candidates(filename):
    """ Import candidates from file.

    :filename: the name of file in data
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        TwitterAccount(
            #parent=DEFAULT_PARENT_KEY,
            screen_name=r['screen_name'],
            checkins=json.loads(r['checkins'])).put()
    return import_entities(filename, loader)


from apps.profileviewer.models import ExpertiseRank


@_REG.api_endpoint(secured=True)
def import_rankings(filename):
    """ Import rankings from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        ExpertiseRank(
            #parent=DEFAULT_PARENT_KEY,
            topic_id=r['topic_id'],
            topic=GeoEntity.getByTFId(r['associate_id']).key,
            region=r['region'],
            candidate=TwitterAccount.getByScreenName(r['candidate']).key,
            rank=int(r['rank']),
            rank_info={'profile': r['profile_type'],
                       'method': r['rank_method']},).put()
    return import_entities(filename, loader)


@_REG.api_endpoint(secured=True)
def rankings_statistics():
    """ Return a statistics for rankings. """
    from itertools import groupby
    ranklists = set()
    rankpoints = set()
    num = 0
    for r in ExpertiseRank.query().fetch():
        ranklists.add((r.topic_id, r.region))
        rankpoints.add((r.topic_id, r.region, r.candidate))
        num += 1
    return {
        'ranklists': len(ranklists),
        'rankpoints': len(rankpoints),
        'regions': {k: len(list(g))
                    for k, g in groupby(sorted(ranklists, key=lambda x: x[1]),
                                        key=lambda x: x[1])},
        'total': num
    }


@_REG.api_endpoint(secured=True, disabled=True)
def clear_rankings():
    """ Delete all rankings from data store. """
    ndb.delete_multi([r.key for r in ExpertiseRank.query().fetch()])
    return {'clear_rankings': 'succeeded!'}


from apps.profileviewer.models import GeoEntity


@_REG.api_endpoint(secured=True)
def import_geoentities(filename):
    """ Import geo-entities from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(r):
        """ Loader for Twitter accounts and checkins. """
        d = json.loads(r['info'])
        GeoEntity(
            tfid=d['id'],
            name=d['name'],
            level=r['level'],
            info=json.loads(r['info']),
            url=r['url']).put()
    return import_entities(filename, loader)


@_REG.api_endpoint(secured=True)
def make_tasks():
    """ Make tasks based on candidates. """
    candidates = ExpertiseRank.listCandidates()
    for c in candidates:
        rankings = ExpertiseRank.getForCandidate(c.candidate)
        AnnotationTask(
            rankings=[r.key for r in rankings],
            candidate=c.candidate).put()
    return {'make_tasks': 'succeeded'}


@_REG.api_endpoint()
def clear_tasks():
    """ Remove all tasks. """
    ts = [t.key for t in AnnotationTask.query().fetch()]
    ndb.delete_multi(ts)
    return {'clear_tasks': 'succeeded'}


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


@_REG.api_endpoint(secured=True)
def make_taskpackages():
    """ Group tasks in to packages. """
    from apps.profileviewer.models import newToken
    for ts in partition(AnnotationTask.query().fetch(), 10):
        tkeys = [t.key for t in ts]
        TaskPackage(
            #parent=DEFAULT_PARENT_KEY,
            tasks=tkeys,
            progress=tkeys,
            done_by=list(),
            confirm_code=newToken('').split('-')[-1],
            assigned_at=dt(2000, 1, 1)
        ).put()
    return {'make_taskpackages': 'succeeded'}


@_REG.api_endpoint()
def assign_taskpackage(_user):
    """ Assign a new task package to the user.

    :_user: The user/session object.
    :returns: @todo

    """
    tp = TaskPackage.fetch_unassigned(1)[0]
    _user.assign(tp)
    return {'action': 'assign_taskpackage',
            'succeeded': True,
            'redirect': '/task_router'}


@_REG.api_endpoint(secured=True, tojson=False)
def export_tpkeys():
    """ Return a list of URLs to those taskpackages.
    :returns: @todo

    """
    import csv
    from StringIO import StringIO
    buf = StringIO()
    csvwr = csv.DictWriter(buf, ['tpkey'])
    csvwr.writeheader()
    for tp in TaskPackage.query().fetch():
        csvwr.writerow({'tpkey': tp.key.urlsafe()})
    return HttpResponse(buf.getvalue(), mimetype='text/csv')


@_REG.api_endpoint(secured=True)
def assert_error():
    """ Bring a debug page for console. """
    assert False
