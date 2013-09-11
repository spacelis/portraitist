#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: view_utils.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:

"""

import gzip
from collections import namedtuple
from datetime import datetime as dt
from itertools import chain
from itertools import groupby

from django.core.exceptions import PermissionDenied

from apps.profileviewer.models import Expert

Focus = namedtuple('Focus', ['name', 'value', 'chart'], verbose=True)


def get_client(request):
    """Return the ip and browser agent of the request

    :request: @todo
    :returns: ip, user_agent

    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    return ip, user_agent


def get_filters(topics, key=lambda x: x['filter_name']):
    """Return filters from related_to fields in each topic

    :topics: @todo
    :returns: @todo

    """
    filters = list()
    entities = chain.from_iterable([t['related_to'] for t in topics])
    for _, vs in groupby(sorted(entities, key=key), key=key):
        vs = list(vs)
        filters.append({
            'name': vs[0]['name'],
            'filter_name': vs[0]['filter_name'],
            'filter_type': vs[0]['filter_type'],
            'explanation': '\n'.join([x['explanation'] for x in vs])
        })
    return filters


def flexopen(filename):
    """@todo: Docstring for flexopen.

    :filename: @todo
    :returns: @todo

    """
    if filename.endswith('.gz'):
        return gzip.open(filename)
    else:
        return open(filename)


def construct_judgement(req):
    """Constructing judgement object out of request

    :req: @todo
    :returns: @todo

    """
    judgement = dict()
    judgement['created_at'] = dt.now().isoformat()
    judgement['candidate'] = Expert.getExpertByHashId(
        req.REQUEST['judgement-candidate']).screen_name

    ip, user_agent = get_client(req)
    judgement['ip'] = ip
    judgement['user_agent'] = user_agent

    judgement['judgements'] = dict()
    for v in req.REQUEST:
        if v.startswith('judgements-'):
            topic_id = v[10:]
            judgement['judgements'][topic_id] = req.REQUEST[v]
    return judgement


def request_property(req, prop):
    """ Get a property from a request

    :req: @todo
    :returns: @todo

    """
    return req.COOKIES.get(prop, None) or req.REQUEST.get(prop, None)


MAGIC_PW = 'dmir2013'


def assert_magic_signed(req, magic_pw=MAGIC_PW):
    """ Protected by MAGIC_PW

    :vf: @todo
    :returns: @todo

    """
    magic = request_property(req, magic_pw)
    if not magic:
        raise PermissionDenied()
