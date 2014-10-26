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
from itertools import groupby

from fn import Stream
from fn import _ as L
from fn.iters import drop
from fn.uniform import zip_longest
from fn.uniform import map
from django.http import Http404
from django.http import HttpResponse

from google.appengine.ext import ndb

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import AnnotationTask
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.util import throttle_map
from apps.profileviewer.api import APIRegistry
from apps.profileviewer.util import fixCompressedEntity


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
            # parent=DEFAULT_PARENT_KEY,
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
            # parent=DEFAULT_PARENT_KEY,
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
                    for k, g in groupby(sorted(ranklists, key=L[1]),
                                        key=L[1])},
        'total': num
    }


@_REG.api_endpoint(secured=True, disabled=True)
def clear_rankings():
    """ Delete all rankings from data store. """
    ndb.delete_multi([r.key for r in ExpertiseRank.query().fetch()])
    return {'clear_rankings': 'succeeded!'}


@_REG.api_endpoint(secured=True, disabled=True)
def reset_progress():
    """ Reset taskpackage progress. """
    for tp in TaskPackage.query.fetch():
        tp.progress = list(tp.tasks)
    return {'reset_progress': 'succeeded!'}


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
            example=r['example'],
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


def partition(it, size=10, margin=None):
    """ Partitioning it into groups of elements in given size.

    The margin is for the last group of elements.
    If there are less than margin number of elements, they will be
    grouped together. E.g., the last group may contain 15, 14, 13
    elements if margin is 15.

    :it: An iterator through some elements.
    :size: The maximum size of a group.
    :margin: If the rest of elements
    :yields: a group containing at most the given size of
    the elements from it.

    """
    from itertools import cycle
    from itertools import groupby
    from itertools import izip

    margin = margin if margin else int(1.5 * size)
    assert margin < 2 * size, \
        'The margin %s is too large for size %s' % (margin, size)

    grps = Stream() << map(
        (lambda x: [i[1] for i in x]),
        map(L[1],
            Stream() <<
            groupby(izip(cycle([0] * size + [1] * size), it),
                    key=L[0])))
    for nex, cur in zip_longest(drop(1, grps), grps):
        if nex and len(cur + nex) <= margin:
            yield cur + nex
            return
        else:
            yield cur


@_REG.api_endpoint(secured=True)
def make_qtasks():
    """ Make tasks based on candidates. """
    candidates = ExpertiseRank.listCandidates()
    for c in candidates:
        rankings = ExpertiseRank.getForCandidate(c.candidate)
        for k, g in groupby(sorted(rankings, key=L.topic_id),
                            key=L.topic_id):
            AnnotationTask(
                rankings=[r.key for r in g],
                candidate=c.candidate).put()
    return {'make_tasks': 'succeeded'}


@_REG.api_endpoint(secured=True)
def make_qtaskpackages():
    """ Group tasks in to packages. """
    from apps.profileviewer.models import newToken
    mapping = sorted([(at.key, at.rankings[0].get().topic_id)
                      for at in AnnotationTask.query().fetch()],
                     key=L[1])
    for topic_id, ts in groupby(mapping, key=L[1]):
        for tkeys in partition([t[0] for t in ts], 10):
            TaskPackage(
                # parent=DEFAULT_PARENT_KEY,
                tasks=tkeys,
                progress=tkeys,
                done_by=list(),
                confirm_code=newToken('').split('-')[-1],
                assigned_at=dt(2000, 1, 1)
            ).put()
    return {'make_taskpackages': 'succeeded'}


@_REG.api_endpoint(secured=True)
def make_taskpackages():
    """ Group tasks in to packages. """
    from apps.profileviewer.models import newToken
    for ts in partition(AnnotationTask.query().fetch(), 10):
        tkeys = [t.key for t in ts]
        TaskPackage(
            # parent=DEFAULT_PARENT_KEY,
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
            'redirect': '/pagerouter'}


@_REG.api_endpoint(secured=True, tojson=False)
def export_taskpackages(_request):
    """ Return a list of URLs to those taskpackages.
    :returns: @todo

    """
    import csv
    url_template = lambda tpid: _request.build_absolute_uri(
        '/pagerouter?action=taskpackage&tpid=%s' % (tpid,))
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = \
        'inline; filename="tpkeys-confirmation.csv"'

    csvwr = csv.DictWriter(response, ['tpkey', 'confirm_code', 'package_size'])
    csvwr.writeheader()
    for tp in TaskPackage.query().fetch():
        csvwr.writerow({'tpkey': url_template(tp.key.urlsafe()),
                        'confirm_code': tp.confirm_code,
                        'package_size': str(len(tp.tasks)),
                        })
    return response


@_REG.api_endpoint(secured=True)
def assert_error():
    """ Bring a debug page for console. """
    assert False


@_REG.api_endpoint(secured=True)
def fix_datastore():
    """ As resutore
    :returns: @todo

    """
    from apps.profileviewer.util import findBrokenFields
    from apps.profileviewer.models import TwitterAccount
    from google.appengine.api.taskqueue import Task
    fields = findBrokenFields(TwitterAccount)
    for k in TwitterAccount.query().fetch(keys_only=True):
        Task(params={'key': k.urlsafe(),
                     'fields': ','.join(fields),
                     '_admin_key': 'tu2013delft'},
             url='/api/data/fix_entity',
             method='GET'
             ).add('batch')
    return {
        'action': 'fix_datastore',
        'suceeded': None,
        'message': 'Check the batch queue for the status of fixing process.'
    }


@_REG.api_endpoint(secured=True)
def fix_entity(key, fields):
    """@todo: Docstring for fix_entity.

    :key: @todo
    :fields: @todo

    """
    fixCompressedEntity(_k(key), fields.split(','))
    return {
        'action': 'fix_entity',
        'suceeded': True,
        'message': 'Fixing compressed field for entity.'
    }
