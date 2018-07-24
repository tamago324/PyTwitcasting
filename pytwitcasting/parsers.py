from pytwitcasting.error import TwitcastingError
from pytwitcasting.models import ModelFactory


class Parser(object):
    """ Parserの基礎クラス """

    def parse(self, api, payload, parse_type, payload_list):
        raise NotImplementedError


class RawParser(Parser):
    """ 返すだけ """

    def parse(self, api, payload, parse_type, payload_list):
        """ payloadからparse_typeのModelクラスのオブジェクトを生成する

        :param api: :class:`pytwitcasting.api.API`
        :param payload: レスポンス(dict)
        :param parse_type: 生成するModelクラス名
        :param payload_list: リストかどうか
        :return: :class:`pytwitcasting.models.Model` の子クラス
        """
        return payload


class ModelParser(Parser):
    """ :class:`pytwitcasting.models.Model` に変換する """

    def __init__(self):
        self.model_factory = ModelFactory()

    def parse(self, api, payload, parse_type, payload_list):
        """ payloadからparse_typeのModelクラスのオブジェクトを生成する

        :param api: :class:`pytwitcasting.api.API`
        :param payload: レスポンス(dict)
        :param parse_type: 生成するModelクラス名
        :param payload_list: リストかどうか
        :return: :class:`pytwitcasting.models.Model` の子クラス
        """
        try:
            if parse_type is None:
                return None
            # ModelFactoryからModelを取得
            model = getattr(self.model_factory, parse_type)
        except AttributeError:
            raise TwitcastingError(f'No model for this payload type: {parse_type}')

        if payload_list:
            result = model.parse_list(api, payload)
        else:
            result = model.parse(api, payload)

        return result
