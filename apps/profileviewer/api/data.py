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

import os
import os.path
import gzip
import csv
import sys
import json
from json import dumps as _j
from datetime import datetime as dt
from itertools import groupby
from itertools import cycle
from itertools import izip

csv.field_size_limit(sys.maxsize)

from fn import Stream
from fn import _ as L
from fn.iters import drop
from fn.uniform import zip_longest
from fn.uniform import map  # pylint: disable=redefined-builtin
from django.http import Http404
from django.http import HttpResponse

from google.appengine.ext import ndb
from google.appengine.api.taskqueue import Task

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import AnnotationTask
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.api import APIRegistry
from apps.profileviewer.util import throttle_map
from apps.profileviewer.util import fixCompressedEntity
from apps.profileviewer.util import listCompressedProperty

from apps.profileviewer.models import GeoEntity
from apps.profileviewer.models import ExpertiseRank
from apps.profileviewer.models import TwitterAccount
from apps.profileviewer.models import newToken

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
        ckey = _k(candidate)
        assert ckey.kind() == 'TwitterAccount'
        return ckey.get().checkins
    except AssertionError:
        return {'error': 'Please specify a valid key toa twiter account.'}


@_REG.api_endpoint(secured=True, tojson=False)
def export_judgements(_):
    """ Export all judgements as json object per line.

    :returns: An iterator going over lines of json objects

    """
    def iter_judgement():
        """ An iterator over all judgements """
        for j in Judgement.query().fetch():
            yield _j({
                k: (v.urlsafe()
                    if isinstance(
                        Judgement._properties[k],  # pylint: disable=W0212
                        ndb.model.KeyProperty)
                    else v)
                for k, v in j.to_dict()
            }) + '\n'
    return HttpResponse(iter_judgement(), mimetype='application/json')


# ------- Import/Export ------
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
    def async_loader(rec):
        """ Async loader. """
        ndb.Return(loader(rec))

    try:
        with flexopen(path) as fin:
            cnt = throttle_map(csv.DictReader(fin), async_loader, pool)
    except IOError:
        raise Http404
    return {
        'action': 'import',
        'type': loader.func_doc,
        'succeeded': True,
        'imported': cnt
    }


@_REG.api_endpoint(secured=True)
def import_candidates(filename):
    """ Import candidates from file.

    :filename: the name of file in data
    :returns: @todo

    """
    def loader(rec):
        """ Loader for Twitter accounts and checkins. """
        TwitterAccount(
            # parent=DEFAULT_PARENT_KEY,
            screen_name=rec['screen_name'],
            checkins=json.loads(rec['checkins'])).put()
    return import_entities(filename, loader)


@_REG.api_endpoint(secured=True)
def import_rankings(filename):
    """ Import rankings from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """
    def loader(rec):
        """ Loader for Rankings. """
        ExpertiseRank(
            # parent=DEFAULT_PARENT_KEY,
            topic_id=rec['topic_id'],
            topic=GeoEntity.getByTFId(rec['associate_id']).key,
            region=rec['region'],
            candidate=TwitterAccount.getByScreenName(rec['candidate']).key,
            rank_method=rec['rank_method'],
            rank_info={'profile_type': rec['profile_type'],
                       'rank': rec['rank']}).put()
    return import_entities(filename, loader)


@_REG.api_endpoint(secured=True)
def rankings_statistics():
    """ Return a statistics for rankings. """
    ranklists = set()
    rankpoints = set()
    num = 0
    # pylint: disable=invalid-name
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


@_REG.api_endpoint(secured=True)
def clear_rankings():
    """ Delete all rankings from data store. """
    # pylint: disable=invalid-name
    rs = ExpertiseRank.query().fetch(keys_only=True)
    ndb.delete_multi(rs)
    return {
        'action': 'clear_rankings',
        'suceeded': True,
        'deleted': len(rs)
    }


@_REG.api_endpoint(secured=True, disabled=True)
def reset_progress():
    """ Reset taskpackage progress. """
    # pylint: disable=invalid-name
    tps = TaskPackage.query.fetch()
    for taskpackage in tps:
        taskpackage.progress = list(taskpackage.tasks)
    return {
        'action': 'reset_progress',
        'suceeded': True,
        'taskpackages': len(tps)
    }


