#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: extra_tags.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Extra tags for used in projects
"""

import json
import urllib2

from django import template
import gae_mini_profiler.templatetags

register = template.Library()


@register.filter
def jsonencode(val):
    """ Encode the dict obj into a json string

    :val: @todo
    :returns: @todo

    """
    return json.dumps(val)


@register.filter
def urldecode(val):
    """ Encode the dict obj into a json string

    :val: @todo
    :returns: @todo

    """
    return urllib2.unquote(val)


@register.simple_tag
def profiler_includes():
    """ A template tag for including extra scripts for profiling. """
    return gae_mini_profiler.templatetags.profiler_includes()
