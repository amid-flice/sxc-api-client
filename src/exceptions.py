import re
import requests


class SxcApiError(Exception):
    def __init__(self, error_code, msg='', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        self.error_code = error_code
        self.msg = msg


class NotEnoughBalanceError(SxcApiError):
    pass


class AnotherOrderIsInProcessError(SxcApiError):
    pass


class NoOrderCodeReturnedError(SxcApiError):
    pass


class InvalidKeyOrNonceError(SxcApiError):
    pass


class InvalidHashError(SxcApiError):
    pass


class OrderNotExistsError(SxcApiError):
    pass


class TooManyOrdersError(SxcApiError):
    pass


class InvalidMarketError(SxcApiError):
    pass


MESSAGE_PATTERN_ERROR_MAP = {
    "\"Invalid API key or nonce\"": InvalidKeyOrNonceError,
    "\"Invalid API hash\"": InvalidHashError,
    "\"There is another order currently being processed in this market. Please wait.\"":
        AnotherOrderIsInProcessError,
    "\"Not enough balance\"": NotEnoughBalanceError,
    "\"You cannot have more than \\d+ orders in this market\"": TooManyOrdersError
}


def raise_by_response(resp: requests.Response):
    if resp.status_code not in [200, 204]:
        msg = resp.content.decode("utf-8") if resp.content else ""
        error_class = SxcApiError
        for pattern, cls in MESSAGE_PATTERN_ERROR_MAP.items():
            if re.match(pattern, msg):
                error_class = cls
                break
        raise error_class(error_code=resp.status_code, msg=msg)
