#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" An api of caching tweets for internal use.

File: taskworker.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    Cache API

"""

from django.views.decorators.csrf import csrf_exempt

from google.appengine.ext import ndb
from google.appengine.api.taskqueue import Task

from apps.profileviewer.api import APIRegistry
from apps.profileviewer.twitter_util import new_twitter_client
from apps.profileviewer.twitter_util import new_foursquare_client
from apps.profileviewer.twitter_util import CATEGORY_MAP
from apps.profileviewer.models import GeoEntity
from apps.profileviewer.models import TwitterAccount
from apps.profileviewer.twitter_util import update_poi_category

api = APIRegistry()


@csrf_exempt
def call_endpoint(request, name):
    """ call_endpoint """
    return api.call_endpoint(request, name)


@api.api_endpoint()
def test_cache_user():
    """ queue_test """
    d = {
        'token': '127747814-FxfJ3TCsQPkTjEa10y0Mn3EnqJbXKW4wo1JuUCT7',
        'secret': '7bXLG3cjt3BuIG2arND7Fe9VHaF95EjUOTsmTbX9MNuaH',
        '_admin_key': 'tu2013delft'
    }

    Task(params=d, url='/api/taskworker/cache_user').add('crawler')


@api.api_endpoint()
def test_cache_checkins():
    """ queue_test """
    d = {
        'token': '127747814-FxfJ3TCsQPkTjEa10y0Mn3EnqJbXKW4wo1JuUCT7',
        'secret': '7bXLG3cjt3BuIG2arND7Fe9VHaF95EjUOTsmTbX9MNuaH',
        'twitter_id': 127747814,
        '_admin_key': 'tu2013delft'
    }

    Task(params=d, url='/api/taskworker/cache_checkins').add('crawler')


@api.api_endpoint(secured=True)
def process_pois(tkey):
    """ crawling poi information for all checkins from a user

    :tkey: A TwitterAccount.
    :returns: @todo

    """
    ta = ndb.Key(urlsafe=tkey, kind='TwitterAccount').get()
    for s in ta.checkins:
        poi_id = s['place']['id']
        if GeoEntity.contains(tfid=poi_id):
            return  # TODO should copy those from Geoentities to checkins
        update_poi_category(s['place'])
    ta.put()


@api.api_endpoint(secured=True)
def cache_checkins(token, secret, twitter_id=None, twitter_account=None):
    """ Crawling the user by screen_name.

    :token: An access_token.
    :secret: An access_token_secret
    :twitter_id: Twitter user id that need to be crawled,
        either this or twitter_account should be given
    :twitter_account: A TwitterAccount that need to be filled with checkins
    :returns: @todo

    """
    cli = new_twitter_client(token, secret)
    try:
        if twitter_account:
            ta = twitter_account
        elif twitter_id:
            ta = TwitterAccount.query(
                TwitterAccount.twitter_id == twitter_id
            ).fetch(1)[0]
        ta.fetchCheckins(cli)

    except IndexError:
        tu = cli.get_user(user_id=twitter_id)
        t = TwitterAccount.createForCheckins(tu.screen_name,
                                             tu.id)
        t.fetchCheckins(cli)


@api.api_endpoint(secured=True)
def cache_user(token, secret):
    """ Cache all the friends of the token owner.

    :token: @todo
    :secret: @todo
    :returns: @todo

    """
    cli = new_twitter_client(token, secret)
    cache_checkins(token, secret, cli.me().id)
    #for f in cli.friends_ids():
        #cache_checkins(token, secret, twitter_id=f)
