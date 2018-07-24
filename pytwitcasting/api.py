import json

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from pytwitcasting.error import TwitcastingException
from pytwitcasting.parsers import ModelParser
from pprint import pprint


API_BASE_URL = 'https://apiv2.twitcasting.tv'

STATUS_CODES_TO_RETRY = (500)


def _requests_retry_session(retries=3,
                            backoff_factor=0.3,
                            status_forcelist=(500, 502, 504),
                            session=None):
    """ リトライ用セッションの作成 """

    session = session or requests.Session()
    # リトライオブジェクトの作成。max_retriesに渡すため
    retry = Retry(total=retries,
                  read=retries,
                  connect=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)

    # urllib3の組み込みHTTPアダプタ
    adapter = HTTPAdapter(max_retries=retry)
    # https:// に接続アダプタを設定する
    session.mount('https://', adapter)
    return session


class API(object):
    """ APIにアクセスする """

    def __init__(self, access_token=None, requests_session=True, application_basis=None,
                 accept_encoding=False, requests_timeout=None):
        """
        :param access_token: アクセストークン
        :type  access_token: str
        :param requsts_session: セッションオブジェクト or セッションを使うかどうか
        :type  requsts_session: :class:`requests.Session <requests.Session>` or bool
        :param application_basis: (optional) TwitcastiongApplicationBasisオブジェクト
        :type  application_basis: :class:`TwitcastingApplicationBasis <pytwitcasting.auth.TwitcastingApplicationBasis>`
        :param accept_encoding: (optional) レスポンスサイズが一定以上だった場合に圧縮するか
        :type  accept_encoding: bool
        :param requests_timeout: (optional)タイムアウト時間
        :type  requests_timeout: int or float
        """
        self._access_token = access_token
        self.application_basis = application_basis
        self.accept_encoding = accept_encoding
        self.requests_timeout = requests_timeout

        if isinstance(requests_session, requests.Session):
            # Sessionオブジェクトが渡されていたら、それを使う
            session = requests_session
        else:
            if requests_session is True:
                # 新しくセッションを作る
                session = requests.Session()
            else:
                # リクエストのたびに毎回セッションを生成し、閉じる(実質セッションを使っていない)
                from requests import api
                session = api

        # リトライ用セッションの作成
        self._session = _requests_retry_session(session=session)

    def _auth_headers(self):
        """ 認可情報がついたヘッダー情報を返す

        :return: 認可情報がついたヘッダー
        """
        if self._access_token:
            return {'Authorization': f'Bearer {self._access_token}'}
        elif self.application_basis:
            return self.application_basis.get_basic_headers()
        else:
            return {}

    def _internal_call(self, method, url, payload, json_data, params):
        """ リクエストの送信

        :param method: リクエストの種類
        :param url: 送信先
        :param payload: POSTリクエストの送信データ
        :param json_data: POSTリクエストのJSONで送りたいデータ
        :param params: クエリ文字列の辞書
        :return: 呼び出したAPIの結果
        """
        if not url.startswith('http'):
            url = API_BASE_URL + url

        args = dict(params=params)
        args['timeout'] = self.requests_timeout
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

        # リトライ処理を行ってくれる
        r = self._session.request(method, url, headers=headers, **args)

        try:
            r.raise_for_status()
        except:
            # len(None)だとTypeErrorになる確認してから
            if r.text and r.text != 'null':
                err = r.json()['error']
                # エラー内容によってdetailsがあるときとない時があるため
                if 'details' in err:
                    details = f"\n {err['details']}"
                else:
                    details = ''
                raise TwitcastingException(r.status_code, err['code'], f"{r.url}:\n {err['message']}{details}")
            else:
                raise TwitcastingException(r.status_code, -1, f'{r.url}:\n error')
        finally:
            # 一応呼んでおく
            r.close()

        if r.text and r.text != 'null':
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
        """ GETリクエスト送信 """
        if args:
            kwargs.update(args)

        return self._internal_call('GET', url, payload, None, kwargs)

    def _post(self, url, args=None, payload=None, json_data=None, **kwargs):
        """ POSTリクエスト送信 """
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
        """ PUTリクエスト送信 """
        if args:
            kwargs.update(args)
        return self._internal_call('PUT', url, payload, None, kwargs)

    def get_user_info(self, user_id):
        """ Get User Info

        ユーザー情報を取得する

        必須パーミッション: Read

        :calls: `GET /users/:user_id <http://apiv2-doc.twitcasting.tv/#get-user-info>`_
        :param user_id: ユーザーのidかscreen_id
        :type user_id: str
        :return: :class:`User <pytwitcasting.models.User>`
        :rtype: :class:`User <pytwitcasting.models.User>`
        """
        res = self._get(f'/users/{user_id}')
        parser = ModelParser()
        return parser.parse(self, res['user'], parse_type='user', payload_list=False)

    def get_movie_info(self, movie_id):
        res = self._get(f'/movies/{movie_id}')
        parser = ModelParser()
        res['movie'] = parser.parse(self, payload=res['movie'], parse_type='movie', payload_list=False)
        res['broadcaster'] = parser.parse(self, payload=res['broadcaster'], parse_type='user', payload_list=False)
        return res

    def verify_credentials(self):
        """ Verify Credentials

        アクセストークンを検証し、ユーザ情報を取得する

        必須パーミッション: Read

        ※ Authorization Code GrantかImplicitでないと、エラーになる

        :calls: `GET /verify_credentials <http://apiv2-doc.twitcasting.tv/#verify-credentials>`_
        :return: - ``app`` : アクセストークンに紐づく :class:`App <pytwitcasting.models.App>`
                 - ``user`` : アクセストークンに紐づく :class:`User <pytwitcasting.models.User>`
        :rtype: dict
        """
        res = self._get('/verify_credentials')
        parser = ModelParser()
        res['app'] = parser.parse(self, payload=res['app'], parse_type='app', payload_list=False)
        res['user'] = parser.parse(self, payload=res['user'], parse_type='user', payload_list=False)
        return res

    def support_user(self, target_user_ids):
        """ Support User

        指定したユーザーのサポーターになる

        必須パーミッション: Write

        :calls: `PUT /support <http://apiv2-doc.twitcasting.tv/#support-user>`_
        :param target_user_ids: サポーターになるユーザのidかscreen_idのリスト。1度に20人まで可能
        :type target_user_ids: list[str]
        :return: サポーター登録を行った件数
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        res = self._put('/support', payload=data)
        return res['added_count'] if res else None

    def unsupport_user(self, target_user_ids):
        """ Unsupport User

        指定したユーザーのサポーターになる

        必須パーミッション: Write

        :calls: `PUT /unsupport <http://apiv2-doc.twitcasting.tv/#unsupport-user>`_
        :param target_user_ids: サポーターを解除するユーザのidかscreen_idのリスト。1度に20人まで可能
        :type target_user_ids: list[str]
        :return: サポーター解除を行った件数
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        res = self._put('/unsupport', payload=data)
        return res['removed_count'] if res else None

    def get_categories(self, lang='ja'):
        """ Get Categories

        配信中のライブがあるカテゴリのみを取得する

        必須パーミッション: Read

        :calls: `GET /categories <http://apiv2-doc.twitcasting.tv/#get-categories>`_
        :param lang: (optional) 検索対象の言語. ``ja`` or ``en``
        :type lang: str
        :return: :class:`Category <pytwitcasting.models.Category>` の配列
        :rtype: list[ :class:`Category <pytwitcasting.models.Category>` ]
        """
        res = self._get('/categories', lang=lang)
        parser = ModelParser()
        return parser.parse(self, res['categories'], parse_type='category', payload_list=True)

    def search_users(self, words, limit=10, lang='ja'):
        """ Search Users

        ユーザを検索する

        必須パーミッション: Read

        :calls: `GET /search/users <http://apiv2-doc.twitcasting.tv/#search-users>`_
        :param words: AND検索する単語のリスト
        :type words: list[str]
        :param limit: (optional) 取得件数. min: ``1`` , max: ``50``
        :type limit: int
        :param lang: (optional) 検索対象のユーザの言語設定. 現在は ``'ja'`` のみ。日本語で設定しているユーザのみ検索可能
        :type lang: str
        :return: :class:`User <pytwitcasting.models.User>` の配列
        :rtype: list[ :class:`User <pytwitcasting.models.User>` ]
        """
        if isinstance(words, list):
            w = ' '.join(words) if len(words) > 1 else words[0]
        else:
            w = words
        res = self._get('/search/users', words=w, limit=limit, lang=lang)
        parser = ModelParser()
        return parser.parse(self, payload=res['users'], parse_type='user', payload_list=True)

    def search_live_movies(self, search_type='new', context=None, limit=10, lang='ja'):
        """ Search Live Movies

        配信中のライブを検索する

        必須パーミッション: Read

        :calls: `GET /search/lives <http://apiv2-doc.twitcasting.tv/#search-live-movies>`_
        :param search_type: (optional) 検索種別。
                            指定できる値は ``tag`` or ``word`` or ``category`` or ``new`` or ``recommend``
        :type search_type: str
        :param context: (optional) 検索内容. ``search_type`` の値によって決まる。詳しくはUsageを見て
        :type context: list[str] or str or None
        :param limit: (optional) 取得件数. min: ``1`` , max: ``100``
        :type limit: int
        :param lang: (optional) 検索対象のユーザの言語設定. 現在は ``ja`` のみ
        :type lang: str
        :return: :class:`Movie <pytwitcasting.models.Movie>` の配列
        :rtype: list[ :class:`Movie <pytwitcasting.models.Movie>` ]

        Usage::

          # ex1) search_type='tag'.(context required)
          >>> movies = api.search_live_movies(search_type='tag', context=['人気', '雑談'])

          # ex2) search_type='word'.(context required)
          >>> movies = api.search_live_movies(search_type='word', context=['ツイキャス', 'ゲーム'])

          # ex3) search_type='category'.(context required).
          #      API.get_categories()で取得できるSubCategoryクラスの`id`を指定
          >>> movies = api.search_live_movies(search_type='category', context='hobby_game_boys_jp')

          # ex4) search_type='new'.(context none)
          >>> movies = api.search_live_movies(search_type='new')

          # ex4) search_type='recommend'.(context none)
          >>> movies = api.search_live_movies(search_type='recommend')
        """
        params = {'type': search_type, 'limit': limit, 'lang': lang}

        # search_typeによってcontentを設定
        if search_type and context:
            if search_type in ['tag', 'word']:
                # パラメータはurlencodeされるためエンコードされるし、
                # ' 'を'+'に変換してくれているから、空白で結合し、渡す
                if isinstance(context, list):
                    w = ' '.join(context) if len(context) > 1 else context[0]
                else:
                    w = context
                params['context'] = w

            elif search_type in ['category']:
                params['context'] = context

            elif search_type in ['new', 'recommend']:
                # 追加しない
                pass

        res = self._get('/search/lives', args=params)
        parser = ModelParser()

        for live_movie in res['movies']:
            live_movie['movie'] = parser.parse(self, payload=live_movie['movie'],
                                               parse_type='movie', payload_list=False)
            live_movie['broadcaster'] = parser.parse(self, payload=live_movie['broadcaster'],
                                                     parse_type='user', payload_list=False)

        return res

    def get_webhook_list(self, limit=50, offset=0, user_id=None):
        """ Get WebHook List

        アプリケーションに紐づく WebHook の一覧を取得する

        *アプリケーション単位でのみ実行可能(Basic)*

        必須パーミッション: any

        :calls: `GET /webhooks <http://apiv2-doc.twitcasting.tv/#get-webhook-list>`_
        :param limit: 取得件数. min: ``1`` , max: ``100``
        :type limit: int
        :param offset: 先頭からの位置. min: ``0``
        :type offset: int
        :param user_id: 対象のユーザのidかscreen_id。imitとoffsetはuser_idが ``None`` のときのみ指定できる
        :type user_id: str or None
        :return: - ``all_count`` : このアプリに登録済みWebHook件数
                 - ``webhooks`` : WebHookの配列
        :rtype: dict
        """
        params = {}
        if user_id:
            params['user_id'] = user_id
        else:
            params['limit'] = limit
            params['offset'] = offset

        res = self._get('/webhooks', args=params)
        parser = ModelParser()
        res['webhooks'] = parser.parse(self, payload=res['webhooks'], parse_type='webhook', payload_list=True)

        return res

    def register_webhook(self, user_id, events):
        """ Register WebHook

        WebHookを新規登録します。これを使うには、アプリケーションでWebHook URLの登録が必須。

        必須パーミッション: any

        :calls: `POST /webhooks <http://apiv2-doc.twitcasting.tv/#register-webhook>`_
        :param user_id: 対象のユーザのid
        :type user_id: str
        :param events: フックするイベント種別の配列。 ``livestart`` or ``liveend``
        :type events: list[str]
        :return: - ``user_id`` : 登録したユーザのid
                 - ``added_events`` : 登録したイベントの種類の配列
        :rtype: dict
        """
        data = {'user_id': user_id, 'events': events}
        # そのまま渡す
        return self._post('/webhooks', json_data=data)

    def remove_webhook(self, user_id, events):
        """ Remove WebHook

        WebHookを削除する

        必須パーミッション: any

        :calls: `DELETE /webhooks <http://apiv2-doc.twitcasting.tv/#remove-webhook>`_
        :param user_id: 対象のユーザのid
        :type user_id: str
        :param events: フックを削除するイベント種別の配列。 ``livestart`` or ``liveend``
        :type events: list[str]
        :return: - ``user_id`` : 登録したユーザのid
                 - ``removed_events`` : 削除されたイベントの種類の配列
        :rtype: dict
        """
        params = {'user_id': user_id, 'events[]': events}
        return self._del('/webhooks', args=params)

    def get_rtmp_url(self):
        """ Get RTMP Url

        アクセストークンに紐づくユーザの配信用のURL(RTMP)を取得する

        必須パーミッション: *Broadcast*

        :calls: `GET /rtmp_url <http://apiv2-doc.twitcasting.tv/#get-rtmp-url>`_
        :return: - ``enabled`` : RTMP配信が有効かどうか
                 - ``url`` : RTMP配信用URL
                 - ``stream_key`` : RTMP配信用キー
        :rtype: dict
        """
        return self._get('/rtmp_url')

    def get_webm_url(self):
        """ Get WebM Url

        アクセストークンに紐づくユーザの配信用のURL (WebM, WebSocket)を取得する

        必須パーミッション: *Broadcast*

        :calls: `GET /webm_url <http://apiv2-doc.twitcasting.tv/#get-webm-url>`_
        :return: - ``enabled`` : WebM配信が有効かどうか
                 - ``url`` : WebM配信用URL
        """
        # (WebMってなに！？)
        return self._get('/webm_url')

    def _get_live_thumbnail_image(self, user_id, size='small', position='latest'):
        return self._get(f'/users/{user_id}/live/thumbnail', size=size, position=position)

    def _get_movies_by_user(self, user_id, offset=0, limit=20):
        res = self._get(f'/users/{user_id}/movies', offset=offset, limit=limit)
        # 配列からMovieクラスの配列を作る
        parser = ModelParser()
        res['movies'] = parser.parse(self, res['movies'], parse_type='movie', payload_list=True)

        return res

    def _get_current_live(self, user_id):
        # TODO: ライブ中ではない場合、エラーを返すでよいのか
        res = self._get(f'/users/{user_id}/current_live')
        parser = ModelParser()
        res['movie'] = parser.parse(self, res['movie'], parse_type='movie', payload_list=False)
        res['broadcaster'] = parser.parse(self, res['broadcaster'], parse_type='user', payload_list=False)
        return res

    def _get_comments(self, movie_id, offset=0, limit=10, slice_id=None):
        params = {'offset': offset, 'limit': limit}

        if slice_id:
            params['slice_id'] = slice_id

        res = self._get(f'/movies/{movie_id}/comments', args=params)
        parser = ModelParser()
        res['comments'] = parser.parse(self, res['comments'], parse_type='comment', payload_list=True)

        return res

    def _post_comment(self, movie_id, comment, sns='none'):
        data = {'comment': comment, 'sns': sns}
        res = self._post(f'/movies/{movie_id}/comments', payload=data)
        parser = ModelParser()
        res['comment'] = parser.parse(self, res['comment'], parse_type='comment', payload_list=False)
        return res

    def _delete_comment(self, movie_id, comment_id):
        res = self._del(f'/movies/{movie_id}/comments/{comment_id}')
        return res['comment_id']

    def _get_supporting_status(self, user_id, target_user_id):
        res = self._get(f'/users/{user_id}/supporting_status', target_user_id=target_user_id)
        parser = ModelParser()
        res['target_user'] = parser.parse(self, res['target_user'], parse_type='user', payload_list=False)
        return res

    def _get_supporting_list(self, user_id, offset=0, limit=20):
        res = self._get(f'/users/{user_id}/supporting', offset=offset, limit=limit)
        parser = ModelParser()
        res['supporting'] = parser.parse(self, res['supporting'], parse_type='user', payload_list=True)
        return res

    def _get_supporter_list(self, user_id, offset=0, limit=20, sort='ranking'):
        res = self._get(f'/users/{user_id}/supporters', offset=offset, limit=limit, sort=sort)
        parser = ModelParser()
        res['supporters'] = parser.parse(self, res['supporters'], parse_type='user', payload_list=True)
        return res
