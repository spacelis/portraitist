#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The api utils.

File: __init__.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    The api utils.

"""

import json
import inspect
import yaml
from collections import namedtuple

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpResponse

from apps.profileviewer.util import request_property
from apps.profileviewer.util import get_user
from apps.profileviewer.util import set_user


class APIRegistry(object):

    """ A registry for api methods. """

    EndPointSpec = namedtuple('EndPointSpec', ['func',
                                               'spec',
                                               'secured',
                                               'disabled',
                                               'tojson'])

    ReservedArguments = {
        '_user': lambda req: get_user(req),
        '_request': lambda req: req
    }

    def __init__(self):
        self._ENDPOINTS = dict()

    def api_endpoint(self, secured=False, disabled=False, tojson=True):
        """ An decorator for API registry.

        Usage:
            reg = APIRegistry()
            @reg.api_endpoint(secured=True)
            def an_api(a, b):
                # Do some stuff with a, b
                return # some stuff

        """

        def decorator(func):
            """ The decorator for collecting api methods. """
            name = func.__name__
            self._ENDPOINTS[name] = APIRegistry.EndPointSpec(
                func=func,
                spec=inspect.getargspec(func),
                secured=secured,
                disabled=disabled,
                tojson=tojson)
            return func

        return decorator

    @staticmethod
    def check_secure(req):
        """ Check whether the call is secured.

        :req: @todo
        :returns: @todo

        """
        if request_property(req, '_admin_key') != 'tu2013delft':
            raise PermissionDenied

    def call_endpoint(self, request, name):
        """Call endpoint by name.

        :request: Django HttpRequest object.
        :name: The name of the endpoint to call.
        :returns: Json string response.

        """
        try:
            endpoint = self._ENDPOINTS[name]
            if endpoint.secured:
                APIRegistry.check_secure(request)
            if endpoint.disabled:
                raise KeyError()
            kwargs = {k: request.REQUEST.get(k, None)
                      for k in endpoint.spec.args
                      if k not in APIRegistry.ReservedArguments}
            for k in APIRegistry.ReservedArguments.keys():
                if k in endpoint.spec.args:
                    kwargs[k] = APIRegistry.ReservedArguments[k](request)
        except KeyError:
            raise Http404
        ret = endpoint.func(**kwargs)  # pylint: disable=W0142
        if endpoint.tojson:
            resp = HttpResponse(json.dumps(ret), mimetype="application/json")
        else:
            resp = ret
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        if '_user' in endpoint.spec.args:
            return set_user(resp, kwargs['_user'])
        return resp
