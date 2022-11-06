# SouthXChange Python API Client
`SxcAPIClient` is a simple Python wrapper around SouthXChange API implementing all the requests as described in [official documentation](https://main.southxchange.com/Content/swagger/ui/?urls.primaryName=API%20v4#/).
API v4 is supported so far.

## Table of contents
* [Quick start](#quick_start)
  * [Installation](#installation)
  * [Usage](#usage)
* [Requests](#requests)
  * [Public data](#public_data)
    * [List markets](#list_markets)
    * [Get price](#get_price)
    * [List prices](#list_prices)
    * [List market history](#list_market_history)
    * [List market history by granularity](#scroll_market_history_by_granularity)
    * [List order book](#list_order_book)
    * [List trades](#list_trades)
    * [List fees](#list_fees)
  * [Private data](#private_data)
    * [Get user info](#get_user_info)
    * [List wallets](#list_wallets)
    * [Place order](#place_order)
    * [Cancel order](#cancel_order)
    * [Cancel market orders](#cancel_market_orders)
    * [List pending orders](#list_pending_orders)
    * [Get order](#get_order)
    * [List orders by codes](#list_orders_by_codes)
    * [Generate new address](#generate_new_address)
    * [List addresses](#list_addresses)
    * [Generate Lightning Network invoice](#generate_ln_invoice)
    * [Withdraw](#withdraw)
    * [List balances](#list_balances)
    * [List transactions](#list_transactions)


<a name="quick_start"></a>
## Quick start
<a name="installation"></a>
### Installation
```commandline
pip3 install sxc-api-client
```
<a name="usage"></a>
### Usage
Querying publicly available data is as simple as that:
```python
from sxc_api_client import SxcApiClient
client = SxcApiClient()
markets = client.list_markets()
```
If you are going to have a deal with private data as well (i.e. bound to a specific account) you have to provide your API access and secret keys:
```python
from sxc_api_client import SxcApiClient
client = SxcApiClient("your_access_key", "your_secret_key")
orders = client.list_pending_orders()
```

<a name="requests"></a>
## Requests
<a name="public_data"></a>
### Public data

---

<a name="list_markets"></a>
#### list_markets()
Lists all markets.
* **Returns**

    Markets.


* **Example**
```python
>>> client.list_markets()
[
    ['DASH', 'BTC', 5],
    ['LTC', 'BTC', 7]
]
```

---

<a name="get_price"></a>
#### get_price(target_currency: str, reference_currency: str)
Gets price of a given market.


* **Parameters** 
    * **target_currency** – Listing currency code.
    * **reference_currency** – Reference currency code.


* **Returns**

    Price of a given market.


* **Example**


```python
>>> client.get_price('CRW', 'BTC')
{
    'Bid': 0.067417841,
    'Ask': 0.067808474,
    'Last': 0.068148556,
    'Variation24Hr': -8.38,
    'Volume24Hr': 2.63158984
}
```

---

<a name="list_prices"></a>
#### list_prices()
Lists prices of all markets.


* **Returns**

    Market prices.


* **Example**
```python
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
```

---

<a name="list_market_history"></a>
#### list_market_history(target_currency: str, reference_currency: str, start_ts: int | float, end_ts: int | float, periods: int)
List market history between two dates. Please keep in mind it is strongly recommended to pass `start_ts` and
`end_ts` so that difference between them is aliquot to `periods`; otherwise unexpected data may be
returned without any warning. Besides, as a rule of thumb consider that the value of statement
`(end_ts - start) / periods` should be equal to one of the values defined in
`sxc_api_client.constants.MarketHistoryIntervals`. Hopefully those restrictions will be eliminated in
SouthXChange API.


* **Parameters** 
    * **target_currency** – Listing currency code.
    * **reference_currency** – Reference currency code.
    * **start_ts** – Start timestamp from January 1, 1970.
    * **end_ts** – End timestamp from January 1, 1970.
    * **periods** – Number of periods to get. Limited to 500; if bigger value is provided API silently resets it to 500.


* **Returns**

    Market history.


* **Example**

```python
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
```

---

<a name="scroll_market_history_by_granularity"></a>
#### scroll_market_history_by_granularity(target_currency: str, reference_currency: str, start_ts: int | float, end_ts: int | float, granularity: int, \*\*kwargs)
List market history between two dates with given granularity. A handier version of
`src.client.SxcApiClient.list_market_history()`


* **Parameters**
    * **target_currency** – Listing currency code.
    * **reference_currency** – Reference currency code.
    * **start_ts** – Start timestamp from January 1, 1970.
    * **end_ts** – End timestamp from January 1, 1970.
    * **granularity** – Interval in seconds. Use constants defined in `sxc_api_client.constants.MarketHistoryIntervals`.
    * **strict_mode** – Raise exception if granularity in a response does not match the given one.
    Such a case is possible when either (1) arbitrary granularity (except values defined in
    `sxc_api_client.constants.MarketHistoryIntervals`) is provided or (2) currency pair was listed on the market
    after the given start_ts or (3) end_ts is relatively far in the future. Defaults to True.


* **Returns**

    Market history.


* **Example**

```python
>>> from sxc_api_client import MarketHistoryIntervals
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
```

---

<a name="list_order_book"></a>
#### list_order_book(target_currency: str, reference_currency: str)
Lists order book of a given market.


* **Parameters** 
    * **target_currency** – Listing currency code.
    * **reference_currency** – Reference currency code.


* **Returns**

    Order book.


* **Example**
```python
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
```

---

<a name="list_trades"></a>
#### list_trades(target_currency: str, reference_currency: str)
Lists the latest trades in a given market.


* **Parameters**
    * **target_currency** – Listing currency code.
    * **reference_currency** – Reference currency code.


* **Returns**

    Latest trades.


* **Example**
```python
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
```

---

<a name="list_fees"></a>
#### list_fees()
Get general information about currencies, markets, trader levels and their fees.


* **Returns**

    Fees data.


* **Example**
```python
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
```

<a name="private_data"></a>
### Private data

---

<a name="get_user_info"></a>
#### get_user_info()
Get user information (level). Use `SxcApiClient.list_fees()` to retrieve actual fees applicable to user
level.


* **Returns**

    User information.


* **Example**
```python
>>> client.get_user_info()
{'TraderLevel': 'TraderLevel1'}
```

---

<a name="list_wallets"></a>
#### list_wallets()
Retrieves the status for all wallets.


* **Returns**

    Wallets information.


* **Example**
```python
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
```

---

<a name="place_order"></a>
#### place_order(target_currency: str, reference_currency: str, order_type: str, amount: float, limit_price: float, amount_in_reference_currency: bool = False)
Places an order in a given market.


* **Parameters**
    * **target_currency** – Market listing currency.
    * **reference_currency** – Market reference currency.
    * **order_type** – Order type. Possible values: “buy”, “sell”. Use constants defined in
    `sxc_api_client.constants.OrderTypes`.
    * **amount** – Order amount in listing currency.
    * **limit_price** – Optional price in reference currency. If None then order is executed at market price.
    * **amount_in_reference_currency** – True if order amount is in reference currency; defaults to False.


* **Returns**

    Order code.


* **Example**

```python
>>> from sxc_api_client.constants import OrderTypes
>>> client.place_order('ETH', 'BTC', OrderTypes.BUY.value, 0.01, 0.068344600)
'64065725'
```

---

<a name="cancel_order"></a>
#### cancel_order(order_code: str)
Cancels a given order.


* **Parameters**

    * **order_code** – Order code.


* **Returns**

    None


* **Example**


```python
>>> client.cancel_order('60000000')
```

---

<a name="cancel_market_orders"></a>
#### cancel_market_orders(target_currency: str, reference_currency: str)
Cancels all orders in a given market.


* **Parameters**
  * **target_currency** – Market listing currency.
  * **reference_currency** – Market reference currency.


* **Returns**

    None


* **Example**
```python
>>> client.cancel_market_orders('ETC', 'BTC')
```

---

<a name="list_pending_orders"></a>
#### list_pending_orders()
Lists all pending orders.


* **Returns**

    Pending orders.


* **Example**
```python
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
    }, {
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
```

---

<a name="get_order"></a>
#### get_order(code: str)
Gets a given order.


* **Parameters**
  * **code** – Order code to get.


* **Returns**

    Order data.


* **Example**
```python
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
```

---

<a name="list_orders_by_codes"></a>
#### list_orders_by_codes(codes: list[str], page_index: int = 0, page_size: int = 50)
Lists orders by given codes.


* **Parameters** 
    * **codes** – Orders codes.
    * **page_index** – Page index.
    * **page_size** – Page size. Maximum: 50.


* **Returns**

    Orders data.


* **Example**
```python
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
```

---

<a name="generate_new_address"></a>
#### generate_new_address(currency: str)
Generates a new address for a given cryptocurrency.


* **Parameters**
  * **currency** – Currency for which a new address will be generated.


* **Returns**

    New address data.


* **Example**
```python
>>> client.generate_new_address('ETH')
{
    'Id': 987654321,
    'Address': '0xce8b37b3b3e0347ff22a884e0df7f3b225112b27'
}
```

---

<a name="list_addresses"></a>
#### list_addresses(currency: str, page_index: int = 0, page_size: int = 50)
Lists addresses of a given currency.


* **Parameters** 
    * **currency** – Currency code.
    * **page_index** – Page index.
    * **page_size** – Page size. Maximum: 50.


* **Returns**

    Addresses data.


* **Example**
```python
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
```

---

<a name="generate_ln_invoice"></a>
#### generate_ln_invoice(currency: str, amount: float)
Generates a new Lightning Network invoice for a given cryptocurrency. Permission required: Generate New Address


* **Parameters** 
    * **currency** – Currency code for which the invoice will be generated. Possible values: ‘BTC’, ‘LTC’.
    * **amount** – Invoice amount.


* **Returns**

    Payment request (invoice).


* **Example**
```python
>>> client.generate_ln_invoice('LTC', 1.0)
'lnbc20m1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqhp58yjmdan79s6...'
```

---

<a name="withdraw"></a>
#### withdraw(currency: str, destination: str, destination_type: int, amount: float)
Withdraws to a given address. Permission required: “Withdraw”.


* **Parameters** 
    * **currency** – Currency code to withdraw.
    * **destination** – The withdrawal destination address.
    * **destination_type** – Destination type. Use constants defined in
    `sxc_api_client.constants.WithdrawalDestinationTypes`.
    * **amount** – Amount to withdraw. Destination address will receive this amount minus fees.


* **Returns**

    Withdrawal data.


* **Example**

```python
>>> from sxc_api_client.constants import WithdrawalDestinationTypes
>>> client.withdraw('LTC', 'SOME_ADDRESS_HERE', WithdrawalDestinationTypes.CRYPTO_ADDRESS.value, 0.5)
{
    'Status': 'ok',
    'Max': 0.29,
    'MaxDaily': 1.0,
    'MovementId': 9876543210
}
```

---

<a name="list_balances"></a>
#### list_balances()
Lists non-zero balances for all currencies


* **Returns**

    Balances.


* **Example**
```python
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
```

---

<a name="list_transactions"></a>
#### list_transactions(target_currency: Optional[str] = None, transaction_type: str = 'transactions', optional_filter: Optional[int] = None, page_index: int = 0, page_size: int = 50)
Lists all transactions. Permission required: “List Balances”.


* **Parameters** 
    * **target_currency** – Currency code.
    * **transaction_type** – Transaction type. Refer to class `sxc_api_client.constants.TransactionTypes`
    to get all allowed values. Note: If “transactions” is provided then trade transactions and buy fees are
    returned; if you want to get fee for sell order then you have to make a request once again with
    target_currency = reference currency and filter a response by relevant “TradeId”.
    Though if transaction type “tradesbyordercode” is provided then the request will return matching trade
    transaction along with buy/sell trade fees.
    * **optional_filter** – Optional filter. Possible values: the order code if transaction type is
    “tradesbyordercode”; the address ID if transaction type is “depositsbyaddressid”.
    * **page_index** – Page index.
    * **page_size** – Page size. Maximum: 50.


* **Returns**

    Transactions data.


* **Example**

```python
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
        }, {
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
```