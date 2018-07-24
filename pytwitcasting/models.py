from pytwitcasting.utils import parse_datetime
from pprint import pprint


class Model(object):
    """ レスポンスオブジェクトのベースクラス """

    def __init__(self, api=None):
        self._api = api

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Model <pytwitcasting.models.Model>`
        """
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Model <pytwitcasting.models.Model>` のリスト
        :rtype: List[ :class:`Model <pytwitcasting.models.Model>` ]
        """
        results = list()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))

        return results

    # XXX: Pickleするかどうか


class User(Model):
    """ ユーザを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`User <pytwitcasting.api.User>`
        """
        user = cls(api)
        setattr(user, '_json', json)

        for k, v in json.items():
            if k == 'created':
                setattr(user, k, parse_datetime(v))
            else:
                setattr(user, k, v)

        return user

    def get_live_thumbnail_image(self, **kwargs):
        """ Get Live Thumbnail Image

        配信中のライブのサムネイル画像を取得する。

        :calls: `GET /users/:user_id/live/thumbnail <http://apiv2-doc.twitcasting.tv/#live-thumbnail>`_
        :param size: (optional) 画像サイズ。``'small'`` or ``'large'``
        :type size: str
        :param position: (optional) 取得する位置。ライブ開始時点か最新か。 ``'beginning'`` or ``'latest'``
        :type position: str
        :return: - ``bytes_data`` : サムネイルの画像データ(bytes)
                 - ``file_ext`` : ファイル拡張子( ``'jepg'`` or ``'png'`` )
        :rtype: dict
        """
        return self._api._get_live_thumbnail_image(user_id=self.id, **kwargs)

    def get_movies(self, **kwargs):
        """ Get Movies by User

        ユーザーが保有する過去ライブ(録画)の一覧を作成日時の降順で取得する

        :calls: `GET /users/:user_id/movies <http://apiv2-doc.twitcasting.tv/#get-movies-by-user>`_
        :param offset: (optional) 先頭からの位置. default: ``0``, min: ``0``
        :type offset: int
        :param limit: (optional) 最大取得件数. default: ``20`` , min: ``1`` , max: ``50``
        :type limit: int
        :return: - ``total_count`` : offset,limitの条件での総件数
                 - ``movies`` : :class:`Movie <pytwitcasting.models.Movie>` の配列
        :rtype: dict
        """
        return self._api._get_movies_by_user(user_id=self.id, **kwargs)

    def get_current_live(self):
        """ Get Current Live

        ユーザーが配信中の場合、ライブ情報を取得する

        :calls: `GET /users/:user_id/current_live <http://apiv2-doc.twitcasting.tv/#get-current-live>`_
        :return: - ``movie`` : :class:`Movie <pytwitcasting.models.Movie>`
                 - ``broadcaster`` : :class:`User <pytwitcasting.models.User>`
                 - ``tags`` : 設定されているタグの配列
        :rtype: dict
        """
        return self._api._get_current_live(user_id=self.id)

    def get_supporting_status(self, id):
        """ Get Supporting Status

        ユーザーが、ある別のユーザのサポーターであるかの状態を取得する

        :calls: `GET /users/:user_id/supporting_status <http://apiv2-doc.twitcasting.tv/#get-supporting-status>`_
        :param target_user_id: 状態を取得する対象のユーザのidかscreen_id
        :type target_user_id: str
        :return: - ``is_supporting`` : サポーターかどうか
                 - ``target_user`` : :class:`User <pytwitcasting.models.User>`
        :rtype: dict
        """
        return self._api._get_supporting_status(user_id=self.id, target_user_id=id)

    def get_supporting_list(self, **kwargs):
        """ Supporting List

        指定したユーザ*が*サポートしているユーザの一覧を取得する

        :calls: `GET /users/:user_id/supporting <http://apiv2-doc.twitcasting.tv/#supporting-list>`_
        :param offset: (optional) 先頭からの位置. default: ``0`` , min: ``0``
        :type offset: int
        :param limit: (optional) 最大取得件数. default: ``20`` , min: ``1``, max: ``20``
        :type limit: int
        :return: - ``total`` : 全レコード数
                 - ``users`` : :class:`User <pytwitcasting.models.User>` のリスト
        :rtype: dict
        """
        return self._api._get_supporting_list(user_id=self.id, **kwargs)

    def get_supporter_list(self, **kwargs):
        """ Supporting List

        指定したユーザ*を*サポートしているユーザの一覧を取得する

        :calls: `GET /users/:user_id/supporters <http://apiv2-doc.twitcasting.tv/#supporter-list>`_
        :param offset: (optional) 先頭からの位置. default: ``0`` , min: ``0``
        :type offset: int
        :param limit: (optional) 最大取得件数. default: ``20`` , min: ``1`` , max: ``20``
        :type limit: int
        :param sort: (optional) 並び順. 'ranking'(貢献度順) or 'new'(新着順)
        :type sort: str
        :return: - ``total`` : 全レコード数
                 - ``users`` : :class:`User <pytwitcasting.models.User>` のリスト
        :rtype: dict
        """
        return self._api._get_supporter_list(user_id=self.id, **kwargs)


class Supporter(User):
    """ サポーターユーザを表すオブジェクト
    ``point`` と ``total_point`` 以外は :class:`User <pytwitcasting.models.User>` と同じ
    """
    pass


class Movie(Model):
    """ ライブ（録画）を表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Movie <pytwitcasting.api.Movie>`
        """
        movie = cls(api)
        setattr(movie, '_json', json)

        for k, v in json.items():
            if k == 'created':
                setattr(movie, k, parse_datetime(v))
            else:
                setattr(movie, k, v)

        return movie

    def get_comments(self, **kwargs):
        """ Get Comments

        コメントを作成日時の降順で取得する

        :calls: `GET /movies/:movie_id/comments <http://apiv2-doc.twitcasting.tv/#get-comments>`_
        :param offset: (optional) 先頭からの位置. min:0
        :type offset: int
        :param limit: (optional) 取得件数. min:1, max:50
        :type limit: int
        :param slice_id: (optional) このコメントID以降のコメントを取得する
        :type slice_id: int
        :return: - ``movie_id`` : ライブID
                 - ``all_count`` : 総コメント数
                 - ``comments`` : :class:`Comment <pytwitcasting.models.Comment>` の配列
        """
        return self._api._get_comments(movie_id=self.id, **kwargs)

    def post_comment(self, comment, **kwargs):
        """ Post Comment

        コメントを投稿する。 ユーザ単位でのみ実行可能

        :calls: `POST /movies/:movie_id/comments <http://apiv2-doc.twitcasting.tv/#post-comment>`_
        :param comment: 投稿するコメント
        :type comment: str
        :param sns: (optional) SNSへの同時投稿。
                    ``none`` :   SNSへ投稿しない.
                    ``normal`` : 投稿する.
                    ``reply`` :  配信者への返信として投稿する.
        :type sns: str
        :return: - ``movie_id`` : ライブID
                 - ``all_count`` : 総コメント数
                 - ``comment`` : 投稿した :class:`Comment <pytwitcasting.models.Comment>`
        :rtype: dict
        """
        return self._api._post_comment(movie_id=self.id, comment=comment, **kwargs)

    def delete_comment(self, comment_id):
        """ Delete Comment

        コメントを削除する。ユーザ単位でのみ実行可能

        コメント投稿者か、ライブ配信者に紐づくアクセストークンであれば削除可能

        :calls: `DELETE /movies/:movie_id/comments/:comment_id <http://apiv2-doc.twitcasting.tv/#delete-comment>`_
        :param comment_id: 投稿するコメントID
        :type comment_id: int
        :return: 削除したコメントID
        """
        return self._api._delete_comment(movie_id=self.id, comment_id=comment_id)


class App(Model):
    """ アプリケーションを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`App <pytwitcasting.api.App>`
        """
        app = cls(api)
        setattr(app, '_json', json)

        for k, v in json.items():
            setattr(app, k, v)

        return app


class Credentials():
    """ 検証結果を表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Credentials <pytwitcasting.api.Credentials>`
        """
        credentials = Credentials()
        setattr(credentials, '_json', json)

        for k, v in json.items():
            if k == 'user':
                setattr(credentials, k, User.parse(v))
            elif k == 'app':
                setattr(credentials, k, App.parse(v))
            else:
                setattr(credentials, k, v)

        return credentials


class Comment(Model):
    """ コメントを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Comment <pytwitcasting.api.Comment>`
        """
        comment = cls(api)
        setattr(comment, '_json', json)

        for k, v in json.items():
            if k == 'created':
                setattr(comment, k, parse_datetime(v))
            elif k == 'from_user':
                setattr(comment, k, User.parse(api, v))
            else:
                setattr(comment, k, v)

        return comment


class Category(Model):
    """ 配信カテゴリを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`Category <pytwitcasting.api.Category>`
        """
        category = cls(api)
        setattr(category, '_json', json)

        for k, v in json.items():
            if k == 'sub_categories':
                setattr(category, k, SubCategory.parse_list(api, v))
            else:
                setattr(category, k, v)

        return category


class SubCategory(Model):
    """ 配信サブカテゴリを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`SubCategory <pytwitcasting.api.SubCategory>`
        """
        sub_category = cls(api)
        setattr(sub_category, '_json', json)

        for k, v in json.items():
            setattr(sub_category, k, v)

        return sub_category


class WebHook(Model):
    """ WebHookを表すオブジェクト """

    @classmethod
    def parse(cls, api, json):
        """ レスポンスをもとに属性を追加する

        :param api: :class:`API <pytwitcasting.api.API>`
        :param json: APIレスポンスのdict
        :return: :class:`WebHook <pytwitcasting.api.WebHook>`
        """
        webhook = cls(api)
        setattr(webhook, '_json', json)

        for k, v in json.items():
            setattr(webhook, k, v)

        return webhook


# XXX: Errorオブジェクトいる？？


class ModelFactory(object):
    # これを通して、parseする
    user = User
    movie = Movie
    app = App
    comment = Comment
    category = Category
    sub_catetgory = SubCategory
    webhook = WebHook
