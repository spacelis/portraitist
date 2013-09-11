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

from apps.profileviewer.models import Expert
from django.http import HttpResponse


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
    return 'Please specify either a screen_name or comma separated names.'


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
    return HttpResponse(api(**request.REQUEST),
                        mimetype="application/json")
