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
from apps.profileviewer.models import Expert
from django.http import HttpResponse


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


APIENDPOINTS = {
    'expert_checkins': expert_checkins,
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
