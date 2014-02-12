#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Views.

File: views.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    This is the main module for rendering user profiles.

"""

from decorator import decorator
from collections import namedtuple

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import Http404
from django.core.exceptions import PermissionDenied

from apps.profileviewer.models import _k
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import User

#from apps.profileviewer.form_map import get_gform_url
from apps.profileviewer.util import request_property
from apps.profileviewer.util import get_scores
from apps.profileviewer.util import get_user
from apps.profileviewer.util import get_client


COOKIE_LIFE = 90 * 24 * 3600


@decorator
def login_required(view, *args, **kwargs):
    """ Redirect users to login page if the user have not login yet. """
    req = args[0]
    user = User.getOrCreate(request_property(req, 'session_token'))
    if user.key:
        view(*args, **kwargs)
    else:
        raise PermissionDenied


def user_context(request):
    """ A context processor that processing the user information.

    :request: @todo
    :returns: @todo

    """
    user = get_user(request)
    return {'user': user.js_encode()}


def home(request):
    """ The welcome page. """
    return render_to_response('main.html', {},
                              context_instance=RequestContext(request))


def taskpackage(request, task_pack_id):
    """

    :request: @todo
    :task_pack_key: The urlsafe key to a task_pack
    :returns: @todo

    """
    user = get_user(request)
    tp_key = _k(task_pack_id, 'TaskPackage')
    user.assign(tp_key)
    r = redirect('/task_router')
    r.set_cookie('session_token', user.session_token)
    return r


def task_router(request):
    """ Routing tasks by tasks.

    :request: Django HTTP request object.
    :returns: Page

    """
    user = get_user(request)
    try:
        task_key = user.task_package.get().nextTaskKey()
        return redirect('/task/' + task_key.urlsafe())
    except TaskPackage.NoMoreTask as e:
        return redirect('/confirm_code/' + e.cf_code)
    raise Http404


def confirm_code_view(_, value):
    """ Render a page for confirmation code.

    :_: request but not used
    :returns: @todo

    """
    r = render_to_response('taskpack_confirmation.html',
                           {'confirm_code': value})
    return r


def survey(request):
    """ Showing a survey to judges.

    :request: @todo
    :returns: @todo

    """
    user = get_user(request)
    ea = user.email_account.get()
    return render_to_response('survey.html', {'assessor_email': ea.email})


class DataViewFilterSet(object):

    """ The filter information for zoom in/out of data in web interface. """

    Filter = namedtuple('Filter', ['name', 'level', 'relation'])

    def __init__(self):
        self.filters = dict()

    @staticmethod
    def getDescription(f):
        """ Return a discription of the filter.

        :f: @todo
        :returns: @todo

        """
        if f.level == 'POI':
            return 'This is a place (POI) in category of %s, %s.' % \
                (f.relation['category'], f.relation['zcategory'])
        elif f.level == 'CATEGORY':
            return 'This is a category that contains %s.' % \
                (', '.join(f.relation))
        else:
            return 'This is a general category that contains'
        # FIXME generate a list of filters for easy navigation.

    def addPOI(self, e):
        """ Add a new entity for filtering. """
        pass


def annotation_view(request, task_key):
    """Return a specific profile give a user's screen_name.

    :request: @todo
    :task: @todo
    :returns: @todo

    """
    user = get_user(request)
    task = _k(task_key, 'AnnotationTask').get()
    rs = [r.get() for r in task.rankings]
    ts = [r.topic.get() for r in rs]
    topics = {r.topic_id: {
        'topic_id': r.topic_id,
        'topic_type': t.level,
        'topic': t.name,
        'region': r.region
    } for t, r in zip(ts, rs)}

    return render_to_response(
        'expert_view.html',
        {
            'user': user.js_encode(),
            'topics': topics.values(),
            'candidate': task.candidate.urlsafe(),
            'task_key': task_key,
            'filters': [{'name': t.name,
                        'type': t.level,
                        'description': t.level} for t in ts],
            'topic_judgement': 'null'
        },
        context_instance=RequestContext(request))


# FIXME need to be refactored since models changed
#def judgement_review(_, judge_id):
    #""" Showing all judgement from a judge and see the quality

    #:request: @todo
    #:returns: @todo

    #"""
    #judge = Judge.getJudgeById(judge_id)
    #judges = [{
        #'this': j.judge_id == judge_id,
        #'jid': j.judge_id,
        #'page': idx
    #} for idx, j in enumerate(Judge.query().order(Judge.judge_id).fetch())]
    #return render_to_response(
        #'judgement_review.html',
        #{'judgements': judgement_for_review(judge.judgements),
         #'email': judge.email,
         #'name': judge.nickname,
         #'judge_id': judge_id,
         #'judges': judges
         #}
    #)


