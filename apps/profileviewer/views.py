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
    data = {'screen_names': Expert.get_all_screen_names()}
    return render_to_response('main.html', data,
                              context_instance=RequestContext(request))


@csrf_protect
def upload(request):
    """Upload the data to dbstore

    :request: @todo
    :returns: @todo

    """
    if 'csv_text' in request.REQUEST:
        Expert.upload(request.REQUEST['csv_text'])
    return redirect('/')


@csrf_protect
def submit_judgment(request):
    """Submit judgment into the database

    :request: @todo
    :returns: @todo

    """
    judgment = dict()
    for v in request.REQUEST:
        if v.startswith('topic-'):
            judgment[v] = request.REQUEST[v]
    e = Expert.update_judgment(request.REQUEST['exp-id'], judgment)
    return redirect('/')


def import_data(_, filename):
    """Upload the data to dbstore

    :request: @todo
    :returns: @todo

    """
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with open(datapath) as fin:
        Expert.upload(fin)
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


def view_profile(request, screen_name):
    """Return a specific profile give a user's screen_name

    :request: @todo
    :screen_name: @todo
    :returns: @todo

    """
    return render_to_response('viewer.html',
                              Expert.get_by_screen_name(screen_name),
                              context_instance=RequestContext(request))
