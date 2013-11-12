#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Utilities.

File: util.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Some useful functions

"""


import json
from google.appengine.ext import ndb


def jsonfy(obj, keys):
    """ Convert the values of keys into json strings.

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


def fixCompressed(model):
    """ Correct the restore of the data containing the compressed field.

    :returns: None

    Test Case:
        class TestModel(ndb.Model):
            name = ndb.StringProperty(indexed=True)
            data = ndb.JsonProperty(compressed=True)

        from apps.profileviewer.util import fixCompressed
        fixCompressed(TestModel)

        print TestModel.query().fetch()[0]
    """
    # pylint: disable-msg=W0212
    # Find all fixable field of data Models
    fixable = list()
    for n, p in model._properties.iteritems():
        print n, p
        if p.__class__ == ndb.model.JsonProperty and p._compressed:
            fixable.append(n)

    # apply the fixing
    print fixable
    for ins in model.query().fetch():
        for p in fixable:
            if not isinstance(ins._values.get(p).b_val,
                              ndb.model._CompressedValue):
                ins._values.get(p).b_val = \
                    ndb.model._CompressedValue(ins._values.get(p).b_val)
                ins.put()
