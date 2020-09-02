from utils import UrlHelper

import requests
from lxml import html
import warnings
import re

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
        if cls.__session is not None and cls.__session.cookies.get('AWSALBCORS') is not None:
            return True

        return False

    @classmethod
    def logout(cls):
        cls.__session = None

    @classmethod
    def login(cls, credentials):
        if cls.is_logged_in():
            warnings.warn(
                "You are already logged in.  If you want to logout call Session.logout().  Returning session")
            return cls.__session
        
        url = 'https://www.investopedia.com/auth/realms/investopedia/shopify-auth/inv-simulator/login?&redirectUrl=https%3A%2F%2Fwww.investopedia.com%2Fauth%2Frealms%2Finvestopedia%2Fprotocol%2Fopenid-connect%2Fauth%3Fresponse_type%3Dcode%26approval_prompt%3Dauto%26redirect_uri%3Dhttps%253A%252F%252Fwww.investopedia.com%252Fsimulator%252Fhome.aspx%26client_id%3Dinv-simulator-conf'
        cls.__session = requests.Session()
        resp = cls.__session.get(url)
        
        tree = html.fromstring(resp.text)
        script_with_url = tree.xpath('//script/text()')[0]

        redirect_url = re.search(r'REDIRECT_URL\s=\s"([^"]+)"', script_with_url).group(1)
        resp = cls.__session.get(redirect_url.encode('utf-8').decode('unicode_escape'))
        tree = html.fromstring(resp.text)
        post_url = tree.xpath('//form/@action')[0]
        payload = credentials
        resp = cls.__session.post(post_url,data=payload)

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
