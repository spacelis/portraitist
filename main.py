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


#import django.views.debug
#from werkzeug.debug import DebuggedApplication
#def null_technical_500_response(request, exc_type, exc_value, tb):
    #raise exc_type, exc_value, tb
#django.views.debug.technical_500_response = null_technical_500_response
#application = DebuggedApplication(application, evalex=True)
