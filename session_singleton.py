from utils import UrlHelper

import requests
from lxml import html
import warnings

class NotLoggedInException(Exception):
    pass

class InvestopediaAuthException(Exception):
    pass

class Session:
    class __Session(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__int__(*args, **kwargs)

    __session = None

    def __new__(cls):
        if not cls.is_logged_in():
            raise NotLoggedInException(
                "Not logged in, call login() first with auth cookie")

        return cls.__session

    def __getattr__(self, name):
        return getattr(self.__session, name)

    def __setattr__(self, name):
        return setattr(self.__session, name)

    @classmethod
    def is_logged_in(cls):
        if cls.__session is not None and cls.__session.cookies.get('UI4') is not None:
            return True

        return False

    @classmethod
    def logout(cls):
        cls.__session = None

    @classmethod
    def login(cls, auth_cookie_value):
        if cls.is_logged_in():
            raise InvestopediaAuthException(
                "Already logged in.  This exception is to prevent inadvertantly overwriting the auth cookie.  Use Session.logout() first")
        if cls.__session is not None and auth_cookie_value == cls.__auth_cookie:
            warnings.warn(
                "authenticated session already exists, returning session")
            return cls.__session

        url = UrlHelper.route('portfolio')

        auth_cookie = {
            "version": 0,
            "name": 'UI4',
            "value": auth_cookie_value,
            "port": None,
            # "port_specified":False,
            "domain": '.investopedia.com',
            # "domain_specified":False,
            # "domain_initial_dot":False,
            "path": '/',
            # "path_specified":True,
            "secure": False,
            "expires": None,
            "discard": True,
            "comment": None,
            "comment_url": None,
            "rest": {},
            "rfc2109": False
        }

        cls.__session = requests.Session()
        cls.__session.cookies.set(**auth_cookie)

        url = UrlHelper.route('home')
        resp = cls.__session.get(url)

        if not resp.ok:
            cls.__session = None
            raise InvestopediaAuthException(
                "Got status code %s when fetching %s" % (resp.status_code, url))

        tree = html.fromstring(resp.text)
        sign_out_link = tree.xpath(
            '//div[@class="left-nav"]//ul/li/a[text()="Sign Out"]')
        if len(sign_out_link) < 1:
            warnings.warn(
                "Could not locate sign out link on home page.  Session may not have authenticated.")

        return cls.__session

    @classmethod
    def logout(cls):
        cls.__session = None
