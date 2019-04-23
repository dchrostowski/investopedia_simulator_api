# This demonstrates the trade queue.  Trades will be validated & executed while concurrently fetching quotes and option chain lookups
from investopedia_api import InvestopediaApi, TradeExceedsMaxSharesException
import json
import datetime

def do_stuff(client):
    p = client.portfolio
    print("account value: %s" % p.account_value)
    print("cash: %s" % p.cash)
    print("buying power: %s" % p.buying_power)
    print("annual return pct: %s" % p.annual_return_pct)

    # get a quote
    quote = client.get_stock_quote('GOOG')
    print(quote.__dict__)
    quote = client.get_stock_quote('AMZN')
    print(quote.__dict__)
    quote = client.get_stock_quote('AAPL')
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

    # option chain lookup
    lookup = client.get_option_chain('AAPL')
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

    # option chain lookup
    lookup = client.get_option_chain('AMZN')
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

cookies = {}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)
auth_cookie = cookies['streetscrape_test']
# pass the value of the UI4 cookie after logging in to the site.
client = InvestopediaApi(auth_cookie)
trade_queue = client.TradeQueue()

trade1 = client.StockTrade("AMZN",10,'BUY')
trade2 = client.StockTrade("GOOGL",2,'SELL_SHORT')
trade3 = client.StockTrade("AAPL",4,'SELL_SHORT')

trade_queue.enqueue(trade1)
trade_queue.enqueue(trade2)
trade_queue.enqueue(trade3)

do_stuff(client)

trade_queue.finish()