from constants import *
from session_singleton import Session
from utils import UrlHelper
from parsers import Parsers
from IPython import embed
import re

from utils import subclass_method

class Portfolio(list):
    def __init__(
        self,
        account_value,
        buying_power,
        cash,
        annual_return_pct,
        stock_portfolio=StockPortfolio(),
        shorted_portfolio=None):
        self.account_value = account_value
        self.buying_power = buying_power
        self.cash = cash
        self.annual_return_pct = annual_return_pct
        # Lazy props
        self.stock_portfolio = None
        self.shorted_portfolio = None
        self.option_portfolio = None

    @subclass_method
    def total_value(self):
        return sum((p.value) for p in self)

    @subclass_method
    def total_gain(self):
        return sum((p.gain) for p in self)
        

    @property
    def stock_portfolio(self):
        return self._stock_portfolio

    @property
    def shorted_portfolio(self):
        return self._shorted_portfolio

    @property
    def option_portfolio(self):
        return self._option_portfolio

    @classmethod 
    def initialize(self):
        pass

class StockPortfolio(Portfolio):
    def __init__(self, positions=[]):
        for p in positions:
            self.append(p)

class Position(object):
    def __init__(self,total_gain,total_value):
        self.total_gain = total_gain
        self.total_value = total_value




