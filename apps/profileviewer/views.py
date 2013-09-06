#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: views.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    This is the main module for rendering user profiles.
"""

#import twitter
import json
import gzip
from urllib import unquote
from datetime import datetime as dt
from collections import namedtuple
from collections import defaultdict

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic
Focus = namedtuple('Focus', ['name', 'value', 'chart'], verbose=True)
MAGIC_PW = 'dmir2013'


def assert_magic_signed(request, magic_pw=MAGIC_PW):
    """ Protected by MAGIC_PW

    :vf: @todo
    :returns: @todo

    """
    magic = request.COOKIES.get(magic_pw, 0) or \
        request.REQUEST.get(magic_pw, 0)
    if not magic:
        raise PermissionDenied()


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    no_inst = request.COOKIES.get('no_inst', 0) or \
        request.REQUEST.get('no_inst', 0)
    expert = Expert.get_one_assigned()
    if no_inst:
        return redirect('/expert_view/' + expert)
    else:
        r = render_to_response('instructions.html', {'expert': expert},
                               context_instance=RequestContext(request))
        r.set_cookie(MAGIC_PW, 1, 2592000)  # expires in 10 days
        return r


def list_data_dir(request):
    """List the content of dir

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os
    from os import path
    return HttpResponse('\n'.join(os.listdir(path.join(APP_PATH, 'data'))),
                        mimetype="application/json")


def flexopen(filename):
    """@todo: Docstring for flexopen.

    :filename: @todo
    :returns: @todo

    """
    if filename.endswith('.gz'):
        return gzip.open(filename)
    else:
        return open(filename)


def import_expert(request, filename):
    """Upload the expert to dbstore

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with flexopen(datapath) as fin:
        Expert.upload(fin)
    return redirect('/')


def expert_view(request, screen_name):
    """Return a specific profile give a user's screen_name

    :request: @todo
    :screen_name: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    expert = Expert.get_by_screen_name(screen_name)
    focus = defaultdict(str)
    for e in expert['expertise']:
        detail = Topic.getTopicById(e['topic_id'])['detail']

        if 'poi' in e['topic_id']:  # For poi topics
            focus[Focus(detail['name'], detail['id'], 'p')] += '\n'
            helpmsg = '\nThe lower-level category belonging to %s.'\
                % (detail['name'], )
            focus[Focus(detail['category']['name'],
                        detail['category']['name'],
                        'c')] += helpmsg
            helpmsg = '\nThe category that %s belongs to.' \
                % (detail['name'],)
            focus[Focus(detail['category']['zero_category_name'],
                        detail['category']['zero_category_name'],
                        'z')] += helpmsg
            e['topic_type'] = 'A place belonging to the category [%s, %s].' \
                % (detail['category']['name'],
                   detail['category']['zero_category_name'])

        elif 'zcate' not in e['topic_id']:  # For cate topics
            focus[Focus(detail['name'], detail['name'], 'c')] += '\n'
            focus[Focus(detail['zero_category_name'],
                        detail['zero_category_name'],
                        'z')] += ('\nThe top-level category'
                                  ' that %s belongs to.') \
                % (detail['name'],)
            e['topic_type'] = ('A lower-level category belonging'
                               ' to the category [%s].') \
                % (detail['zero_category_name'], )

        else:  # For zcate topics
            focus[Focus(detail['name'], detail['name'], 'z')] += '\n'
            e['topic_type'] = 'A top-level category.'
    expert['focus'] = {k: v.strip() for k, v in focus.iteritems()}
    return render_to_response('expert_view.html', expert,
                              context_instance=RequestContext(request))


def get_client(request):
    """ Return the judge's IP and Browser
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    return ip, user_agent


@csrf_protect
def submit_expert_judgment(request):
    """Submit judgment into the database

    :request: @todo
    :returns: @todo

    """
    judgment = {'judgments': {}}
    for v in request.REQUEST:
        if v.startswith('judgments-'):
            topic_id = v[10:]
            judgment['judgments'][topic_id] = request.REQUEST[v]
    judgment['judger'] = json.loads(unquote(
        request.COOKIES.get('judge', '{}')))
    ip, user_agent = get_client(request)
    judgment['judger']['ip'] = ip
    judgment['judger']['created_at'] = dt.now().isoformat()
    judgment['judger']['user_agent'] = user_agent
    Expert.update_judgment(request.REQUEST['exp_id'], judgment)
    return redirect('/home?no_inst=1')


# ------------------------ TOPIC VIEW ---------------------


def import_topic(request, filename):
    """Upload the data to dbstore

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with flexopen(datapath) as fin:
        Topic.upload(fin)
    return redirect('/')


def topic_view(request, topic_id):
    """Show a page for judging this topic

    :request: @todo
    :topic_id: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    data = {'topic': Topic.query(Topic.topic_id == topic_id).fetch(1)[0]}
    data['names'] = json.dumps(data['topic'].experts[:3])
    return render_to_response('topic_view.html',
                              data,
                              context_instance=RequestContext(request))


@csrf_protect
def submit_topic_judgment(request):
    """Submit a judgment on a topic

    :request: @todo
    :topic_id: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    j = request.REQUEST['judgment']
    jid = request.REQUEST['jid']
    Topic.update_judgment(jid, j)
    return redirect('/')


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
