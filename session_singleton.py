from utils import UrlHelper
from constants import *

from singleton_decorator import singleton
import requests
from IPython import embed
from lxml import html


class Session2:
    class __Session2(requests.Session):
        def __init__(self,*args,**kwargs):
            super().__int__(*args,**kwargs)

        def logout(self):
            self = None

    __session = None
    __auth_cookie = None


    def __new__(cls):
        if cls.__session is None:
            raise InvestopediaAuthException("Not logged in, call login() first with auth cookie")
            return
        return cls.__session

    def __getattr__(self,name):
        return getattr(self.__session,name)

    def __setattr__(self,name):
        return setattr(self.__session,name)

    

    @classmethod
    def login(cls,auth_cookie_value):
        if cls.__session is not None:
            raise InvestopediaAuthException("Already logged in.  Logout first before attempting to login again")
        
        url = UrlHelper.route('portfolio')
        

        auth_cookie = {
            "version":0,
            "name":'UI4',
            "value":auth_cookie_value,
            "port":None,
            # "port_specified":False,
            "domain":'www.investopedia.com',
            # "domain_specified":False,
            # "domain_initial_dot":False,
            "path":'/',
            # "path_specified":True,
            "secure":False,
            "expires":None,
            "discard":True,
            "comment":None,
            "comment_url":None,
            "rest":{},
            "rfc2109":False
        }

        cls.__session = requests.Session()
        cls.__session.cookies.set(**auth_cookie)
        print("about to do url=urlheler.route('home')")
        
        url = UrlHelper.route('home')
        resp = cls.__session.get(url)
        if resp.status_code != 200:
            __session = None
            __auth_cookie = None
            raise InvestopediaAuthException("Got status code %s when fetching %s" % (resp.status_code,url))

        tree = html.fromstring(resp.text)
        sign_out_link = tree.xpath('//div[@class="left-nav"]//ul/li/a[text()="Sign Out"]')
        if len(sign_out_link) < 1:
            raise InvestopediaAuthException("Could not authenticate with cookie")

        #awards_url = tree.xpath('//div[@class="sim-page"]//div[contains(@class,"box") and contains(@class,"info")]/div[contains(@class,"box")]/div[@class="title"]/h2/a[text()="Your Awards"]/@href')[0]
        #awards_qs = UrlHelper.get_query_params(awards_url)
        #user_id = awards_qs['userId']
        return cls.__session
