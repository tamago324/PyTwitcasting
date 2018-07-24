.. introdutction.rst

Introduction
============

PyTwitcastingは `TwitCasting API v2(β) <http://apiv2-doc.twitcasting.tv/>`__ を使うためのPython3.x用ライブラリ。

Pythonから `TwitCasting <https://twitcasting.tv/>`__ の情報にアクセスできる。


Hello PyTwitcasting
-------------------

まずは、 https://twitcasting.tv/developernewapp.php でアプリの作成を行う

作成できたら、以下のコードを実行。

.. code-block :: python

    from pytwitcasting.auth import TwitcastingApplicationBasis
    from pytwitcasting.api import API

    client_id = 'ClientID'
    client_secret = 'ClientSecret'
    app_basis = TwitcastingApplicationBasis(client_id=client_id,
                                            client_secret=client_secret)

    api = API(application_basis=app_basis)

    print(api.get_user_info('twitcasting_jp').name)
    # ツイキャス公式
    
BASIC認証を使ったアプリケーション単位でのアクセスでユーザー情報を取得するサンプルコード。

すべての情報にアクセスするにはOAuth認証で取得したアクセストークンを使う。認証については :doc:`認証チュートリアル <auth_tutorial>` を参照してください。


Instollation
------------

PyPIからインストール::

    pip install pytwitcasting

ソースからインストール::

    git clone https://github.com/tamago324/PyTwitcasting.git
    cd PyTwitcasting
    python setup.py install

Licensing
---------

PyTwitcastingは `MITライセンス <https://opensource.org/licenses/mit-license.php>`__ の下で配布されています。

What next?
----------

TwitcastingのAPIについては :doc:`APIリファレンス <apis>` を参照してください。

PyTwitcastingのクラスについては :doc:`クラスリファレンス <referense>` を参照してください。
