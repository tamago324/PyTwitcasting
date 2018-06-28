import json
import pytest

from pytwitcasting.api import API
from pytwitcasting.models import User
from pytwitcasting.utils import parse_datetime


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


@pytest.fixture
def user(json_data):
    user = User(None)
    user._json = json_data
    user.id = '2756718188'
    user.created = parse_datetime(1408883011)
    return user


@pytest.fixture
def json_data():
    return json.loads("""
        {
            "id": "2756718188",
            "created": 1408883011
        }
    """)


def test_parse_user(user, json_data):
    api = API(None)
    usr = User()

    # import pudb; pudb.set_trace()  # デバッグコード
    res = usr.parse(api, json_data)

    assert getattr(res, '_json') == user._json
    assert getattr(res, 'id') == user.id
    assert getattr(res, 'created') == user.created
