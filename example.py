import json

from investopedia_api import InvestopediaSimulatorAPI

# cookie should look like {auth_cookie:'abcdabcd1234...'}
with open('auth_cookie.json') as ifh:
    cookie = json.load(ifh)

# Instantiate as you see fit, doesn't need to be a keywork arg
client = InvestopediaSimulatorAPI(**cookie)
portfolio = client.stock_portfolio

print("Default (active) game: %s" % client.active_game)
print("Portfolio total value: %s" % portfolio.total_value)
for holding in portfolio:
    print("\nStock symbol: %s (%s)" % (holding.stock.symbol, holding.stock.url))
    print("Start price: %s" % holding.start)
    print("Current price: %s" % holding.current)
    print("Net return: %s\n" % holding.net_return)