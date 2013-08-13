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

import twitter
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    return render_to_response('viewer.html', {},
                              context_instance=RequestContext(request))
