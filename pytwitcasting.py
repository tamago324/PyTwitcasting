# urllib.parse.pares_qs()を使えるようにするため、urllib.parseでインポートする
import urllib.parse
import time

import requests


OAUTH_BASE_URL = 'https://apiv2.twitcasting.tv/oauth2/authorize'

class TwitcastingImplicit(object):
    """
    Implicitでの認可フロー
    http://apiv2-doc.twitcasting.tv/#implicit
    """

    def __init__(self, client_id, state=None):
        """
        Parameters:
             = client_id - このアプリのclient id
             - state - このアプリのCSRFトークン
        """
        self.client_id = client_id
        self.state = state

    def get_authorize_url(self, state=None):
        """
        認可のためのURLを取得
        """

        payload = {'client_id': self.client_id,
                   'response_type': 'token'}

        if state is None:
            state = self.state
        if state is not None:
            payload['state'] = state

        urlparams = urllib.parse.urlencode(payload)

        return f'{OAUTH_BASE_URL}?{urlparams}'

    def parse_response_url(self, url):
        """
        認可後にリダイレクトしたURLから認可情報を解析し取り出す
        """
        try:
            # URLから認可情報を取り出す
            # urllib.parse.parse_qs()を使う
            token_info = urllib.parse.parse_qs(url.split('#')[1])
            for k, v in token_info.items():
                # リストの１つ目を取り出して設定
                item = v[0]
                token_info[k] = item

            token_info = self._add_custom_values_to_token_info(token_info)
            return token_info
        except IndexError:
            return None

    def _add_custom_values_to_token_info(self, token_info):
        """ 
        WebAPIでは取得できない値を追加する
        """
        # トークンの失効日時
        token_info['expires_at'] = int(time.time()) + int(token_info['expires_in'])
        return token_info
