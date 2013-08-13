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

import json
import twitter
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


def test_data():
    """return mock data
    :returns: @todo

    """
    data = dict()
    data['map_data'] = {'center': [48.0, 2.35],
                        'markers': {
                            'paris_marker': {'position': 'Paris, France',
                                'info_window':{
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
    return {k: json.dumps(v) for k, v in data.iteritems()}


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    return render_to_response('viewer.html', test_data(),
                              context_instance=RequestContext(request))
