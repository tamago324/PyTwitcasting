
from pytwitcasting.error import TwitcastingError, TwitcastingException
from pytwitcasting.models import ModelFactory

import json


class Parser(object):

    def parse(self, api, payload, parse_type, payload_list):
        """
            payloadからparse_typeのModelクラスのオブジェクトを生成する

            Parameters:
                - payload - APIのレスポンス(dict)
                - parse_type - 生成するModelクラス名
                - payload_list - リストかどうか

            Return:
                生成したModelクラス
        """
        raise NotImplementedError


class RawParser(Parser):

    def parse(self, api, payload, parse_type, payload_list):
        return payload


class ModelParser(Parser):

    def __init__(self):
        self.model_factory = ModelFactory()

    def parse(self, api, payload, parse_type, payload_list):
        try:
            if parse_type is None:
                return 
            # ModelFactoryからModelを取得
            model = getattr(self.model_factory, parse_type)
        except AttributeError:
            raise TwitcastingError(f'No model for this payload type: {parse_type}')

        if payload_list:
            result = model.parse_list(api, payload)
        else:
            result = model.parse(api, payload)

        return result
