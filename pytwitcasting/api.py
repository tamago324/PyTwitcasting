import json

import requests

from pytwitcasting.error import TwitcastingException
from pytwitcasting.parsers import ModelParser
from pprint import pprint


API_BASE_URL = 'https://apiv2.twitcasting.tv'


class API(object):

    def __init__(self, auth=None, requests_session=True, application_basis=None,
                 accept_encoding=False, requests_timeout=None):
        """
            Parameters:
                - auth - アクセストークン
                - requsts_session - セッションオブジェクト or セッションを使うかどうか
                - TwitcastiongApplicationBasis - (option)
                    TwitcastiongApplicationBasisオブジェクト
                    (アプリケーション単位のアクセスオブジェクト)
                - accept_encodeing - (option) レスポンスサイズが一定以上だった場合に圧縮するか
                - requests_timeout - タイムアウト時間
        """
        self._auth = auth
        self.application_basis = application_basis
        self.accept_encoding = accept_encoding
        self.requests_timeout = requests_timeout

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
                raise TwitcastingException(r.status_code, -1, f'{r.url}:\n error')
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
                # retはどうするの
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
                Userオブジェクト
        """
        res = self._get(f'/users/{user_id}')
        parser = ModelParser()
        return parser.parse(self, res['user'], parse_type='user', payload_list=False)

    def verify_credentials(self):
        """
            Verify Credentials
            アクセストークンを検証し、ユーザ情報を取得する
            必須パーミッション: Read

            ※ Authorization Code GrantかImplicitでないと、エラーになる

            Return:
                - dict - {'app': アクセストークンに紐づくApp,
                          'user': アクセストークンに紐づくUser}
        """
        res = self._get('/verify_credentials')
        parser = ModelParser()
        res['app'] = parser.parse(self, payload=res['app'], parse_type='app', payload_list=False)
        res['user'] = parser.parse(self, payload=res['user'], parse_type='user', payload_list=False)
        return res

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
                - dict - {'movie': Movie,
                          'broadcaster': 配信者のUser,
                          'tags': 設定されているタグの配列}
        """
        res = self._get(f'/movies/{movie_id}')
        parser = ModelParser()
        res['movie'] = parser.parse(self, payload=res['movie'], parse_type='movie', payload_list=False)
        res['broadcaster'] = parser.parse(self, payload=res['broadcaster'], parse_type='user', payload_list=False)
        return res

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
                          'movies': Movieの配列}
        """
        res = self._get(f'/users/{user_id}/movies', offset=offset, limit=limit)
        # 配列からMovieクラスの配列を作る
        parser = ModelParser()
        res['movies'] = parser.parse(self, res['movies'], parse_type='movie', payload_list=True)

        return res

    def get_current_live(self, user_id):
        """
            Get Current Live
            ユーザーが配信中の場合、ライブ情報を取得する
            必須パーミッション: Read

            Parameters:
                - user_id - ユーザーのidかscreen_id

            Return:
                - dict - {'movie': Movieオブジェクト,
                          'user': 配信者のUser,
                          'tags': 設定されているタグの配列}
        """
        # TODO: ライブ中ではない場合、エラーを返すでよいのか
        res = self._get(f'/users/{user_id}/current_live')
        parser = ModelParser()
        res['movie'] = parser.parse(self, res['movie'], parse_type='movie', payload_list=False)
        res['user'] = parser.parse(self, res['broadcaster'], parse_type='user', payload_list=False)
        del res['broadcaster']
        return res

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
                          'comments': Commentの配列}
        """
        params = {'offset': offset, 'limit': limit}

        if slice_id:
            params['slice_id'] = slice_id

        res = self._get(f'/movies/{movie_id}/comments', args=params)
        parser = ModelParser()
        res['comments'] = parser.parse(self, res['comments'], parse_type='comment', payload_list=True)

        return res

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
                          'comment': 投稿したComment}
        """
        data = {'comment': comment, 'sns': sns}
        res = self._post(f'/movies/{movie_id}/comments', payload=data)
        parser = ModelParser()
        res['comment'] = parser.parse(self, res['comment'], parse_type='comment', payload_list=False)
        return res

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
                - 削除したコメントID
        """
        res = self._del(f'/movies/{movie_id}/comments/{comment_id}')
        return res['comment_id']

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
                          'user': 対象ユーザのUser}
        """
        res = self._get(f'/users/{user_id}/supporting_status', target_user_id=target_user_id)
        parser = ModelParser()
        res['user'] = parser.parse(self, res['target_user'], parse_type='user', payload_list=False)
        del res['target_user']
        return res

    def support_user(self, target_user_ids):
        """
            Support User
            指定したユーザーのサポーターになる
            必須パーミッション: Write

            Parameters:
                - target_user_ids - サポーターになるユーザのidかscreen_idのリスト
                                    1度に20人まで可能

            Return:
                サポーター登録を行った件数
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        res = self._put('/support', payload=data)
        return res['added_count'] if res else None

    def unsupport_user(self, target_user_ids):
        """
            Unsupport User
            指定したユーザーのサポーターになる
            必須パーミッション: Write

            Parameters:
                - target_user_ids - サポーターを解除するユーザのidかscreen_idのリスト
                                    1度に20人まで可能

            Return:
                サポーター解除を行った件数
        """
        # dataとして渡す
        data = {'target_user_ids': target_user_ids}
        res = self._put('/unsupport', payload=data)
        return res['removed_count'] if res else None

    def get_supporting_list(self, user_id, offset=0, limit=20):
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
                          'users': Userの配列}
        """
        res = self._get(f'/users/{user_id}/supporting', offset=offset, limit=limit)
        parser = ModelParser()
        res['users'] = parser.parse(self, res['supporting'], parse_type='user', payload_list=True)
        del res['supporting']
        return res

    def get_supporter_list(self, user_id, offset=0, limit=20, sort='ranking'):
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
                          'users': Userの配列}
        """
        res = self._get(f'/users/{user_id}/supporters', offset=offset, limit=limit, sort=sort)
        parser = ModelParser()
        res['users'] = parser.parse(self, res['supporters'], parse_type='user', payload_list=True)
        del res['supporters']
        return res

    def get_categories(self, lang='ja'):
        """
            Get Categories
            配信中のライブがあるカテゴリのみを取得する
            必須パーミッション: Read

            Parameters:
                - lang - 検索対象の言語. 'ja' or 'en'
                         構造体みたいなのないの

            Return:
                Categoryオブジェクトの配列
        """
        res = self._get('/categories', lang=lang)
        parser = ModelParser()
        return parser.parse(self, res['categories'], parse_type='category', payload_list=True)

    def search_users(self, words, limit=10, lang='ja'):
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
                Userの配列
        """
        w = ' '.join(words) if len(words) > 1 else words[0]
        res = self._get('/search/users', words=w, limit=limit, lang=lang)
        parser = ModelParser()
        return parser.parse(self, payload=res['users'], parse_type='user', payload_list=True)

    def search_live_movies(self, search_type='new', context=None, limit=10, lang='ja'):
        """
            Search Live Movies
            配信中のライブを検索する
            必須パーミッション: Read

            Parameters:
                - search_type - 検索種別. 
                                 'tag' or 'word' or 'category' or 
                                 'new'(新着) or 'recommend'(おすすめ)
                - context - 検索内容.search_typeの値によって決まる(required: type=tag, word, category)
                             search_type='tag' or 'word': AND検索する単語のリスト
                             search_type='category': サブカテゴリID
                             search_type='new' or 'recommend': None(不要)
                - limit - 取得件数. min:1, max:100
                - lang - 検索対象のユーザの言語設定. 現在は'ja'のみ

            Return:
                Movieオブジェクトの配列
                `/movies/:movie_id`と同じ結果
        """
        params = {'type': search_type, 'limit': limit, 'lang': lang}

        # search_typeによってcontentを設定
        if search_type and context:
            if search_type in ['tag', 'word']:
                # パラメータはurlencodeされるためエンコードされるし、
                # ' 'を'+'に変換してくれているから、空白で結合し、渡す
                w = ' '.join(context) if len(context) > 1 else context[0]
                params['context'] = w

            elif search_type in ['category']:
                params['content'] = content

            elif search_type in ['new', 'recommend']:
                # 追加しない
                pass

        res = self._get('/search/lives', args=params)
        parser = ModelParser()
        return parser.parse(self, payload=res['movies'], parse_type='movie', payload_list=True)

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
                - dict - {'all_count': このアプリに登録済みWebHook件数,
                          'webhooks': WebHookの配列}
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
        """
            Register WebHook
            WebHookを新規登録します
            これを使うには、アプリケーションでWebHook URLの登録が必須
            必須パーミッション: any

            Parameters:
                - user_id - 対象のユーザのid
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
                - user_id - 対象のユーザのid
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
