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

import inspect
from json import dumps as _j
from functools import wraps
from decorator import decorator

from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404

from google.appengine.ext import ndb

from apps.profileviewer.models import _k
from apps.profileviewer.models import Judgement


@decorator
def secured_request_handler(func, *args, **kwargs):
    """ Make sure the call comes from admin. """
    req = kwargs.get('req', None) or args[0]
    if (req.REQUEST.get('_admin_key', None) or
            req.COOKIES.get('_admin_key', None)) != 'tu2013delft':
        raise PermissionDenied
    return func(*args, **kwargs)

_ENDPOINTS = dict()


def api_endpoint(endpoint):
    """ An decorator for API registry.

    Usage:
        @api_endpoint
        def an_api(req, a, b):
            # Do some stuff with a, b
            return # some stuff

    """
    argspec = inspect.getargspec(endpoint)
    _ENDPOINTS[endpoint.__name__] = endpoint, argspec

    @wraps
    def wrapper(*args, **kwargs):
        """ wrapper. """
        return endpoint(*args, **kwargs)

    return wrapper


def call_endpoint(request, name):
    """Call endpoint by name.

    :request: @todo
    :endpoint_name: @todo
    :returns: @todo

    """
    try:
        endpoint, argspec = _ENDPOINTS[name]
        kwargs = {k: request.REQUEST.get(k, None) for k in argspec.args}
        return HttpResponse(endpoint(**kwargs),  # pylint: disable-msg=W0142
                            mimetype="application/json")
    except KeyError:
        raise Http404


@api_endpoint
@secured_request_handler
def checkins(candidate):
    """ Return all checkins for the candidate.

    :candidate: The urlsafe key to the TwitterAccount.
    :returns: All checkins from the database made by the twitter user

    """
    try:
        c = _k(candidate)
        assert c.kind == 'TwitterAccount'
        return _j(c.get().checkins)
    except AssertionError:
        return _j({'error': 'Please specify either a '
                   'screen_name or comma separated names.'})


@api_endpoint
@secured_request_handler
def export_judgements():
    """ Export all judgements as json object per line.

    :returns: An iterator going over lines of json objects

    """
    # pylint: disable-msg=W0212
    def iter_judgement():
        """ An iterator over all judgements """
        for j in Judgement.query().fetch():
            yield _j({
                k: v.urlsafe()
                if isinstance(Judgement._properties[k], ndb.Key)
                else v
                for k, v in j.to_dict()
            }) + '\n'
    return iter_judgement()
    # pylint: enable-msg=W0212


@api_endpoint
@secured_request_handler
def assert_error():
    """ Bring a debug page for console. """
    assert False
