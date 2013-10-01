#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: models.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
Github: http://github.com/spacelis
Description:
    Expertise data model
"""

import csv
import json
from uuid import uuid4
from datetime import timedelta
from datetime import datetime as dt
from zlib import compress
from zlib import decompress
from hashlib import sha1

from django.http import Http404
from google.appengine.ext import ndb

DEFAULT_APP_NAME = 'geo-expertise-2'
MIN30 = timedelta(minutes=30)
csv.field_size_limit(500000)


def getUID():
    """ Return a UUID in str()
    :returns: @todo

    """
    return str(uuid4())


def parent_key(name, appname=DEFAULT_APP_NAME):
    """@todo: Docstring for parent_key.

    :name: @todo
    :appname: @todo
    :returns: @todo

    """
    return ndb.Key(appname, name)


class Judge(ndb.Model):

    """ A class representing users as judges."""

    # pylint: disable-msg=E1101
    nickname = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    judge_id = ndb.StringProperty(indexed=True)
    judgement_no = ndb.IntegerProperty(indexed=True)
    judgements = ndb.JsonProperty()
    # pylint: enable-msg=E1101

    @classmethod
    def upload(cls, fstream):
        """ Upload data to dbs by reading from a stream
        :fstream: A stream like object
        :returns: None

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('judge'),
                nickname='',
                email='',
                judge_id=row['judge_id'],
                judgement_no=int(row['judgement_no']),
                judgements=json.loads(row['judgements']),
                ).put()

    @classmethod
    def newJudge(cls, email, nickname):
        """ Create a new judge user

        :email: An email address associate with this judge
        :nickname: An nickname used for greeting
        :returns: A newly created ndb judge object

        """
        print email, nickname
        js = Judge.query(Judge.email == email).fetch()
        if len(js) > 0:
            return js[0]
        else:
            return cls(parent=parent_key('judge'),
                       judge_id=getUID(),
                       judgement_no=0,
                       email=email,
                       nickname=nickname,
                       judgements=list())

    @classmethod
    def getJudgeById(cls, judge_id):
        """Return the judge object by given judge_id

        :judge_id: An string id assigned to each judge
        :returns: return the judge ndb object

        """
        judges = Judge.query(Judge.judge_id == judge_id).fetch(1)
        if not judges:
            return Judge(parent=parent_key('judge'),
                         judge_id=judge_id,
                         judgement_no=0,
                         judgements=list())
        return judges[0]

    @classmethod
    def addJudgement(cls, judge, judgement):
        """@todo: Docstring for addJudgement.

        :judge: The id of the judge
        :judgement: A dict object holding the judgement made by the judge
        :returns: The ndb object of the judge

        """
        e = Expert.getExpertByScreenName(judgement['candidate'])
        e.judged_by.append(judge.judge_id)
        e.judged_no += 1
        e.put()
        judge.judgements.append(judgement)
        judge.judgement_no += 1
        judge.put()
        return judge

    @classmethod
    def statistics(cls):
        """ Return a dict object filled with statistics information

        :returns: {'judge_no', 'judgement_no'}

        """
        js = [j.judgement_no for j in
              Judge.query(projection=[Judge.judgement_no])]
        return {'judge_no': len(js),
                'j_judgement_no': sum(js)}


