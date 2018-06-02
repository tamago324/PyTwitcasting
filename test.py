import os
import webbrowser
from pprint import pprint

from pytwitcasting import TwitcastingImplicit

if __name__ == '__main__':
    client_id = os.environ['TWITCASTING_CLIENT_ID']
    tc_imp = TwitcastingImplicit(client_id)
    auth_url = tc_imp.get_authorize_url()
    webbrowser.open(auth_url)
    response = input('リダイレクトされたURLを入力 => ')

    token_info = tc_imp.parse_response_auth_info(response)
    pprint(token_info)
