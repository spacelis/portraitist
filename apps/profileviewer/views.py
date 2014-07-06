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
from itertools import groupby
from fn import _

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

# from apps.profileviewer.form_map import get_gform_url
from apps.profileviewer.util import request_property
from apps.profileviewer.util import get_scores
from apps.profileviewer.util import get_user
from apps.profileviewer.util import get_client


COOKIE_LIFE = 90 * 24 * 3600


def vdebug(x):
    """@todo: Docstring for vdebug.

    :x: @todo
    :returns: @todo

    """
    print x
    return x


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
    user.assign(tp_key.get())
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

    Relation = namedtuple('Relation', ('poi', 'cate', 'zcate'))
    Filter = namedtuple('Filter', ('name', 'level', 'description'))

    def __init__(self):
        self.relationship = []

    @staticmethod
    def getPoiDescription(relatives):
        """ Return a discription of a poi filter.

        :f: @todo
        :returns: @todo

        """
        cate = [c for _, c in relatives if c]
        return 'This is a place (POI)%s.' % (
            ('in category of' + ', '.join(cate)) if cate else '',
        )

    @staticmethod
    def getCateDescription(relatives):
        """ Return a discription of a category filter.

        :f: @todo
        :returns: @todo

        """
        poi = [p for t, p in relatives if t == 'of' and p]
        zcate = [z for t, z in relatives if t == 'in' and z]

        return '''This is a category%s%s.''' % (
            (' that contains ' + ', '.join(poi)) if poi else '',
            (' and a subcategory in ' + ', '.join(zcate)) if zcate else ''
        )

    @staticmethod
    def getZCateDescription(relatives):
        """ Return a discription of a zero_category filter.

        :f: @todo
        :returns: @todo

        """
        sub = [c for _, c in relatives if c]
        return 'This is a top category%s.' % (
            (' that contains ' + ', '.join(sub)) if sub else '',
            )

    def addTopic(self, t):
        """ Add a new entity for filtering. """
        if t.level == 'POI':
            self.relationship.append(DataViewFilterSet.Relation(
                t.name,
                t.info['category']['name'],
                t.info['category']['zero_category_name']))
        elif t.level == 'CATEGORY':
            self.relationship.append(DataViewFilterSet.Relation(
                '',
                (
                    t.info['name']
                    if t.info['name'] != t.info['zero_category_name']
                    else ''
                ),
                t.info['zero_category_name']))

    def make_filters(self):
        """ Return a set of filters.
        :returns: @todo

        """
        rel = [
            DataViewFilterSet.Filter(
                poi,
                'p',
                DataViewFilterSet.getPoiDescription(
                    set(reduce((_ + _),
                               [[('in', p.cate), ('in', p.zcate)] for p in g],
                               []))
                )
            )
            for poi, g in groupby(self.relationship, key=_.poi)
            if poi
        ] + [
            DataViewFilterSet.Filter(
                cate,
                'c',
                DataViewFilterSet.getCateDescription(
                    set(reduce((_ + _),
                               [[('has', p.poi), ('in', p.zcate)] for p in g],
                               []))
                )
            )
            for cate, g in groupby(self.relationship, key=_.cate)
            if cate
        ] + [
            DataViewFilterSet.Filter(
                zcate,
                'z',
                DataViewFilterSet.getZCateDescription(
                    set(reduce((_ + _),
                               [[('has', p.poi), ('has', p.cate)] for p in g],
                               []))
                )
            )
            for zcate, g in groupby(self.relationship, key=_.zcate)
            if zcate
        ]
        return rel


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

    # make filters out of topics
    filterset = DataViewFilterSet()
    for x, g in groupby(ts, key=_.name):
        filterset.addTopic(g.next())

    return render_to_response(
        'expert_view.html',
        {
            'user': user.js_encode(),
            'topics': topics.values(),
            'candidate': task.candidate.urlsafe(),
            'task_key': task_key,
            'filters': filterset.make_filters(),
            'topic_judgement': 'null'
        },
        context_instance=RequestContext(request))


# FIXME need to be refactored since models changed
# def judgement_review(_, judge_id):
#     """ Showing all judgement from a judge and see the quality
#
#     :request: @todo
#     :returns: @todo
#
#     """
#     judge = Judge.getJudgeById(judge_id)
#     judges = [{
#         'this': j.judge_id == judge_id,
#         'jid': j.judge_id,
#         'page': idx
#     } for idx, j in enumerate(Judge.query().order(Judge.judge_id).fetch())]
#     return render_to_response(
#         'judgement_review.html',
#         {'judgements': judgement_for_review(judge.judgements),
#          'email': judge.email,
#          'name': judge.nickname,
#          'judge_id': judge_id,
#          'judges': judges
#          }
#     )


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

# def judgement_overview(request):
#     """@todo: Docstring for judgement_overview.
#
#     :request: @todo
#     :returns: @todo
#
#     """
#     assert_magic_signed(request)
#     data = dict()
#     estat = Expert.statistics()
#     jstat = Judge.statistics()
#     data.update(estat)
#     data.update(jstat)
#     return render_to_response('judgement_overview.html',
#                               data,
#                               context_instance=RequestContext(request))


# -------------- Twitter Lead Generation Cards ----------

# @csrf_exempt
# def lgc_submit(request):
#     """Submitting a Lead Generation Card
#
#     :request: @todo
#     :returns: @todo
#
#     """
#     R = request.REQUEST
#     name = R['name']
#     token = R['token']
#     card = R['card']
#     email = R['email']
#     screen_name = R['screen_name']
#     gform_url = get_gform_url(screen_name)
#
#     Participant.newParticipant(name=name,
#                                token=token,
#                                card=card,
#                                email=email,
#                                screen_name=screen_name,
#                                gform_url=gform_url).put()
#     send_self_survey_email(
#         'https://geo-expertise.appspot.com/general_survey?token='
#         + token, name, email)
#     return HttpResponse('Sucess!')
#
#
# @csrf_protect
# def general_survey(request):
#     """ Showing the gernal survey for participants
#
#     :request: @todo
#     :returns: @todo
#
#     """
#     R = request.REQUEST
#     if 'token' in R:
#         try:
#             p = Participant.query(
#                 Participant.token == request.REQUEST['token']
#             ).fetch(1)[0]
#             r = render_to_response('self_survey.html',
#                                    {'gform_url': p.gform_url})
#             r.set_cookie('judge_email', p.email)
#             r.set_cookie('judge_nick', p.name)
#             return r
#         except:
#             raise Http404
#     elif 'screen_name' in R and 'email' in R:
#         token = str(uuid4())
#         screen_name = R['screen_name'][1:]
#         gform_url = get_gform_url(screen_name)
#         Participant.newParticipant(
#             name=None,
#             card=None,
#             token=token,
#             email=R['email'],
#             screen_name=screen_name,
#             gform_url=gform_url).put()
#         r = render_to_response('self_survey.html',
#                                {'gform_url': gform_url})
#         r.set_cookie('judge_email', R['email'])
#         r.set_cookie('judge_nick', screen_name)
#         return r
#     else:
#         return render_to_response(
#             'participant_reg.html',
#             context_instance=RequestContext(request))


# -------------------------- test view ------------------

def test_view(request):
    """ a test view """
    return render_to_response('test_view.html',
                              {'test': [{'x': ['food', 'bar', 'haha']},
                                        {'x': ['xxx', 'yyy']}]},
                              context_instance=RequestContext(request))
