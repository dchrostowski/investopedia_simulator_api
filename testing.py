import json
from IPython import embed

from investopedia_api import InvestopediaSimulatorAPI
from api_models import *
from utils import UrlHelper
from session_singleton import Session2

# cookie should look like {auth_cookie:'abcdabcd1234...'}
with open('auth_cookie.json') as ifh:
    auth_cookies = json.load(ifh)

cookie = auth_cookies['streetscrape_test']
session = Session2.login(cookie)
derp = Derp()
embed()
# Instantiate as you see fit, doesn't need to be a keywork arg
client = InvestopediaSimulatorAPI(cookie)
ocl = client.option_lookup('teo')



portfolio = client.option_portfolio
#print(portfolio)
#ocl = client.option_lookup('teo')
