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
import json

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic
from apps.profileviewer.models import Judge
from apps.profileviewer.models import Participant
from apps.profileviewer.form_map import FORMMAP

from apps.profileviewer.view_utils import get_filters
from apps.profileviewer.view_utils import flexopen
from apps.profileviewer.view_utils import construct_judgement
from apps.profileviewer.view_utils import assert_magic_signed
from apps.profileviewer.view_utils import MAGIC_PW
from apps.profileviewer.view_utils import assure_judge
from apps.profileviewer.view_utils import request_property


COOKIE_LIFE = 90 * 24 * 3600


def home(request):
    """Return a homepage

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    no_inst = request_property(request, 'no_inst')
    submitted_tasks = request_property(request, 'submitted_tasks')
    done_survey = request_property(request, 'done_survey')
    if submitted_tasks > 5 and not done_survey:
        r = redirect('/survey')
        r.set_cookie('done_survey', 1, COOKIE_LIFE)
        return r
    expert_hash_id = Expert.getTask()
    if no_inst:
        return redirect('/expert_view/' + expert_hash_id)
    else:
        r = render_to_response('instructions.html', {'expert': expert_hash_id},
                               context_instance=RequestContext(request))
        r.set_cookie(MAGIC_PW, 1, COOKIE_LIFE)
        return r


def list_data_dir(request):
    """List the content of dir

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os
    from os import path
    return HttpResponse('\n'.join(os.listdir(path.join(APP_PATH, 'data'))),
                        mimetype="application/json")


def survey(request):
    """ Showing a survey to judges

    :request: @todo
    :returns: @todo

    """
    j = assure_judge(request)
    return render_to_response('survey.html', {'judge_email': j.email})


def import_expert(request, filename):
    """Upload the expert to dbstore

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with flexopen(datapath) as fin:
        Expert.upload(fin)
    return redirect('/')


def expert_view(request, hash_id):
    """Return a specific profile give a user's screen_name

    :request: @todo
    :screen_name: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    expert = Expert.getExpertInfoByHashId(hash_id)
    topics = [Topic.getTopicById(tid) for tid in expert['topics']]
    filters = get_filters(topics)
    return render_to_response(
        'expert_view.html',
        {
            'expert': expert,
            'topics': topics,
            'filters': filters
        },
        context_instance=RequestContext(request))


@csrf_protect
def submit_expert_judgement(request):
    """Submit judgement into the database

    :request: @todo
    :returns: @todo

    """
    judge = assure_judge(request)
    judgement = construct_judgement(request)
    j = Judge.addJudgement(judge, judgement)
    r = redirect('/home?no_inst=1')
    r.set_cookie('submitted_tasks', j.judgement_no, 90 * 24 * 3600)
    r.set_cookie('judge_id', j.judge_id, 90 * 24 * 3600)
    return r


# ------------------------ TOPIC VIEW ---------------------


def import_topic(request, filename):
    """Upload the data to dbstore

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with flexopen(datapath) as fin:
        Topic.upload(fin)
    return redirect('/')


def topic_view(request, topic_id):
    """Show a page for judging this topic

    :request: @todo
    :topic_id: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    data = {'topic': Topic.query(Topic.topic_id == topic_id).fetch(1)[0]}
    data['names'] = json.dumps(data['topic'].experts[:3])
    return render_to_response('topic_view.html',
                              data,
                              context_instance=RequestContext(request))


@csrf_protect
def submit_topic_judgement(request):
    """Submit a judgement on a topic

    :request: @todo
    :topic_id: @todo
    :returns: @todo

    """
    _ = request
    return redirect('/')


# ------------------------ OVERVIEW ---------------------

def import_judge(request, filename):
    """Import judgements

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    from apps import APP_PATH
    import os.path
    datapath = os.path.join(APP_PATH, 'data', filename)
    with flexopen(datapath) as fin:
        Judge.upload(fin)
    return redirect('/')


def judgement_overview(request):
    """@todo: Docstring for judgement_overview.

    :request: @todo
    :returns: @todo

    """
    assert_magic_signed(request)
    data = dict()
    estat = Expert.statistics()
    jstat = Judge.statistics()
    data.update(estat)
    data.update(jstat)
    return render_to_response('judgement_overview.html',
                              data,
                              context_instance=RequestContext(request))


# -------------- Twitter Lead Generation Cards ----------

def lgc_submit(request):
    """Submitting a Lead Generation Card

    :request: @todo
    :returns: @todo

    """
    R = request.REQUEST
    name = R['name']
    token = R['token']
    card = R['card']
    email = R['email']
    screen_name = R['screen_name']

    Participant.newParticipant(name=name,
                               token=token,
                               card=card,
                               email=email,
                               screen_name=screen_name).put()
    gform_id = FORMMAP.get(screen_name,
                           '1LwV2mJUWb9Kx-Pl_nQz_vpUZOY3KdVkb6W4B7ez6Obc')
    resp = render_to_response('self_servey.html', {'gform_id': gform_id})
    resp.set_cookie('judge_email', email, COOKIE_LIFE)
    resp.set_cookie('judge_nick', name, COOKIE_LIFE)
    return resp


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
