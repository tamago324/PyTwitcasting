import os
import unittest

from pytwitcasting.api import API
from pytwitcasting.models import User
from pytwitcasting.utils import parse_datetime

TOKEN = os.environ['ACCESS_TOKEN']


"""
. <- ここで以下のコマンドを実行する
├── pytwitcasting
│   ├── api.py
│   ├── auth.py
│   ├── error.py
│   ├── models.py
│   ├── parsers.py
│   └── utils.py
└── tests
    └── test_userparse.py

$ pipenv run python3 -m unittest discover tests
"""


class Test_UserParse(unittest.TestCase):

    def setUp(self):
        self._json = {
            "id": "2756718188",
            "screen_id": "tamago324_pad",
            "name": "たまたまご",
            "image": "http://imagegw02.twitcasting.tv/image3s/pbs.twimg.com/profile_images/948168012854583298/0rFfF-lX_normal.jpg",
            "profile": "Vim Python とか / アイコンは[@rpaci_]が書いてくれた",
            "level": 30,
            "last_movie_id": "467161696",
            "is_live": False,
            "supporter_count": 190,
            "supporting_count": 40,
            "created": 1408883011
        }

        self._user = User(None)
        self._user._json = self._json
        self._user.id = '2756718188'
        self._user.screen_id = 'tamago324_pad'
        self._user.name = 'たまたまご'
        self._user.image = 'http://imagegw02.twitcasting.tv/image3s/pbs.twimg.com/profile_images/948168012854583298/0rFfF-lX_normal.jpg'
        self._user.profile = 'Vim Python とか / アイコンは[@rpaci_]が書いてくれた'
        self._user.level = 30
        self._user.last_movie_id = "467161696"
        self._user.is_live = False
        self._user.supporter_count = 190
        self._user.supporting_count = 40
        # XXX: これをテストする
        self._user.created = parse_datetime(1408883011)

    def test_parse(self):
        api = API(TOKEN)
        user = User()

        # import pudb; pudb.set_trace()  # デバッグコード
        res = user.parse(api, self._json)

        self.assertEqual(getattr(res, '_json'), self._user._json)
        self.assertEqual(getattr(res, 'id'), self._user.id)
        self.assertEqual(getattr(res, 'screen_id'), self._user.screen_id)
        self.assertEqual(getattr(res, 'name'), self._user.name)
        self.assertEqual(getattr(res, 'image'), self._user.image)
        self.assertEqual(getattr(res, 'profile'), self._user.profile)
        self.assertEqual(getattr(res, 'level'), self._user.level)
        self.assertEqual(getattr(res, 'last_movie_id'), self._user.last_movie_id)
        self.assertEqual(getattr(res, 'is_live'), self._user.is_live)
        self.assertEqual(getattr(res, 'supporter_count'), self._user.supporter_count)
        self.assertEqual(getattr(res, 'supporting_count'), self._user.supporting_count)
        self.assertEqual(getattr(res, 'created'), self._user.created)
