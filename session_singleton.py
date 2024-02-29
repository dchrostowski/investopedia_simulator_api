from utils import UrlHelper

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

import os

class Session:
    class __Session(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__int__(*args, **kwargs)

    __session = None
    

    def __new__(cls):
        if not cls.is_logged_in():
            raise NotLoggedInException(
                "Not logged in, call login() first with auth cookie")
        
        cls.refresh_token()

        return cls.__session

    def __getattr__(self, name):
        return getattr(self.__session, name)

    def __setattr__(self, name):
        return setattr(self.__session, name)
    
    
    @classmethod
    def refresh_token(cls):
        print("refresh token called")
        if cls.is_logged_in():
            
            session = cls.__session
            auth_data = {}
            with open("./auth.json",'r') as ifh:
                auth_data = json.loads(ifh.readline())

            
            
            cls.__session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            refresh_token = auth_data['refresh_token']
            payload = Queries.refresh_token(refresh_token)

            auth_data = json.loads(cls.__session.post(REFRESH_AUTH_TOKEN_URL, data=Queries.refresh_token(refresh_token)).text)
            with open('./auth.json','w') as ofh:
                ofh.write(json.dumps(auth_data))

            cls.__session.headers.update({'Authorization': "Bearer %s" % auth_data['access_token'], 'Content-Type': 'application/json'})


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
                auth_data = json.loads(ifh.readline())
                authorization_header = {'Authorization': "Bearer %s" % auth_data['access_token']}
                cls.__session = requests.Session()
                cls.__session.headers.update(authorization_header)
                cls.__session.headers.update({'Content-Type':'application/json'})
                

        
        resp = cls.__session.post(API_URL,data=Queries.read_user_id())

        if not resp.ok:
            cls.__session = None
            raise InvestopediaAuthException(
                "Got status code %s when fetching %s" % (resp.status_code, url))

        

        return cls.__session

    @classmethod
    def logout(cls):
        cls.__session = None