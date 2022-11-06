from datetime import timedelta
from enum import Enum
from strenum import StrEnum

MILLISECONDS_IN_SECOND = 1000
RESPONSE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
RESPONSE_DATETIME_FORMAT_MS = f"{RESPONSE_DATETIME_FORMAT}.%f"
MAX_MARKET_HISTORY_PERIODS = 500
TRANSACTIONS_MAX_PAGE_SIZE = 50


class MarketHistoryIntervals(Enum):
    MINUTES_1 = timedelta(minutes=1).total_seconds()
    MINUTES_5 = timedelta(minutes=5).total_seconds()
    MINUTES_30 = timedelta(minutes=30).total_seconds()
    HOURS_1 = timedelta(hours=1).total_seconds()
    HOURS_6 = timedelta(hours=6).total_seconds()
    HOURS_12 = timedelta(hours=12).total_seconds()
    DAYS_1 = timedelta(days=1).total_seconds()
    DAYS_3 = timedelta(days=3).total_seconds()
    DAYS_7 = timedelta(days=7).total_seconds()


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
