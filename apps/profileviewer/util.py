#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Utilities.

File: util.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Some useful functions

"""


import gzip
import base64
import json

from itertools import chain
from itertools import groupby
from collections import namedtuple

from django.utils.dateparse import parse_datetime

from google.appengine.ext import ndb
from google.appengine.api import mail

from apps.profileviewer.models import User


def throttle_map(it, callback, size=20):
    """ Looping over items utilizing async futures.

    :it: The iterator.
    :callback: A function to call which returns a future for the result.
    :size: The max number of concurrent in-process futures.
    """
    l = list()
    for r in it:
        if len(l) < size:
            l.append(callback(r))
        else:
            f = ndb.Future.wait_any(l)
            l.remove(f)
            l.append(callback(r))


def get_user(request):
    """ Return the session attach to this request. """
    # session_toke is actually a token to a (temporary) user
    return User.getOrCreate(request_property(request, 'session_token'))


def set_user(response, user):
    """ Set session token for the response.

    :response: The HttpResonse
    :user: The user that should attach to this response
    :returns: The same response

    """
    response.set_cookie('session_token', user.session_token)
    return response


def jsonfy(obj, keys):
    """ Convert the values of keys into json strings.

    :obj: @todo
    :keys: @todo
    :returns: @todo

    """
    nobj = dict()
    for k in obj:
        if k in keys:
            nobj[k] = json.dumps(obj[k])
        else:
            nobj[k] = obj[k]
    return nobj


def b64json_encode(obj):
    """ Return a string of base64 encoded json object. """
    return base64.b64encode(json.dumps(obj))


def b64json_decode(json_obj):
    """ Return a dict of base64 encoded json object. """
    return json.loads(base64.b64decode(json_obj))


def listCompressedProperty(model):
    """ Correct the restore of the data containing the compressed field.

    :returns: None

    Test Case:
        class TestModel(ndb.Model):
            name = ndb.StringProperty(indexed=True)
            data = ndb.JsonProperty(compressed=True)

        from apps.profileviewer.util import fixCompressed
        fixCompressed(TestModel)

        print TestModel.query().fetch()[0]

    """
    # pylint: disable-msg=W0212
    # Find all fixable field of data Models
    return [n
            for n, p in model._properties.iteritems()
            if (p.__class__ == ndb.model.JsonProperty or
                p.__class__ == ndb.model.StringProperty) and p._compressed]


def fixCompressedEntity(key, fields):
    """ Fix Compressiion Error for the entity with tkey.
        :key: The key of the entity.
        :fields:  A list of field names.

    """
    # apply the fixing
    ins = key.get()
    for p in fields:
        if ins._values.get(p) and not isinstance(ins._values.get(p).b_val,
                                                 ndb.model._CompressedValue):
            ins._values.get(p).b_val = \
                ndb.model._CompressedValue(ins._values.get(p).b_val)
            ins.put()


Focus = namedtuple('Focus', ['name', 'value', 'chart'], verbose=True)


def get_client(request):
    """Return the ip and browser agent of the request.

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
    """Return filters from related_to fields in each topic.

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


def get_scores(req):
    """Constructing judgement object out of request.

    :req: @todo
    :returns: @todo

    """
    scores = dict()
    for v in req.REQUEST:
        if v.startswith('pv-judgements-'):
            topic_id = v[14:]
            scores[topic_id] = req.REQUEST[v]
    return scores


def get_traceback(req):
    """Constructing judgement object out of request.

    :req: @todo
    :returns: @todo

    """
    return req.REQUEST['pv-annotation-traceback']


def request_property(req, prop, default=None, b64json=False):
    """ Get a property from a request or cookie.

    :req: The request object
    :prop: The name of the property
    :default: The default value when the prop doesn't exist
    :b64json: Whether de/encoding is needed (base64 . json)
    :returns: The value of the property

    """
    if b64json:
        f = b64json_decode
    else:
        def f(x):
            return x

    if prop in req.GET:
        return f(req.GET[prop])
    if prop in req.POST:
        return f(req.POST[prop])
    elif prop in req.COOKIES:
        return f(req.COOKIES[prop])
    else:
        return default


def judgement_for_review(judgements):
    """ transform judgements for review.

    :judgements: @todo
    :returns: @todo

    """
    for j, pj in zip(judgements, [None] + judgements):
        j['created_at'] = parse_datetime(j['created_at'])
        if pj:
            j['effort'] = '%.3f' % ((j['created_at'] - pj['created_at'])
                                    .total_seconds() / 60.0, )
        else:
            j['effort'] = 'Unknown'
    return judgements


def send_self_survey_email(survey_url, name, email):
    """Send an email to the ones who clicked the participating email.

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
