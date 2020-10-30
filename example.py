from investopedia_api import InvestopediaApi, TradeExceedsMaxSharesException
import json
import datetime

credentials = {}
with open('credentials.json') as ifh:
    credentials = json.load(ifh)
# look at credentials_example.json
# credentials = {"username": "you@example.org", "password": "yourpassword" }
client = InvestopediaApi(credentials)

p = client.portfolio

print("account value: %s" % p.account_value)
print("cash: %s" % p.cash)
print("buying power: %s" % p.buying_power)
print("annual return pct: %s" % p.annual_return_pct)

# get a quote
quote = client.get_stock_quote('GOOG')
print(quote.__dict__)



# option chain lookup
lookup = client.get_option_chain('MSFT')
# get all options expiring between the date range specified
for chain in lookup.search_by_daterange(datetime.datetime.now(), datetime.datetime(2100, 1, 1)):
    print("--------------------------------")
    print("calls expiring on %s" % chain.expiration_date_str)
    for call in chain.calls:
        print(call)
    print("puts expiring on %s" % chain.expiration_date_str)
    for put in chain.puts:
        print(put)
    print("--------------------------------")


option_contract = lookup.get('MSFT2217R80')
# order_type, duration, and send_email default to Market, Good Till Cancelled, and True respectively
option_trade = client.OptionTrade(
    option_contract, 10, trade_type='buy to open')
trade_info = None
try:
    trade_info = option_trade.validate()
except TradeExceedsMaxSharesException as e:
    option_trade.quantity = e.max_shares
    trade_info = option_trade.validate()
if option_trade.validated:
    print(trade_info)
    option_trade.execute()
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
    if quote is not None:
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

    try:
        print(quote.__dict__)
        print("---------------------")
    except Exception as e:
        print("bad quote for %s" % pos.symbol)

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

# sell a long position
if len(long_positions) > 0:
    # Generates a trade to sell all owned shares of position
    trade = long_positions[0].sell()
    # validate the trade
    trade_info = trade.validate()
    if trade.validated:
        print(trade_info)
        trade.execute()
    # place the order
    # validated.execute()

# cover a shorted position
if len(short_positions) > 0:
    # generates a trade that will cover a shorted position
    trade = short_positions[0].cover()
    trade_info = trade.validate()
    if trade.validated:
        print(trade_info)
        trade.execute()

# close out an option
if len(my_options) > 0:
    trade = None
    for option_position in my_options:
        if not option_position.is_expired:
            trade = option_position.close()
            trade_info = trade.validate()
            if trade.validated:
                print(trade_info)
                trade.execute()
            break


# construct a trade (see trade_common.py and stock_trade.py for a hint)
trade1 = client.StockTrade(symbol='GOOG', quantity=10, trade_type='buy',
                           order_type='market', duration='good_till_cancelled', send_email=True)
# validate the trade
trade_info = trade1.validate()
print(trade_info)

# change the trade to a day order
trade1.duration = 'day_order'
# Another way to change the trade to a day order
trade1.duration = client.TradeProperties.Duration.DAY_ORDER()

# make it a limit order
trade1.order_type = 'limit 20.00'
# alternate way
trade1.order_type = client.TradeProperties.OrderType.LIMIT(20.00)

# validate it, see changes:
trade_info = trade1.validate()
if trade1.validated:
    print(trade_info)
    trade1.execute()

# View open orders / pending trades
client.refresh_portfolio()
open_orders = client.open_orders

# cancel the first open order / pending trade
open_orders[0].cancel()
client.refresh_portfolio()
