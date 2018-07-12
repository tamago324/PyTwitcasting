
from datetime import datetime

import os
import webbrowser

from pytwitcasting.auth import (
    TwitcastingImplicit,
    TwitcastingOauth
)


def parse_datetime(string):
    return datetime.fromtimestamp(string)


def get_access_token_prompt_implicit(client_id=None):
    """
    Implicit authorization flow
    http://apiv2-doc.twitcasting.tv/#implicit
    """

    if not client_id:
        client_id = os.environ['TWITCASTING_CLIENT_ID']

    tc_imp = TwitcastingImplicit(client_id)
    auth_url = tc_imp.get_authorize_url()
    webbrowser.open(auth_url)
    print(f'Opened {auth_url} in your browser')

    print()
    print()

    response = input('Enter the URL you were redirected to: ')

    print()
    print()

    token_info = tc_imp.get_access_token(response)

    if token_info:
        return token_info['access_token']
    else:
        return None


def get_access_token_prompt_oauth(client_id=None, client_secret=None, redirect_uri=None, state=None):
    """
    Authorization Code Grant flow
    http://apiv2-doc.twitcasting.tv/#authorization-code-grant
    """
    if not client_id:
        client_id = os.environ['TWITCASTING_CLIENT_ID']

    if not client_secret:
        client_secret = os.environ['TWITCASTING_CLIENT_SECRET']

    if not redirect_uri:
        redirect_uri = os.environ['TWITCASTING_REDIRECT_URI']

    tc_oauth = TwitcastingOauth(client_id, client_secret, redirect_uri, state)
    auth_url = tc_oauth.get_authorize_url()
    webbrowser.open(auth_url)
    print(f'Opened {auth_url} in your browser')

    print()
    print()

    response = input('Enter the URL you were redirected to: ')

    print()
    print()

    code = tc_oauth.parse_response_code(response)
    token_info = tc_oauth.get_access_token(code)

    if token_info:
        return token_info['access_token']
    else:
        return None
