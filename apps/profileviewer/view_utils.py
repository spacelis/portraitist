#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: view_utils.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:

"""

from collections import defaultdict
from collections import namedtuple

from apps.profileviewer.models import Topic

Focus = namedtuple('Focus', ['name', 'value', 'chart'], verbose=True)


def get_client(request):
    """Return the ip and browser agent of the request

    :request: @todo
    :returns: ip, user_agent

    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    return ip, user_agent


def prepare_focus(data):
    """ Prepare the data we focus

    :data: @todo
    :returns: @todo

    """
    focus = defaultdict(str)
    for e in data['expertise']:
        detail = Topic.getTopicById(e['topic_id'])['detail']

        if 'poi' in e['topic_id']:  # For poi topics
            focus[Focus(detail['name'], detail['id'], 'p')] += '\n'
            helpmsg = '\nThe lower-level category belonging to %s.'\
                % (detail['name'], )
            focus[Focus(detail['category']['name'],
                        detail['category']['name'],
                        'c')] += helpmsg
            helpmsg = '\nThe category that %s belongs to.' \
                % (detail['name'],)
            focus[Focus(detail['category']['zero_category_name'],
                        detail['category']['zero_category_name'],
                        'z')] += helpmsg
            e['topic_type'] = 'A place belonging to the category [%s, %s].' \
                % (detail['category']['name'],
                   detail['category']['zero_category_name'])

        elif 'zcate' not in e['topic_id']:  # For cate topics
            focus[Focus(detail['name'], detail['name'], 'c')] += '\n'
            focus[Focus(detail['zero_category_name'],
                        detail['zero_category_name'],
                        'z')] += ('\nThe top-level category'
                                  ' that %s belongs to.') \
                % (detail['name'],)
            e['topic_type'] = ('A lower-level category belonging'
                               ' to the category [%s].') \
                % (detail['zero_category_name'], )

        else:  # For zcate topics
            focus[Focus(detail['name'], detail['name'], 'z')] += '\n'
            e['topic_type'] = 'A top-level category.'
    data['focus'] = {k: v.strip() for k, v in focus.iteritems()}
    return data
