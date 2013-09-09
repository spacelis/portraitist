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

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic
from apps.profileviewer.view_utils import prepare_focus
from apps.profileviewer.view_utils import get_client

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
        r.set_cookie(MAGIC_PW, 1, 90 * 24 * 3600)
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
    data = Expert.get_by_screen_name(screen_name)
    return render_to_response('expert_view.html', prepare_focus(data),
                              context_instance=RequestContext(request))


@csrf_protect
def submit_expert_judgment(request):
    """Submit judgment into the database

    :request: @todo
    :returns: @todo

    """
    judgment = dict()
    judgment['created_at'] = dt.now().isoformat()

    judgment['judgments'] = dict()
    for v in request.REQUEST:
        if v.startswith('judgments-'):
            topic_id = v[10:]
            judgment['judgments'][topic_id] = request.REQUEST[v]
    ip, user_agent = get_client(request)

    judgment['judger'] = dict()
    judgment['judger']['judge_id'] = unquote(
        request.COOKIES.get('judge_id', None))
    judgment['judger']['ip'] = ip
    judgment['judger']['user_agent'] = user_agent
    Expert.update_judgment(request.REQUEST['exp_id'], judgment)
    r = redirect('/home?no_inst=1')
    r.set_cookie('submitted_tasks',
                 int(request.COOKIES.get('submitted_tasks', 0)) + 1,
                 90 * 24 * 3600)
    return r


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
    jid = request.COOKIES['judge_id']
    Topic.update_judgment(jid, j)
    return redirect('/')


# ------------------------ TOPIC VIEW ---------------------

def judgment_overview(request):
    """@todo: Docstring for judgment_overview.

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    data = dict()
    es = Expert.get_judged_expert()
    data['judgments'] = sum([e.judgment_number for e in es])
    data['judgers'] = set()
    for e in es:
        for j in e.judgments:
            data['judgers'].add(j['judger']['ip'])
    data['topics'] = set()
    for e in es:
        for j in e.judgments:
            for t in j['judgments'].iterkeys():
                data['topics'].add(t)
    return render_to_response('judgment_overview.html',
                              data,
                              context_instance=RequestContext(request))


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