@_REG.api_endpoint(secured=True)
def import_geoentities(filename):
    """ Import geo-entities from file.

    :filename: The filename of the ranking file.
    :returns: @todo

    """

    def loader(rec):
        """ Loader for Location info. """
        info = json.loads(rec['info'])
        GeoEntity(
            tfid=info['id'],
            name=info['name'],
            level=rec['level'],
            info=json.loads(rec['info']),
            example=rec['example'],
            url=rec['url']).put()
    return import_entities(filename, loader)


@_REG.api_endpoint()
def clear_tasks():
    """ Remove all tasks. """
    tasks = AnnotationTask.query().fetch(keys_only=True)
    ndb.delete_multi(tasks)
    return {
        'action': 'clear_tasks',
        'succeeded': True,
        'deleted': len(tasks)
    }


@_REG.api_endpoint()
def clear_taskpackages():
    """ Remove all tasks. """
    tasks = TaskPackage.query().fetch(keys_only=True)
    ndb.delete_multi(tasks)
    return {
        'action': 'clear_taskpackages',
        'succeeded': True,
        'deleted': len(tasks)
    }


def partition(iterator, size=10, margin=None):
    """ Partitioning iterator into groups of elements in given size.

    The margin is for the last group of elements.
    If there are less than margin number of elements, they will be
    grouped together. E.g., the last group may contain 15, 14, 13
    elements if margin is 15.

    :iterator: An iterator through some elements.
    :size: The maximum size of a group.
    :margin: If the rest of elements
    :yields: a group containing at most the given size of
    the elements from iterator.

    """

    margin = margin if margin else int(1.5 * size)
    assert margin < 2 * size, \
        'The margin %s is too large for size %s' % (margin, size)

    grps = Stream() << map(
        (lambda x: [i[1] for i in x]),
        map(L[1],
            Stream() <<
            groupby(izip(cycle([0] * size + [1] * size), iterator),
                    key=L[0])))
    for nex, cur in zip_longest(drop(1, grps), grps):
        if nex and len(cur + nex) <= margin:
            yield cur + nex
            return
        else:
            yield cur


@_REG.api_endpoint(secured=True)
def make_simple_tasks(rank_method, topic_id):
    """ Make tasks based on candidates. """
    candidates = ExpertiseRank.listCandidates(rank_method, topic_id)
    cnt = 0
    for cand in candidates:
        rankings = ExpertiseRank.getForCandidate(cand.candidate)
        for _, grp in groupby(sorted(rankings, key=L.topic_id),
                              key=L.topic_id):
            AnnotationTask(
                rankings=[r.key for r in grp],
                candidate=cand.candidate).put()
            cnt += 1
    return {
        'action': 'make_simple_tasks',
        'succeeded': True,
        'tasks': len(AnnotationTask.query().fetch(keys_only=True)),
        'num': cnt
    }


@_REG.api_endpoint(secured=True)
def make_compact_tasks():
    """ Make tasks based on candidates. """
    candidates = ExpertiseRank.listCandidates()
    cnt = 0
    for cand in candidates:
        rankings = ExpertiseRank.getForCandidate(cand.candidate)
        AnnotationTask(
            rankings=[r.key for r in rankings],
            candidate=cand.candidate).put()
        cnt += 1
    return {
        'action': 'make_compact_tasks',
        'succeeded': True,
        'tasks': len(AnnotationTask.query().fetch(keys_only=True)),
        'num': cnt
    }


@_REG.api_endpoint(secured=True)
def make_topical_taskpackages():
    """ Group tasks in to packages. """
    mapping = sorted([(at.key, at.rankings[0].get().topic_id)
                      for at in AnnotationTask.query().fetch()],
                     key=L[1])
    cnt = 0
    for _, tasks in groupby(mapping, key=L[1]):
        for tkeys in partition([t[0] for t in tasks], 10):
            TaskPackage(
                # parent=DEFAULT_PARENT_KEY,
                tasks=tkeys,
                progress=tkeys,
                done_by=list(),
                confirm_code=newToken('').split('-')[-1],
                assigned_at=dt(2000, 1, 1)
            ).put()
            cnt += 1
    return {
        'action': 'make_topical_taskpackages',
        'succeeded': True,
        'task_packages': len(TaskPackage.query().fetch(keys_only=True)),
        'num': cnt
    }


