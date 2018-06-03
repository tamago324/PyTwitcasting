import base64
import json
import urllib.parse
import time

import requests


OAUTH_BASE_URL = 'https://apiv2.twitcasting.tv/oauth2/authorize'
API_BASE_URL = 'https://apiv2.twitcasting.tv'
 
# TODO: 認可でのExceptionクラス必要であれば

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

    def get_access_token(self, url):
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

class TwitCastingApplicationBasis(object):
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


class TwitcastingException(Exception):
    def __init__(self, http_status, code, msg):
        self.http_status = http_status
        self.code = code
        self.msg = msg

    def __str__(self):
        return f'http status: {self.http_status}, code: {self.code} {self.msg}'


class Twitcasting(object):

    def __init__(self, auth=None, requests_session=True, application_basis=None, accept_encoding=False):
        """
            Parameters:
                - auth - アクセストークン
                - requsts_session - セッションオブジェクト or セッションを使うかどうか
                - TwitcastiongApplicationBasis - (option)
                    TwitcastiongApplicationBasisオブジェクト
                    (アプリケーション単位のアクセスオブジェクト)
                - accept_encodeing - (option) レスポンスサイズが一定以上だった場合に圧縮するか
        """
        self._auth = auth
        self.application_basis = application_basis
        self.accept_encoding = accept_encoding
        
        if isinstance(requests_session, requests.Session):
            # セッションを渡されたら、それを使う
            self._session = session
        else:
            if requests_session:
                # 新しくセッションを作る
                self._session = requests.Session()
            else:
                # リクエストのたびに毎回セッションを生成し、閉じる(実質セッションを使っていない)
                from requests import api
                self._session = api

    def _auth_headers(self):
        """
            認可情報がついたヘッダー情報を返す
        """
        if self._auth:
            return {'Authorization': f'Bearer {self._auth}'}
        elif self.application_basis:
            return self.application_basis.get_basic_headers()
        else:
            return {}

    def _internal_call(self, method, url, payload, params):
        """
            リクエストの送信

            Parameters:
                - method - リクエストの種類
                - url - 送信先
                - payload - POSTリクエストの送信データ
                - params - クエリ文字列の辞書
        """
        if not url.startswith('http'):
            url = API_BASE_URL + url

        args = dict(params=params)
        if payload:
            args['data'] = json.dumps(payload)

        # TODO: timeoutはどうするか

        headers = self._auth_headers()
        headers['X-Api-Version'] = '2.0'
        headers['Accept'] = 'application/json'
        if self.accept_encoding:
            headers['Accept-Encoding'] = 'gzip'

        r = self._session.request(method, url, headers=headers, **args)

        try:
            r.raise_for_status()
        except:
            # len(None)だとTypeErrorになる確認してから
            if r.text and len(r.text) > 0 and r.text != 'null':
                err = r.json()['error']
                # エラー内容によってdetailsがあるときとない時があるため
                if 'details' in err:
                    details = f"\n {err['details']}"
                else:
                    details = ''
                raise TwitcastingException(r.status_code, err['code'], f"{r.url}:\n {err['message']}{details}")
            else:
                raise TwitcastingException(r.status_code, -1, f'r.url:\n error')
        finally:
            # 一応呼んでおく
            r.close()

        if r.text and len(r.text) > 0 and r.text != 'null':
            if r.headers['Content-Type'] in ['image/jpeg', 'image/png']:
                # get_live_thumbnail_imageのとき
                return r.content
            else:
                return r.json()
        else:
            return None

    def _get(self, url, args=None, payload=None, **kwargs):
        """
            GETリクエスト送信
        """
        if args:
            kwargs.update(args)

        # TODO:リトライ処理を入れるべき

        return self._internal_call('GET', url, payload, kwargs)

    def _post(self, url, args=None, payload=None, **kwargs):
        """
            POSTリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('POST', url, payload, kwargs)

    def _del(self, url, args=None, payload=None, **kwargs):
        """
            DELETEリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('DELETE', url, payload, kwargs)

    def _put(self, url, args=None, payload=None, **kwargs):
        """
            PUTリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('PUT', url, payload, kwargs)

    def get_user_info(self, user_id):
        """
            Get User Info
            ユーザー情報を取得する

            Parameters:
                - user_id - ユーザーのidかscreen_id
        """
        return self._get(f'/users/{user_id}')

    def verify_credentials(self):
        """
            Verify Credentials
            アクセストークンを検証し、ユーザ情報を取得する
            ※ Authorization Code GrantかImplicitでないと、エラーになる
        """
        return self._get(f'/verify_credentials')

    def get_live_thumbnail_image(self, user_id, size='small', position='latest'):
        """
            Get Live Thumbnail Image
            配信中のライブのサムネイル画像を取得する。

            Parameters:
                - user_id - ユーザーのidかscreen_id
                - size - 画像サイズ. 'small' or 'large'
                - position - ライブ開始時点か最新か. 'beginning' or 'latest'
        """
        return self._get(f'/users/{user_id}/live/thumbnail', size=size, position=position)

    def get_movie_info(self, movie_id):
        """
            Get Movie Info
            ライブ（録画）情報を取得する

            Parameters:
                - movie_id - ライブID
        """
        return self._get(f'/movies/{movie_id}')

    def get_movies_by_user(self, user_id, offset=0, limit=20):
        """
            Get Movies by User
            ユーザーが保有する過去ライブ（録画）の一覧を作成日時の降順で取得する

            Parameters:
                - user_id - ユーザーのidかscreen_id
                - offset - 先頭からの位置. min:0
                - limit - 最大取得件数. min:1, max:50
        """
        return self._get(f'/users/{user_id}/movies', offset=offset, limit=limit)


































