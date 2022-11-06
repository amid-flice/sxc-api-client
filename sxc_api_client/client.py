import requests
from datetime import datetime, timezone
from math import ceil
from typing import Dict, Callable, Any, Generator

from sxc_api_client.constants import MILLISECONDS_IN_SECOND, MAX_MARKET_HISTORY_PERIODS, RESPONSE_DATETIME_FORMAT, \
    RESPONSE_DATETIME_FORMAT_MS, MAX_PAGE_SIZE, TransactionTypes
from sxc_api_client.exceptions import raise_by_response, SxcAuthDataMissingError, SxcInvalidMarketError, \
    SxcMarketHistoryError
from sxc_api_client.request_params import SxcApiRequestParams


class SxcApiClient:
    _BASE_URL = "https://www.southxchange.com/api/v4"

    def __init__(self, access_key: str = '', secret_key: str = ''):
        self.access_key = access_key
        self.secret_key = secret_key

    @staticmethod
    def send_request(params: SxcApiRequestParams) -> Any:
        if params.auth_required and not all([params.access_key, params.secret_key]):
            raise SxcAuthDataMissingError("Request requires authentication. Please provide API access and secret keys.")
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
        
        :example:
        >>> client.list_markets()
        [
            ['DASH', 'BTC', 5],
            ['LTC', 'BTC', 7]
        ]
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/markets"
        )
        return self.send_request(params)

    def get_price(self, target_currency: str, reference_currency: str) -> dict:
        """
        Gets price of a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Price of a given market.

        :example:
        >>> client.get_price('CRW', 'BTC')
        {
            'Bid': 0.067417841,
            'Ask': 0.067808474,
            'Last': 0.068148556,
            'Variation24Hr': -8.38,
            'Volume24Hr': 2.63158984
        }
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/price/{target_currency}/{reference_currency}"
        )
        resp = self.send_request(params)
        if not resp:
            self._raise_invalid_market_error()
        return resp

    def list_prices(self) -> list[dict]:
        """
        Lists prices of all markets.

        :return: Market prices.
        
        :example:
        >>> client.list_prices()
        [
            {
                'Market': 'DASH/BTC',
                'Bid': 0.002117966,
                'Ask': 0.002131398,
                'Last': 0.002142643,
                'Variation24Hr': 0.25,
                'Volume24Hr': 5.6542005
            },
            {
                'Market': 'LTC/BTC',
                'Bid': 0.00328,
                'Ask': 0.003289038,
                'Last': 0.003324991,
                'Variation24Hr': -0.38,
                'Volume24Hr': 33.92142523
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

    def list_market_history(self, target_currency: str, reference_currency: str, start_ts: int | float,
                            end_ts: int | float, periods: int) -> list[dict]:
        """
        List market history between two dates. Please keep in mind it is strongly recommended to pass `start_ts` and
        `end_ts` so that difference between them is aliquot to `periods`; otherwise unexpected data may be
        returned without any warning. Besides, as a rule of thumb consider that the value of statement
        `(end_ts - start) / periods` should be equal to one of the values defined in
        :class:`src.constants.MarketHistoryIntervals`. Hopefully those restrictions will be solved soon in
        SouthXChange API.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :param start_ts: Start timestamp from January 1, 1970.
        :param end_ts: End timestamp from January 1, 1970.
        :param periods: Number of periods to get. Limited to 500; if bigger value is provided API silently resets it to
            500.
        :return: Market history.

        :example:
        >>> client.list_market_history('ETH', 'BTC',
        ...                            datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp(),
        ...                            datetime(2022, 1, 3, tzinfo=timezone.utc).timestamp(),
        ...                            2)
        [
            {
                'Date': datetime.datetime(2022, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.079624402,
                'PriceLow': 0.077018168,
                'PriceOpen': 0.079384817,
                'PriceClose': 0.077232438,
                'Volume': 0.70592287
            }, {
                'Date': datetime.datetime(2022, 1, 2, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.080658164,
                'PriceLow': 0.077179415,
                'PriceOpen': 0.077232438,
                'PriceClose': 0.079098818,
                'Volume': 0.59452678
            }, {
                'Date': datetime.datetime(2022, 1, 3, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.080598789,
                'PriceLow': 0.067001496,
                'PriceOpen': 0.079098818,
                'PriceClose': 0.079553838,
                'Volume': 2.18225486
            }
        ]
        """
        DATE_KEY = "Date"
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/history/{target_currency}/{reference_currency}/"
                f"{int(start_ts * MILLISECONDS_IN_SECOND)}/{int(end_ts * MILLISECONDS_IN_SECOND)}/{periods}"
        )
        result = self.send_request(params) or []
        for entry in result:
            entry[DATE_KEY] = self._to_datetime(entry[DATE_KEY])
        return result

    def scroll_market_history_by_granularity(self, target_currency: str, reference_currency: str, start_ts: int | float,
                                             end_ts: int | float, granularity: int, **kwargs) \
            -> Generator[list[dict], None, None]:
        """
        List market history between two dates with given granularity. A handier version of
        :meth:`src.client.SxcApiClient.list_market_history`

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :param start_ts: Start timestamp from January 1, 1970.
        :param end_ts: End timestamp from January 1, 1970.
        :param granularity: Interval in seconds. Use constants defined in :class:`src.constants.MarketHistoryIntervals`.
        :param strict_mode: Raise exception if granularity in a response does not match the given one.
            Such a case is possible when either (1) arbitrary granularity (except values defined in
            :class:`src.constants.MarketHistoryIntervals`) is provided or (2) currency pair was listed on the market
            after the given `start_ts` or (3) `end_ts` is relatively far in the future. Defaults to True.
        :return: Market history.

        :example:
        >>> from sxc_api_client.constants import MarketHistoryIntervals
        >>> for m in client.scroll_market_history_by_granularity(
        ...         'ETH', 'BTC',
        ...         datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp(),
        ...         datetime(2022, 1, 3, tzinfo=timezone.utc).timestamp(),
        ...         MarketHistoryIntervals.DAYS_1.value):
        ...     print(m)
        [
            {
                'Date': datetime.datetime(2022, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.079624402,
                'PriceLow': 0.077018168,
                'PriceOpen': 0.079384817,
                'PriceClose': 0.077232438,
                'Volume': 0.70592287
            }, {
                'Date': datetime.datetime(2022, 1, 2, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.080658164,
                'PriceLow': 0.077179415,
                'PriceOpen': 0.077232438,
                'PriceClose': 0.079098818,
                'Volume': 0.59452678
            }, {
                'Date': datetime.datetime(2022, 1, 3, 0, 0, tzinfo=datetime.timezone.utc),
                'PriceHigh': 0.080598789,
                'PriceLow': 0.067001496,
                'PriceOpen': 0.079098818,
                'PriceClose': 0.079553838,
                'Volume': 2.18225486
            }
        ]
        """
        def validate_granularity(data):
            if len(data) < 2:
                return
            resp_granularity = int(data[1][DATE_KEY].timestamp() - data[0][DATE_KEY].timestamp())
            if resp_granularity != granularity:
                raise SxcMarketHistoryError(f"Granularity in the response does not match the given one: "
                                            f"{resp_granularity} vs {granularity}")

        DATE_KEY = "Date"
        strict_mode = kwargs.get('strict_mode', True)

        periods = int(ceil((end_ts - start_ts) / granularity))
        req_start_ts = start_ts
        periods_remained = periods
        while periods_remained > 0:
            req_periods = min(periods_remained, MAX_MARKET_HISTORY_PERIODS)
            req_end_ts = req_start_ts + granularity * req_periods
            interim_result = self.list_market_history(target_currency, reference_currency, req_start_ts, req_end_ts,
                                                      req_periods)
            if strict_mode:
                validate_granularity(interim_result)
            # market history listing range is inclusive, i.e. in order to avoid duplicates start timestamp
            # for the next request must be shifted one period forward
            req_start_ts = req_end_ts + granularity
            periods_remained -= req_periods + 1
            yield interim_result

    def list_order_book(self, target_currency: str, reference_currency: str) -> dict[str, list[dict]]:
        """
        Lists order book of a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Order book.

        :example:
        >>> client.list_order_book('ETH', 'BTC')
        {
            "BuyOrders": [
                {
                    "Index": 0,
                    "Amount": 0.00147298,
                    "Price": 0.067889252
                },
                {
                    "Index": 1,
                    "Amount": 0.1979,
                    "Price": 0.067889251
                }
            ],
            "SellOrders": [
                {
                    "Index": 0,
                    "Amount": 0.01103169,
                    "Price": 0.068781728
                },
                {
                    "Index": 1,
                    "Amount": 0.2991489,
                    "Price": 0.06901085
                }
            ]
        }
        """
        params = self._get_request_params(
            method=requests.get,
            url=f"{self._BASE_URL}/book/{target_currency}/{reference_currency}"
        )
        resp = self.send_request(params)
        if not resp:
            self._raise_invalid_market_error()
        return resp

    def list_trades(self, target_currency: str, reference_currency: str) -> list[dict]:
        """
        Lists the latest trades in a given market.

        :param target_currency: Listing currency code.
        :param reference_currency: Reference currency code.
        :return: Latest trades.

        :example:
        >>> client.list_trades('ETH', 'BTC')
        [
            {
                'At': 1668012323,
                'Amount': 0.38359823,
                'Price': 0.068379352,
                'Type': 'buy'
            }, {
                'At': 1668012304,
                'Amount': 0.45140177,
                'Price': 0.068379352,
                'Type': 'buy'
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
        Get general information about currencies, markets, trader levels and their fees.

        :return: Fees data.

        :example:
        >>> client.list_fees()
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
                    "MinOrderListingCurrency": None,
                    "PricePrecision": None
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
            url=f"{self._BASE_URL}/fees"
        )
        return self.send_request(params)

    def get_user_info(self) -> dict:
        """
        Get user information (level). Use :meth:`SxcApiClient.list_fees` to retrieve actual fees applicable to user
        level.

        :return: User information.

        :example:
        >>> client.get_user_info()
        {'TraderLevel': 'TraderLevel1'}
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/getUserInfo",
            auth_required=True
        )
        return self.send_request(params)

    def list_wallets(self) -> list[dict]:
        """
        Retrieves the status for all wallets.

        :return: Wallets information.

        :example:
        >>> client.list_wallets()
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
        :param order_type: Order type. Possible values: "buy", "sell". Use constants defined in
            :class:`src.constants.OrderTypes`.
        :param amount: Order amount in listing currency.
        :param limit_price: Optional price in reference currency. If `None` then order is executed at market price.
        :param amount_in_reference_currency: `True` if order amount is in reference currency; defaults to `False`.
        :return: Order code.

        :example:
        >>> from sxc_api_client import OrderTypes
        >>> client.place_order('ETH', 'BTC', OrderTypes.BUY.value, 0.01, 0.068344600)
        '64065725'
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

        :example:
        >>> client.cancel_order('60000000')
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

        :example:
        >>> client.cancel_market_orders('ETC', 'BTC')
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
        
        :example:
        >>> client.list_pending_orders()
        [
            {
                'Code': '163421247',
                'Type': 'sell',
                'Amount': 218.55863408,
                'OriginalAmount': 218.55863408,
                'LimitPrice': 0.000001356,
                'ListingCurrency': 'CRW',
                'ReferenceCurrency': 'BTC',
                'DateAdded': datetime.datetime(2022, 1, 28, 0, 1, 9, 767000, tzinfo=datetime.timezone.utc)
            },
            {
                'Code': '199829936',
                'Type': 'buy',
                'Amount': 0.05507009,
                'OriginalAmount': 0.05507009,
                'LimitPrice': 0.002609047,
                'ListingCurrency': 'LTC',
                'ReferenceCurrency': 'BTC',
                'DateAdded': datetime.datetime(2022, 10, 11, 6, 0, 48, 797000, tzinfo=datetime.timezone.utc)
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

    def get_order(self, code: str) -> dict:
        """
        Gets a given order.

        :param code: Order code to get.
        :return: Order data.

        :example:
        >>> client.get_order('203765246')
        {
            'Code': '203765246',
            'Type': 'sell',
            'Amount': 0.16542518,
            'PendingAmount': 0.0,
            'LimitPrice': 0.00226272,
            'ListingCurrency': 'DASH',
            'ReferenceCurrency': 'BTC',
            'Status': 'executed',
            'DateAdded': datetime.datetime(2022, 11, 7, 15, 30, 10, 460000, tzinfo=datetime.timezone.utc)
        }
        """
        DATE_ADDED_KEY = "DateAdded"
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/getOrder",
            payload={
                "code": code
            },
            auth_required=True
        )
        order = self.send_request(params)
        if order:
            order[DATE_ADDED_KEY] = self._to_datetime(order[DATE_ADDED_KEY])
        return order

    def list_orders_by_codes(self, codes: list[str], page_index: int = 0, page_size: int = MAX_PAGE_SIZE) -> list[dict]:
        """
        Lists orders by given codes.

        :param codes: Orders codes.
        :param page_index: Page index.
        :param page_size: Page size. Maximum: 50.
        :return: Orders data.

        :example:
        >>> client.list_orders_by_codes(['203579724', '203587899'])
        [
            {
                'Code': '203579724',
                'Type': 'sell',
                'Amount': 0.04181474,
                'PendingAmount': 0.0,
                'LimitPrice': 0.002148943,
                'ListingCurrency': 'DASH',
                'ReferenceCurrency': 'BTC',
                'Status': 'executed',
                'DateAdded': datetime.datetime(2022, 11, 6, 10, 45, 25, 930000, tzinfo=datetime.timezone.utc)
            },
            {
                'Code': '203587899',
                'Type': 'buy',
                'Amount': 1115.3285116,
                'PendingAmount': 1115.3285116,
                'LimitPrice': 2.61e-07,
                'ListingCurrency': 'GRC',
                'ReferenceCurrency': 'BTC',
                'Status': 'booked',
                'DateAdded': datetime.datetime(2022, 11, 6, 12, 0, 9, 107000, tzinfo=datetime.timezone.utc)
            }
        ]
        """
        DATE_ADDED_KEY = "DateAdded"
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/getOrders",
            payload={
                "code": codes,
                "pageIndex": page_index,
                "pageSize": page_size
            },
            auth_required=True
        )
        orders = self.send_request(params)
        for order in orders:
            order[DATE_ADDED_KEY] = self._to_datetime(order[DATE_ADDED_KEY])
        return orders

    def generate_new_address(self, currency: str) -> dict:
        """
        Generates a new address for a given cryptocurrency.

        :param currency: Currency for which a new address will be generated.
        :return: New address data.

        :example:
        >>> client.generate_new_address('ETH')
        {
            'Id': 987654321,
            'Address': '0xce8b37b3b3e0347ff22a884e0df7f3b225112b27'
        }
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/generateNewAddress",
            payload={
                "currency": currency
            },
            auth_required=True
        )
        return self.send_request(params)

    def list_addresses(self, currency: str, page_index: int = 0, page_size: int = MAX_PAGE_SIZE) -> dict:
        """
        Lists addresses of a given currency.

        :param currency: Currency code.
        :param page_index: Page index.
        :param page_size: Page size. Maximum: 50.
        :return: Addresses data.

        :example:
        >>> client.list_addresses('ETH')
        {
            'TotalElements': 2,
            'Result': [
                {
                    'Id': 987654321,
                    'Address': '0xce8b37b3b3e0347ff22a884e0df7f3b225112b27'
                }, {
                    'Id': 987654322,
                    'Address': '0xce8b37b3b3e0347ff22a884e0df7f3b225112b28'
                }
            ]
        }
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/listAddresses",
            payload={
                "currency": currency,
                "pageIndex": page_index,
                "pageSize": page_size
            },
            auth_required=True
        )
        return self.send_request(params)

    def generate_ln_invoice(self, currency: str, amount: float) -> str:
        """
        Generates a new Lightning Network invoice for a given cryptocurrency. Permission required: Generate New Address

        :param currency: Currency code for which the invoice will be generated. Possible values: 'BTC', 'LTC'.
        :param amount: Invoice amount.
        :return: Payment request (invoice).

        :example:
        >>> client.generate_ln_invoice('LTC', 1.0)
        'lnbc20m1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqhp58yjmdan79s6...'
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/getLNInvoice",
            payload={
                "currency": currency,
                "amount": amount
            },
            auth_required=True
        )
        return self.send_request(params)

    def withdraw(self, currency: str, destination: str, destination_type: int, amount: float) -> dict:
        """
        Withdraws to a given address. Permission required: "Withdraw".

        :param currency: Currency code to withdraw.
        :param destination: The withdrawal destination address.
        :param destination_type: Destination type. Use constants defined in
         :class:`src.constants.WithdrawalDestinationTypes`.
        :param amount: Amount to withdraw. Destination address will receive this amount minus fees.
        :return: Withdrawal data.
        :example:
        >>> from sxc_api_client import WithdrawalDestinationTypes
        >>> client.withdraw('LTC', 'SOME_ADDRESS_HERE', WithdrawalDestinationTypes.CRYPTO_ADDRESS.value, 0.5)
        {
            'Status': 'ok',
            'Max': 0.29,
            'MaxDaily': 1.0,
            'MovementId': 9876543210
        }
        """
        params = self._get_request_params(
            method=requests.post,
            url=f"{self._BASE_URL}/withdraw",
            payload={
                "currency": currency,
                "destination": destination,
                "destinationType": destination_type,
                "amount": amount
            },
            auth_required=True
        )
        return self.send_request(params)

    def list_balances(self) -> list[dict]:
        """
        Lists non-zero balances for all currencies

        :return: Balances.
        :example:
        >>> client.list_balances()
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
                          page_size: int = MAX_PAGE_SIZE) -> dict:
        """
        Lists all transactions. Permission required: "List Balances".

        :param target_currency: Currency code.
        :param transaction_type: Transaction type. Refer to class :class:`src.constants.TransactionTypes`
            to get all allowed values. Note: If "transactions" is provided then trade transactions and buy fees are
            returned; if you want to get fee for sell order then you have to make a request once again with
            `target_currency` = reference currency and filter a response by relevant "TradeId".
            Though if transaction type "tradesbyordercode" is provided then the request will return matching trade
            transaction along with buy/sell trade fees.
        :param optional_filter: Optional filter. Possible values: the order code if transaction type is
            "tradesbyordercode"; the address ID if transaction type is "depositsbyaddressid".
        :param page_index: Page index.
        :param page_size: Page size. Maximum: 50.
        :return: Transactions data.

        :example:
        >>> from sxc_api_client import TransactionTypes
        >>> client.list_transactions(transaction_type=TransactionTypes.TRADES_BY_ORDER_CODE.value,
        ...                          optional_filter='199077234')
        {
            'TotalElements': 2,
            'Result': [
                {
                    'Date': datetime.datetime(2022, 11, 1, 20, 40, 5, 57000, tzinfo=datetime.timezone.utc),
                    'CurrencyCode': 'DASH',
                    'Amount': 0.0,
                    'TotalBalance': 30.91380084,
                    'Type': 'tradefee',
                    'Status': 'confirmed',
                    'Address': None,
                    'Hash': None,
                    'Price': 0.0,
                    'OtherAmount': 0.0,
                    'OtherCurrency': None,
                    'OrderCode': None,
                    'TradeId': 19737424,
                    'MovementId': None,
                    'TransactionId': 491636439
                },
                {
                    'Date': datetime.datetime(2022, 11, 1, 20, 40, 5, 57000, tzinfo=datetime.timezone.utc),
                    'CurrencyCode': 'DASH',
                    'Amount': 0.00000195,
                    'TotalBalance': 30.91380084,
                    'Type': 'trade',
                    'Status': 'confirmed',
                    'Address': None,
                    'Hash': None,
                    'Price': 0.002017385,
                    'OtherAmount': 0.000000003,
                    'OtherCurrency': 'BTC',
                    'OrderCode': '199077234',
                    'TradeId': 19737424,
                    'MovementId': None,
                    'TransactionId': 491636438
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
        if transaction_type in (TransactionTypes.TRADES_BY_ORDER_CODE, TransactionTypes.DEPOSITS_BY_ADDRESS_ID):
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

    @staticmethod
    def _to_datetime(datetime_str: str) -> datetime:
        """
        Convert datetime string to UTC-aware datetime object.

        :param datetime_str: Datetime string.
        :return: UTC-aware datetime object.
        """
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

    def _raise_invalid_market_error(self):
        raise SxcInvalidMarketError("Market does not exist")
