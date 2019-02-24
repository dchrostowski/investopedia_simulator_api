import json
from IPython import embed

from investopedia_api import InvestopediaSimulatorAPI
from api_models import *

# cookie should look like {auth_cookie:'abcdabcd1234...'}
with open('auth_cookie.json') as ifh:
    cookie = json.load(ifh)

# Instantiate as you see fit, doesn't need to be a keywork arg
client = InvestopediaSimulatorAPI(**cookie)
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

picks = ['ENSG','DMLP','XLNX','CSWI','FCAP','RH','KL','FF','FTNT','MLR','ACNB','FNKO','IRBT','CDNS']


print("START TRADE STUFF")
print("----------------------")
quote = client.get_quote('FCAP')
print(quote)



#td = OrderDuration.GOOD_TILL_CANCELLED()
#ot = OrderType('Market')
#tt = TransactionType.STOCK_BUY()

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
            prepped_trade.execute()
        else:
            print("Couldn't find %s" % pick)