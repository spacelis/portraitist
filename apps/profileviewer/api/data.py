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
from datetime import datetime as dt
from datetime import timedelta
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
from django.shortcuts import redirect

from google.appengine.ext import ndb
import google.appengine.api.taskqueue as tq
import google.appengine.api.memcache as memcache
from google.appengine.datastore.datastore_query import Cursor

from apps.profileviewer.api import APIRegistry
from apps.profileviewer.util import throttle_map
from apps.profileviewer.util import fixCompressedEntity
from apps.profileviewer.util import listCompressedProperty

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import User
from apps.profileviewer.models import AnnotationTask
from apps.profileviewer.models import TaskPackage
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


@_REG.api_endpoint(secured=True)
def export_judgements(curkey):
    """ Export all judgements as json object per line.

    :returns: An iterator going over lines of json objects

    """
    if curkey:
        cur = Cursor(urlsafe=curkey)
    else:
        cur = None
    jdgs, next_cur, more = Judgement.query().fetch_page(10, start_cursor=cur)
    data = [j.as_viewdict() for j in jdgs]
    return {
        'next': APIRegistry.sign('/api/data/export_judgements?curkey=' + next_cur.urlsafe()),
        'data': data,
        'more': more
    }


@_REG.api_endpoint(secured=True)
def assign_taskpackage():
    """ Return a taskpackage unassigned. """
    try:
        mc = memcache.Client()
        pool = mc.gets('geo-expertise-tp-pool')
        tpkey = pool.pop(0)
        tp = _k(tpkey, 'TaskPackage').get()
        if len(tp.progress) == 0:
            tp.progress = tp.tasks
            tp.put()
        mc.cas('geo-expertise-tp-pool', pool, time=360000)
        return tpkey
    except (IndexError, AttributeError):
        tq.Task(params={'_admin_key': APIRegistry.ADMIN_KEY},
                url='/api/data/refill_taskpool',
                method='GET'
               ).add()
        raise TaskPackage.NoMoreTaskPackage()


@_REG.api_endpoint(secured=True)
def refill_taskpool():
    """ Refill the taskpool with non-recently touched tasks.
    :returns: TODO

    """
    tps = [tp.key.urlsafe()
           for tp in sorted(TaskPackage.query().fetch(), key=lambda x: len(x.progress) - len(x.tasks))]
    if len(tps) > 0:
        print 'Refilled with taskpackage:', len(tps)
        assert memcache.set('geo-expertise-tp-pool', tps)
        return {
            'action': 'refill_taskpool',
            'succeeded': True,
            'num': len(tps)
        }


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
                       'rank': rec['rank'],
                       'score': rec['score']}).put()
    return import_entities(filename, loader)


@_REG.api_endpoint(secured=True)
def task_stats():
    """ Return a statistics for tasks. """
    tasks = AnnotationTask.query()
    stats = [(t.key.urlsafe(), r.get().topic_id, t.candidate.urlsafe())
             for t in tasks.fetch()
             for r in t.rankings]
    return {
        'tasks': len(set(t[0] for t in stats)),
        'topics': len(set([t[1] for t in stats])),
        'candidates': len(set([t[2] for t in stats])),
        'rankings': len(stats)
    }


@_REG.api_endpoint(secured=True)
def model_stats():
    """ Return a statistics for tasks. """
    return {
        'AnnotationTask': len(AnnotationTask.query().fetch(keys_only=True)),
        'GeoEntity': len(GeoEntity.query().fetch(keys_only=True)),
        'TwitterAccount': len(TwitterAccount.query().fetch(keys_only=True)),
        'TaskPackage': len(TaskPackage.query().fetch(keys_only=True)),
        'ExpertiseRank': len(ExpertiseRank.query().fetch(keys_only=True)),
        'Judgement': len(Judgement.query().fetch(keys_only=True)),
        'User': len(User.query().fetch(keys_only=True))
    }


@_REG.api_endpoint(secured=True)
def judgement_stats():
    """ Return a statistics for tasks. """
    judgement = Judgement.query()
    stats = judgement.map(lambda x: (x.topic_id, x.candidate.urlsafe()))
    return {
        'judgement': len(stats),
        'topics': len(set([t[0] for t in stats])),
        'candidates': len(set([t[1] for t in stats])),
    }


@_REG.api_endpoint(secured=True)
def reset(level):
    """ Reset for welcoming new judgements
        Users and Judgements will be cleared
        Taskpackages progress will be reset
    """
    # reset levels
    PROGRESS = 'progress'
    ANNOTATION = 'annotation'
    TASKS = 'tasks'
    ALL = 'ALL'

    def remove(kind):
        """ Remove all entities in a model """
        return tq.Task(params={'_admin_key': APIRegistry.ADMIN_KEY,
                               'kind': kind},
                       url='/api/data/clear_entities',
                       method='GET'
                      ).add('batch')

    # Resetting
    if level in [PROGRESS, ANNOTATION, TASKS, ALL]:
        for tp in TaskPackage.query().fetch(keys_only=True):
            tq.Task(params={'key': tp,
                            '_admin_key': APIRegistry.ADMIN_KEY},
                    url='/api/data/reset_progress',
                    method='GET').add('batch')
    if level in [ANNOTATION, TASKS, ALL]:
        remove('User')
        remove('Judgement')
    if level in [TASKS, ALL]:
        remove('TaskPackage')
        remove('AnnotationTask')
    if level == ALL:
        remove('TwitterAccount')
        remove('GeoEntity')
        remove('ExpertiseRank')

    return {
        'action': 'reset',
        'level': level,
        'succeeded': True
    }


