import os
import webbrowser
from pprint import pprint

from pytwitcasting import TwitcastingImplicit
from pytwitcasting import TwitCastingApplicationBasis
from pytwitcasting import Twitcasting

def implicit_test():
    client_id = os.environ['TWITCASTING_CLIENT_ID']
    tc_imp = TwitcastingImplicit(client_id)
    auth_url = tc_imp.get_authorize_url()
    webbrowser.open(auth_url)
    response = input('リダイレクトされたURLを入力 => ')

    token_info = tc_imp.get_access_token(response)
    print('------------------------')
    pprint(token_info)


if __name__ == '__main__':
    client_id = os.environ['TWITCASTING_CLIENT_ID']
    client_secret = os.environ['TWITCASTING_CLIENT_SECRET']
    app_basis = TwitCastingApplicationBasis(client_id, client_secret)
    twitcas = Twitcasting(application_basis=app_basis)

    print(twitcas.get_user_info('tamago324_pad'))
