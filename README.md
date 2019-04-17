## Description
A simple Python API for Investopedia's stock simulator games.  

## Features
This is very much a work-in-progress. However, currently you can:
* Read all positions in your option, stock, and short portfolios
* Buy/Sell long positions
* Short sell/cover short positions
* Submit trade orders - buy long positions, sell short positions
* Perform option chain lookups

To implement:
* Options trading
* Read pending/open trades
* Setting the default game, changing games
* Whatever else I can think of


## Authentication
Investopedia put a recaptcha puzzle thing on their login page.  This was easily circumvented by getting a human being to solve the captcha. After clicking on traffic lights 0-67 times, you will finally see the cookie.  Just copy the value and pass it to the InvestopediaSimulatorAPI constructor. 
### Security considerations
**Don't fork this repo and publish your cookie for the whole world to see.  Anyone with that string can access your account.**  For your convenience I added auth_cooke.json to .gitignore.  If you plan on forking this to a publicly accessible repository then you should probably put your cookie in that untracked file and read from it.

## Environment
Python 3.6.7.  I just use a virtualenv and install using pip from requirements.txt.  If you don't know how to do that:

```
git clone https://github.com/dchrostowski/investopedia_simulator_api.git
cd investopedia_simulator_api
pip install virtualenv
virtualenv -p /path/to/python3 ./venv
source venv/bin/activate
pip install -r requirements.txt
python exmaple.py
```

## Example
### code
```
from investopedia_api import InvestopediaApi
import json

cookies = {}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)
auth_cookie = cookies['streetscrape_test']
# pass the value of the UI4 cookie after logging in to the site.
client = InvestopediaApi(auth_cookie)

p = client.portfolio
print("account value: %s" % p.account_value)
print("cash: %s" % p.cash)
print("buying power: %s" % p.buying_power)
print("annual return pct: %s" % p.annual_return_pct)

# get a quote
quote = client.get_stock_quote('GOOG')
print(quote.__dict__)

# option chain lookup
chain = client.get_option_chain('AAPL')
calls = chain.calls
puts = chain.puts
print(calls[0].__dict__)
print(puts[0].__dict__)


# Read your portfolio
long_positions = client.portfolio.stock_portfolio
short_positions = client.portfolio.short_portfolio
my_options = client.portfolio.option_portfolio

for pos in long_positions:
    print("--------------------")
    print(pos.symbol)
    print(pos.purchase_price)
    print(pos.current_price)
    print(pos.change)
    print(pos.total_value)

    # This gets a quote with addtional info like volume
    quote = pos.quote
    print(quote.__dict__)
    print("---------------------")

for pos in short_positions:
    print("--------------------")
    print(pos.symbol)
    print(pos.purchase_price)
    print(pos.current_price)
    print(pos.change)
    print(pos.total_value)

    # This gets a quote with addtional info like volume
    quote = pos.quote
    print(quote.__dict__)
    print("---------------------")

for pos in my_options:
    print("--------------------")
    print(pos.symbol)
    print(pos.purchase_price)
    print(pos.purchase_price)
    print(pos.current_price)
    print(pos.strike_price)
    print(pos.expiration)
    print(pos.total_value)
    print("---------------------")

if len(long_positions) > 0:
    # Generates a trade to sell all owned shares of position
    trade = long_positions[0].sell()
    # validate the trade
    validated = trade.validate()
    print(validated)
    # place the order
    # validated.execute()

if len(short_positions) > 0:
    # generates a trade that will cover a shorted position
    trade = short_positions[0].cover()
    validated = trade.validate()
    print(validated)
    # validated.execute()

if len(my_options) > 0:
    pos = my_options[-1]
    # This will pull in additonal details for the option like bid,ask,etc if not expired
    quote = pos.quote
    print(quote.__dict__)

# options trading coming soon.

# construct a trade (see stock_trade.py for a hint)
trade = client.StockTrade.Trade(symbol='GOOG',quantity=10,trade_type='buy',order_type='market',duration='good_till_cancelled',send_email=True) 
# validate the trade
validated = trade.validate()
print(validated)

# change the trade to a day order
trade.duration = 'day_order'
# Another way to change the trade to a day order
trade.duration = client.StockTrade.Duration.DAY_ORDER()

# make it a limit order
trade.order_type = 'limit 20.00'
# alternate way
trade.order_type = client.StockTrade.OrderType.LIMIT(20.00)

# validate it, see changes:
validated = trade.validate()
print(validated)

# submit the order
# validated.execute()
```

