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

import yaml

TWITTERCRED = yaml.load(open('cred.yaml'))
