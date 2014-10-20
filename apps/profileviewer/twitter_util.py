#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" A thin layer of API around python-twitter.

File: twitter_util.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    A thin layer of API

"""

import json
import tweepy as tw

with open('cred.json') as fin:
    APICRED = json.load(fin)

with open('category_map.json') as fin:
    CATEGORY_MAP = json.load(fin)


def new_twitter_client(token=None, secret=None):
    """ return a Twitter API object. """
    auth = tw.OAuthHandler(
        APICRED['twitter_consumer_key'],
        APICRED['twitter_consumer_secret'])
    if token and secret:
        auth.set_access_token(token, secret)
    return tw.API(auth)


def new_foursquare_client(token=None, secret=None):  # pylint: disable=W0613
    """ Return a Foursquare API client. """
    import foursquare
    return foursquare.Foursquare(client_id=APICRED['foursq_client_id'],
                                 client_secret=APICRED['foursq_client_secret'])


def strip_checkin(tweet):
    """ Strip useless information from tweets as a checkin.

    :tweet: @todo
    :returns: @todo

    """
    place = tweet['place']
    return {
        'created_at': tweet['created_at'],
        'retweeted': tweet['retweeted'],
        'retweet_count': tweet['retweet_count'],
        'in_reply_to_status_id': tweet['in_reply_to_status_id'],
        'in_reply_to_screen_name': tweet['in_reply_to_screen_name'],
        'in_reply_to_user_id': tweet['in_reply_to_user_id'],
        'favorited': tweet['favorited'],
        'favorite_count': tweet['favorite_count'],
        'id': tweet['id'],
        'text': tweet['text'],
        'place': {
            'place_type': place['place_type'],
            'lng': place['bounding_box']['coordinates'][0][0][0],
            'lat': place['bounding_box']['coordinates'][0][0][1],
            'name': place['name'],
            'full_name': place['full_name'],
            'id': place['id'],
            'category': None,
        },
        'user': {
            'id': tweet['user']['id'],
            'screen_name': tweet['user']['screen_name']
        }
    }


def iter_timeline(timeline, **kwargs):
    """ Iterating though all status in timeline.

    :timeline: The API timeline function which are supposed
        to configured with an auth token.
    :**kwargs: The other parameters needed for the timeline function.
    :yields: the timeline item

    """
    kwargs = dict(kwargs)
    kwargs['count'] = 200
    has_next = True
    while has_next:
        has_next = False
        for i in timeline(**kwargs):
            has_next = True
            yield i
        if has_next:
            kwargs['max_id'] = i.id - 1  # pylint: disable=W0631


def find_place(p):
    """ Find a place on Foursquare with the name and coordinates

    :p: a place request {'lat': xx, 'lng': yy, 'name': zzz}
    :returns: @todo

    """
    cli = new_foursquare_client()
    places = cli.venues.search(  # pylint: disable=E1101
        params={'ll': '%s,%s' % (p['lat'], p['lng']),
                'query': p['name'],
                'radius': 100,
                'intent': 'match'})['venues']
    if len(places) > 0:
        return places[0]
    else:
        return None


def update_poi_category(p):
    """ Find a place on Foursquare and update stored poi's
        category.
    """
    fs_p = find_place(p)
    category = fs_p['cateogry'][0]
    category_id = category['id']
    p['category'] = {
        'id': category_id,
        'name': category['name'],
        'zcateogry_id': CATEGORY_MAP[category_id]['id'],
        'zcategory': CATEGORY_MAP[category_id]['name']}
    return p
