#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The API relate to User management.

File: user.py
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    The API related to User management, such as signup or login.

"""

import re
import tweepy as tw


from google.appengine.api import memcache

from django.http import HttpResponse

from apps.profileviewer.api import APIRegistry
from apps.profileviewer.models import EmailAccount
from apps.profileviewer.models import User
from apps.profileviewer.models import TwitterAccount
from apps.profileviewer.twitter_util import APICRED


_REG = APIRegistry()


EMAILPTN = re.compile(r"^[-!#$%&'*+/0-9=?A-Z^_a-z{|}~]"
                      r"(\.?[-!#$%&'*+/0-9=?A-Z^_a-z{|}~])*"
                      r"@[a-zA-Z](-?[a-zA-Z0-9])*"
                      r"(\.[a-zA-Z](-?[a-zA-Z0-9])*)+$")


def call_endpoint(request, name):
    """Call endpoint by name.

    :request: Django HttpRequest object.
    :name: The name of the endpoint to call.
    :returns: Json string response.

    """
    return _REG.call_endpoint(request, name)


@_REG.api_endpoint()
def email_login(email, passwd, _user):
    """ Login the user with name and passwd.

    :email: the user email.
    :passwd: the passwd.

    """
    try:
        assert EMAILPTN.match(email)
        assert len(passwd) < 50
        user = EmailAccount.login(email, passwd, _user)
        return {'action': 'login',
                'succeeded': True,
                'user': user.as_viewdict()}
    except (ValueError, AssertionError):
        return {'action': 'login',
                'succeeded': False,
                'msg': 'The email or the password is not correct.'}


@_REG.api_endpoint()
def self(_user):
    """ Return the user object of current User.

    :returns: A viewdict object of current user.

    """
    return {'action': 'user/self',
            'succeeded': True,
            'user': _user.as_viewdict()}


@_REG.api_endpoint()
def email_signup(email, passwd, name, _user):
    """ SignUp this user.

    :email: email address.
    :passwd: the password.

    """
    try:
        assert EMAILPTN.match(email)
        assert len(passwd) < 50
        assert len(name) < 50
        user = EmailAccount.signUp(email, passwd,
                                   name, _user)
        user.reset_token()
        return {'action': 'signup',
                'succeeded': True,
                'user': user.as_viewdict()}
    except AssertionError:
        return {'action': 'signup',
                'succeeded': False,
                'msg': 'Please input a valid email or password.'}
    except ValueError:
        return {'action': 'signup',
                'succeeded': False,
                'msg': 'The email address is already registered.'}


@_REG.api_endpoint()
def logout(_user):
    """ SignUp this user.

    :_user: the user issues the request.

    :return: {"action": "logout", "succeeded": true}
    """
    _user.reset_token()
    return {'action': 'logout',
            'succeeded': True,
            'user': User.unit().as_viewdict()}


@_REG.api_endpoint()
def twitter_login(_user):
    """ Step 1 of OAuth to Twitter
    :returns: @todo

    """
    print _user.session_token
    auth = tw.OAuthHandler(
        APICRED['twitter_consumer_key'],
        APICRED['twitter_consumer_secret'],
        'http://localhost:8080/api/user/twitter_oauth_callback')
    url = auth.get_authorization_url()
    memcache.set(key='oauth-' + _user.session_token,  # pylint: disable=E1101
                 value=(auth.request_token.key,
                        auth.request_token.secret),
                 time=1800)
    return {
        'action': 'twitter_login',
        'succeeded': True,
        'redirect': url
    }


PAGE_CLOSE_WINDOW = """
<html>
<header>
<script>
window.close();
</script>
</header>
<body>
This window should now be closed.
</body>
</html>
"""


@_REG.api_endpoint(tojson=False)
def twitter_oauth_callback(_user, oauth_verifier):
    """ Step 3 of OAuth to Twitter
    :returns: @todo

    """
    print _user.session_token
    oauth_cred = memcache.get('oauth-' +  # pylint: disable=E1101
                              _user.session_token)
    auth = tw.OAuthHandler(
        APICRED['twitter_consumer_key'],
        APICRED['twitter_consumer_secret'])
    auth.set_request_token(oauth_cred[0], oauth_cred[1])
    auth.get_access_token(oauth_verifier)
    api = tw.API(auth)

    u = api.verify_credentials()
    if not u:
        return {
            'action': 'twitter_login_callback',
            'succeeded': False,
        }
    try:
        t = TwitterAccount.getByScreenName(u.screen_name)
        t.access_token = auth.access_token.key
        t.access_token_secret = auth.access_token.secret
        t.put()
        t.user.get().inherit(_user)
        return HttpResponse(PAGE_CLOSE_WINDOW)
    except KeyError:
        t = TwitterAccount.createForAccess(
            auth.access_token.key,
            auth.access_token.secret,
            u.screen_name)  # pylint: disable=E1103
        _user.addTwitterAccount(t)
        t.attach(_user)
        return HttpResponse(PAGE_CLOSE_WINDOW)
