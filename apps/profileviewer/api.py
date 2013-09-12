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


class EndPoint(object):

    """A decorator registry"""

    EndPoints = dict()

    def __init__(self, endpoint):
        """Register an endpoint served in API

        :endpoint: @todo

        """
        self._endpoint = endpoint
        EndPoint.EndPoints[endpoint.__name__] = endpoint

    def __call__(self, *args, **kargs):
        """Calling the wrapped endpoint

        :*args: @todo
        :**kargs: @todo
        :returns: @todo

        """
        self._endpoint(*args, **kargs)


@EndPoint
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


def call_endpoint(request, endpoint_name):
    """Call endpoint by name

    :request: @todo
    :endpoint_name: @todo
    :returns: @todo

    """
    endpoint = EndPoint.EndPoints[endpoint_name]
    return HttpResponse(endpoint(**request.REQUEST),
                        mimetype="application/json")
