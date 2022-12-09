from datetime import timedelta
from enum import IntEnum
from strenum import StrEnum


MILLISECONDS_IN_SECOND = 1000
RESPONSE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
RESPONSE_DATETIME_FORMAT_MS = f"{RESPONSE_DATETIME_FORMAT}.%f"
MAX_MARKET_HISTORY_PERIODS = 500
MAX_PAGE_SIZE = 50


class MarketHistoryIntervals(IntEnum):
    MINUTES_1 = int(timedelta(minutes=1).total_seconds())
    MINUTES_5 = int(timedelta(minutes=5).total_seconds())
    MINUTES_30 = int(timedelta(minutes=30).total_seconds())
    HOURS_1 = int(timedelta(hours=1).total_seconds())
    HOURS_6 = int(timedelta(hours=6).total_seconds())
    HOURS_12 = int(timedelta(hours=12).total_seconds())
    DAYS_1 = int(timedelta(days=1).total_seconds())
    DAYS_3 = int(timedelta(days=3).total_seconds())
    DAYS_7 = int(timedelta(days=7).total_seconds())


class TransactionTypes(StrEnum):
    TRANSACTIONS = "transactions"
    DEPOSITS = "deposits"
    WITHDRAWALS = "withdrawals"
    DEPOSITS_WITHDRAWALS = "depositswithdrawals"
    TRADES_BY_ORDER_CODE = "tradesbyordercode"
    DEPOSITS_BY_ADDRESS_ID = "depositsbyaddressid"


class OrderTypes(StrEnum):
    BUY = "buy"
    SELL = "sell"


class WithdrawalDestinationTypes(IntEnum):
    CRYPTO_ADDRESS = 0
    LIGHTNING_NETWORK_INVOICE = 1
    USER_EMAIL_ADDRESS = 2
