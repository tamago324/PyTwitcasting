
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
        return self._api.get_live_thumbnail_image(user_id=self.id, **kwargs)

    def get_movies(self, **kwargs):
        return self._api.get_movies_by_user(user_id=self.id, **kwargs)

    def get_current_live(self):
        return self._api.get_current_live(user_id=self.id)

    def get_supporting_status(self, id):
        return self._api.get_supporting_status(user_id=self.id, target_user_id=id)

    def get_supporting_list(self, **kwargs):
        return self._api.get_supporting_list(user_id=self.id, **kwargs)

    def get_supporter_list(self, **kwargs):
        return self._api.get_supporter_list(user_id=self.id, **kwargs)


class App(Model):

    @classmethod
    def parse(cls, api, json):
        app = cls(api)
        setattr(app, '_json', json)

        for k, v in json.items():
            setattr(app, k, v)

        return app


class Credentials():

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


class Movie(Model):

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
        return self._api.get_comments(movie_id=self.id, **kwargs)

    def post_comment(self, comment, **kwargs):
        return self._api.post_comment(movie_id=self.id, comment=comment, **kwargs)

    def delete_comment(self, comment_id):
        return self._api.delete_comment(movie_id=self.id, comment_id=comment_id)


class Comment(Model):

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

    @classmethod
    def parse(cls, api, json):
        pass


class SubCategory(Model):

    @classmethod
    def parse(cls, api, json):
        pass


class WebHook(Model):

    @classmethod
    def parse(cls, api, json):
        pass


# XXX: Errorオブジェクトいる？？



class ModelFactory(object):
    # これを通して、parseする
    user = User
    app = App
    movie = Movie
    comment = Comment
    category = Category
    sub_catetgory = SubCategory
    webhook = WebHook
