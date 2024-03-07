from investopedia_api import InvestopediaApi, TradeExceedsMaxSharesException
import json
from datetime import datetime, timedelta
from trade_common import OrderLimit, TransactionType, Expiration, StockTrade,OptionTrade
import time
from options import OptionChain, OptionScope

credentials = {}
with open('credentials.json') as ifh:
    credentials = json.load(ifh)
# look at credentials_example.json
# credentials = {"username": "you@example.org", "password": "yourpassword" }
client = InvestopediaApi(credentials)

p = client.portfolio
print("\nPortfolio Details")
print("-------------------------------------------------")
print("Portfolio Value: %s" % p.account_value)
print("Cash: %s" % p.cash)
print("Buying Power: %s" % p.buying_power)
print("Annual Return Percent: %s" % p.annual_return_pct)
print("-------------------------------------------------")

print("\nOpen Orders:")
# To cancel a pending trade, run open_order.cancel()
for open_order in p.open_orders:
    print("-------------------------------------------------")
    print("Trade Type: %s" % open_order.trade_type)
    print("Symbol: %s" % open_order.symbol)
    print("Quantity: %s" % open_order.quantity)
    print("Price: %s" % open_order.order_price)
    print("-------------------------------------------------")
print("-------------------------------------------------")


stock_portfolio = p.stock_portfolio
short_portfolio = p.short_portfolio
option_portfolio = p.option_portfolio

print("\nStock Portfolio Details:")
print("-------------------------------------------------")
print("Market Value: %s" % p.stock_portfolio.market_value)
print("Today's Gain: %s (%s%%)" % (p.stock_portfolio.day_gain_dollar, p.stock_portfolio.day_gain_percent))
print("Total Gain: %s (%s%%)" % (p.stock_portfolio.total_gain_dollar, p.stock_portfolio.total_gain_percent))
print("-------------------------------------------------")

print("\nLong Positions:")
for position in p.stock_portfolio:
    print("-------------------------------------------------")
    print("Company: %s (%s)" % (position.description, position.symbol))
    print("Shares: %s" % position.quantity)
    print("Purchase Price: %s" % position.purchase_price)
    print("Current Price: %s" % position.current_price)
    print("Today's Gain: %s (%s%%)" % (position.day_gain_dollar, position.day_gain_percent))
    print("Total Gain: %s (%s%%)" % (position.total_gain_dollar, position.total_gain_percent))
    print("Market/Total Value: %s" % position.market_value)
    print("\t------------------------------")
    print("\tQuote")
    print("\t------------------------------")
    quote = position.quote
    for k,v in quote.__dict__.items():
        print("\t%s: %s" % (k,v))
    print("\t------------------------------")
    print("-------------------------------------------------")


print("\nShort Positions:")
for position in p.short_portfolio:
    print("-------------------------------------------------")
    print("Company: %s (%s)" % (position.description, position.symbol))
    print("Shares: %s" % position.quantity)
    print("Purchase Price: %s" % position.purchase_price)
    print("Current Price: %s" % position.current_price)
    print("Today's Gain: %s (%s%%)" % (position.day_gain_dollar, position.day_gain_percent))
    print("Total Gain: %s (%s%%)" % (position.total_gain_dollar, position.total_gain_percent))
    print("Market/Total Value: %s" % position.market_value)
    print("\t------------------------------")
    print("\tQuote")
    print("\t------------------------------")
    quote = position.quote
    for k,v in quote.__dict__.items():
        print("\t%s: %s" % (k,v))
    print("\t------------------------------")
    print("-------------------------------------------------")

print("\nOption Positions:")
for position in p.option_portfolio:
    print("-------------------------------------------------")
    print("Company: %s (%s)" % (position.description, position.underlying_symbol))
    print("Symbol: %s" % position.symbol)
    print("Contracts: %s" % position.quantity)
    print("Purchase Price: %s" % position.purchase_price)
    print("Current Price: %s" % position.current_price)
    print("Today's Gain: %s (%s%%)" % (position.day_gain_dollar, position.day_gain_percent))
    print("Total Gain: %s (%s%%)" % (position.total_gain_dollar, position.total_gain_percent))
    print("Market/Total Value: %s" % position.market_value)
    print("\t------------------------------")
    print("\tQuote")
    print("\t------------------------------")
    quote = position.quote
    for k,v in quote.__dict__.items():
        print("\t%s: %s" % (k,v))
    print("\t------------------------------")
    print("-------------------------------------------------")

