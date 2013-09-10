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

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic
from apps.profileviewer.models import Judge
from apps.profileviewer.view_utils import get_filters
from apps.profileviewer.view_utils import flexopen
from apps.profileviewer.view_utils import construct_judgement
from apps.profileviewer.view_utils import assert_magic_signed
from apps.profileviewer.view_utils import MAGIC_PW


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    no_inst = request.COOKIES.get('no_inst', 0) or \
        request.REQUEST.get('no_inst', 0)

    expert = Expert.getTask()
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
    expert = Expert.getExpertInfoByScreenName(screen_name)
    topics = [Topic.getTopicById(tid) for tid in expert['topics']]
    filters = get_filters(topics)
    return render_to_response(
        'expert_view.html',
        {
            'expert': expert,
            'topics': topics,
            'filters': filters
        },
        context_instance=RequestContext(request))


@csrf_protect
def submit_expert_judgment(request):
    """Submit judgment into the database

    :request: @todo
    :returns: @todo

    """
    judge_id = request.COOKIES.get('judge_id')
    judgement = construct_judgement(request)
    j = Judge.addJudgement(judge_id, judgement)
    r = redirect('/home?no_inst=1')
    r.set_cookie('submitted_tasks', j.judgement_no, 90 * 24 * 3600)
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
    _ = request
    return redirect('/')


# ------------------------ OVERVIEW ---------------------

def judgment_overview(request):
    """@todo: Docstring for judgment_overview.

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    data = dict()
    estat = Expert.statistics()
    jstat = Judge.statistics()
    data.update(estat)
    data.update(jstat)
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
