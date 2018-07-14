from pytwitcasting.utils import parse_datetime
from pprint import pprint


class Model(object):

    def __init__(self, api=None):
        self._api = api

    @classmethod
    def parse(cls, api, json):
        """
            ModelParserから呼ばれるときに、APIMethod.apiが渡されていた
        """
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        results = list()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))

        return results

    # XXX: Pickleするかどうか


class User(Model):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-user-info """

    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        setattr(user, '_json', json)

        for k, v in json.items():
            if k == 'created':
                setattr(user, k, parse_datetime(v))
            else:
                setattr(user, k, v)

        return user

    def get_live_thumbnail_image(self, **kwargs):
        """
            Get Live Thumbnail Image
            配信中のライブのサムネイル画像を取得する。

            Parameters:
                - size (optional) - 画像サイズ. 'small' or 'large'
                - position (optional) - ライブ開始時点か最新か. 'beginning' or 'latest'

            Return:
                - dict - {'bytes_data': サムネイルの画像データ(bytes),
                          'file_ext': ファイル拡張子('jepg' or 'png')}
        """
        return self._api.get_live_thumbnail_image(user_id=self.id, **kwargs)

    def get_movies(self, **kwargs):
        """
            Get Movies by User
            ユーザーが保有する過去ライブ（録画）の一覧を作成日時の降順で取得する

            Parameters:
                - offset (optional) - 先頭からの位置. min:0
                - limit (optional) - 最大取得件数. min:1, max:50

            Return:
                - dict - {'total_count': offset,limitの条件での総件数,
                          'movies': Movieの配列}
        """
        return self._api.get_movies_by_user(user_id=self.id, **kwargs)

    def get_current_live(self):
        """
            Get Current Live
            ユーザーが配信中の場合、ライブ情報を取得する

            Return:
                - dict - {'movie': Movieオブジェクト,
                          'broadcaster': 配信者のUser,
                          'tags': 設定されているタグの配列}
        """
        return self._api.get_current_live(user_id=self.id)

    def get_supporting_status(self, id):
        """
            Get Supporting Status
            ユーザーが、ある別のユーザのサポーターであるかの状態を取得する

            Parameters:
                - target_user_id - 状態を取得する対象のユーザのidかscreen_id

            Return:
                - dict - {'is_supporting': サポーターかどうか,
                          'target_user': 対象ユーザのUser}
        """
        return self._api.get_supporting_status(user_id=self.id, target_user_id=id)

    def get_supporting_list(self, **kwargs):
        """
            Supporting List
            指定したユーザがサポート`している`ユーザの一覧を取得する

            Parameters:
                - offset (optional) - 先頭からの位置. min:0
                - limit (optional) - 最大取得件数. min:1, max:20

            Return:
                - dict - {'total': 全レコード数,
                          'users': Userの配列}
        """
        return self._api.get_supporting_list(user_id=self.id, **kwargs)

    def get_supporter_list(self, **kwargs):
        """
            Supporting List
            指定したユーザがサポート`している`ユーザの一覧を取得する

            Parameters:
                - offset (optional) - 先頭からの位置. min:0
                - limit (optional) - 最大取得件数. min:1, max:20
                - sort (optional) - 並び順. 'ranking'(貢献度順) or 'new'(新着順)

            Return:
                - dict - {'total': 全レコード数,
                          'users': Userの配列}
        """
        return self._api.get_supporter_list(user_id=self.id, **kwargs)


class Supporter(User):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#supporting-list """
    pass


class Movie(Model):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-movie-info """

    @classmethod
    def parse(cls, api, json):
        movie = cls(api)
        setattr(movie, '_json', json)

        for k, v in json.items():
            if k == 'created':
                setattr(movie, k, parse_datetime(v))
            else:
                setattr(movie, k, v)

        return movie

    def get_comments(self, **kwargs):
        """
            Get Comments
            コメントを作成日時の降順で取得する

            Parameters:
                - offset (optional) - 先頭からの位置. min:0
                - limit (optional) - 取得件数. min:1, max:50
                - slice_id (optional) - このコメントID以降のコメントを取得する

            Return:
                - dict - {'movie_id': ライブID,
                          'all_count': 総コメント数,
                          'comments': Commentの配列}
        """
        return self._api.get_comments(movie_id=self.id, **kwargs)

    def post_comment(self, comment, **kwargs):
        """
            Post Comment
            コメントを投稿する。 ユーザ単位でのみ実行可能

            Parameters:
                - comment - 投稿するコメント
                - sns (optional) - SNSへの同時投稿. 'none' or 'normal' or 'reply'
                                 none:   SNSへ投稿しない
                                 normal: 投稿する
                                 reply:  配信者への返信として投稿する

            Return:
                - dict - {'movie_id': ライブID,
                          'all_count': 総コメント数,
                          'comment': 投稿したComment}
        """
        return self._api.post_comment(movie_id=self.id, comment=comment, **kwargs)

    def delete_comment(self, comment_id):
        """
            Delete Comment
            コメントを削除する。ユーザ単位でのみ実行可能
            コメント投稿者か、ライブ配信者に紐づくアクセストークンであれば削除可能

            Parameters:
                - comment_id - 投稿するコメント

            Return:
                - 削除したコメントID
        """
        return self._api.delete_comment(movie_id=self.id, comment_id=comment_id)


class App(Model):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#verify-credentials """

    @classmethod
    def parse(cls, api, json):
        app = cls(api)
        setattr(app, '_json', json)

        for k, v in json.items():
            setattr(app, k, v)

        return app


class Credentials():
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#verify-credentials """

    @classmethod
    def parse(cls, api, json):
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
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-comments """

    @classmethod
    def parse(cls, api, json):
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
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-categories """

    @classmethod
    def parse(cls, api, json):
        category = cls(api)
        setattr(category, '_json', json)

        for k, v in json.items():
            if k == 'sub_categories':
                setattr(category, k, SubCategory.parse_list(api, v))
            else:
                setattr(category, k, v)

        return category


class SubCategory(Model):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-categories """

    @classmethod
    def parse(cls, api, json):
        sub_category = cls(api)
        setattr(sub_category, '_json', json)

        for k, v in json.items():
            setattr(sub_category, k, v)

        return sub_category


class WebHook(Model):
    """ Attribute info -> http://apiv2-doc.twitcasting.tv/#get-webhook-list """

    @classmethod
    def parse(cls, api, json):
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