# Make a stock trade
    
# Buy 2 shares of GOOG with limit $100 and no expiration
tt1 = TransactionType.BUY
ol1 = OrderLimit.LIMIT(100)
exp1 = Expiration.GOOD_UNTIL_CANCELLED()
trade1 = StockTrade(portfolio_id=p.portfolio_id, symbol="GOOG", quantity=2, transaction_type=tt1, order_limit=ol1, expiration=exp1)
trade1.validate()
trade1.execute()

# Buy 3 shares of AAPL at market value with expiration set to end of day
# defaults order_limit to OrderLimit.MARKET() and expiration to Expiration.END_OF_DAY())
trade2 = StockTrade(portfolio_id=p.portfolio_id, symbol='AAPL', quantity=3, transaction_type=TransactionType.BUY)
trade2.validate()
trade2.execute()

# short sell 1 share of AMZN
trade3 = StockTrade(portfolio_id=p.portfolio_id, symbol='AMZN', quantity=1, transaction_type=TransactionType.SELL_SHORT)
trade3.validate()
trade3.execute()


client.refresh_portfolio()
p = client.portfolio

for open_order in p.open_orders:
    if open_order.symbol == 'GOOG' and open_order.quantity == 2:
        # cancel GOOG trade
        open_order.cancel()
    
    if open_order.symbol == 'AAPL' and open_order.quantity == 3:
        # cancel AAPL trade
        open_order.cancel()

    if open_order.symbol == 'AMZN' and open_order.quantity == 1:
        # cancel AMZN trade
        open_order.cancel()


stock_portfolio = p.stock_portfolio
if len(p.stock_portfolio) > 0:
    # first long position in portfolio
    first_long_position = p.stock_portfolio[0]
    symbol = first_long_position.symbol
    quantity = first_long_position.quantity
    
    # execute trade to sell position in portfolio
    first_long_position.sell()
    client.refresh_portfolio()
    p = client.portfolio
    for oo in p.open_orders:
        if oo.symbol == symbol and oo.quantity == quantity:
            # cancel trade to sell first position in portfolio
            oo.cancel()

short_portfolio = p.short_portfolio
if len(p.short_portfolio) > 0:
    # first short position in portfolio
    first_short_position = p.short_portfolio[0]
    symbol = first_short_position.symbol
    quantity = first_short_position.quantity
    
    # execute trade to cover position in portfolio
    first_short_position.cover()
    client.refresh_portfolio()
    p = client.portfolio
    for oo in p.open_orders:
        # cancel cover trade you just made
        if oo.symbol == symbol and oo.quantity == quantity:
            # cancel trade to cover first position in portfolio
            oo.cancel()

if len(p.option_portfolio) > 0:
    first_option_contract = p.option_portfolio[0]
    symbol = first_option_contract.symbol
    quantity = first_option_contract.quantity
    first_option_contract.close()
    client.refresh_portfolio()
    p = client.portfolio
    for oo in p.open_orders:
        if oo.symbol == symbol and oo.quantity == quantity:
            oo.cancel()


# Gets all available option contracts for AAPL
oc = client.get_option_chain('AAPL')
all_options = oc.all()
print("There are %s available option contracts for AAPL" % len(all_options))


two_weeks_from_today = datetime.now() + timedelta(days=14)
print("AAPL in-the-money put options expiring within two weeks:")
put_options_near_expiration_itm = oc.search(before=two_weeks_from_today, puts=True, calls=False, scope=OptionScope.IN_THE_MONEY)
for option in put_options_near_expiration_itm:
    print("%s:\n\tbid: %s\n\task: %s\n\tlast price: %s\n\texpires:%s" % (option.symbol, option.bid, option.ask, option.last, option.expiration.strftime("%m/%d/%Y") ))


option_to_buy = put_options_near_expiration_itm[0]
trade4 = OptionTrade(portfolio_id=p.portfolio_id, symbol=option_to_buy.symbol, quantity=1, transaction_type=TransactionType.BUY)
trade4.validate()
trade4.execute()
client.refresh_portfolio()

p = client.portfolio
for oo in p.open_orders:
    if oo.symbol == option_to_buy.symbol:
        oo.cancel()