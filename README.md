# investopedia simulator api

## Description
A simple Python API for Investopedia's stock simulator games.  

## Features
This is very much a work-in-progress. Very messy and unusuabe currently. I'm throwing around some designs. Trading long and short positions currently works quite nicely, but everything else needs an overhaul.

## Authentication
Investopedia put a recaptcha puzzle thing on their login page.  This was pretyt easily circumvented by including a session cookie in the http request.  The session cookie has the name UI4 and just needs to be passed in to the class method of the Session singleton.  (I'm probably going to change it from a singleton and use a class decorator or instance variable or something.)

### Security considerations
**Don't fork this repo and publish your cookie for the whole world to see.  Anyone with that string can access your account.**  For your convenience I added auth_cooke.json to .gitignore.  If you plan on forking this to a publicly accessible repository then you should probably put your cookie in that untracked file and read from it.
  
## Example
### code
import json
from IPython import embed

from investopedia_api import InvestopediaSimulatorAPI
from api_models import *

with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)

"""
I have multiple accounts so I parse the json to a dict which looks like this:
{
    "default": '1234cookievalabcdabcd1234',
    'account1': '6754cookievaldefgdefg1234',
    ...
}

"""
# Instantiate as you see fit, just needs a string of the UI4 cookie value.
client = InvestopediaSimulatorAPI(cookies['default'])


q = client.get_quote('MSFT')
print("quote symbol: %s" % q.symbol)
print("quote comp name: %s" % q.name)
print("quote market price: %s " % q.last)
print("quote change (per share): %s " % q.change)
print("quote change (%%): %s " % q.change_percent)
print(q)

# How to do an option chain lookup
option_lookup_symbol = 'TEO'
print("doing an option chain lookup for %s" % option_lookup_symbol)
ocl = client.option_lookup(option_lookup_symbol)

# ocl.calls and ocl.puts are simply a list of available option contracts

call_option1 = ocl.calls[0]
call_option2 = ocl.calls[1]

put_option1 = ocl.puts[0]
put_option2 = ocl.puts[1]

print("strike price for first call option in chain: %s" %
      call_option1.strike_price)
print("expiration for first call option in chain: %s" %
      call_option1.expiration)
print("strike price for second call option in chain: %s" %
      call_option2.strike_price)
print("expiration for second call option in chain: %s" %
      call_option2.expiration)
print("\n\n")

print("strike price for first put option in chain: %s" %
      put_option1.strike_price)
print("expiration for first put option in chain: %s" % put_option1.expiration)
print("strike price for second put option in chain: %s" %
      put_option2.strike_price)
print("expiration for second put option in chain: %s" % put_option2.expiration)




# The simplest way is to use strings
trade1 = StockTrade(
    stock='GOOG',
    quantity=10,
    transaction_type='buy',
    order_type='market',
    order_duration='good_till_cancelled',
    sendEmail=True
)

# These can also be changed prior to callling the validate() method
trade1.quantity  = 20
trade1.transaction_type = 'sell_short'
trade1.order_duration = 'day_order'
trade1.order_type = OrderType.MARKET()

validated1 = trade1.validate()
print(validated1)
validated1.execute()

quote = client.get_quote('AAPL')
qty_shares_to_buy = int(3200 / quote.last)
# can also pass in a Quote object to more easily calculate how many shares you want to trade
trade2 = StockTrade(
    stock=quote, 
    quantity=10,
    # StockTrade can also take special object instances defined in stock_trade (see stock_trade.py)
    transaction_type=TransactionType.BUY(),
    order_type=OrderType.MARKET(),
    order_duration=OrderDuration.GOOD_TILL_CANCELLED(),
    sendEmail=True
)

validated2 = trade2.validate()
validated2.execute()

# This is to inteintionally trigger a TradeExceedsMaxSharesException (because simulator rules) which can be handled during the invocation of validate()
trade3 = StockTrade(
    stock='AMZN',
    quantity=9999999999999999999,
    transaction_type='buy',
    order_type='market',
    order_duration='good_till_cancelled',
    sendEmail=True
)
validated3 = None
try:
    validated3 = trade3.validate()
except TradeExceedsMaxSharesException as e:
    if e.max_shares > 0:
        trade3.quantity = e.max_shares
        print("trade3 set to %s shares" % trade3.quantity)
        validated3 = trade3.validate()
        print(validated3)
        validated3.execute()

## More Info / Documentation ##
This is a work in progress.  I'll add more documentation as I continue developing.  I also plan on making this a module and publishing to pip.
