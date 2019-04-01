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

print('-------------------------')
for pos in client.portfolio.find('TEVA'):
    print(pos.__dict__)


for pos in client.portfolio.option_portfolio.find('TEVA'):
    print(pos.__dict__)

for pos in client.portfolio.stock_portfolio.find('TMO'):
    print(pos.__dict__)
print("---------------------------")




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
