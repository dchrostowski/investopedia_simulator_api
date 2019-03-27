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
# Instantiate as you see fit, just needs a string of the cookie value.
client1 = InvestopediaSimulatorAPI(cookies['aggregate'])
client2 = InvestopediaSimulatorAPI(cookies['default'])


portfolio1 = client1.stock_portfolio
portfolio2 = client2.stock_portfolio

print(portfolio1.cash)
print(portfolio2.cash)
embed()


print("Default (active) game: %s" % client.active_game)
print("Portfolio total value: %s" % portfolio.total_value)
for holding in portfolio:
    print("\nStock symbol: %s (%s)" %
          (holding.security.symbol, holding.security.url))
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

p = client.stock_portfolio
print("portfolio annual %% return: %s" % p.annual_return_pct)
print("cash: %s" % p.cash)
print("buying power: %s" % p.buying_power)

picks = ['GOOG', 'AAPL', 'AMZN']

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

trades = []
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
                transaction_type=TransactionType.BUY(),
                order_type=OrderType.MARKET(),
                order_duration=OrderDuration.GOOD_TILL_CANCELLED(),
                sendEmail=True
            )

            trades.append(trade)

        else:
            print("Couldn't find %s" % pick)

# Trade can also take strings ()
trade2 = StockTrade(
    stock='GRMN',
    quantity=10,
    transaction_type='buy',
    order_type='market',
    order_duration='good_till_cancelled',
    sendEmail=True
)

# This is to inteintionally trigger a TradeExceedsMaxSharesException which gets handled below
trade3 = StockTrade(
    stock='CYBR',
    quantity=9999999999999999999,
    transaction_type='buy',
    order_type='market',
    order_duration='good_till_cancelled',
    sendEmail=True
)

# Can change the trade like so:

trade2.transaction_type = 'sell_short'
# alternatively can do this:
# trade2.transaction_type = TransactionType.SELL_SHORT()

# modifying the order type with a string is not supported because order types can get complicated
trade2.order_type = OrderType.LIMIT(10.61)

trade2.order_duration = 'day_order'
# can also do this:
# trade2.order_duration = OrderDuration.DAY_ORDER()

trades.append(trade2)
trades.append(trade3)
prepped_trades = []

for trade in trades:
    print("------------------------------\npreparing:")
    try:
        validated = trade.validate()
    except TradeExceedsMaxSharesException as max_shares_error:
        max_shares = max_shares_error.max_shares
        if max_shares > 0:
            print("Adjusting trade for %s." % trade.symbol)
            trade.quantity = max_shares_error.max_shares
            validated_trade = trade.validate()

    print(validated)
    validated.execute()
    # uncomment to execute the trade
    # validated.execute()
