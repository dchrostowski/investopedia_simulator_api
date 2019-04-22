## Description
A simple Python API for Investopedia's stock simulator games.  

## Features
This is very much a work-in-progress. However, currently you can:
* Read all positions in your option, stock, and short portfolios
* Buy/Sell long positions
* Short sell/cover short positions
* Submit trade orders - buy long positions, sell short positions
* Perform option chain lookups
* See branch devel/options_trading_2 for options trading (will be merged soon.)

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
auth_cookie = cookies['account_cookie']
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
