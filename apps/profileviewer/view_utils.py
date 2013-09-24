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
from apps.profileviewer.models import Judge
from google.appengine.api import mail

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
    ip, user_agent = get_client(req)
    scores = dict()
    for v in req.REQUEST:
        if v.startswith('pv-judgements-'):
            topic_id = v[14:]
            scores[topic_id] = req.REQUEST[v]
    judgement = {
        'created_at': dt.now().isoformat(),
        'candidate': Expert.getExpertByHashId(
            req.REQUEST['pv-candidate-hash-id']).screen_name,
        'ip': ip,
        'user_agent': user_agent,
        'scores': scores
    }
    return judgement


def request_property(req, prop, default=None):
    """ Get a property from a request or cookie

    :req: The request object
    :prop: the name of the property
    :default: the default value when the prop doesn't exist
    :returns: @todo

    """
    if prop in req.REQUEST:
        return req.REQUEST[prop]
    elif prop in req.COOKIES:
        return req.COOKIES[prop]
    else:
        return default


MAGIC_PW = 'dmir2013'


def assert_magic_signed(req, magic_pw=MAGIC_PW):
    """ Protected by MAGIC_PW

    :vf: @todo
    :returns: @todo

    """
    magic = request_property(req, magic_pw)
    if not magic:
        raise PermissionDenied()


OLD_JUDGE = {'128.59.65.204': '608e6304-975e-44f9-8274-428706e6ad2a',
             '129.252.131.185': '09d0510e-a8a5-4776-a63a-fb20a5f38826',
             '130.161.91.175': '07e284c5-d549-4147-af63-dccd10c89e6a',
             '131.107.192.26': '92ce77e9-59ad-4530-875b-95cfa51c33a4',
             '131.180.203.8': '6f96fed9-dd0e-4a2e-872b-e9f73ac0e808',
             '131.180.220.139': '62eaa7eb-cec3-493f-a1ca-2d12aede3ba4',
             '131.180.220.212': '981b4e7e-745b-4d50-90d2-d5d6ac18de70',
             '131.180.42.115': '08699293-81d0-455f-8868-d66978d14a3a',
             '138.38.108.253': 'd4f5ec11-ac74-4a1a-887e-b701f56e1b12',
             '145.94.215.79': 'b41667f2-3d46-430d-8ca8-d42a7dd9a112',
             '192.16.196.142': 'a337ecb9-abcd-4c73-b3e6-8619eefccb21',
             '77.162.62.125': '42eea441-9096-4e72-8035-cc50b482392c'}


def assure_judge(req):
    """ make sure the user matches the judge in datastore

    :req: @todo
    :returns: @todo

    """
    judge_id = req.COOKIES.get('judge_id', '')
    judge_nick = req.COOKIES.get('judge_nick', '')
    judge_email = req.COOKIES.get('judge_email', '')
    ip, _ = get_client(req)
    j = None
    if judge_id:
        js = Judge.query(Judge.judge_id == judge_id).fetch(1)
        if len(js) > 0:
            return js[0]
        elif ip in OLD_JUDGE:
            js = Judge.query(Judge.judge_id == OLD_JUDGE[ip]).fetch(1)
            if len(js) > 0:
                j.email = judge_email
                j.nickname = judge_nick
                j.put()
                return j
        else:
            j = Judge.newJudge(judge_email, judge_nick)
            j.put()
            return j
    else:
        j = Judge.newJudge(judge_email, judge_nick)
        j.put()
        return j
    return None


def send_self_survey_email(survey_url, name, email):
    """Send an email to the ones who clicked the participating email

    :survey_url: @todo
    :returns: @todo

    """
    mail.send_mail(sender="Wen Li <spacelis@gmail.com>",
                   to="%s <%s>" % (name, email),
                   subject=("Your participation to "
                            "GeoExpertise project has been approved"),
                   body="""
Dear %s,

Thank you for participating our project!
Please follow the link below to the survey:

%s

You may find more information about the project and our privacy terms at
Terms - http://geo-expertise.appspot.com/terms
About - http://geo-expertise.appspot.com/about

Best,
Wen Li
""" % (name, survey_url))
