import os
import pytest

from pytwitcasting.api import API
from pytwitcasting.models import (
    User
)

# 見づらくなるため、image_dataに定義してある
import image_data


TOKEN = os.environ['ACCESS_TOKEN']


@pytest.fixture
def user():
    user = User()
    user._api = API(TOKEN)
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

@pytest.fixture
def live_thumbnail_image_data():
    data = {}
    data['file_ext'] = 'jpeg'
    data['bytes_data'] = image_data.live_thumbnail_image_data
    return data

@pytest.fixture
def live_thumbnail_image_data_large():
    data = {}
    data['file_ext'] = 'jpeg'
    data['bytes_data'] = image_data.live_thumbnail_image_large_data
    return data

@pytest.fixture
def live_thumbnail_image_data_beginning():
    data = {}
    data['file_ext'] = 'jpeg'
    data['bytes_data'] = image_data.live_thumbnail_image_beginning_data
    return data
