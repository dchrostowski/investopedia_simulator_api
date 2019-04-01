from constants import *
from session_singleton import Session
from utils import UrlHelper
from IPython import embed
import re
import inspect

from utils import subclass_method, coerce_method_params
from stock_trade import StockTrade


class Portfolio(object):
    allowable_portfolios = {
        'LongPosition': ['StockPortfolio'],
        'ShortPosition': ['ShortPortfolio'],
        'OptionPosition': ['OptionPortfolio']
    }
    @coerce_method_params
    def __init__(
        self: object,
        account_value: Decimal,
        buying_power: Decimal,
        cash: Decimal,
        annual_return_pct: Decimal,
        stock_portfolio: object,
        short_portfolio: object,
        option_portfolio: object
    ):
        self.account_value = account_value
        self.buying_power = buying_power
        self.cash = cash
        self.annual_return_pct = annual_return_pct

        self._stock_portfolio = stock_portfolio
        self._short_portfolio = short_portfolio
        self._option_portfolio = option_portfolio

    @classmethod
    def _validate_append(cls,portfolio,position):
        portfolio_type = type(portfolio).__name__
        position_type = type(position).__name__
        assert_val = (portfolio_type in cls.allowable_portfolios[position_type])
        assert assert_val, "Cannot insert a %s into a %s" % (position_type,portfolio_type)

    @property
    @subclass_method
    def total_value(self):
        return sum((p.total_value) for p in self)

    @property
    @subclass_method
    def total_change(self):
        return sum(p.total_change for p in self)

    def find(self,symbol):
        if type(self).__name__ == 'Portfolio':
            found = []
            found.append(self.stock_portfolio.find(symbol))
            found.append(self.short_portfolio.find(symbol))


    def append(self,item):
        self.__class__._validate_append(self,item)
        super().append(item)

    @property
    def stock_portfolio(self):
        return self._stock_portfolio

    @property
    def short_portfolio(self):
        return self._short_portfolio

    @property
    def option_portfolio(self):
        return self._option_portfolio


class StockPortfolio(Portfolio,list):
    def __init__(self, positions=[]):
        for p in positions:
            self.append(p)


class ShortPortfolio(Portfolio,list):
    def __init__(self,positions=[]):
        for p in positions:
            self.append(p)

class OptionPortfolio(Portfolio,list):
    def __init__(self,positions=[]):
        for p in positions:
            self.append(p)




class Position(object):
    @coerce_method_params
    def __init__(
      self: object, 
      portfolio_id: str, 
      symbol: str, 
      quantity: int, 
      description:str, 
      purchase_price: Decimal, 
      current_price: Decimal, 
      total_value: Decimal ):

        self.portfolio_id = portfolio_id
        self.symbol = symbol
        self.quantity = quantity
        self.description = description
        self.purchase_price = purchase_price
        self.current_price = current_price
        self.total_value = total_value

    @property
    @subclass_method
    def total_change(self):
        return self.change * self.quantity


class LongPosition(Position):
    stock_type_assertion = 'long'

    def __init__(self, quote_fn, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert(stock_type == self.stock_type_assertion)
        self.stock_type = stock_type
        self._quote_fn = quote_fn
        self._quote = None
    
    @property
    def change(self):
        return self.current_price - self.purchase_price

    @property
    def quote(self):
        if self._quote is None:
            self._quote = self._quote_fn()
        return self._quote

    def sell(self,**trade_kwargs):
        trade_kwargs['symbol'] = self.symbol
        trade_kwargs.setdefault('quantity',self.quantity)
        trade_kwargs['trade_type'] = 'sell'
        return StockTrade(**trade_kwargs)
        
        


class ShortPosition(Position):
    stock_type_assertion = 'short'

    def __init__(self, quote_fn, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self.stock_type = stock_type
        self._quote_fn = quote_fn
        self._quote = None

    # note that short positions value go up when the underlying security goes down
    @property
    def change(self):
        return self.purchase_price - self.current_price

    @property
    def quote(self):
        if self._quote is None:
            self._quote = self._quote_fn()
        return self._quote
    
    def cover(self, **trade_kwargs):
        trade_kwargs['symbol'] = self.symbol
        trade_kwargs.setdefault('quantity',self.quantity)
        trade_kwargs['trade_type'] = 'buy_to_cover'
        return StockTrade(**trade_kwargs)


class OptionPosition(Position):
    stock_type_assertion = 'option'
    def __init__(self, option_contract, quote_fn, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self._quote_fn = quote_fn
        self.option_contract = option_contract
        self.stock_type = stock_type
        self.strike_price = self.option_contract.strike_price
        self.contract_type = self.option_contract.contract_type
        self.expiration = self.option_contract.expiration
        self._quote_fn = quote_fn
        self._quote = None

    @property
    def quote(self):
        if self._quote is None:
            self.option_contract = self._quote_fn()
            self._quote=True
        return self.option_contract
            
    def close(self):
        pass

class StockQuote(object):
    @coerce_method_params
    def __init__(
        self:object,
        symbol: str,
        name: str,
        exchange: str,
        last: Decimal,
        change: Decimal,
        change_percent: Decimal,
        volume:int
        
    ):
        self.symbol = symbol
        self.name = name
        self.last = last
        self.exchange = exchange
        self.change = change
        self.change_percent = change_percent
        self.volume = volume
        
