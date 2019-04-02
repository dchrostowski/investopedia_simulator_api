from investopedia_api import InvestopediaApi
import json
from IPython import embed
import time

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

sp = p.short_portfolio
op = p.option_portfolio

from itertools import chain



symbols_to_short = ['adnt','CPS','DF','INWK','FTD','ORN','INWK','arex','TEDU','ROX','CLW','PRA','AREX','OMI','RLGY','RAIL','OBE','NEWM']
symbols_to_buy = ['ENSG','HMNF','CYBR','HMNF','DMLP','DRI','CDNS','GRMN','ATHM','TPL','UBNT','OKE']
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

shorts = {sym: int(1000/client.get_stock_quote(sym).last) for sym in shortf}
buys = {sym: int(1000/client.get_stock_quote(sym).last) for sym in buyf}

print(shorts)
print(buys)

for k,v in shorts.items():
    time.sleep(2)
    trade = client.StockTrade.Trade(k,v,'sell_short')
    print(trade)
    time.sleep(3)
    try:
        v = trade.validate()
        print(v)
        time.sleep(3)
        v.execute()
        time.sleep(3)
    except Exception:
        pass

for k,v in buys.items():
    time.sleep(2)
    trade = client.StockTrade.Trade(k,v,'buy')
    print(trade)
    time.sleep(3)
    try:
        v = trade.validate()
        print(v)
        time.sleep(3)
        v.execute()
        time.sleep(3)
    except Exception:
        pass





