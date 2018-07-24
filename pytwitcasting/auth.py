import base64
import urllib.parse
import time

import requests

from pytwitcasting.error import TwitcastingError


OAUTH_TOKEN_URL = 'https://apiv2.twitcasting.tv/oauth2/access_token'
OAUTH_BASE_URL = 'https://apiv2.twitcasting.tv/oauth2/authorize'


def _get_authorize_url(client_id, response_type, state=None):
    """ 認可のためのURLを取得

    :param client_id: ClientID
    :param response_type: code or token
    :param state: CSRFトークン
    :return: 認可するためのURL
    :rtype: str
    """
    payload = {'client_id': client_id,
               'response_type': response_type}

    if state is not None:
        payload['state'] = state

    urlparams = urllib.parse.urlencode(payload)

    return f'{OAUTH_BASE_URL}?{urlparams}'


class TwitcastingImplicit(object):
    """ Implicitでの認可フロー

    http://apiv2-doc.twitcasting.tv/#implicit
    """

    def __init__(self, client_id, state=None):
        """
        :param client_id: このアプリのCliendID
        :type client_id: str
        :param state: (optional) このアプリのCSRFトークン
        :type state: str
        """
        self.client_id = client_id
        self.state = state

    def get_authorize_url(self, state=None):
        """ 認可のためのURLを取得

        :param state: CSRFトークン
        :type state: str
        :return: 認可するためのURL
        :rtype: str
        """
        return _get_authorize_url(client_id=self.client_id, response_type='token', state=state)

    def get_access_token(self, url):
        """ 認可後にリダイレクトしたURLから認可情報を解析し取り出す

        :param url: リダイレクトされたURL
        :type url: str
        :return: トークンの情報
        :rtype: dict
        """
        try:
            # URLから認可情報を取り出す
            # urllib.parse.parse_qs()を使う
            token_info = urllib.parse.parse_qs(url.split('#')[1])
            for k, v in token_info.items():
                item = v[0]
                token_info[k] = item

            # CSRFの比較
            if self.state:
                r_state = token_info.get('state', None)
                if r_state is None or not self.state == r_state:
                    raise TwitcastingError('Invalid CSRF token')

            token_info = self._add_expires_at_to_token_info(token_info)
            return token_info
        except IndexError:
            # XXX: raiseじゃなくていいの？
            return None

    def _add_expires_at_to_token_info(self, token_info):
        """ 失効日時を追加する

        :param token_info: WebAPIから取得した認可情報
        :type token_info: dict
        :return: ``expires_at`` が追加された認可情報
        :rtype: dict
        """
        # トークンの失効日時
        token_info['expires_at'] = int(time.time()) + int(token_info['expires_in'])
        return token_info


class TwitcastingApplicationBasis(object):
    """ アプリケーション単位でのアクセス

    http://apiv2-doc.twitcasting.tv/#access-token

    なんかこれ微妙なクラスな気がする...

    Usage::

      >>> import os
      >>> from pytwitcasting.auth import TwitcastingApplicationBasis
      >>> from pytwitcasting.api import API
      >>>
      >>> client_id = os.environ['TWITCASTING_CLIENT_ID']
      >>> client_secret = os.environ['TWITCASTING_CLIENT_SECRET']
      >>> app_basis = TwitcastingApplicationBasis(client_id, client_secret)
      >>> api = API(application_basis=app_basis)
      >>> api.get_user_info('tamago324_pad').name
      'たまたまご'

    """
    def __init__(self, client_id, client_secret):
        """

        :param client_id: ClientID
        :type client_id: str
        :param client_secret: ClientSecret
        :type client_secret: str
        """
        self.client_id = client_id
        self.client_secret = client_secret

    def get_basic_headers(self):
        """ Basicの認証ヘッダーを返す

        :return: 認可情報を含むヘッダー
        :rtype: str
        """
        enc = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode('utf-8')
        return {'Authorization': f'Basic {enc}'}


class TwitcastingOauth(object):
    """ Authorization Code Grantの認可フロー

    http://apiv2-doc.twitcasting.tv/#authorization-code-grant
    """

    def __init__(self, client_id, client_secret, redirect_uri, state=None):
        """
        :param client_id: ClientID
        :type client_id: str
        :param client_secret: ClientSecret
        :type client_secret: str
        :param redirect_uri: リダイレクト先(Callback URL)
        :type redirect_uri: str
        :param state: CRCFトークン
        :type state: str
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state

    def get_authorize_url(self, state=None):
        """ 認可のためのURLを取得

        :param state: CSRFトークン
        :type state: str
        :return: 認可するためのURL
        :rtype: str
        """
        return _get_authorize_url(client_id=self.client_id, response_type='code', state=state)

    def parse_response_code(self, url):
        """ 認可後にリダイレクトしたURLから認可情報を解析し取り出す

        :param url: リダイレクトされたURL
        :type url: str
        :return: アクセストークン取得コード
        :rtype: str
        """
        try:
            qry = url.split('?code=')[1].split('&')

            # CSRFトークンの確認
            if self.state:
                qry_state = qry[1].split('state=')[1]
                if not self.state == qry_state:
                    raise TwitcastingError('Invalid CSRF token')
            code = qry[0]
            return code
        except IndexError:
            return None

    def get_access_token(self, code):
        """ コードを用い、アクセストークンを取得する

        :param code: コード( :meth:`pytwitcasting.auth.TwitcastingOauth.get_response_code` の戻り値)
        :type code: str
        :return: 認可情報
        :rtype: dict
        """
        payload = {'code': code,
                   'grant_type': 'authorization_code',
                   'client_id': self.client_id,
                   'client_secret': self.client_secret,
                   'redirect_uri': self.redirect_uri}

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        res = requests.post(OAUTH_TOKEN_URL, data=payload, headers=headers)

        if res.status_code != 200:
            raise TwitcastingError(res.reason)

        token_info = res.json()
        token_info = self._add_expires_at_to_token_info(token_info)
        return token_info

    def _add_expires_at_to_token_info(self, token_info):
        """ 失効日時を追加する

        :param token_info: WebAPIから取得した認可情報
        :type token_info: dict
        :return: ``expires_at`` が追加された認可情報
        :rtype: dict
        """
        # トークンの失効日時
        token_info['expires_at'] = int(time.time()) + int(token_info['expires_in'])
        return token_info
