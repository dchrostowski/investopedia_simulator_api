import json
from IPython import embed

from investopedia_api import InvestopediaSimulatorAPI
from api_models import *
from utils import UrlHelper
from session_singleton import Session
from test_class import TestClass

# cookie should look like {auth_cookie:'abcdabcd1234...'}
with open('auth_cookie.json') as ifh:
    auth_cookies = json.load(ifh)

client = InvestopediaSimulatorAPI(auth_cookies['streetscrape_test'])

embed()
