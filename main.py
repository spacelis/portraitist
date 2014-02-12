#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: main.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    This file is used to start the server on Google App Engine.
"""
import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

#import gae_mini_profiler.profiler
#application = gae_mini_profiler.profiler.ProfilerWSGIMiddleware(application)
