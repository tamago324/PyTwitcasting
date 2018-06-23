
class TwitcastingError(Exception):
    pass


class TwitcastingException(Exception):
    def __init__(self, http_status, code, msg):
        self.http_status = http_status
        self.code = code
        self.msg = msg

    def __str__(self):
        return f'http status: {self.http_status}, code: {self.code} {self.msg}'

