from investopedia_api import InvestopediaApi
import json
from IPython import embed
import time
import sys

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

lp = p.stock_portfolio
open_orders = client.portfolio.open_orders


for pos in lp:
    if pos.symbol.upper() in [o.symbol.upper() for o in open_orders]:
        print("open order for %s; skipping" % pos.symbol)
        continue
    trade = pos.sell()
    print(trade)
    #validated = trade.validate()
    #print(validated)
    #validated.execute()
embed()
for order in open_orders:
    order.cancel()

sys.exit()
sp = p.short_portfolio
op = p.option_portfolio

from itertools import chain


embed()

symbols_to_short = ['DPLD','CBL','BGG','ASNA','PAM','UEPS','LLEX','TGB','DY','LBY','TUSK','VNET','MD']
symbols_to_buy = []
shortf = []
buyf = []
for sym in symbols_to_short:
    if len([s for s in p.find(sym)]) == 0:
        shortf.append(sym)

for sym in symbols_to_buy:
    if len([s for s in p.find(sym)]) == 0:
        buyf.append(sym)

shortf = list(set(shortf))
buyf = list(set(buyf))
shorts = {}
for sym in shortf:
    quote = client.get_stock_quote(sym)
    if quote:
        shorts[sym] = int(1000/quote.last)


#shorts = {sym: int(1000/client.get_stock_quote(sym).last) for sym in shortf}
buys = {sym: int(1000/client.get_stock_quote(sym).last) for sym in buyf}

print(shorts)
print(buys)

for k,v in shorts.items():
    trade = client.StockTrade.Trade(k,v,'sell_short')
    print(trade)
    try:
        v = trade.validate()
        print(v)
        v.execute()
    except Exception:
        pass

for k,v in buys.items():
    trade = client.StockTrade.Trade(k,v,'buy')
    print(trade)

    try:
        v = trade.validate()
        print(v)
        v.execute()
    except Exception:
        pass





