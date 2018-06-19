
from pytwitcasting.utils import parse_datetime
from pprint import pprint


class Model(object):

    def __init__(self, api=None):
        self._api = api

    @classmethod
    def parse(self, api, json):
        """
            ModelParserから呼ばれるときに、APIMethod.apiが渡されていた
        """
        raise NotImplementedError

    @classmethod
    def parse_list(self, api, json_list):
        results = list()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))

        return results

    # XXX: Pickleするかどうか


# class Status(Model):
#
#     @classmethod
#     def parse(cls, api, json):
#         status = cls(api)
#         setattr(status, '_json', json)
#
#         for k, v in json:
#             if k == 'created':
#                 setattr(user, k, parse_datetime(v))
#             elif k == 'user':
#                 setattr(user, k, User.parse(v))
#             else:
#                 setattr(user, k, v)
#
#         return status

class User(Model):

    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        setattr(user, '_json', json)
        print(type(json))
        pprint(json)

        for k, v in json.items():
            if k == 'created':
                setattr(user, k, parse_datetime(v))
            else:
                setattr(user, k, v)

        return user

    def get_live_thumbnail_image(self):
        pass

    def get_movies(self):
        pass

    def get_current_live(self):
        pass

    def get_supporting_status(self):
        pass

    def get_supporting_list(self):
        pass

    def get_supporter_list(self):
        pass


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

    def get_comments(self):
        pass

    def post_comments(self):
        pass

    def delete_comments(self):
        pass


class Comment(Model):

    @classmethod
    def parse(cls, api, json):
        pass


class SupporterUser(User):
    """
        Userとほぼ同じため、Userを継承する？
    """

    @classmethod
    def parse(cls, api, json):
        pass


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
    supporter_user = SupporterUser
    category = Category
    sub_catetgory = SubCategory
    webhook = WebHook
