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
from apps.profileviewer.util import jsonfy
from apps.profileviewer.models import Expert


def test_data(screen_name):
    """return mock data
    :returns: @todo

    """
    _ = screen_name
    data = dict()
    data['map_data'] = {'center': [48.0, 2.35],
                        'markers': {
                            'paris_marker': {
                                'position': 'Paris, France',
                                'info_window': {
                                    'content': 'somebla<br>somebla',
                                    'showOn': 'mouseover',
                                    'hideOn': 'mouseout',
                                }},
                            'london': {'position': 'London, UK'},
                        }}
    data['cate_pie_data'] = [
        ['Task', 'Hours per Day'],
        ['Work',     11],
        ['Eat',      2],
        ['Commute',  2],
        ['Watch TV', 2],
        ['Sleep',    7]]

    data['cate_timelines_data'] = [
        ['Year', 'Sales', 'Expenses'],
        ['2004',  1000,      400],
        ['2005',  1170,      460],
        ['2006',  660,       1120],
        ['2007',  1030,      540]]

    data['poi_pie_data'] = data['cate_pie_data']
    data['topics'] = [{'name': 'Olympus', 'id': 't01'},
                      {'name': 'Old Church', 'id': 't02'}]
    return jsonfy(data, ['map_data',
                         'cate_pie_data',
                         'cate_timelines_data',
                         'poi_pie_data'])


def chart_format(screen_name):
    """Return a set of data prepared for charting

    :screen_name: @todo
    :returns: @todo

    """
    expert = Expert.get_by_screen_name(screen_name)


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


def view_profile(request, screen_name):
    """Return a specific profile give a user's screen_name

    :request: @todo
    :screen_name: @todo
    :returns: @todo

    """
    return render_to_response('viewer.html', test_data(screen_name),
                              context_instance=RequestContext(request))