@_REG.api_endpoint(secured=True)
def reset_progress(tpkey):
    """ Reset taskpackage progress. """
    # pylint: disable=invalid-name
    tp = ndb.Key(urlsafe=tpkey).get()
    tp.progress = list(tp.tasks)
    tp.assigned_at = dt.strptime("2000-01-01", "%Y-%m-%d")
    tp.put()
    return {
        'action': 'reset_taskpackage',
        'suceeded': True,
        'tasks': len(tp.tasks),
        'ready': len(tp.progress)
    }


@_REG.api_endpoint(secured=True)
def clear_entities(kind):
    """ Remove all entities from the given model

    :kind: The name of the model (str)
    :returns: TODO

    """
    import apps.profileviewer.models as models
    ins = getattr(models, kind).query().fetch(keys_only=True)
    ndb.delete_multi(ins)
    return {
        'action': 'clear_entities',
        'kind': kind,
        'num': len(ins)
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
                rank = rank_key.get()
                if rank.rank_info['profile_type'] == 'rankCheckinProfile':
                    yield atask.key, rank.rank_method, rank.topic_id
    pairs = sorted(iter_annotationtask(), key=lambda x: (x[1], x[2]))
    cnt = 0
    for _, tasks in groupby(pairs, key=lambda x: (x[1], x[2])):
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
def AxdFKxbczxW(cf_code):
    """ Verify confirmation code.

    :cf_code: TODO
    :returns: TODO

    """
    try:
        return len(TaskPackage.query(TaskPackage.confirm_code == cf_code).fetch()[0].progress) == 0
    except:  # pylint: disable=bare-except
        pass
    return False


def export_as_csv(records):
    """ Export the records in csv

    :records: A list of records in dict objects
    :returns: A http response

    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="exported_taskpackages.csv"'

    iterrec = iter(records)
    try:
        rec = iterrec.next()
        csvwr = csv.DictWriter(response, rec.keys())
        csvwr.writeheader()
        csvwr.writerow(rec)
        csvwr.writerows(iterrec)
    except StopIteration:
        pass
    return response


@_REG.api_endpoint(secured=True, tojson=False)
def tasksearch(_request, timespan):
    """TODO: Docstring for tasks.
    :returns: TODO

    """
    start, end = [dt.strptime(x, '%Y-%m-%dT%H:%M:%S') for x in timespan.split(',')]
    url_template = lambda tid: _request.build_absolute_uri('/task/%s?review=1' % (tid,))
    resp = HttpResponse()
    resp.write('<html><body><ol>')
    for tp in TaskPackage.query(TaskPackage.assigned_at > start, TaskPackage.assigned_at < end).fetch():
        for t in tp.tasks:
            resp.write('<li><a href="{0}">{1.topic_id}</a></li>'
                       .format(url_template(t.urlsafe()),
                               t.get().rankings[0].get()))
    resp.write('</ol></body></html>')
    return resp


@_REG.api_endpoint(secured=True, tojson=False)
def export_taskpackages(_request, fmt='csv', verbose=False):
    """ Return a list of URLs to those taskpackages.
    :returns: @todo

    """
    from collections import Counter
    url_template = lambda tpid: _request.build_absolute_uri(
        '/pagerouter?action=taskpackage&tpid=%s' % (tpid,))

    def major_ranking(tasks):
        """ Find the major rank_method in the tasks """
        return Counter([r.get().rank_method
                        for t in tasks
                        for r in t.get().rankings]).most_common(1)[0]

    def iter_taskpackage():
        """ Iterating though task packages """
        for taskpackage in TaskPackage.query().fetch():
            if len(taskpackage.progress) == 0:
                continue
            if verbose:
                yield {'tpkey': taskpackage.key.urlsafe(),
                       'url': url_template(taskpackage.key.urlsafe()),
                       'confirm_code': taskpackage.confirm_code,
                       'rank_method': major_ranking(taskpackage.tasks),
                       'package_size': str(len(taskpackage.tasks))}
            else:
                yield {'tpkey': taskpackage.key.urlsafe(),
                       'url': url_template(taskpackage.key.urlsafe()),
                       'confirm_code': taskpackage.confirm_code}

    if fmt == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="exported_taskpackages.json"'
        json.dump(list(iter_taskpackage()), response)
    else:
        response = export_as_csv(iter_taskpackage())
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
        tq.Task(params={'key': k.urlsafe(),
                        'fields': ','.join(fields),
                        '_admin_key': APIRegistry.ADMIN_KEY},
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
        'suceeded': 'Unknown',
        'num': cnt,
        'message': 'The Fixing tasks added to the batch queue.'
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
