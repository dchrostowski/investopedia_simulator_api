import json
from IPython import embed

from investopedia_api import InvestopediaSimulatorAPI
from api_models import *

# cookie should look like {"here I'm just using a json object with multiple cookies defined"}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)

# Instantiate as you see fit, doesn't need to be a keywork arg
client = InvestopediaSimulatorAPI(cookies['default'])
portfolio = client.stock_portfolio


print("Default (active) game: %s" % client.active_game)
print("Portfolio total value: %s" % portfolio.total_value)
for holding in portfolio:
    print("\nStock symbol: %s (%s)" % (holding.security.symbol, holding.security.url))
    print("Start price: %s" % holding.start)
    print("Current price: %s" % holding.current)
    print("Net return: %s\n" % holding.net_return)

q = client.get_quote('AAPL')
print("quote symbol: %s" % q.symbol)
print("quote comp name: %s" % q.name)
print("quote market price: %s " % q.last)
print("quote change (per share): %s " % q.change)
print("quote change (%%): %s " % q.change_percent)
print(q)

"""
q2 = client.get_quote('AMZN')
print(q2)

p = client.stock_portfolio
print("portfolio annual %% return: %s" % p.annual_return_pct)
print("cash: %s" % p.cash)
print("buying power: %s" % p.buying_power)
"""

picks = ['GOOG','AAPL','AMZN']


print("START TRADE STUFF")
print("----------------------")
quote = client.get_quote('FCAP')
print(quote)

# How to do an option chain lookup
option_lookup_symbol = 'TEO'
print("doing an option chain lookup for %s" % option_lookup_symbol)
ocl = client.option_lookup(option_lookup_symbol)

 # ocl.calls and ocl.puts are simply a list of available option contracts

call_option1 = ocl.calls[0]
call_option2 = ocl.calls[1]

put_option1 = ocl.puts[0]
put_option2 = ocl.puts[1]

print("strike price for first call option in chain: %s" % call_option1.strike_price)
print("expiration for first call option in chain: %s" % call_option1.expiration)
print("strike price for second call option in chain: %s" % call_option2.strike_price)
print("expiration for second call option in chain: %s" % call_option2.expiration)
print("\n\n")

print("strike price for first put option in chain: %s" % put_option1.strike_price)
print("expiration for first put option in chain: %s" % put_option1.expiration)
print("strike price for second put option in chain: %s" % put_option2.strike_price)
print("expiration for second put option in chain: %s" % put_option2.expiration)


for pick in picks:
    stocks = portfolio.find_by_symbol(pick)
    if len(stocks) > 0:
        print("already own or have an order in for %s" % stocks[0].security)
    else:
        quote = client.get_quote(pick)
        if quote:
            qty_shares_to_buy = int(3200 / quote.last)
            trade = StockTrade(
                stock=quote,
                quantity=qty_shares_to_buy,
                transaction_type=TransactionType.STOCK_BUY(), 
                order_type=OrderType.MARKET(),
                order_duration=OrderDuration.GOOD_TILL_CANCELLED(),
                sendEmail=True
            )

            prepped_trade = client.prepare_trade(trade)
            print(prepped_trade)
            # uncomment to execute the trade
            #prepped_trade.execute()
        else:
            print("Couldn't find %s" % pick)