@_REG.api_endpoint(secured=True)
def make_methodical_taskpackages():
    """ Group tasks in to packages. """
    def iter_annotationtask():
        """ iterating though pairs of task and rank_method."""
        for atask in AnnotationTask.query().fetch():
            for rank_key in atask.rankings:
                yield atask.key, rank_key.get().rank_info['rank_method']
    pairs = sorted(iter_annotationtask(), key=L[1])
    cnt = 0
    for _, tasks in groupby(pairs, key=L[1]):
        for tkeys in partition([t[0] for t in tasks], 10):
            TaskPackage(
                # parent=DEFAULT_PARENT_KEY,
                tasks=tkeys,
                progress=tkeys,
                done_by=list(),
                confirm_code=newToken('').split('-')[-1],
                assigned_at=dt(2000, 1, 1)
            ).put()
            cnt += 1
    return {
        'action': 'make_methodical_taskpackages',
        'succeeded': True,
        'taskpackages': len(TaskPackage.query().fetch(keys_only=True)),
        'num': cnt
    }


@_REG.api_endpoint(secured=True)
def make_random_taskpackages():
    """ Group tasks in to packages. """
    cnt = 0
    for tasks in partition(AnnotationTask.query().fetch(), 10):
        tkeys = [t.key for t in tasks]
        TaskPackage(
            # parent=DEFAULT_PARENT_KEY,
            tasks=tkeys,
            progress=tkeys,
            done_by=list(),
            confirm_code=newToken('').split('-')[-1],
            assigned_at=dt(2000, 1, 1)
        ).put()
        cnt += 1
    return {
        'action': 'make_random_taskpackages',
        'succeeded': True,
        'taskpackages': len(TaskPackage.query().fetch(keys_only=True)),
        'num': cnt
    }


@_REG.api_endpoint()
def assign_taskpackage(_user):
    """ Assign a new task package to the user.

    :_user: The user/session object.
    :returns: @todo

    """
    taskpackage = TaskPackage.fetch_unassigned(1)[0]
    _user.assign(taskpackage)
    return {'action': 'assign_taskpackage',
            'succeeded': True,
            'redirect': '/pagerouter'}


@_REG.api_endpoint(secured=True, tojson=False)
def export_taskpackages(_request):
    """ Return a list of URLs to those taskpackages.
    :returns: @todo

    """
    url_template = lambda tpid: _request.build_absolute_uri(
        '/pagerouter?action=taskpackage&tpid=%s' % (tpid,))
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = \
        'inline; filename="tpkeys-confirmation.csv"'

    csvwr = csv.DictWriter(response, ['tpkey', 'confirm_code', 'package_size'])
    csvwr.writeheader()
    for taskpackage in TaskPackage.query().fetch():
        if len(taskpackage.progress) == 0:
            continue
        csvwr.writerow({'tpkey': url_template(taskpackage.key.urlsafe()),
                        'confirm_code': taskpackage.confirm_code,
                        'package_size': str(len(taskpackage.tasks))})
    return response


@_REG.api_endpoint(secured=True)
def assert_error():
    """ Bring a debug page for console. """
    assert False


# Fix compression wrapping for the restored data


def add_fixing_task(model):
    """ Add a fixing task to GAE queue so that the server will call the tasks
        at the defined schedule rate.

    """
    fields = listCompressedProperty(model)
    i = 0
    for i, k in enumerate(model.query().fetch(keys_only=True)):
        Task(params={'key': k.urlsafe(),
                     'fields': ','.join(fields),
                     '_admin_key': 'tu2013delft'},
             url='/api/data/fix_entity',
             method='GET').add('batch')
    return i


@_REG.api_endpoint(secured=True)
def fix_datastore():
    """ As resutore
    :returns: @todo

    """
    cnt = add_fixing_task(TwitterAccount)
    cnt += add_fixing_task(GeoEntity)
    cnt += add_fixing_task(ExpertiseRank)
    return {
        'action': 'fix_datastore',
        'suceeded': None,
        'message': '%s fixing tasks add to the batch queue.' % (cnt, )
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
