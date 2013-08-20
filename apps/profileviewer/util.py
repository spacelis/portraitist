#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: util.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Some useful functions
"""


import json


def jsonfy(obj, keys):
    """Convert the values of keys into json strings

    :obj: @todo
    :keys: @todo
    :returns: @todo

    """
    nobj = dict()
    for k in obj:
        if k in keys:
            nobj[k] = json.dumps(obj[k])
        else:
            nobj[k] = obj[k]
    return nobj
