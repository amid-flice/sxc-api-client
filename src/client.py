import requests
from datetime import datetime, timezone
from math import ceil
from typing import Dict, Callable, Any

from src.constants import MILLISECONDS_IN_SECOND, MAX_MARKET_HISTORY_PERIODS, RESPONSE_DATETIME_FORMAT, \
    RESPONSE_DATETIME_FORMAT_MS, TransactionTypes, TRANSACTIONS_MAX_PAGE_SIZE
from src.exceptions import raise_by_response
from src.request_params import SxcApiRequestParams


class SxcApiClient:
    _BASE_URL = "https://www.southxchange.com/api/v4"

    def __init__(self, access_key: str = None, secret_key: str = None):
        self.access_key = access_key
        self.secret_key = secret_key

    @staticmethod
    def send_request(params: SxcApiRequestParams) -> Any:
        func_request = params.method
        resp = func_request(**params.request_args)
        raise_by_response(resp)
        if resp.status_code == 204:
            return None
        return resp.json()

    def list_markets(self) -> list[list[str, str]]:
        """
        Lists all markets.

        :return: Markets.
        :Example:
        [
            [
                "DASH",
                "BTC"
            ],
            [
                "LTC",
                "BTC"
            ]
        ]
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/markets",
            auth_required=True
        )
        return self.send_request(params)

    def get_price(self, target_currency: str, reference_currency: str) -> dict:
        """
        Gets price of a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Price of a given market.
        :Example:
        {
            "Bid": 0.000000604,
            "Ask": 0.000000779,
            "Last": 0.000000759,
            "Variation24Hr": 0.0,
            "Volume24Hr": 74.37446475
        }
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/price/{target_currency}/{reference_currency}"
        )
        return self.send_request(params)

    def list_prices(self) -> list[dict]:
        """
        Lists prices of all markets.

        :return: Market prices.
        :Example:
        [
            {
                "Market": "DASH/BTC",
                "Bid": 0.002117966,
                "Ask": 0.002131398,
                "Last": 0.002142643,
                "Variation24Hr": 0.25,
                "Volume24Hr": 5.6542005
            },
            {
                "Market": "LTC/BTC",
                "Bid": 0.00328,
                "Ask": 0.003289038,
                "Last": 0.003324991,
                "Variation24Hr": -0.38,
                "Volume24Hr": 33.92142523
            }
        ]
        """
        LAST_UPDATE_KEY = "LastUpdate"
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/prices",
            auth_required=True
        )
        resp = self.send_request(params)
        for w in resp:
            w[LAST_UPDATE_KEY] = self._to_datetime(w[LAST_UPDATE_KEY])
        return resp

    def list_market_history(self, target_currency: str, reference_currency: str, start_ts: int, end_ts: int,
                            granularity: int) -> list[dict]:
        """
        List market history between two dates.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :param start_ts: Start timestamp from January 1, 1970.
        :param end_ts: End timestamp from January 1, 1970.
        :param granularity: Interval in seconds. Use constants defined in :class:`src.constants.MarketHistoryIntervals`.
        :return: Market history.
        :Example:
        [
            {
                "Date": datetime.datetime(2022, 8, 23, 0, 0, tzinfo=datetime.timezone.utc),
                "PriceHigh": 0.000000861,
                "PriceLow": 0.000000832,
                "PriceOpen": 0.000000861,
                "PriceClose": 0.000000832,
                "Volume": 250.81775954
            },
            {
                "Date": datetime.datetime(2022, 8, 23, 6, 0, tzinfo=datetime.timezone.utc),
                "PriceHigh": 0.000000832,
                "PriceLow": 0.000000832,
                "PriceOpen": 0.000000832,
                "PriceClose": 0.000000832,
                "Volume": 0.0
            },
            {
                "Date": datetime.datetime(2022, 8, 23, 12, 0, tzinfo=datetime.timezone.utc),
                "PriceHigh": 0.000001031,
                "PriceLow": 0.0000007,
                "PriceOpen": 0.000000832,
                "PriceClose": 0.0000007,
                "Volume": 985.6552949
            }
        ]
        """
        DATE_KEY = "Date"
        end_ts_initial = end_ts
        periods_initial = int((end_ts - start_ts) / granularity)
        iterations = ceil(periods_initial / MAX_MARKET_HISTORY_PERIODS)
        if iterations == 1:
            params = self._get_request_params(
                method=requests.get,
                url=f"{self._BASE_URL}/history/{target_currency}/{reference_currency}/"
                    f"{start_ts * MILLISECONDS_IN_SECOND}/{end_ts * MILLISECONDS_IN_SECOND}/{periods_initial}"
            )
            interim_result = self.send_request(params)
            if not len(interim_result):
                return []
            for entry in interim_result:
                entry[DATE_KEY] = self._to_datetime(entry[DATE_KEY])
            # re-request market history data in case currency pair was introduced on the market after the requested
            # start date; otherwise the response will contain data with improper interval
            first_entry_ts = interim_result[0][DATE_KEY].timestamp()
            if first_entry_ts > start_ts:
                start_ts = ceil(first_entry_ts / granularity) * granularity
                return self.list_market_history(target_currency, reference_currency, start_ts, end_ts, granularity)
            return interim_result

        periods_remained = periods_initial
        result = []
        while periods_remained > 0:
            periods = min(periods_remained, MAX_MARKET_HISTORY_PERIODS)
            end_ts = min(start_ts + granularity * periods, end_ts_initial)
            interim_result = self.list_market_history(target_currency, reference_currency, start_ts, end_ts,
                                                      granularity)
            result.extend(interim_result)
            start_ts = end_ts
            periods_remained -= periods
        return result

    def list_order_book(self, target_currency: str, reference_currency: str) -> dict[str, list[dict]]:
        """
        Lists order book of a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Order book.
        :Example:
        {
            "BuyOrders": [
                {
                    "Index": 0,
                    "Amount": 0.03086135,
                    "Price": 0.003240298
                },
                {
                    "Index": 1,
                    "Amount": 20.45,
                    "Price": 0.003240297
                }
            ],
            "SellOrders": [
                {
                    "Index": 0,
                    "Amount": 0.00150627,
                    "Price": 0.003270581
                },
                {
                    "Index": 1,
                    "Amount": 0.01847108,
                    "Price": 0.003270582
                }
            ]
        }
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/book/{target_currency}/{reference_currency}"
        )
        return self.send_request(params)

    def list_trades(self, target_currency: str, reference_currency: str) -> list[dict]:
        """
        Lists the latest trades in a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Latest trades.
        :Example:
        [
            {
                "At": 1667752941,
                "Amount": 0.3131722,
                "Price": 0.003324991,
                "Type": "buy"
            },
            {
                "At": 1667752939,
                "Amount": 0.00308295,
                "Price": 0.003324991,
                "Type": "buy"
            },
            {
                "At": 1667752929,
                "Amount": 0.18600116,
                "Price": 0.00331565,
                "Type": "sell"
            }
        ]
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/trades/{target_currency}/{reference_currency}"
        )
        return self.send_request(params)

    def list_fees(self) -> dict:
        """
        Get general information about currencies, markets and fees.

        :return: General information.
        :Example:
        {
            "Currencies": [
                {
                    "Code": "BTC",
                    "Name": "Bitcoin",
                    "Precision": 9,
                    "MinDeposit": 0.00005,
                    "DepositFeeMin": 0.0,
                    "MinWithdraw": 0.0002,
                    "WithdrawFee": 0.0,
                    "WithdrawFeeMin": 0.00015,
                    "MinAmount": 0.000000001
                },
                {
                    "Code": "ETH",
                    "Name": "Ethereum",
                    "Precision": 8,
                    "MinDeposit": 0.01,
                    "DepositFeeMin": 0.0,
                    "MinWithdraw": 0.007,
                    "WithdrawFee": 0.0,
                    "WithdrawFeeMin": 0.0035,
                    "MinAmount": 0.0
                }
            ],
            "Markets": [
                {
                    "ListingCurrencyCode": "ETH",
                    "ReferenceCurrencyCode": "BTC",
                    "MakerFee": 0.001,
                    "TakerFee": 0.003,
                    "MinOrderListingCurrency": null,
                    "PricePrecision": null
                }
            ],
            "TraderLevels": [
                {
                    "Name": "TraderLevel1",
                    "MinVolumeAmount": 0.1,
                    "MinVolumeCurrency": "BTC",
                    "MakerFeeRebate": 0.2,
                    "TakerFeeRebate": 0.2
                },
                {
                    "Name": "TraderLevel2",
                    "MinVolumeAmount": 0.5,
                    "MinVolumeCurrency": "BTC",
                    "MakerFeeRebate": 0.4,
                    "TakerFeeRebate": 0.4
                }
            ]
        }
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/fees",
            auth_required=True
        )
        return self.send_request(params)

    def list_wallets(self) -> list[dict]:
        """
        Retrieves the status for all wallets.

        :return: Wallets information.
        :Example:
        [
            {
                "Currency": "BTC",
                "CurrencyName": "Bitcoin",
                "LastUpdate": datetime.datetime(2022, 11, 6, 16, 50, 23, 277000, tzinfo=datetime.timezone.utc),
                "Status": "Good",
                "Type": "Crypto",
                "LastBlock": 762000,
                "Version": "210100",
                "Connections": 10,
                "RequiredConfirmations": 2
            },
            {
                "Currency": "ETH",
                "CurrencyName": "Ethereum",
                "LastUpdate": datetime.datetime(2022, 11, 6, 16, 50, 26, 327000, tzinfo=datetime.timezone.utc),
                "Status": "Good",
                "Type": "Crypto",
                "LastBlock": 15912281,
                "Version": "v1.10.23-omnibus-b38477ec",
                "Connections": 100,
                "RequiredConfirmations": 20
            }
        ]
        """
        LAST_UPDATE_KEY = "LastUpdate"
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/wallets",
            auth_required=True
        )
        resp = self.send_request(params)
        for w in resp:
            w[LAST_UPDATE_KEY] = self._to_datetime(w[LAST_UPDATE_KEY])
        return resp

    def place_order(self, target_currency: str, reference_currency: str, order_type: str, amount: float,
                    limit_price: float, amount_in_reference_currency: bool = False) -> str:
        """
        Places an order in a given market.

        :param target_currency: Market listing currency.
        :param reference_currency: Market reference currency.
        :param order_type: Order type. Possible values: "buy", "sell". Refer to class :class:`src.constants.OrderTypes`.
        :param amount: Order amount in listing currency.
        :param limit_price: Optional price in reference currency. If `None` then order is executed at market price.
        :param amount_in_reference_currency: `True` if order amount is in reference currency; defaults to `False`.
        :return: Order code.
        """
        payload = {
            "listingCurrency": target_currency,
            "referenceCurrency": reference_currency,
            "type": order_type,
            "amount": amount,
            "amountInReferenceCurrency": amount_in_reference_currency
        }
        if limit_price:
            payload["limitPrice"] = limit_price
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/placeOrder",
            payload=payload,
            auth_required=True
        )
        return self.send_request(params)

    def cancel_order(self, order_code: str) -> None:
        """
        Cancels a given order.

        :param order_code: Order code.
        :return: None
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/cancelOrder",
            payload={
                "orderCode": order_code
            },
            auth_required=True
        )
        return self.send_request(params)

    def cancel_market_orders(self, target_currency: str, reference_currency: str) -> None:
        """
        Cancels all orders in a given market.

        :param target_currency: Market listing currency.
        :param reference_currency: Market reference currency.
        :return: None
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/cancelMarketOrders",
            payload={
                "listingCurrency": target_currency,
                "referenceCurrency": reference_currency
            },
            auth_required=True
        )
        return self.send_request(params)

    def list_pending_orders(self) -> list[dict]:
        """
        Lists all pending orders.

        :return: Pending orders.
        :Example:
        [
            {
                "Code": "163421247",
                "Type": "sell",
                "Amount": 218.55863408,
                "OriginalAmount": 218.55863408,
                "LimitPrice": 0.000001356,
                "ListingCurrency": "CRW",
                "ReferenceCurrency": "BTC",
                "DateAdded": datetime.datetime(2022, 1, 28, 0, 1, 9, 767000, tzinfo=datetime.timezone.utc)
            },
            {
                "Code": "199829936",
                "Type": "buy",
                "Amount": 0.05507009,
                "OriginalAmount": 0.05507009,
                "LimitPrice": 0.002609047,
                "ListingCurrency": "LTC",
                "ReferenceCurrency": "BTC",
                "DateAdded": datetime.datetime(2022, 10, 11, 6, 0, 48, 797000, tzinfo=datetime.timezone.utc)
            }
        ]
        """
        DATE_ADDED_KEY = "DateAdded"
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/listOrders",
            auth_required=True
        )
        orders = self.send_request(params)
        for order in orders:
            order[DATE_ADDED_KEY] = self._to_datetime(order[DATE_ADDED_KEY])
        return orders

    def list_balances(self) -> list[dict]:
        """
        Lists non-zero balances for all currencies

        :return: balances
        :Example:
        [
            {
                "Currency": "BIGO",
                "Deposited": 300.0,
                "Available": 300.0,
                "Unconfirmed": 0.0
            },
            {
                "Currency": "BTC",
                "Deposited": 0.1,
                "Available": 0.05,
                "Unconfirmed": 0.0
            }
        ]
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/listBalances",
            auth_required=True
        )
        return self.send_request(params)

    def list_transactions(self, target_currency: str = None,
                          transaction_type: str = TransactionTypes.TRANSACTIONS.value,
                          optional_filter: int = None, page_index: int = 0,
                          page_size: int = TRANSACTIONS_MAX_PAGE_SIZE) -> dict:
        """
        Lists transactions by page.

        :param target_currency: target currency
        :param transaction_type: transaction type. Refer to class :class:`src.constants.TransactionTypes`
         to get all allowed values
        :param optional_filter: optional filter. Possible values: the order code if transaction type is
         "tradesbyordercode"; the address ID if transaction type is "depositsbyaddressid".
        :param page_index: page index
        :param page_size: page size. Maximum: 50
        :return: transactions
        :Example:
        {
            "TotalElements": 2,
            "Result": [
                {
                    "Date": datetime.datetime(2022, 11, 1, 20, 40, 5, 57000, tzinfo=datetime.timezone.utc),
                    "CurrencyCode": "DASH",
                    "Amount": 0.0,
                    "TotalBalance": 30.91380084,
                    "Type": "tradefee",
                    "Status": "confirmed",
                    "Address": null,
                    "Hash": null,
                    "Price": 0.0,
                    "OtherAmount": 0.0,
                    "OtherCurrency": null,
                    "OrderCode": null,
                    "TradeId": 19737424,
                    "MovementId": null,
                    "TransactionId": 491636439
                },
                {
                    "Date": datetime.datetime(2022, 11, 1, 20, 40, 5, 57000, tzinfo=datetime.timezone.utc),
                    "CurrencyCode": "DASH",
                    "Amount": 0.00000195,
                    "TotalBalance": 30.91380084,
                    "Type": "trade",
                    "Status": "confirmed",
                    "Address": null,
                    "Hash": null,
                    "Price": 0.002017385,
                    "OtherAmount": 0.000000003,
                    "OtherCurrency": "BTC",
                    "OrderCode": "199077234",
                    "TradeId": 19737424,
                    "MovementId": null,
                    "TransactionId": 491636438
                }
            ]
        }
        """
        DATE_KEY = "Date"

        payload = {
            "transactionType": transaction_type,
            "pageIndex": page_index,
            "pageSize": page_size,
            "sortField": DATE_KEY,
            "descending": True
        }

        if target_currency:
            payload["currency"] = target_currency
        if transaction_type in (TransactionTypes.TRADES_BY_ORDER_CODE.value, TransactionTypes.DEPOSITS_BY_ADDRESS_ID):
            payload["optionalFilter"] = optional_filter

        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/listTransactions",
            payload=payload,
            auth_required=True
        )
        resp = self.send_request(params)

        for tx in resp["Result"]:
            tx[DATE_KEY] = self._to_datetime(tx[DATE_KEY])
        return resp

    def get_user_info(self) -> dict:
        """
        Get user information.

        :return: user information.
        :Example:
        {
            "TraderLevel": "TraderLevel1"
        }
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/getUserInfo",
            auth_required=True
        )
        return self.send_request(params)

    @staticmethod
    def _to_datetime(datetime_str: str) -> datetime:
        try:
            # extract split seconds and convert them to microseconds
            # as Python does not yet support more precise fractions
            datetime_parts = datetime_str.split(".")
            microseconds = datetime_parts[1][:6]
            dt = datetime.strptime(".".join([datetime_parts[0], microseconds]), RESPONSE_DATETIME_FORMAT_MS)
        except (ValueError, IndexError):
            dt = datetime.strptime(datetime_str, RESPONSE_DATETIME_FORMAT)
        return dt.replace(tzinfo=timezone.utc)

    def _get_request_params(self, method: Callable, url: str, payload: Dict = None, auth_required=False)\
            -> SxcApiRequestParams:
        return SxcApiRequestParams(
            method=method,
            url=url,
            payload=payload or {},
            auth_required=auth_required,
            access_key=self.access_key,
            secret_key=self.secret_key
        )
