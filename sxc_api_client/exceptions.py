import re
import requests


class SxcApiError(Exception):
    def __init__(self, msg, response_status_code: int = None, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        self.msg = msg
        self.response_status_code = response_status_code


class SxcAuthDataMissingError(SxcApiError):
    ...


class SxcNotEnoughBalanceError(SxcApiError):
    ...


class SxcAnotherOrderIsInProcessError(SxcApiError):
    ...


class SxcInvalidKeyOrNonceError(SxcApiError):
    ...


class SxcInvalidHashError(SxcApiError):
    ...


class SxcOrderNotExistsError(SxcApiError):
    ...


class SxcTooManyOrdersError(SxcApiError):
    ...


class SxcInvalidMarketError(SxcApiError):
    ...


class SxcNotEnoughPermissionError(SxcApiError):
    ...


class SxcUnsupportedCurrencyError(SxcApiError):
    ...


class SxcInvalidDestinationTypeError(SxcApiError):
    ...


class SxcMarketHistoryError(SxcApiError):
    ...


class SxcArgumentError(SxcApiError):
    ...


class SxcOrderAmountBelowMinimumError(SxcApiError):
    ...


_MESSAGE_PATTERN_ERROR_MAP = {
    re.compile('"Invalid API key or nonce"'): SxcInvalidKeyOrNonceError,
    re.compile('"Invalid API hash"'): SxcInvalidHashError,
    re.compile('"There is another order currently being processed in this market. Please wait."'):
        SxcAnotherOrderIsInProcessError,
    re.compile('"Not enough balance"'): SxcNotEnoughBalanceError,
    re.compile('"API key with not enough permission"'): SxcNotEnoughPermissionError,
    re.compile('"You cannot have more than \\d+ orders in this market"'): SxcTooManyOrdersError,
    re.compile('"Currency \\w+ does not support lightning invoice"'): SxcUnsupportedCurrencyError,
    re.compile('"Destination Type invalid"'): SxcInvalidDestinationTypeError,
    re.compile('"Market does not exist."'): SxcInvalidMarketError,
    re.compile('"Amount below minimum"'): SxcOrderAmountBelowMinimumError
}


def raise_by_response(resp: requests.Response):
    if resp.status_code in [200, 204]:
        return
    msg = resp.content.decode("utf-8") if resp.content else ""
    error_class = SxcApiError
    for pattern, cls in _MESSAGE_PATTERN_ERROR_MAP.items():
        if pattern.search(msg):
            error_class = cls  # type: type[SxcApiError]
            break
    raise error_class(msg, resp.status_code)