class Topic(ndb.Model):

    """Judgment tasks"""
    ZCATE_TOPIC = 'A topic about a top-level category.'
    CATE_TOPIC = 'A topic about a lower-level category.'
    POI_TOPIC = 'A topic about a specific place.'

    # pylint: disable-msg=E1101
    topic_id = ndb.StringProperty(indexed=True)
    topic = ndb.StringProperty()
    region = ndb.StringProperty()
    topic_type = ndb.ComputedProperty(
        lambda self: Topic.ZCATE_TOPIC if 'zcate' in self.topic_id
        else (Topic.CATE_TOPIC if 'cate' in self.topic_id
              else Topic.POI_TOPIC))

    experts = ndb.JsonProperty()
    related_to = ndb.JsonProperty()

    assigned = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

    @classmethod
    def getTopicById(cls, topic_id):
        """ Return topic by topic_id

        :topic_id: A given topic_id, e.g. "poi-0001", "zcate-0009"
        :returns: A dict object representing a Topic

        """
        t = cls.query(cls.topic_id == topic_id).fetch(1)[0]
        return {'topic_id': t.topic_id,
                'topic': t.topic,
                'region': t.region,
                'topic_type': t.topic_type,
                'related_to': t.related_to}

    @classmethod
    def upload(cls, fstream):
        """ Upload data to dbs by reading from a stream
        :fstream: A stream like object
        :returns: None

        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('topic'),
                topic_id=row['topic_id'],
                topic=row['topic'],
                region=row['region'],
                experts=json.loads(row['experts']),
                related_to=json.loads(row['related_to']),
                ).put()


class Participant(ndb.Model):  # pylint: disable-msg=R0903

    """Persistency of Participant from Twitter Ads Campaign"""

    # pylint: disable-msg=E1101
    name = ndb.StringProperty(indexed=True)
    token = ndb.StringProperty(indexed=True)
    card = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)
    screen_name = ndb.StringProperty(indexed=True)
    gform_url = ndb.StringProperty()
    # pylint: enable-msg=E1101

    @classmethod
    def newParticipant(cls, name, token, card,  # pylint: disable-msg=R0913
                       email, screen_name, gform_url):
        """ Create and return a new Participant

        :returns: A new Participant

        """
        return cls(name=name,
                   token=token,
                   card=card,
                   email=email,
                   screen_name=screen_name,
                   gform_url=gform_url)


class Expert(ndb.Model):

    """Candidate Expert for judging"""

    # pylint: disable-msg=E1101
    screen_name = ndb.StringProperty(indexed=True)
    hash_id = ndb.ComputedProperty(
        lambda self: sha1(self.screen_name).hexdigest())

    topics = ndb.JsonProperty()
    checkins_store = ndb.BlobProperty()
    judged_by = ndb.StringProperty(repeated=True, indexed=True)
    judged_no = ndb.IntegerProperty(indexed=True)

    assigned = ndb.DateTimeProperty(indexed=True)
    # pylint: enable-msg=E1101

    class ExpertNotExists(Http404):
        """ Exception when the expert queried does not exist"""
        pass

    @classmethod
    def getExpertsByPriority(cls, limit=10):
        """ Get a list of experts sorted by their priority for judging

        :returns: A list of experts

        """
        assert limit > 0
        return cls.query(Expert.assigned < (dt.now() - MIN30))\
            .order(Expert.assigned, Expert.judged_no)\
            .fetch(limit)

    @classmethod
    def getExpertInfoByHashId(cls, hash_id):
        """ Return a dict object holding basic information about the expert

        :screen_name: The screen_name of the expert
        :returns: A dict {'screen_name': str, 'topics': [topic_id: str]}

        """
        topics = cls.getExpertByHashId(hash_id).topics
        return {'hash_id': hash_id,
                'topics': topics}

    @classmethod
    def getExpertByHashId(cls, hash_id):
        """ Return a ndb object of the given expert

        :screen_name: The screen_name
        :returns: A ndb object of the expert

        """
        try:
            return cls.query(Expert.hash_id == hash_id).fetch(1)[0]
        except IndexError:
            raise Expert.ExpertNotExists(hash_id)

    @classmethod
    def getExpertInfoByScreenName(cls, screen_name):
        """ Return a dict object holding basic information about the expert

        :screen_name: The screen_name of the expert
        :returns: A dict {'screen_name': str, 'topics': [topic_id: str]}

        """
        e = cls.getExpertByScreenName(screen_name)
        return {'screen_name': e.screen_name,
                'topics': e.topics}

    @classmethod
    def getExpertByScreenName(cls, screen_name):
        """ Return a ndb object of the given expert

        :screen_name: The screen_name
        :returns: A ndb object of the expert

        """
        try:
            return cls.query(Expert.screen_name == screen_name).fetch(1)[0]
        except IndexError:
            raise Expert.ExpertNotExists(screen_name)

    @classmethod
    def getScreenNames(cls, limit=10):
        """ Return a list of screen_names ordered by their priority for judging

        :returns: [screen_name: str]

        """
        return [e.screen_name for e in cls.getExpertsByPriority(limit=limit)]

    @staticmethod
    def getCheckinsInJson(expert):
        """ Get the checkin profile for given user and return a json string

        :returns: checkins: json

        """
        return decompress(expert.checkins_store)

    @classmethod
    def getTask(cls):
        """ Get only one from the ordered screen_names by priority for judging

        :returns: screen_name

        """
        e = cls.getExpertsByPriority(1)[0]
        e.assigned = dt.now()
        e.put()
        return e.hash_id

    @classmethod
    def getJudgedExperts(cls):
        """ Return all judged experts
        :returns: [expert: Expert]

        """
        es = cls.query(Expert.judged_no > 0).fetch()
        return es

    @classmethod
    def upload(cls, fstream):
        """Upload data to dbs by reading from csv file stream
        """
        for row in csv.DictReader(fstream):
            cls(parent=parent_key('expert'),
                screen_name=row['screen_name'],
                topics=json.loads(row['topics']),
                checkins_store=compress(row['checkins']),
                assigned=dt(2013, 1, 1),
                ).put()

    @classmethod
    def statistics(cls):
        """ Return a set of statistics

        :returns: {'judged_experts': int, 'expert_no': int,
                   'judgement_no': int}

        """
        es = [e.judged_no for e in
              Expert.query(projection=[Expert.judged_no]).fetch()]
        return {'judged_experts': len([e for e in es if e > 0]),
                'expert_no': len(es),
                'e_judgement_no': sum(es)}


class TaskPackage(ndb.Model):

    """ A package of tasks"""

    # pylint: disable-msg=E1101

    task_pack_id = ndb.StringProperty(indexed=True)
    tasks = ndb.StringProperty(repeated=True)
    tasks_done = ndb.StringProperty(repeated=True)
    confirm_code = ndb.StringProperty()

    # pylint: enable-msg=E1101

    class TaskPackageNotExists(Http404):
        """ If the task_pack_id doesn't exists"""
        pass

    class NoMoreTask(Exception):
        """ If there is no more tasks to assign"""
        pass

    @classmethod
    def construct(cls, psize=10):
        """ Construct task packages from those undone tasks
        :returns: @todo

        """
        tp = TaskPackage(parent=parent_key('taskpackage'),
                         task_pack_id=getUID(),
                         tasks=list(),
                         tasks_done=list(),
                         confirm_code=getUID().split('-')[-1])
        tp_cnt = 0
        t_cnt = 0
        tp_list = list()
        for e in Expert.query().fetch():
            if len(tp.tasks) < psize:
                tp.tasks.append(e.hash_id)
                t_cnt += 1
            else:
                tp.put()
                tp_list.append({'id': tp.task_pack_id,
                                'cf_code': tp.confirm_code})
                tp_cnt += 1
                tp = TaskPackage(task_pack_id=getUID(),
                                 tasks=list(),
                                 tasks_done=list(),
                                 confirm_code=getUID().split('-')[-1])
                tp.tasks.append(e.hash_id)
                t_cnt += 1
        if len(tp.tasks) > 0:
            tp.put()
            tp_list.append({'id': tp.task_pack_id,
                            'cf_code': tp.confirm_code})
            tp_cnt += 1
        return {'assigned_tasks': t_cnt,
                'created_packages': tp_cnt,
                'task_packages': tp_list}

    @classmethod
    def getTaskPackage(cls, task_pack_id):
        """ Get a reference to the task package by task_pack_id

        :task_pack_id: @todo
        :returns: @todo

        """
        try:
            return TaskPackage.query(TaskPackage.task_pack_id == task_pack_id)\
                .fetch(1)[0]
        except IndexError:
            raise TaskPackage.TaskPackageNotExists(task_pack_id)

    @classmethod
    def getTask(cls, task_pack_id):
        """ Get a new task from a task package

        :task_pack_id: @todo
        :returns: @todo

        """
        try:
            return cls.getTaskPackage(task_pack_id).tasks[0]
        except IndexError:
            raise TaskPackage.NoMoreTask()

    @classmethod
    def getConfirmationCode(cls, task_pack_id):
        """ Get the confirmation code by tp_id

        :task_pack_id: @todo
        :returns: @todo

        """
        return cls.getTaskPackage(task_pack_id).confirm_code

    @classmethod
    def submitTask(cls, task_pack_id, expert_hash_id):
        """ Mark a task been done by the assessor

        :task_pack_id: @todo
        :expert_hash_id: @todo
        :returns: @todo

        """
        tp = cls.getTaskPackage(task_pack_id)
        tlist = list(tp.tasks)
        pos = tlist.index(expert_hash_id)
        del tlist[pos]
        if len(tlist) > 0:
            tnext = tlist[0]
        else:
            tnext = None
        tp.tasks = tlist
        tp.tasks_done.append(expert_hash_id)
        tp.put()
        return tnext
