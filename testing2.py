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