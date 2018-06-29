import os
import pytest
import vcr

from pytwitcasting.api import API
from pytwitcasting.models import User

TOKEN = os.environ['ACCESS_TOKEN']

# URLとリクエストメソッドが一致するリクエストが同一とみなされる
tape = vcr.VCR(
    serializer='json',
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    # アクセストークンを消去する
    filter_headers=['Authorization']
)


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
def user_key():
    return ['id', 'screen_id', 'name', 'image', 'profile', 'level',
            'last_movie_id', 'is_live', 'supporter_count',
            'supporting_count', 'created']


@tape.use_cassette('user_info.json')
def test_get_user_info(user_key):
    api = API(auth=TOKEN)

    user = api.get_user_info('tamago324_pad')

    assert isinstance(user, User)
    assert user.screen_id == 'tamago324_pad'

    for k in user_key:
        assert hasattr(user, k)
