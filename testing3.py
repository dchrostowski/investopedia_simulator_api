
from investopedia_api import InvestopediaApi
from IPython import embed
import json
import datetime

cookies = {}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)
auth_cookie = cookies['streetscrape_test']
# pass the value of the UI4 cookie after logging in to the site.
client = InvestopediaApi(auth_cookie)


lookup = client.get_option_chain('MSFT', strike_price_proximity=6)
for chain in lookup.search_by_daterange(datetime.datetime.now(), datetime.datetime(2100, 1, 1)):
    print("--------------------------------")
    print("calls expiring on %s" % chain.expiration_date_str)
    for call in chain.calls:
        print(call)
    print("puts expiring on %s" % chain.expiration_date_str)
    for put in chain.puts:
        print(put)
    print("--------------------------------")

chain2 = list(lookup.values())[1]
some_contract = chain2.calls[3]
print(some_contract)
trade_type = client.TradeProperties.TradeType('BUY_TO_OPEN')
duration = client.TradeProperties.Duration.GOOD_TILL_CANCELLED()
order_type = 'market'
trade = client.OptionTrade(
    some_contract, 2, trade_type=trade_type, order_type=order_type, duration=duration)

trade.validate()
if trade.validated:
    trade.execute()

trade_type2 = 'BUY'
duration2 = client.TradeProperties.Duration.DAY_ORDER()
trade2 = client.StockTrade(
    'GOOG', 14, trade_type=trade_type2, order_type=order_type, duration=duration2)

trade2.validate()
if trade2.validated:
    trade2.execute()
#trade = client.Stocks.Trade(symbol='GOOG',quantity=10,trade_type='buy',order_type='market',duration='good_till_cancelled',send_email=True)
#ott = OptionTradeType.BUY()

#ott2 = OptionTradeType.SELL_TO_CLOSE()
