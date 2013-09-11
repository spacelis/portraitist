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

import json

from django.http import HttpResponse
from google.appengine.ext import ndb

from apps.profileviewer.models import Expert

def expert_checkins(screen_name=None, names=None):
    """Return all checkins for the expert

    :screen_name: @todo
    :returns: @todo

    """
    if screen_name:
        e = Expert.get_by_screen_name(screen_name)
        return e['checkins']
    elif names:
        r = dict()
        for n in names.split(','):
            r[n] = Expert.get_by_screen_name(n)
        return r
    else:
        return {'error': 'Please specify either a screen_name '
                'or comma separated names.'}


def export_judgments():
    """ return all judgments
    :returns: @todo

    """
    judgments = list()
    for e in Expert.query(Expert.judgment_number > 0).fetch():
        if not isinstance(e._values.get("judgments").b_val,
                            ndb.model._CompressedValue):
            e._values.get('judgments').b_val = ndb.model._CompressedValue(
                e._values.get('judgments').b_val)
        for jd in e.judgments:
            jd['screen_name'] = e.screen_name
            judgments.append(jd)
    return judgments


APIENDPOINTS = {
    'expert_checkins': expert_checkins,
    'export_judgments': export_judgments,
}


def endpoints(request, api_name):
    """An API return json data

    :request: @todo
    :api_name: @todo
    :returns: @todo

    """
    api = APIENDPOINTS[api_name]
    return HttpResponse(json.dumps(api(**request.REQUEST)),
                        mimetype="application/json")