### Output
```
(inv_env) dan@bohr:~/git/investopedia_simulator_api$ python example.py 
account value: 106983.64
cash: 77601.01
buying power: 59510.73
annual return pct: 106.41
{'symbol': 'GOOG', 'name': 'ALPHABET INC. CLASS C', 'last': Decimal('1173.3100'), 'exchange': 'NASDAQ', 'change': Decimal('13.17'), 'change_percent': Decimal('1.11'), 'volume': 1269971}
{'raw': {'Year': 2019, 'Month': 4, 'AskSize': 1, 'Ask': 67.3, 'BidSize': 10, 'Bid': 62.85, 'PercentChange': 0, 'Change': 0, 'PreviousClose': 64.58, 'OpenInterest': 8, 'Volume': 2, 'Low': 64.58, 'High': 64.58, 'Close': 64.58, 'Open': 64.58, 'LastSize': 2, 'Last': 64.58, 'StrikePrice': 125, 'InTheMoney': True, 'Delay': 0, 'Outcome': 'Success', 'Type': 'Call', 'Exchange': 'OPRA', 'AskTime': '4:23:12 PM', 'AskDate': '3/29/2019', 'BidTime': '4:23:12 PM', 'BidDate': '3/29/2019', 'PreviousCloseDate': '3/29/2019', 'OpenInterestDate': '3/29/2019', 'Time': '2:39:47 PM', 'Date': '3/29/2019', 'Currency': 'USD', 'ExpirationDate': '4/5/2019', 'BaseSymbol': 'AAPL', 'SymbologyType': 'DTNSymbol', 'Symbol': 'AAPL1905D125', 'Identity': None, 'Message': 'Delay times are 15 mins for OPRA.'}, 'contract_name': 'AAPL1905D125', 'base_symbol': 'AAPL', 'contract_type': 'Call', 'expiration': datetime.datetime(2019, 4, 5, 0, 0), 'strike_price': 125, 'last': 64.58, 'bid': 62.85, 'ask': 67.3, 'volume': 2, 'open_int': 8}
{'raw': {'Year': 2019, 'Month': 4, 'AskSize': 18, 'Ask': 0.01, 'BidSize': 5, 'Bid': 0.01, 'PercentChange': 0, 'Change': 0, 'PreviousClose': 0.01, 'OpenInterest': 321, 'Volume': 195, 'Low': 0.01, 'High': 0.01, 'Close': 0.01, 'Open': 0.01, 'LastSize': 45, 'Last': 0.01, 'StrikePrice': 125, 'InTheMoney': False, 'Delay': 0, 'Outcome': 'Success', 'Type': 'Put', 'Exchange': 'OPRA', 'AskTime': '4:06:16 PM', 'AskDate': '3/29/2019', 'BidTime': '3:36:13 PM', 'BidDate': '3/11/2019', 'PreviousCloseDate': '3/18/2019', 'OpenInterestDate': '3/29/2019', 'Time': '11:29:15 AM', 'Date': '3/18/2019', 'Currency': 'USD', 'ExpirationDate': '4/5/2019', 'BaseSymbol': 'AAPL', 'SymbologyType': 'DTNSymbol', 'Symbol': 'AAPL1905P125', 'Identity': None, 'Message': 'Delay times are 15 mins for OPRA.'}, 'contract_name': 'AAPL1905P125', 'base_symbol': 'AAPL', 'contract_type': 'Put', 'expiration': datetime.datetime(2019, 4, 5, 0, 0), 'strike_price': 125, 'last': 0.01, 'bid': 0.01, 'ask': 0.01, 'volume': 195, 'open_int': 321}
--------------------
TMO
269.75
273.72
3.97
1094.88
{'symbol': 'TMO', 'name': 'THERMO FISHER SCIENTIFIC INC.', 'last': Decimal('273.7200'), 'exchange': 'NYSE', 'change': Decimal('37.35'), 'change_percent': Decimal('15.80'), 'volume': 1193810}
---------------------
--------------------
WLTW
176.96
175.65
-1.31
6147.75
{'symbol': 'WLTW', 'name': 'WILLIS TOWERS WATSON PUBLIC LIMITED COMPANY', 'last': Decimal('175.6500'), 'exchange': 'NASDAQ', 'change': Decimal('27.91'), 'change_percent': Decimal('18.89'), 'volume': 745442}
---------------------
--------------------
BLL
58.30
57.86
-0.44
3471.60
{'symbol': 'BLL', 'name': 'BALL CORPORATION', 'last': Decimal('57.8600'), 'exchange': 'NYSE', 'change': Decimal('15.91'), 'change_percent': Decimal('37.93'), 'volume': 2795432}
---------------------
--------------------
TEVA
16.22
15.68
0.54
12544.00
{'symbol': 'TEVA', 'name': 'TEVA PHARMACEUTICAL INDUSTRIES LIMITED SPONSORED ADR', 'last': Decimal('15.6800'), 'exchange': 'NYSE', 'change': Decimal('6.96'), 'change_percent': Decimal('30.74'), 'volume': 8785184}
---------------------
--------------------
CPS
49.28
46.96
2.32
939.20
{'symbol': 'CPS', 'name': 'COOPER-STANDARD HOLDINGS INC.', 'last': Decimal('46.9600'), 'exchange': 'NYSE', 'change': Decimal('89.95'), 'change_percent': Decimal('65.70'), 'volume': 163446}
---------------------
--------------------
ADNT
12.68
12.96
-0.28
1036.80
{'symbol': 'ADNT', 'name': 'ADIENT PLC', 'last': Decimal('12.9600'), 'exchange': 'NYSE', 'change': Decimal('28.68'), 'change_percent': Decimal('68.88'), 'volume': 1500673}
---------------------
--------------------
FBK
31.44
31.76
-0.32
1111.60
{'symbol': 'FBK', 'name': 'FB FINANCIAL CORPORATION', 'last': Decimal('31.7600'), 'exchange': 'NYSE', 'change': Decimal('12.32'), 'change_percent': Decimal('27.95'), 'volume': 35290}
---------------------
--------------------
STKL1915O5
0.95
0.95
0.95
5.0
2019-03-15
950.00
---------------------
--------------------
CURO1915O10
0.50
0.50
0.50
10.0
2019-03-15
50.00
---------------------
--------------------
UNIT1915O10
2.00
2.00
1.80
10.0
2019-03-15
1800.00
---------------------
--------------------
MAXR1918P7.5
3.10
3.10
3.30
7.5
2019-04-18
1650.00
---------------------
--------------------
INWK1918P2.5
0.05
0.05
0.05
2.5
2019-04-18
95.00
---------------------
--------------------
KHC1918P32.5
0.92
0.92
0.45
32.5
2019-04-18
2025.00
---------------------
--------------------
ADNT1918P16
2.00
2.00
2.60
16.0
2019-04-18
1300.00
---------------------
--------------------
CPS1918P55
3.80
3.80
6.10
55.0
2019-04-18
3050.00
---------------------
--------------------
DF1918P3
0.35
0.35
0.15
3.0
2019-04-18
75.00
---------------------
--------------------
OMI1918P5
1.00
1.00
0.35
5.0
2019-04-18
350.00
---------------------
--------------------
RLGY1918P12.5
0.95
0.95
1.15
12.5
2019-04-18
1150.00
---------------------
--------------------
DPLO1918P7.5
2.10
2.10
1.65
7.5
2019-04-18
1650.00
---------------------
--------------------
HZN1918P2.5
0.40
0.40
0.50
2.5
2019-04-18
50.00
---------------------
--------------------
CCRN1918P7.5
0.41
0.41
0.15
7.5
2019-04-18
15.00
---------------------
--------------------
CEL1918D5
0.10
0.10
0.05
5.0
2019-04-18
50.00
---------------------
{'Description': 'TMO', 'Transaction': 'Stock: Sell at Market Open', 'StopLimit': 'n/a', 'Duration': 'Good Till Cancelled', 'Price': '$273.72', 'Quantity': '4', 'Commision': '$14.99', 'Est_Total': '$1,079.89'}
{'Description': 'TEVA', 'Transaction': 'Cover Stock: Cover at Market Open', 'StopLimit': 'n/a', 'Duration': 'Good Till Cancelled', 'Price': '$15.68', 'Quantity': '800', 'Commision': '$14.99', 'Est_Total': '$12,558.99'}
{'raw': {'Year': 2019, 'Month': 4, 'AskSize': 240, 'Ask': 0.25, 'BidSize': 9, 'Bid': 0.05, 'PercentChange': 0, 'Change': 0, 'PreviousClose': 0.05, 'OpenInterest': 42, 'Volume': 2, 'Low': 0.03, 'High': 0.05, 'Close': 0.05, 'Open': 0.03, 'LastSize': 1, 'Last': 0.05, 'StrikePrice': 5, 'InTheMoney': False, 'Delay': 0, 'Outcome': 'Success', 'Type': 'Call', 'Exchange': 'OPRA', 'AskTime': '3:49:47 PM', 'AskDate': '3/29/2019', 'BidTime': '9:40:44 AM', 'BidDate': '3/19/2019', 'PreviousCloseDate': '3/19/2019', 'OpenInterestDate': '3/29/2019', 'Time': '9:40:44 AM', 'Date': '3/19/2019', 'Currency': 'USD', 'ExpirationDate': '4/18/2019', 'BaseSymbol': 'CEL', 'SymbologyType': 'DTNSymbol', 'Symbol': 'CEL1918D5', 'Identity': None, 'Message': 'Delay times are 15 mins for OPRA.'}, 'contract_name': 'CEL1918D5', 'base_symbol': 'CEL', 'contract_type': 'Call', 'expiration': datetime.datetime(2019, 4, 18, 0, 0), 'strike_price': 5, 'last': 0.05, 'bid': 0.05, 'ask': 0.25, 'volume': 2, 'open_int': 42}
{'Description': 'GOOG', 'Transaction': 'Stock: Buy at Market Open', 'StopLimit': 'n/a', 'Duration': 'Good Till Cancelled', 'Price': '$1,173.31', 'Quantity': '10', 'Commision': '$14.99', 'Est_Total': '$11,748.09'}
{'Description': 'GOOG', 'Transaction': 'Stock: Buy at Limit', 'StopLimit': '$20.00', 'Duration': 'Day Order', 'Price': '$20.00', 'Quantity': '10', 'Commision': '$24.99', 'Est_Total': '$224.99'}
```

## More Info / Documentation ##
This is a work in progress.  I'll add more documentation as I continue developing.  I also plan on making this a module and publishing to pip.