@csrf_protect
def submit_annotation(request):
    """Submit judgement into the database

    :request: A HttpRequest[POST]
    :returns: A HttpResponse

    """
    user = get_user(request)
    if user.isDead():
        raise PermissionDenied
    user.touch()

    try:
        task_key = request.POST.get('pv-task-key', None)
        task = _k(task_key, 'AnnotationTask').get()
    except TypeError:
        raise Http404

    scores = get_scores(request)
    ipaddr, user_agent = get_client(request)
    Judgement.add(user, task, scores, ipaddr, user_agent)

    user.accomplish(task)

    return redirect('/task_router')


# ------------------------ OVERVIEW ---------------------

#def judgement_overview(request):
    #"""@todo: Docstring for judgement_overview.

    #:request: @todo
    #:returns: @todo

    #"""
    #assert_magic_signed(request)
    #data = dict()
    #estat = Expert.statistics()
    #jstat = Judge.statistics()
    #data.update(estat)
    #data.update(jstat)
    #return render_to_response('judgement_overview.html',
                              #data,
                              #context_instance=RequestContext(request))


# -------------- Twitter Lead Generation Cards ----------

#@csrf_exempt
#def lgc_submit(request):
    #"""Submitting a Lead Generation Card

    #:request: @todo
    #:returns: @todo

    #"""
    #R = request.REQUEST
    #name = R['name']
    #token = R['token']
    #card = R['card']
    #email = R['email']
    #screen_name = R['screen_name']
    #gform_url = get_gform_url(screen_name)

    #Participant.newParticipant(name=name,
                               #token=token,
                               #card=card,
                               #email=email,
                               #screen_name=screen_name,
                               #gform_url=gform_url).put()
    #send_self_survey_email(
        #'https://geo-expertise.appspot.com/general_survey?token='
        #+ token, name, email)
    #return HttpResponse('Sucess!')


#@csrf_protect
#def general_survey(request):
    #""" Showing the gernal survey for participants

    #:request: @todo
    #:returns: @todo

    #"""
    #R = request.REQUEST
    #if 'token' in R:
        #try:
            #p = Participant.query(
                #Participant.token == request.REQUEST['token']
            #).fetch(1)[0]
            #r = render_to_response('self_survey.html',
                                   #{'gform_url': p.gform_url})
            #r.set_cookie('judge_email', p.email)
            #r.set_cookie('judge_nick', p.name)
            #return r
        #except:
            #raise Http404
    #elif 'screen_name' in R and 'email' in R:
        #token = str(uuid4())
        #screen_name = R['screen_name'][1:]
        #gform_url = get_gform_url(screen_name)
        #Participant.newParticipant(
            #name=None,
            #card=None,
            #token=token,
            #email=R['email'],
            #screen_name=screen_name,
            #gform_url=gform_url).put()
        #r = render_to_response('self_survey.html',
                               #{'gform_url': gform_url})
        #r.set_cookie('judge_email', R['email'])
        #r.set_cookie('judge_nick', screen_name)
        #return r
    #else:
        #return render_to_response(
            #'participant_reg.html',
            #context_instance=RequestContext(request))


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
