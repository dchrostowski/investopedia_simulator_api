## Description
A simple Python API for Investopedia's stock simulator games.  

## Features
Currently you can:
* Read all positions in your option, stock, and short portfolios
* Buy/Sell long positions
* Short sell/cover short positions
* Perform option chain lookups
* Buy/sell options
* Read pending/open trades

Todo:
* Setting the default game, changing games
* Whatever else I can think of


## Authentication
Simply pass a dict to InvetopediaAPI constructor with a username and password.  
```
from investopedia_api import InvestopediaApi
credentials = {"username" "youremail@example.org", "password": "your password"}
client = InvestopediaAPI(credentials)
p = client.portfolio
print("account value: %s" % p.account_value)
```

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

credentials = {}
with open('credentials.json') as ifh:
    credentials = json.load(ifh)

# look at credentials_example.json
# credentials = {"username": "you@example.org", "password": "yourpassword"}
client = InvestopediaApi(credentials)

p = client.portfolio
print("account value: %s" % p.account_value)
print("cash: %s" % p.cash)
print("buying power: %s" % p.buying_power)
print("annual return pct: %s" % p.annual_return_pct)

# get a quote
quote = client.get_stock_quote('GOOG')
print(quote.__dict__)

# Read your portfolio
long_positions = client.portfolio.stock_portfolio
short_positions = client.portfolio.short_portfolio
my_options = client.portfolio.option_portfolio

# Place a buy order for 10 shares of Google with a limit of $1000/share

# shorthand for client.TradeProperties.TradeType.BUY()
trade_type = 'buy'

#shorthand for client.TradeProperties.OrderType.LIMIT(1000)
limit_1000 = 'limit 1000'

trade = client.StockTrade('GOOG',10,trade_type,order_type=limit_1000)
trade_info = trade.validate()
if trade.validated:
    print(trade_info)
    trade.execute()

# See example.py for more examples.
```

## More Info / Documentation ##
This is a work in progress.  I'll add more documentation as I continue developing.  I also plan on making this a module and publishing to pip.
