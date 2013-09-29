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
from uuid import uuid4

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import Http404

from apps.profileviewer.models import Expert
from apps.profileviewer.models import Topic
from apps.profileviewer.models import Judge
from apps.profileviewer.models import Participant
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.form_map import get_gform_url

from apps.profileviewer.view_utils import get_filters
from apps.profileviewer.view_utils import flexopen
from apps.profileviewer.view_utils import construct_judgement
from apps.profileviewer.view_utils import assert_magic_signed
from apps.profileviewer.view_utils import assure_judge
from apps.profileviewer.view_utils import request_property
from apps.profileviewer.view_utils import send_self_survey_email


COOKIE_LIFE = 90 * 24 * 3600


def taskrouter(request):
    """ Routing tasks by tasks

    :request: @todo
    :returns: @todo

    """
    no_inst = request_property(request, 'no_inst')
    submitted_tasks = int(request_property(request, 'submitted_tasks', 0))
    done_survey = request_property(request, 'done_survey')
    if (submitted_tasks >= 5) and (done_survey is None):
        r = redirect('/survey')
        r.set_cookie('done_survey', 1, COOKIE_LIFE)
        return r
    task_pack_id = request_property(request, 'task_pack_id')
    if task_pack_id:
        try:
            expert_hash_id = TaskPackage.getTask(task_pack_id)
        except TaskPackage.NoMoreTask:
            confirm_code = TaskPackage.getConfirmationCode(task_pack_id)
            r = render_to_response('taskpack_confirmation.html',
                                   {'confirm_code': confirm_code})
            r.delete_cookie('task_pack_id')
            return r
        except TaskPackage.TaskPackageNotExists:
            raise Http404
    else:
        expert_hash_id = Expert.getTask()
    if no_inst:
        r = redirect('/expert_view/' + expert_hash_id)
    else:
        r = render_to_response('instructions.html', {'expert': expert_hash_id},
                               context_instance=RequestContext(request))
    if task_pack_id:
        r.set_cookie('task_pack_id', task_pack_id, COOKIE_LIFE)
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
    task_pack_id = request_property(request, 'task_pack_id')
    if task_pack_id:
        TaskPackage.submitTask(
            task_pack_id,
            request.REQUEST['pv-candidate-hash-id'])
    r = redirect('/home?no_inst=1')

    # pylint: disable-msg=E1101
    r.set_cookie('submitted_tasks', j.judgement_no, 90 * 24 * 3600)
    r.set_cookie('judge_id', j.judge_id, 90 * 24 * 3600)
    # pylint: enable-msg=E1101
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

@csrf_exempt
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
    gform_url = get_gform_url(screen_name)

    Participant.newParticipant(name=name,
                               token=token,
                               card=card,
                               email=email,
                               screen_name=screen_name,
                               gform_url=gform_url).put()
    send_self_survey_email(
        'https://geo-expertise.appspot.com/general_survey?token='
        + token, name, email)
    return HttpResponse('Sucess!')


@csrf_protect
def general_survey(request):
    """ Showing the gernal survey for participants

    :request: @todo
    :returns: @todo

    """
    R = request.REQUEST
    if 'token' in R:
        try:
            p = Participant.query(
                Participant.token == request.REQUEST['token']
            ).fetch(1)[0]
            r = render_to_response('self_survey.html',
                                   {'gform_url': p.gform_url})
            r.set_cookie('judge_email', p.email)
            r.set_cookie('judge_nick', p.name)
            return r
        except:
            raise Http404
    elif 'screen_name' in R and 'email' in R:
        token = str(uuid4())
        screen_name = R['screen_name'][1:]
        gform_url = get_gform_url(screen_name)
        Participant.newParticipant(
            name=None,
            card=None,
            token=token,
            email=R['email'],
            screen_name=screen_name,
            gform_url=gform_url).put()
        r = render_to_response('self_survey.html',
                               {'gform_url': gform_url})
        r.set_cookie('judge_email', R['email'])
        r.set_cookie('judge_nick', screen_name)
        return r
    else:
        return render_to_response(
            'participant_reg.html',
            context_instance=RequestContext(request))


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
