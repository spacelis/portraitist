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

import json
from decorator import decorator
from collections import namedtuple
from itertools import groupby
from fn import _ as L
from fn import F
from fn import op
from fn.iters import map  # pylint: disable=redefined-builtin

from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden
from django.http import Http404
from django.conf import settings

from apps.profileviewer.models import _k
from apps.profileviewer.models import TaskPackage
from apps.profileviewer.models import Judgement
from apps.profileviewer.models import User

# from apps.profileviewer.form_map import get_gform_url
from apps.profileviewer.util import request_property
from apps.profileviewer.util import get_scores
from apps.profileviewer.util import get_traceback
from apps.profileviewer.util import get_user
from apps.profileviewer.util import get_client


COOKIE_LIFE = 90 * 24 * 3600


def vdebug(x):
    """@todo: Docstring for vdebug.

    :x: @todo
    :returns: @todo

    """
    print(x)
    return x


def assert_error(request):
    """TODO: Docstring for assert_error.

    :request: TODO
    :returns: TODO

    """
    assert False


def error500(request):
    """ Show a 505 error page

    :request: TODO
    :returns: TODO

    """
    from google.appengine.api import mail
    from datetime import datetime
    user = get_user(request)
    ip, ua = get_client(request)
    subject = '[Geoexpertise] A server error occured'
    body = """
    Time: {3}
    User: {0.session_token}
    IP: {1}, {2}
    Tasks: {0.finished_tasks}
    Now on Taskpackage: {0.task_package!s}
    """.format(user, ip, ua, user, datetime.utcnow())

    mail.send_mail(sender="Wen Li <spacelis@gmail.com>",
                   to="Wen Li <spacelis@gmail.com>",
                   subject=("[Geoexpertise] An error 500 occurred"),
                   body=body)
    raise Http404


@decorator
def login_required(view, *args, **kwargs):
    """ Redirect users to login page if the user have not login yet. """
    req = args[0]
    user = User.getOrCreate(request_property(req, 'session_token'))
    if user.key:
        view(*args, **kwargs)
    else:
        return HttpResponseForbidden('<h1>403</h1>')


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


def taskpackage(request):
    """

    :request: @todo
    :task_pack_key: The urlsafe key to a task_pack
    :returns: @todo

    """
    user = get_user(request)
    tp_key = _k(request_property(request, 'tpid'), 'TaskPackage')
    user.assign(tp_key.get())
    r = redirect('/pagerouter')
    r.set_cookie('session_token', user.session_token)
    return r


def pagerouter(request):
    """ Routing tasks by tasks.

    :request: Django HTTP request object.
    :returns: Page

    """
    user = get_user(request)

    if request_property(request, 'action') == 'taskpackage':
        return taskpackage(request)
    elif request_property(request, 'no_instruction') != '1':
        return redirect('/instructions')
    elif request_property(request, 'no_survey') != '1':
        return redirect('/survey')

    try:
        task_key = user.task_package.get().nextTaskKey()
        return redirect('/task/%s?show_rk=1' %  # FIXME should be remove when release
                        (task_key.urlsafe(),))
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
    user = get_user(request).touch()
    if user.email_account is None:
        return render_to_response('survey.html',
                                  {'judge_email': '',
                                   'judge_id': user.key.urlsafe(),
                                   'user': user.js_encode()})
    ea = user.email_account.get()
    return render_to_response('survey.html', {'judge_email': ea.email,
                                              'judge_id': user.key.urlsafe(),
                                              'user': user.js_encode()})


