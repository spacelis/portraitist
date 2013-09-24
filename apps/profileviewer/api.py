#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: api.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    The api endpoints
"""

import inspect
import json
from json import dumps as _j

from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Judge


def assert_admin(req):
    """Make sure the call comes from admin

    :req: @todo
    :returns: @todo

    """
    if (req.REQUEST.get('_admin_key', None) or
            req.COOKIES.get('_admin_key', None)) != 'tu2013delft':
        raise PermissionDenied


class EndPoint(object):

    """A decorator registry"""

    EndPoints = dict()

    def __init__(self, secured=False):
        """Register an endpoint served in API

        :endpoint: @todo

        """
        self.secured = secured

    def __call__(self, endpoint):
        """Calling the wrapped endpoint

        :endpoint: real endpoint handler
        :returns: @todo

        """
        EndPoint.EndPoints[endpoint.__name__] = (endpoint, self.secured)


def call_endpoint(request, endpoint_name):
    """Call endpoint by name

    :request: @todo
    :endpoint_name: @todo
    :returns: @todo

    """
    if endpoint_name not in EndPoint.EndPoints:
        raise Http404
    endpoint, secured = EndPoint.EndPoints[endpoint_name]

    (not secured) or assert_admin(request)  # pylint: disable-msg=W0106
    argspec = inspect.getargspec(endpoint)
    args = {k: request.REQUEST.get(k, None) for k in argspec.args}
    return HttpResponse(endpoint(**args),  # pylint: disable-msg=W0142
                        mimetype="application/json")


@EndPoint(secured=False)
def expert_checkins(hash_id=None):
    """Return all checkins for the expert

    :hash_id: The hashlib.sha1 of twitter screen_name
    :returns: All checkins from the database made by the twitter user

    """
    if hash_id:
        checkins = Expert.getCheckinsInJson(
            Expert.getExpertByHashId(hash_id)
        )
        return checkins
    return _j({'error': 'Please specify either a '
              'screen_name or comma separated names.'})


@EndPoint(secured=True)
def sync_judgement():
    """Update Expert judged_by and judgement_no from Judge entities
    :returns: @todo

    """
    for e in Expert.query().fetch():
        e.judged_by = list()
        e.judged_no = 0
        e.put()
    for j in Judge.query().fetch():
        if isinstance(j.judgements, unicode):
            j.judgements = json.loads(j.judgements)
            j.put()
        j.judgement_no = len(j.judgements)
        j.put()
        assert isinstance(j.judgements, list), \
            'j.judgements is of type %s' % (type(j.judgements), )
        for ju in j.judgements:
            e = Expert.query(Expert.screen_name == ju['candidate']).fetch(1)[0]
            e.judged_by.append(j.judge_id)  # pylint: disable-msg=E1101
            e.judged_no += 1
            e.put()
    return _j({'msg': 'Sucesses!'})


@EndPoint(secured=True)
def ensure_datatype():
    """ When upload datastore finished, this function should be called to make
        sure the data types are correct.
    :returns: @todo

    """
    for j in Judge.query().fetch():
        if isinstance(j.judgements, str) or isinstance(j.judgements, unicode):
            j.judgements = json.loads(j.judgements)
            j.put()
    return _j({'msg': 'Sucesses!'})


@EndPoint(secured=True)
def view_judgements(judge_id):
    """ Return all judgements made by the judge

    :judge_id: The judge_id of a Judge
    :returns: All Judgement from the Judge in JSON

    """
    return _j(Judge.query(Judge.judge_id == judge_id).fetch(1)[0].judgements)


@EndPoint(secured=True)
def export_judgements():
    """
    :returns: @todo

    """
    def iter_judgement():
        """ An iterator over all judgements """
        for j in Judge.query().fetch():
            for ju in j.judgements:
                ju['judge_id'] = j.judge_id
                ju['judge_email'] = j.email
                ju['judge_nick'] = j.nickname
                yield _j(ju) + '\n'
    return iter_judgement()


@EndPoint(secured=True)
def assert_error():
    """ Bring a debug page for console
    """
    assert False
