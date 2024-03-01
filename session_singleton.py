from utils import UrlHelper

import os
import requests
from lxml import html
import warnings
import re
import json
from IPython import embed
from constants import API_URL, REFRESH_AUTH_TOKEN_URL
from queries import Queries

class NotLoggedInException(Exception):
    pass

class InvestopediaAuthException(Exception):
    pass



class Session:
    class __Session(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__int__(*args, **kwargs)

    __session = None
    __auth_data = None
    __credentials = None

    def __new__(cls):
        cls._load_tokens()
        if not cls.is_logged_in():
            raise NotLoggedInException(
                "Not logged in.  Call Session.login()")
        cls.refresh_token()
        return cls.__session

    def __getattr__(self, name):
        return getattr(self.__session, name)

    def __setattr__(self, name):
        return setattr(self.__session, name)
    
    @classmethod
    def refresh_token(cls):
        if cls.is_logged_in():
            cls.__session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            refresh_token = cls.__auth_data['refresh_token']
            resp = cls.__session.post(REFRESH_AUTH_TOKEN_URL, data=Queries.refresh_token(refresh_token))

            if not resp.ok:
                warnings.warn("Problem with auth tokens, attempting to login again...")
                cls.logout()
                return cls.login(cls.__credentials)
            
            new_auth_data = json.loads(resp.text)
            cls.__auth_data = new_auth_data
            new_headers = {
                'Authorization': "Bearer %s" % cls.__auth_data['access_token'],
                'Content-Type': 'application/json'
            }
            
            cls.__session.headers.update(new_headers)
            cls._save_tokens()
            return cls.__session
        
    @classmethod
    def _load_tokens(cls):
        if not os.path.exists('auth.json'):
            cls.login(cls.__credentials)
        if cls.__auth_data is None:
            with open('auth.json','r') as auth_file:
                cls.__auth_data = json.load(auth_file)

    @classmethod
    def _save_tokens(cls):
        if cls.__auth_data is not None:
            with open('auth.json','w') as auth_file:
                json.dump(cls.__auth_data,auth_file)

    @classmethod
    def is_logged_in(cls):
        if cls.__session is not None and cls.__session.headers.get('Authorization') is not None:
            return True
        return False

    @classmethod
    def logout(cls):
        cls.__session = None
        cls.__auth_data = None
        os.remove('auth.json')

    @classmethod
    def login(cls, credentials):
        cls.__credentials = credentials
        if not os.path.exists('auth.json'):
            os.system("npm install")
            print("Logging into Investopedia...")
            os.system("node ./auth.js %s %s" % (credentials['username'],credentials['password']))

            if not os.path.exists("auth.json"):
                raise InvestopediaAuthException("Unable to login with credentials '%s', '%s'" % (credentials['username'],credentials['password']))
        
        cls._load_tokens()
        session_headers = {
            'Authorization': "Bearer %s" % cls.__auth_data['access_token'],
            'Content-Type': 'application/json'
        }

        cls.__session = requests.Session()
        cls.__session.headers.update(session_headers)
        cls.refresh_token()

        resp = cls.__session.post(API_URL,data=Queries.read_user_id())

        if not resp.ok:
            cls.__session = None
            raise InvestopediaAuthException(
                "Got status code %s when fetching %s" % (resp.status_code, API_URL))
        
        return cls.__session