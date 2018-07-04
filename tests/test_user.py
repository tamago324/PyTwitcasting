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

@vcr.use_cassette
def test_get_live_thumbnail_image(user, live_thumbnail_image_data):
    res = user.get_live_thumbnail_image()
    for k in live_thumbnail_image_data.keys():
        assert res[k] == live_thumbnail_image_data[k]

@vcr.use_cassette
def test_get_live_thumbnail_image_large(user, live_thumbnail_image_data_large):
    res = user.get_live_thumbnail_image(size='large')
    for k in live_thumbnail_image_data_large.keys():
        assert res[k] == live_thumbnail_image_data_large[k]

@vcr.use_cassette
def test_get_live_thumbnail_image_beginning(user, live_thumbnail_image_data_beginning):
    res = user.get_live_thumbnail_image(position='beginning')
    for k in live_thumbnail_image_data_beginning.keys():
        assert res[k] == live_thumbnail_image_data_beginning[k]

@vcr.use_cassette
def test_save_live_thumbnail_image(user, tmpdir):
    """ ライブサムネイル画像が保存できるか """
    res = user.get_live_thumbnail_image()
    f = tmpdir.mkdir('images').join(f'live_thumbnail.{res["file_ext"]}')
    try:
        f.write(res['bytes_data'], mode='wb')
    except:
        assert False
    else:
        assert True

@vcr.use_cassette
def test_save_live_thumbnail_image_large(user, tmpdir):
    """ ライブサムネイル画像が保存できるか
        sizeに'large'を指定
    """
    res = user.get_live_thumbnail_image(size='large')
    f = tmpdir.mkdir('images').join(f'live_thumbnail_large.{res["file_ext"]}')
    try:
        f.write(res['bytes_data'], mode='wb')
    except:
        assert False
    else:
        assert True

@vcr.use_cassette
def test_save_live_thumbnail_image_beginning(user, tmpdir):
    """ ライブサムネイル画像が保存できるか
        positionに'beginning'を指定
    """
    res = user.get_live_thumbnail_image(position='beginning')
    f = tmpdir.mkdir('images').join(f'live_thumbnail_beginning.{res["file_ext"]}')
    try:
        f.write(res['bytes_data'], mode='wb')
    except:
        assert False
    else:
        assert True
