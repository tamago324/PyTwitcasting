import base64
import json
import urllib.parse
import time

import requests


OAUTH_BASE_URL = 'https://apiv2.twitcasting.tv/oauth2/authorize'
OAUTH_TOKEN_URL = 'https://apiv2.twitcasting.tv/oauth2/access_token'
API_BASE_URL = 'https://apiv2.twitcasting.tv'
 
class TwitcastingError(Exception):
    pass


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

            Return:
                認可情報がついたヘッダー
        """
        if self._auth:
            return {'Authorization': f'Bearer {self._auth}'}
        elif self.application_basis:
            return self.application_basis.get_basic_headers()
        else:
            return {}

    def _internal_call(self, method, url, payload, json_data, params):
        """
            リクエストの送信

            Parameters:
                - method - リクエストの種類
                - url - 送信先
                - payload - POSTリクエストの送信データ
                - json_data - POSTリクエストのJSONで送りたいデータ
                - params - クエリ文字列の辞書

            Return:
                呼び出したAPIの結果
        """
        if not url.startswith('http'):
            url = API_BASE_URL + url

        args = dict(params=params)
        if payload:
            args['data'] = json.dumps(payload)
        if json_data:
            args['json'] = json_data

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

        # TODO:200以外のときはどうする？

        if r.text and len(r.text) > 0 and r.text != 'null':
            if r.headers['Content-Type'] in ['image/jpeg', 'image/png']:
                # 拡張子の取得
                file_ext = r.headers['Content-Type'].replace('image/', '')
                ret = {'bytes_data': r.content,
                       'file_ext': file_ext}
                return ret
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

        return self._internal_call('GET', url, payload, None, kwargs)

    def _post(self, url, args=None, payload=None, json_data=None, **kwargs):
        """
            POSTリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('POST', url, payload, json_data, kwargs)

    def _del(self, url, args=None, payload=None, **kwargs):
        """
            DELETEリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('DELETE', url, payload, None, kwargs)

    def _put(self, url, args=None, payload=None, **kwargs):
        """
            PUTリクエスト送信
        """
        if args:
            kwargs.update(args)
        return self._internal_call('PUT', url, payload, None, kwargs)

    def get_user_info(self, user_id):
        """
            Get User Info
            ユーザー情報を取得する
            必須パーミッション: Read

            Parameters:
                - user_id - ユーザーのidかscreen_id

            Return:
                - dict - {'user': Userオブジェクト}
        """
        return self._get(f'/users/{user_id}')

    def verify_credentials(self):
        """
            Verify Credentials
            アクセストークンを検証し、ユーザ情報を取得する
            必須パーミッション: Read

            ※ Authorization Code GrantかImplicitでないと、エラーになる

            Return:
                - dict - {'app': アクセストークンに紐づくAppオブジェクト,
                          'user': アクセストークンに紐づくUserオブジェクト}
        """
        return self._get('/verify_credentials')

    def get_live_thumbnail_image(self, user_id, size='small', position='latest'):
        """
            Get Live Thumbnail Image
            配信中のライブのサムネイル画像を取得する。
            必須パーミッション: Read

            Parameters:
                - user_id - ユーザーのidかscreen_id
                - size - 画像サイズ. 'small' or 'large'
                - position - ライブ開始時点か最新か. 'beginning' or 'latest'

            Return:
                - dict - {'bytes_data': サムネイルの画像データ(bytes),
                          'file_ext': ファイル拡張子('jepg' or 'png')}
        """
        return self._get(f'/users/{user_id}/live/thumbnail', size=size, position=position)

    def get_movie_info(self, movie_id):
        """
            Get Movie Info
            ライブ（録画）情報を取得する
            必須パーミッション: Read

            Parameters:
                - movie_id - ライブID

            Return:
                - dict - {'movie': Movieオブジェクト,
                          'broadcaster': 配信者のUserオブジェクト,
                          'tags': 設定されているタグの配列}
        """
        return self._get(f'/movies/{movie_id}')

    def get_movies_by_user(self, user_id, offset=0, limit=20):
        """
            Get Movies by User
            ユーザーが保有する過去ライブ（録画）の一覧を作成日時の降順で取得する
            必須パーミッション: Read

            Parameters:
                - user_id - ユーザーのidかscreen_id
                - offset - 先頭からの位置. min:0
                - limit - 最大取得件数. min:1, max:50

            Return:
                - dict - {'total_count': offset,limitの条件での総件数,
                          'movies': Movieオブジェクトの配列}
        """
        return self._get(f'/users/{user_id}/movies', offset=offset, limit=limit)

    def get_current_live(self, user_id):
        """
            Get Current Live
            ユーザーが配信中の場合、ライブ情報を取得する
            必須パーミッション: Read

            Parameters:
                - user_id - ユーザーのidかscreen_id

            Return:
                - dict - {'movie': Movieオブジェクト,
                          'broadcaster': 配信者のUserオブジェクト,
                          'tags': 設定されているタグの配列}
        """
        # TODO: ライブ中ではない場合、エラーを返すでよいのか
        return self._get(f'/users/{user_id}/current_live')

    def get_comments(self, movie_id, offset=0, limit=10, slice_id=None):
        """
            Get Comments
            コメントを作成日時の降順で取得する
            必須パーミッション: Read

            Parameters:
                - movie_id - ライブID
                - offset - 先頭からの位置. min:0
                - limit - 取得件数. min:1, max:50
                - slice_id - このコメントID以降のコメントを取得する

            Return:
                - dict - {'movie_id': ライブID,
                          'all_count': 総コメント数,
                          'comments': Commentオブジェクトの配列}
        """
        params = {'offset': offset, 'limit': limit}

        if slice_id is not None:
            params['slice_id'] = slice_id
        return self._get(f'/movies/{movie_id}/comments', args=params)

    def post_comment(self, movie_id, comment, sns='none'):
        """
            Post Comment
            コメントを投稿する。 ユーザ単位でのみ実行可能
            必須パーミッション: Write

            Parameters:
                - movie_id - ライブID
                - comment - 投稿するコメント
                - sns - SNSへの同時投稿. 'none' or 'normal' or 'reply'
                        none: SNSへ投稿しない
                        normal: 投稿する
                        reply: 配信者への返信として投稿する

            Return:
                - dict - {'movie_id': ライブID,
                          'all_count': 総コメント数,
                          'comment': Commentオブジェクト}
        """
        data = {'comment': comment, 'sns': sns}
        return self._post(f'/movies/{movie_id}/comments', payload=data)

    def delete_comment(self, movie_id, comment_id):
        """
            Delete Comment
            コメントを削除する。ユーザ単位でのみ実行可能
            コメント投稿者か、ライブ配信者に紐づくアクセストークンであれば削除可能
            必須パーミッション: Write

            Parameters:
                - movie_id - ライブID
                - comment_id - 投稿するコメント

            Return:
                - dict - {'comment_id': 削除したコメントID}
        """
        return self._del(f'/movies/{movie_id}/comments/{comment_id}')

    def get_supporting_status(self, user_id, target_user_id):
        """
            Get Supporting Status
            ユーザーが、ある別のユーザのサポーターであるかの状態を取得する
            必須パーミッション: Read
            
            Parameters:
                - user_id - ユーザのidかscreen_id
                - target_user_id - 状態を取得する対象のユーザのidかscreen_id

            Return:
                - dict - {'is_supporting': サポーターかどうか,
                          'target_user': 対象ユーザのUserオブジェクト}
        """
        return self._get(f'/users/{user_id}/supporting_status', target_user_id=target_user_id)

    def support_user(self, target_user_ids):
        """
            Support User
            指定したユーザーのサポーターになる
            必須パーミッション: Write
            
            Parameters:
                - target_user_ids - サポーターになるユーザのidかscreen_idのリスト
                                    1度に20人まで可能

            Return:
                - dict - {'added_count': サポーター登録を行った件数}
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        return self._put('/support', payload=data)

    def unsupport_user(self, target_user_ids):
        """
            Unsupport User
            指定したユーザーのサポーターになる
            必須パーミッション: Write
            
            Parameters:
                - target_user_ids - サポーターを解除するユーザのidかscreen_idのリスト
                                    1度に20人まで可能

            Return:
                - dict - {'removed_count': サポーター解除を行った件数}
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        return self._put('/unsupport', payload=data)

    def supporting_list(self, user_id, offset=0, limit=20):
        """
            Supporting List
            指定したユーザがサポート`している`ユーザの一覧を取得する
            必須パーミッション: Read
            
            Parameters:
                - user_id - ユーザのidかscreen_id
                - offset - 先頭からの位置. min:0
                - limit - 最大取得件数. min:1, max:20

            Return:
                - dict - {'total': 全レコード数,
                          'supporting': Supportingオブジェクトの配列}
        """
        return self._get(f'/users/{user_id}/supporting', offset=offset, limit=limit)

    def supporter_list(self, user_id, offset=0, limit=20, sort='ranking'):
        """
            Supporting List
            指定したユーザがサポート`している`ユーザの一覧を取得する
            必須パーミッション: Read
            
            Parameters:
                - user_id - ユーザのidかscreen_id
                - offset - 先頭からの位置. min:0
                - limit - 最大取得件数. min:1, max:20
                - sort - 並び順. 'ranking'(貢献度順) or 'new'(新着順)

            Return:
                - dict - {'total': 全レコード数,
                          'supporting': Supportingオブジェクトの配列}
        """
        return self._get(f'/users/{user_id}/supporters', offset=offset, limit=limit, sort=sort)

    def get_categories(self, lang='ja'):
        """
            Get Categories
            配信中のライブがあるカテゴリのみを取得する
            必須パーミッション: Read
            
            Parameters:
                - lang - 検索対象の言語. 'ja' or 'en'

            Return:
                - dict - {'categories': Categoryオブジェクトの配列}
        """
        return self._get('/categories', lang=lang)

    def serach_users(self, words, limit=10, lang='ja'):
        """
            Search Users
            ユーザを検索する
            必須パーミッション: Read
            
            Parameters:
                - words - AND検索する単語のリスト
                - limit - 取得件数. min:1, max:50
                - lang - 検索対象のユーザの言語設定. 現在は'ja'のみ
                         日本語で設定しているユーザのみ検索可能

            Return:
                - dict - {'users': Userオブジェクトの配列}
        """
        # これじゃだめっぽい...
        # ブラウザと一緒の結果にはならないの！？
        w = ' '.join(words) if len(words) > 1 else words[0]
        return self._get('/search/users', words=urllib.parse.quote(w), limit=limit, lang=lang)

    def search_live_movies(self, search_type='tag', content=None, limit=10, lang='ja'):
        """
            Search Live Movies
            配信中のライブを検索する
            必須パーミッション: Read
            
            Parameters:
                - search_type - 検索種別. 
                                 'tag' or 'word' or 'category' or 
                                 'new'(新着) or 'recommend'(おすすめ)
                - content - 検索内容.search_typeの値によって決まる(required: type=tag, word, category)
                             search_type='tag' or 'word': AND検索する単語のリスト
                             search_type='category': サブカテゴリID
                             search_type='new' or 'recommend': None(不要)
                - limit - 取得件数. min:1, max:100
                - lang - 検索対象のユーザの言語設定. 現在は'ja'のみ

            Return:
                - dict - {'movies': Movieオブジェクトの配列}
                         `/movies/:movie_id`と同じ結果
        """
        params = {'type': search_type, 'limit': limit, 'lang': lang}

        # search_typeによってcontentを設定
        if search_type and content:
            if search_type in ['tag', 'word']:
                # TODO: これだとWebとおなじ結果にはならない
                w = ' '.join(content) if len(content) > 1 else content[0]
                params['content'] = urllib.parse.quote(w)
            elif search_type in ['category']:
                params['content'] = content
            elif search_type in ['new', 'recommend']:
                # 追加しない
                pass

        return self._get('/search/lives', args=params)

    def get_webhook_list(self, limit=50, offset=0, user_id=None):
        """
            Get WebHook List
            アプリケーションに紐づく WebHook の一覧を取得する
            *******************************************
            *アプリケーション単位でのみ実行可能(Basic)*
            *******************************************
            必須パーミッション: any
            
            Parameters:
                - limit - 取得件数. min:1, max:100
                - offset - 先頭からの位置. min:0
                - user_id - 対象のユーザのidかscreen_id

                limitとoffsetはuser_idがNoneのときのみ指定できる

            Return:
                - dict - {'all_count': 登録済みWebHook件数,
                          'webhooks': WebHookオブジェクトの配列}
        """
        params = {}
        if user_id:
            params['user_id'] = user_id
        else:
            params['limit'] = limit
            params['offset'] = offset
        return self._get('/webhooks', args=params)

    def register_webhook(self, user_id, events):
        """
            Register WebHook
            WebHookを新規登録します
            これを使うには、アプリケーションでWebHook URLの登録が必須
            必須パーミッション: any
            
            Parameters:
                - user_id - 対象のユーザのidかscreen_id
                - events - フックするイベント種別の配列
                            'livestart', 'liveend'

            Return:
                - dict - {'user_id': 登録したユーザのid,
                          'added_events': 登録したイベントの種類の配列}
        """
        data = {'user_id': user_id, 'events': events}
        # そのまま渡す
        return self._post('/webhooks', json_data=data)

    def remove_webhook(self, user_id, events):
        """
            Remove WebHook
            WebHookを削除する
            必須パーミッション: any
            
            Parameters:
                - user_id - 対象のユーザのidかscreen_id
                - events - フックを削除するイベント種別の配列
                            'livestart', 'liveend'

            Return:
                - dict - {'user_id': 登録したユーザのid,
                          'removed_events': 削除されたイベントの種類の配列}
        """
        params = {'user_id': user_id, 'events[]': events}
        return self._del('/webhooks', args=params)
    
    def get_rtmp_url(self):
        """
            Get RTMP Url
            アクセストークンに紐づくユーザの配信用のURL(RTMP)を取得する
            *******************************
            *必須パーミッション: Broadcast*
            *******************************

            Return:
                - dict - {'enabled': RTMP配信が有効かどうか,
                          'url': RTMP配信用URL,
                          'stream_key': RTMP配信用キー}
        """
        return self._get('/rtmp_url')

    def get_webm_url(self):
        """
            Get WebM Url
            アクセストークンに紐づくユーザの配信用のURL (WebM, WebSocket)を取得する
            *******************************
            *必須パーミッション: Broadcast*
            *******************************

            Return:
                - dict - {'enabled': WebM配信が有効かどうか,
                          'url': WebM配信用URL}
        """
        # (WebMってなに！？)
        return self._get('/webm_url')
























