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
Session.login(cookies['default'])
session = Session()

url = UrlHelper.route('portfolio')
resp = session.get(url)
tree = html.fromstring(resp.text)

longs = Parsers.positions(tree)
embed()
