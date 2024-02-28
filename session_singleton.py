from utils import UrlHelper

import requests
from lxml import html
import warnings
import re
import json
from IPython import embed
from constants import API_URL

class NotLoggedInException(Exception):
    pass

class InvestopediaAuthException(Exception):
    pass

import os

class Session:
    class __Session(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__int__(*args, **kwargs)
            self.url='https://api.investopedia.com/simulator/graphql'

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
        if cls.__session is not None and cls.__session.headers.get('Authorization') is not None:
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
        
        if os.path.exists("auth.json"):
            os.remove('auth.json')
        os.system("npm install")
        print("Logging into Investopedia...")
        os.system("node ./auth.js %s %s" % (credentials['username'],credentials['password']))

        if not os.path.exists("auth.json"):
            raise InvestopediaAuthException("Unable to login with credentials '%s', '%s'" % (credentials['username'],credentials['password']))

        else:
            with open('./auth.json','r') as ifh:
                authorization_header = json.loads(ifh.readline())
                cls.__session = requests.Session()
                cls.__session.headers.update(authorization_header)
                cls.__session.headers.update({'Content-Type':'application/json'})
                

        
        gl_query = {"operationName":"ReadUserId","variables":{},"query":"query ReadUserId {\n  readUser {\n    ... on UserErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on User {\n      id\n      __typename\n    }\n    __typename\n  }\n}\n"}
        resp = cls.__session.post(API_URL,data=json.dumps(gl_query))

        if not resp.ok:
            cls.__session = None
            raise InvestopediaAuthException(
                "Got status code %s when fetching %s" % (resp.status_code, url))

        

        return cls.__session

    @classmethod
    def logout(cls):
        cls.__session = None