import time

import pytest

from pytwitcasting.api import API
from pytwitcasting.models import User

from tests.myvcr import vcr
import tests.conftest as conf


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


@vcr.use_cassette
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
