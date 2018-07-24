# PyTwitcasting

PyTwitcastingはTwitcastingのAPIv2(β)を使うためのライブラリ

## インストール

pipでインストール

```sh
pipenv install pytwitcasting
```

GitHubからクローンしてインストール

```sh
git clone https://github.com/tamago324/PyTwitcasting.git
cd PyTwitcasting
pipenv run python3 setup.py install
```

## 使用例

まずは、 https://twitcasting.tv/developernewapp.php でアプリの作成を行う

例）ユーザー名の表示

```python
from pytwitcasting.auth import TwitcastingApplicationBasis
from pytwitcasting.api import API

client_id = 'ClientID'
client_secret = 'ClientSecret'
app_basis = TwitcastingApplicationBasis(client_id=client_id,
                                        client_secret=client_secret)

api = API(application_basis=app_basis)

print(api.get_user_info('twitcasting_jp').name)
# ツイキャス公式
```

## ドキュメント

ドキュメントは http://pytwitcasting.readthedocs.io/ja/latest/

## ライセンス

[MIT](https://choosealicense.com/licenses/mit/)
