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
#from django.http import HttpResponse
import json
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    data = {'topics': Topic.query().fetch(10)}
    return render_to_response('main.html', data,
                              context_instance=RequestContext(request))


def import_expert(_, filename):
    """Upload the expert to dbstore

    :request: @todo
    :returns: @todo

    """
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with open(datapath) as fin:
        Expert.upload(fin)
    return redirect('/')


def expert_view(request, screen_name):
    """Return a specific profile give a user's screen_name

    :request: @todo
    :screen_name: @todo
    :returns: @todo

    """
    expert = Expert.get_by_screen_name(screen_name)
    for e in expert['expertise']:
        detail = Topic.getTopicById(e['topic_id'])['detail']
        e['detail'] = json.dumps(detail)
        if 'poi' in e['topic_id']:  # For poi topics
            e['focus_name'] = [e['topic'],
                               detail['category']['name'],
                               detail['category']['zero_category_name']]
            e['focus_id'] = [detail['id'],
                             detail['category']['name'],
                             detail['category']['zero_category_name']]
        elif 'zcate' not in e['topic_id']:  # For cate topics
            e['focus_name'] = [detail['name'], detail['zero_category_name']]
            e['focus_id'] = [detail['name'], detail['zero_category_name']]
        else:  # For zcate topics
            e['focus_name'] = [detail['name']]
            e['focus_id'] = [detail['name']]

        e['focus_name_json'] = json.dumps(e['focus_name'])
        e['focus_id_json'] = json.dumps(e['focus_id'])
    return render_to_response('expert_view.html', expert,
                              context_instance=RequestContext(request))


def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))


@csrf_protect
def submit_expert_judgment(request):
    """Submit judgment into the database

    :request: @todo
    :returns: @todo

    """
    judgment = dict()
    for v in request.REQUEST:
        if v.startswith('topic-'):
            judgment[v] = request.REQUEST[v]
    Expert.update_judgment(request.REQUEST['exp_id'], judgment)
    return redirect('/')


def import_topic(_, filename):
    """Upload the data to dbstore

    :request: @todo
    :returns: @todo

    """
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with open(datapath) as fin:
        Topic.upload(fin)
    return redirect('/')


def topic_view(request, topic_id):
    """Show a page for judging this topic

    :request: @todo
    :topic_id: @todo
    :returns: @todo

    """
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
    j = request.REQUEST['judgment']
    jid = request.REQUEST['jid']
    Topic.update_judgment(jid, j)
    return redirect('/')