class FilterSetMaker(object):

    """ The filter information for zoom in/out of data in web interface. """

    Relation = namedtuple('Relation', ('poi', 'pid', 'cate', 'zcate'))
    Filter = namedtuple('Filter', ('name', 'pid', 'level', 'description'))

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
            (' in category of' + ', '.join(cate)) if cate else '',
        )

    @staticmethod
    def getCateDescription(relatives):
        """ Return a discription of a category filter.

        :f: @todo
        :returns: @todo

        """
        poi = [p for t, p in relatives if t == 'of' and p]
        zcate = [z for t, z in relatives if t == 'in' and z]

        return '''This is a subcategory%s%s.''' % (
            (' in ' + ', '.join(zcate)) if zcate else '',
            (' and contains ' + ', '.join(poi)) if poi else ''
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
            self.relationship.append(FilterSetMaker.Relation(
                t.name,
                t.info['id'],
                t.info['category']['name'],
                t.info['category']['zero_category_name']))
        elif t.level == 'CATEGORY':
            self.relationship.append(FilterSetMaker.Relation(
                '',
                None,
                (
                    t.info['name']
                    if t.info['name'] != t.info['zero_category_name']
                    else ''
                ),
                t.info['zero_category_name']))

    def getFilterSet(self):
        """ Return a set of filters.
        :returns: @todo

        """
        rel = [
            FilterSetMaker.Filter(
                poi,
                g.next().pid,
                'p',
                FilterSetMaker.getPoiDescription(
                    set(reduce((L + L),
                               [[('in', p.cate), ('in', p.zcate)] for p in g],
                               []))
                )
            )
            for poi, g in groupby(sorted(self.relationship, key=L.poi),
                                  key=L.poi)
            if poi
        ] + [
            FilterSetMaker.Filter(
                cate,
                None,
                'c',
                FilterSetMaker.getCateDescription(
                    set(reduce((L + L),
                               [[('has', p.poi), ('in', p.zcate)] for p in g],
                               []))
                )
            )
            for cate, g in groupby(sorted(self.relationship, key=L.cate),
                                   key=L.cate)
            if cate
        ] + [
            FilterSetMaker.Filter(
                zcate,
                None,
                'z',
                FilterSetMaker.getZCateDescription(
                    set(reduce((L + L),
                               [[('has', p.poi), ('has', p.cate)] for p in g],
                               []))
                )
            )
            for zcate, g in groupby(sorted(self.relationship, key=L.zcate),
                                    key=L.zcate)
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
    if user.task_package is None and not settings.DEBUG:
        raise Http404
    show_rk = request_property(request, 'show_rk', False)
    task = _k(task_key, 'AnnotationTask').get()
    rs = [r.get() for r in task.rankings]
    ts = [r.topic.get() for r in rs]
    if not show_rk:
        title = lambda ts, _: '\n'.join(
            ['Example Inquiry:'] +
            [q + '?'
             for q in ts[0].example.split('? ')])[:-1]
    else:
        title = lambda _, rs: '\n'.join(
            [rs[0].candidate.get().screen_name] +
            ['{0}, {1[profile_type]}: {1[rank]} ({1[score]:.6})'.format(r.rank_method, r.rank_info)
             for r in rs])

    def mk_topic(ts, rs):
        """ Prepare topics for the view """
        return {'topic_id': rs[0].topic_id,
                'topic_type': ts[0].level,
                'topic': ts[0].name,
                'region': rs[0].region,
                'title': title(ts, rs)}

    red = op.foldl(lambda x, y: dict(x.items() + y.items()), {})
    topics = red(map(
        F() >> (lambda item: (item[0], list(item[1]))) >>
        (lambda item: {item[0]: mk_topic(*zip(*item[1]))}),
        groupby(
            sorted(
                zip(ts, rs), key=L[1].topic_id),
            key=L[1].topic_id)))

    # make filters out of topics
    fsm = FilterSetMaker()
    for _, g in groupby(ts, key=L.name):
        fsm.addTopic(g.next())
    fs = fsm.getFilterSet()
    fs_injson = json.dumps([
        {'name': f.name, 'level': f.level, 'pid': f.pid} for f in fs
    ])

    return render_to_response(
        'expert_view.html',
        {
            'user': user.js_encode(),
            'topics': topics.values(),
            'candidate': task.candidate.urlsafe(),
            'task_key': task_key,
            'filters': fs,
            'filters_json': fs_injson,
            'topic_judgement': 'null'
        },
        context_instance=RequestContext(request))


# TODO need to be refactored since models changed
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
        raise Http404
    user.touch()

    try:
        task_key = request.POST.get('pv-task-key', None)
        task = _k(task_key, 'AnnotationTask').get()

        scores = get_scores(request)
        ipaddr, user_agent = get_client(request)
        tb = get_traceback(request)
        Judgement.add(user, task, scores, ipaddr, user_agent, tb)

        user.accomplish(task)

    except TypeError:
        raise Http404
    return redirect('/pagerouter')


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
    return render_to_response('instructions.html',
                              {'goto': '#'},
                              context_instance=RequestContext(request))
