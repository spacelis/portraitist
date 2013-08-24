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


def expert_checkins(screen_name):
    """Return all checkins for the expert

    :screen_name: @todo
    :returns: @todo

    """
    e = Expert.get_by_screen_name(screen_name)
    return e['checkins']


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
