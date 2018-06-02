# urllib.parse.pares_qs()を使えるようにするため、urllib.parseでインポートする
import urllib.parse
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

    def parse_response_auth_info(self, url):
        """
        認可後にリダイレクトしたURLから認可情報を解析し取り出す
        """
        try:
            # URLから認可情報を取り出す
            # urllib.parse.parse_qs()を使う
            auth_dic = urllib.parse.parse_qs(url.split('#')[1])
            auth_info = {}
            for k, v in auth_dic.items():
                auth_info[k] = v[0]
            return auth_info
        except IndexError:
            return None
