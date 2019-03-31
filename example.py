from investopedia_api import InvestopediaApi
import json
from IPython import embed

cookies = {}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)
auth_cookie = cookies['streetscrape_test']
client = InvestopediaApi(auth_cookie)

long_positions = client.portfolio.stock_portfolio
print(long_positions.total_value)
short_positions = client.portfolio.short_portfolio
print(short_positions.total_value)

for position in long_positions:
    print(position.symbol)
    print(position.purchase_price)
    print(position.current_price)

trade = client.StockTrade.Trade(stock='GOOG',quantity=10,transaction_type='buy',order_type='market',order_duration='good_till_cancelled',sendEmail=True) 
print(trade.validate())
trade.order_duration = 'day_order'
trade.order_type = client.StockTrade.OrderType.LIMIT(10)
print(trade.validate())
"""
from api_models2 import Portfolio, StockPortfolio, Position
from IPython import embed
from utils import UrlHelper
from lxml import html
from parsers import Parsers
from session_singleton import Session
import json

cookies = {}
with open('auth_cookie.json') as ifh:
    cookies = json.load(ifh)
Session.login(cookies['streetscrape_test'])
portfolio = Parsers.get_portfolio()
embed()
"""


"""
session = Session()

url = UrlHelper.route('portfolio')
resp = session.get(url)
tree = html.fromstring(resp.text)

longs = Parsers.positions(tree)
embed()

pos1 = Position('1234','GOOG', '40', "Google Stock",1000.00,1001.0,4040.00)
pos2 = Position(portfolio_id='1234',symbol='GOOG',quantity='40',description="google stock", purchase_price="1000.00",current_price="1001.02", total_value="40000.02")
print("END")
embed()
"""