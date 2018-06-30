import time

import pytest

from pytwitcasting.api import API
from pytwitcasting.models import User

import tests.config as conf


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

$ pipenv run python3 -m pytest
"""

@pytest.fixture
def user():
    user = User()
    user._api = API(conf.TOKEN)
    # レスポンスをもとに生成
    user.created = 1408883011
    user.id = '2756718188'
    user.image = 'http://imagegw02.twitcasting.tv/image3s/pbs.twimg.com/profile_images/948168012854583298/0rFfF-lX_normal.jpg'
    user.is_live = False
    user.last_movie_id = '467161696'
    user.level = 30
    user.name = 'たまたまご'
    user.profile = 'Vim Python とか / アイコンは[@rpaci_]が書いてくれた'
    user.screen_id = 'tamago324_pad'
    user.supporter_count = 190
    user.supporting_count = 40
    return user


@conf.tape.use_cassette
def test_get_user_info(user):
    api = API(auth=conf.TOKEN)

    res = api.get_user_info('tamago324_pad')

    # 型チェック
    assert isinstance(res, User)

    # フィールドの値確認
    for k in user.__dict__.keys():
        if k == 'created':
            # タイムスタンプ->unixtimeに変換し、比較
            assert time.mktime(getattr(res, k).timetuple()) == getattr(user, k)
        elif k == '_api':
            # 型の確認
            assert isinstance(getattr(res, k), type(getattr(user, k)))
        else:
            assert getattr(res, k) == getattr(user, k)

