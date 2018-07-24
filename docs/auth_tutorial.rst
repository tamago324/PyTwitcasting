.. auth_tutoial.rst

Authorization tutorial
======================

まずは、 https://twitcasting.tv/developernewapp.php でアプリの作成を行う

作成できたら、アクセストークンを取得する。認証方法は２つある。

- Implicit Grant Type
- Authorization Code Grant

Implicit Grant Type
-------------------

以下のコードを ``get_access_token_implicit.py`` で保存し、実行する

.. code-block :: python

    # get_access_token_implicit.py
    from pytwitcasting.utils import get_access_token_prompt_implicit

    client_id = 'アプリのClientID'

    access_token = get_access_token_prompt_implicit(client_id=client_id)

    print('アクセストークン↓')
    print(access_token)


ブラウザで、認証ボタンをクリックする。リダイレクトされたURLをコピーし、 ``Enter the URL you were redirected to:`` の横に貼り付け、Enter


::

    $ python3 get_access_token_oauth.py
    Opened https://apiv2.twitcasting.tv/oauth2/authorize?client_id={ClientID}&response_type=code in your browser


    Enter the URL you were redirected to: リダイレクトされたURLを貼り付ける

    アクセストークン↓
    {これがアクセストークン}

アクセストークンを ``.env`` とかに保存すればOK!(Pipenvの場合)


Authorization Code Grant
------------------------

以下のコードを ``get_access_token_oauth.py`` で保存し、実行する

.. code-block :: python

    # get_access_token_oauth.py
    from pytwitcasting.utils import get_access_token_prompt_oauth

    client_id = 'アプリのClientID'
    client_secret = 'アプリのClientSecret'
    redirect_uri = 'アプリのCallback URL'

    access_token = get_access_token_prompt_oauth(client_id=client_id,
                                                 client_secret=client_secret,
                                                 redirect_uri=redirect_uri)

    print('アクセストークン↓')
    print(access_token)


ブラウザで、認証ボタンをクリックする。リダイレクトされたURLをコピーし、 ``Enter the URL you were redirected to:`` の横に貼り付け、Enter

::

    $ python3 get_access_token_oauth.py
    Opened https://apiv2.twitcasting.tv/oauth2/authorize?client_id={ClientID}&response_type=code in your browser


    Enter the URL you were redirected to: リダイレクトされたURLを貼り付ける

    アクセストークン↓
    {これがアクセストークン}


アクセストークンを ``.env`` とかに保存すればOK!(Pipenvの場合)
