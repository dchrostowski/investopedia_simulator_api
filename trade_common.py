import re
from ratelimit import limits, sleep_and_retry
from session_singleton import Session
from constants import *
import warnings
from queries import Queries
import json
import warnings


class InvalidTradeTypeException(Exception):
    pass

class InvalidOrderTypeException(Exception):
    pass


class InvalidOrderDurationException(Exception):
    pass

class TradeNotValidatedException(Exception):
    pass

class DuplicateTradeException(Exception):
    pass


class TransactionType(object):
    BUY = 'BUY'
    SELL = 'SELL'
    SELL_SHORT = 'SELL_SHORT'
    BUY_TO_COVER = 'BUY_TO_COVER'

class OrderLimit(dict):
    @classmethod
    def MARKET(cls):
        return cls({'limit': None})
    
    @classmethod
    def LIMIT(cls,price):
        return cls({'limit': int(price)})
    
    @classmethod
    def STOP(cls,price):
        return cls({'stop': int(price)})
    
    @classmethod
    def TRAILING_STOP(cls,val):
        val = str(val)
        dict_val = {'trailingStop': None}
        pct_regex = re.search(r'^(\d+)\%$',val)
        dol_regex = re.search(r'^\$?(\d+)$',val)
        if pct_regex:
            dict_val['trailingStop'] = {'percentage': int(pct_regex.group(1))}
            return cls(dict_val)
        
        elif dol_regex:
            dict_val['trailingStop'] = {'price': int(dol_regex.group(1))}
            return cls(dict_val)
        
        else:
            raise InvalidOrderTypeException("Invalid argument for TRAILING_STOP.  Call with OrderType.TRAILING_STOP('5%') or OrderType.TRAILING_STOP(5)")

class Expiration(dict):
    @classmethod
    def END_OF_DAY(cls):
        return cls({'expiryType':"END_OF_DAY"})
    
    @classmethod
    def GOOD_UNTIL_CANCELLED(cls):
        return cls({'expiryType':'GOOD_UNTIL_CANCELLED'})
    
    @classmethod
    def DAY_ONLY(cls):
        return cls.END_OF_DAY()


class Trade(object):
    def __init__(
            self,
            portfolio_id,
            symbol,
            quantity,
            transaction_type,
            order_limit=OrderLimit.MARKET(),
            expiration=Expiration.END_OF_DAY()):
        
        self._portfolio_id = portfolio_id
        self._symbol = symbol
        self._quantity = quantity
        self._transaction_type = transaction_type
        self._order_limit = order_limit
        self._expiration = expiration
        self._operation_name = None
        self._validated = False
        self._executed = False

    @property
    def portfolio_id(self):
        return self._portfolio_id
    
    @portfolio_id.setter
    def portfolio_id(self,portfolio_id):
        self._validated = False
        self._portfolio_id = portfolio_id

    @property
    def symbol(self):
        return self._symbol
    
    @symbol.setter
    def symbol(self,symbol):
        self._validated = False
        self._symbol = symbol

    @property
    def quantity(self):
        return self._quantity
    
    @quantity.setter
    def quantity(self,quantity):
        self._validated = False
        self._quantity = quantity

    @property
    def transaction_type(self):
        return self._transaction_type
    
    @transaction_type.setter
    def transaction_type(self,transaction_type):
        self._validated = False
        self._transaction_type = transaction_type
    
    @property
    def order_limit(self):
        return self._order_limit
    
    @order_limit.setter
    def order_limit(self,order_limit):
        self._validated = False
        self._order_limit = order_limit

    @property
    def expiration(self):
        return self._expiration
    
    @expiration.setter
    def expiration(self,expiration):
        self._validated = False
        self._expiration = expiration

    def validate(self):
        session = Session()
        request_data = None
        if self._operation_name == 'OptionTrade':
            request_data = Queries.validate_option_trade(self)
        if self._operation_name == 'StockTrade':
            request_data = Queries.validate_stock_trade(self)
        resp = session.post(API_URL,data=request_data)
        resp.raise_for_status()
        resp_json = json.loads(resp.text)
        response_key = "preview%s" % self._operation_name
        if resp_json.get('errors',None) is not None:
            for error in resp_json['errors']:
                warnings.warn(error['message'])
            self._validated = False
            return
        elif resp_json['data'][response_key].get('errorMessages',None) is not None:
            errors = resp_json['data']['previewStockTrade']['errorMessages']
            for error in errors:
                warnings.warn(error)
            self._validated = False
            return
        
        print("Trade validated!")
        self._validated = True

    def execute(self):
        if not self._validated:
            raise TradeNotValidatedException("Trade not validated!")
        
        if self._executed:
            raise DuplicateTradeException("Trade already executed.  Call reset() on Trade object to submit trade again")
        
        session = Session()
        request_data = None
        if self._operation_name == 'OptionTrade':
            request_data = Queries.execute_option_trade(self)
        if self._operation_name == 'StockTrade':
            request_data = Queries.execute_stock_trade(self)
        resp = session.post(API_URL, data=request_data)

        resp.raise_for_status()
        resp_json = json.loads(resp.text)
        
        response_key = "submit%s" % self._operation_name

        if resp_json.get('errors',None) is not None:
            for error in resp_json['errors']:
                warnings.warn(error['message'])
            self._executed = False
            self._validated = False
            return

        elif resp_json['data'][response_key].get('errorMessages',None) is not None:
            errors = resp_json['data'][response_key]['errorMessages']
            for error in errors:
                warnings.warn(error)
            self._executed = False
            self._validated = False
            return
        
        self._executed = True
        print("Trade executed!")

    def reset(self):
        self._validated = False
        self._executed = False

class StockTrade(Trade):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._operation_name = 'StockTrade'

class OptionTrade(Trade):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._operation_name = 'OptionTrade'
    
    
       




class PreparedTrade(dict):
    def __init__(self, url, form_data, **kwargs):
        self.url = url
        self.submit_form_data = form_data
        self.update(kwargs)

    @sleep_and_retry
    @limits(calls=6, period=20)
    def execute(self):
        session = Session()
        resp = session.post(self.url, data=self.submit_form_data)
        return resp
