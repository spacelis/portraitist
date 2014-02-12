#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests for twitter_utils.

File: test_twitter_util.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:


"""

import json
import unittest
import apps.profileviewer.twitter_util as tw


class TestTwitterUitl(unittest.TestCase):

    """Test Twitter Util functions. """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_strip_checkin(self):
        """ test strip_checkin """
        data = r"""
{
    "contributors" : null,
    "truncated" : false,
    "text" : "Watching UFC 128 tonight? Check out @HeavyMMA's \"FIGHT DAY,\" the only live UFC pre-show. Livestreaming now! http://www.heavy.com/mma",
    "in_reply_to_status_id" : null,
    "id" : 49248121833799680,
    "favorite_count" : 0,
    "entities" : {
        "symbols" : [ ],
        "user_mentions" : [
            {
                "indices" : [
                    36,
                    45
                ],
                "id_str" : "87779193",
                "screen_name" : "HeavyMMA",
                "name" : "Heavy MMA",
                "id" : 87779193
            }
        ],
        "hashtags" : [ ],
        "urls" : [ ]
    },
    "retweeted" : false,
    "coordinates" : null,
    "source" : "web",
    "in_reply_to_screen_name" : null,
    "id_str" : "49248121833799680",
    "retweet_count" : 0,
    "in_reply_to_user_id" : null,
    "favorited" : false,
    "user" : {
        "follow_request_sent" : false,
        "profile_use_background_image" : true,
        "geo_enabled" : true,
        "verified" : false,
        "profile_text_color" : "333333",
        "profile_image_url_https" : "https://si0.twimg.com/profile_images/2290351466/12lwwypf87a0wexpelg5_normal.jpeg",
        "profile_sidebar_fill_color" : "DDEEF6",
        "is_translator" : false,
        "id" : 100032665,
        "entities" : {
            "url" : {
                "urls" : [
                    {
                        "url" : "http://t.co/YDL3VZWywx",
                        "indices" : [
                            0,
                            22
                        ],
                        "expanded_url" : "http://www.morris-king.com/",
                        "display_url" : "morris-king.com"
                    }
                ]
            },
            "description" : {
                "urls" : [ ]
            }
        },
        "followers_count" : 737,
        "protected" : false,
        "location" : "New York, NY",
        "default_profile_image" : false,
        "id_str" : "100032665",
        "utc_offset" : -18000,
        "statuses_count" : 2027,
        "description" : "The Morris + King Company is a NY-based PR and marketing agency with a national reputation for results-driven campaigns and inventive messaging strategies.",
        "friends_count" : 947,
        "profile_link_color" : "0EC7F5",
        "profile_image_url" : "http://a0.twimg.com/profile_images/2290351466/12lwwypf87a0wexpelg5_normal.jpeg",
        "notifications" : null,
        "profile_background_image_url_https" : "https://si0.twimg.com/profile_background_images/573839504/cgjitv45ovuqyqj1s715.jpeg",
        "profile_background_color" : "F9FFF7",
        "profile_background_image_url" : "http://a0.twimg.com/profile_background_images/573839504/cgjitv45ovuqyqj1s715.jpeg",
        "name" : "Morris + King ",
        "lang" : "en",
        "profile_background_tile" : false,
        "favourites_count" : 2,
        "screen_name" : "Morris_King",
        "url" : "http://t.co/YDL3VZWywx",
        "created_at" : "Mon Dec 28 19:53:39 +0000 2009",
        "contributors_enabled" : false,
        "time_zone" : "Eastern Time (US & Canada)",
        "profile_sidebar_border_color" : "C0DEED",
        "default_profile" : false,
        "following" : null,
        "listed_count" : 37
    },
    "geo" : null,
    "in_reply_to_user_id_str" : null,
    "lang" : "en",
    "created_at" : "",
    "in_reply_to_status_id_str" : null,
    "place" : {
        "category" : {
            "pluralName" : "Offices",
            "primary" : true,
            "name" : "Office",
            "shortName" : "Office",
            "id" : "4bf58dd8d48988d124941735",
            "icon" : {
                "prefix" : "https://foursquare.com/img/categories_v2/building/default_",
                "suffix" : ".png"
            },
            "zero_category" : "4d4b7105d754a06375d81259",
            "zero_category_name" : "Professional & Other Places"
        },
        "country_code" : "US",
        "url" : "https://api.twitter.com/1.1/geo/id/fe1725bebee0705f.json",
        "country" : "United States",
        "place_type" : "poi",
        "bounding_box" : {
            "type" : "Polygon",
            "coordinates" : [
                [
                    [
                        -73.9919762461243,
                        40.73806481946583
                    ],
                    [
                        -73.9919762461243,
                        40.73806481946583
                    ],
                    [
                        -73.9919762461243,
                        40.73806481946583
                    ],
                    [
                        -73.9919762461243,
                        40.73806481946583
                    ]
                ]
            ]
        },
        "full_name" : "The Morris + King Company, New York",
        "attributes" : {
            "street_address" : "101 Fifth Avenue"
        },
        "id" : "fe1725bebee0705f",
        "name" : "The Morris + King Company"
    }
}
        """
        s = tw.strip_checkin(json.loads(data))
        self.assertEqual(s['place']['lat'], 40.73806481946583)
        self.assertEqual(s['place']['lng'], -73.9919762461243)
        self.assertEqual(s['place']['place_type'], 'poi')
        self.assertEqual(s['user']['id'], 100032665)
        self.assertEqual(s['user']['screen_name'], "Morris_King")
        self.assertEqual(s['place']['category']['id'], "4bf58dd8d48988d124941735")
        self.assertEqual(s['place']['category']['zcategory'], "4d4b7105d754a06375d81259")
