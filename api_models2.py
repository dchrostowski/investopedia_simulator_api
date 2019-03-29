from constants import *
from session_singleton import Session
from utils import UrlHelper
from IPython import embed
import re
import accepts
import inspect

from utils import subclass_method


class Portfolio(list):
    def __init__(
        self,
        account_value,
        buying_power,
        cash,
        annual_return_pct,
        stock_portfolio
    ):
        self.account_value = account_value
        self.buying_power = buying_power
        self.cash = cash
        self.annual_return_pct = annual_return_pct

        self._stock_portfolio = stock_portfolio
        # self._shorted_portfolio = shorted_portfolio
        # self._option_portfolio = option_portfolio

    @subclass_method
    def total_value(self):
        return sum((p.total_value) for p in self)

    @subclass_method
    def total_gain(self):
        return sum((p.total_gain) for p in self)

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

    def __call__(self):
        return self.__class__


class Position(object):
    def __init__(self, portfolio_id, symbol, quantity, description, purchase_price, current_price, total_value, total_change):
        self.portfolio_id = portfolio_id
        self.symbol = symbol
        self.quantity = quantity
        self.description = description
        self.purchase_price = purchase_price
        self.current_price = current_price
        self.total_value = total_value
        self.total_change = total_change

    @classmethod
    def from_tr_element(cls, tr):
        pass


class LongPosition(Position):
    stock_type_assertion = 'long'

    def __init__(self, trade_link, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self.stock_type = stock_type
        self.trade_link = trade_link


class ShortPosition(Position):
    stock_type_assertion = 'short'

    def __init__(self, trade_link, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self.stock_type = stock_type
        self.trade_link = trade_link


class OptionPosition(Position):
    stock_type_assertion = 'long'

    def __init__(self, trade_link, stock_type, **kwargs):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self.stock_type = stock_type
        self.trade_link = trade_link
