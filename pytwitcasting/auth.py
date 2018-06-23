import base64
import urllib.parse
import time

import requests


OAUTH_TOKEN_URL = 'https://apiv2.twitcasting.tv/oauth2/access_token'
OAUTH_BASE_URL = 'https://apiv2.twitcasting.tv/oauth2/authorize'


class TwitcastingImplicit(object):
    """
    Implicitでの認可フロー
    http://apiv2-doc.twitcasting.tv/#implicit
    """

    def __init__(self, client_id, state=None):
        """
        Parameters:
             - client_id - このアプリのclient id
             - state - このアプリのCSRFトークン
        """
        self.client_id = client_id
        self.state = state

    def get_authorize_url(self, state=None):
        """
            認可のためのURLを取得

            Parameters:
                - state - CSRFトークン

            Return:
                認可するためのURL
        """

        payload = {'client_id': self.client_id,
                   'response_type': 'token'}

        if state is None:
            state = self.state
        if state is not None:
            payload['state'] = state

        urlparams = urllib.parse.urlencode(payload)

        return f'{OAUTH_BASE_URL}?{urlparams}'

    def get_access_token(self, url):
        """
            認可後にリダイレクトしたURLから認可情報を解析し取り出す

            Parameters:
                - url - リダイレクトされたURL

            Return:
                トークンの情報
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

            token_info = self._add_custom_values_to_token_info(token_info)
            return token_info
        except IndexError:
            return None

    def _add_custom_values_to_token_info(self, token_info):
        """ 
            WebAPIでは取得できない値を追加する

            Parameters:
                - token_info - WebAPIから取得した認可情報

            Return:
                情報が追加されたtoken_info
        """
        # トークンの失効日時
        token_info['expires_at'] = int(time.time()) + int(token_info['expires_in'])
        return token_info

class TwitcastingApplicationBasis(object):
    """
        アプリケーション単位でのアクセス
        http://apiv2-doc.twitcasting.tv/#access-token
        なんかこれ微妙なクラスな気がする...
    """
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_basic_headers(self):
        enc = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode('utf-8')
        return {'Authorization': f'Basic {enc}'}

class TwitcastingOauth(object):
    """
        Authorization Code Grantの認可フロー
        http://apiv2-doc.twitcasting.tv/#authorization-code-grant
    """

    def __init__(self, client_id, client_secret, redirect_uri, state=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state

    def get_authorize_url(self, state=None):
        """
            認可のためのURLを取得

            Parameters:
                - state - CSRFトークン

            Return:
                認可するためのURL
        """
        payload = {'client_id': self.client_id,
                   'response_type': 'code'}

        if state is None:
            state = self.state
        if state is not None:
            payload['state'] = state

        urlparams = urllib.parse.urlencode(payload)

        return f'{OAUTH_BASE_URL}?{urlparams}'

    def parse_response_code(self, url):
        """
            認可後にリダイレクトしたURLから認可情報を解析し取り出す

            Parameters:
                - url - リダイレクトされたURL

            Return:
                アクセストークン取得コード
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
        """
            コードを使って、アクセストークンを取得する

            Parameters:
                - code - 取得したコード

            Return:
                認可情報
        """
        payload = {'code': code, 
                   'grant_type': 'authorization_code',
                   'client_id': self.client_id,
                   'client_secret': self.client_secret,
                   'redirect_uri': self.redirect_uri}

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # TODO: proxiesがなんなのかわかんない...
        res = requests.post(OAUTH_TOKEN_URL, data=payload, headers=headers)

        if res.status_code != 200:
            raise TwitcastingError(res.reason)

        token_info = res.json()
        token_info = self._add_custom_values_to_token_info(token_info)
        return token_info

    def _add_custom_values_to_token_info(self, token_info):
        """ 
            WebAPIでは取得できない値を追加する

            Parameters:
                - token_info - WebAPIから取得した認可情報

            Return:
                情報が追加されたtoken_info
        """
        # トークンの失効日時
        token_info['expires_at'] = int(time.time()) + int(token_info['expires_in'])
        return token_info
