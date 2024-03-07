from constants import *
from session_singleton import Session
from utils import UrlHelper
import re
from itertools import chain
from datetime import datetime
from decimal import Decimal

from utils import subclass_method, coerce_method_params, date_regex
from trade_common import StockTrade, TransactionType
from option_trade import OptionTrade



class InvalidSecurityTypeException(Exception):
    pass


class OpenOrder(object):
    @coerce_method_params
    def __init__(
        self: object,
        order_id: int,
        cancel_fn: object,
        symbol: str,
        quantity: int,
        order_price: Decimal,
        trade_type: str
    ):
        self.order_id = order_id
        self.cancel_fn = cancel_fn
        # strptime with %-m/%-d/%Y %-I:%M:%S %p SHOULD WORK
        # because it looks like this: 4/1/2019 11:10:35 PM
        self.trade_type = trade_type
        self.symbol = symbol
        self.quantity = quantity
        self.order_price = order_price
        self.active = True

    def cancel(self):        
        cancelled =  self.cancel_fn()
        if cancelled:
            self.active = False
            print("Order ID %s cancelled!" % self.order_id)



class SubPortfolio(object):
    def __init__(self,portfolio_id,market_value,day_gain_dollar,day_gain_percent,total_gain_dollar,total_gain_percent):
        self.portfolio_id = portfolio_id
        self.market_value = market_value
        self.day_gain_dollar = day_gain_dollar
        self.day_gain_percent = day_gain_percent
        self.total_gain_dollar = total_gain_dollar
        self.total_gain_percent = total_gain_percent

    @subclass_method
    def find(self,symbol):
        for p in self:
            if hasattr(p,'underlying'):
                if symbol.upper() == p.underlying:
                    return p

            if symbol.upper() == p.symbol:
                return p
            
            

class Portfolio(object):
    allowable_portfolios = {
        'LongPosition': ['StockPortfolio'],
        'ShortPosition': ['ShortPortfolio'],
        'OptionPosition': ['OptionPortfolio']
    }
    @coerce_method_params
    def __init__(
        self: object,
        portfolio_id: int,
        game_id: int,
        game_name: str,
        account_value: Decimal,
        buying_power: Decimal,
        cash: Decimal,
        annual_return_pct: Decimal,
        stock_portfolio: object,
        short_portfolio: object,
        option_portfolio: object,
        open_orders: object
    ):
        self.portfolio_id = portfolio_id
        self.game_id = game_id
        self.game_name = game_name
        self.account_value = account_value
        self.buying_power = buying_power
        self.cash = cash
        self.annual_return_pct = annual_return_pct

        self._stock_portfolio = stock_portfolio
        self._short_portfolio = short_portfolio
        self._option_portfolio = option_portfolio
        self._open_orders = open_orders

    @property
    def stock_portfolio(self):
        return self._stock_portfolio

    @property
    def short_portfolio(self):
        return self._short_portfolio

    @property
    def option_portfolio(self):
        return self._option_portfolio
    
    @property
    def open_orders(self):
        orders = []
        for oo in self._open_orders:
            if oo.active:
                orders.append(oo)

        return orders
    
    # def refresh(self):
    #     self = Parsers.generate_portfolio(self.portfolio_id,self.game_id,self.game_name)

    




class StockPortfolio(SubPortfolio, list):
    def __init__(self, positions=[], **kwargs):
        super().__init__(**kwargs)
        for p in positions:
            if p.stock_type == 'long':
                self.append(p)
            else:
                raise InvalidSecurityTypeException("Security type should be stock, got '%s" % p.stock_type)


class ShortPortfolio(SubPortfolio, list):
    def __init__(self, positions=[], **kwargs):
        super().__init__(**kwargs)
        for p in positions:
            if p.stock_type == 'short':
                self.append(p)
            else:
                raise InvalidSecurityTypeException("Security type should be short, got '%s" % p.stock_type)


class OptionPortfolio(SubPortfolio, list):
    def __init__(self, positions=[], **kwargs):
        super().__init__(**kwargs)
        for p in positions:
            if p.stock_type == 'option':
                self.append(p)
            else:
                raise InvalidSecurityTypeException("Security type should be option, got '%s" % p.stock_type)

class Position(object):
    @coerce_method_params
    def __init__(
            self: object,
            portfolio_id: str,
            symbol: str,
            quantity: int,
            description: str,
            purchase_price: Decimal,
            market_value: Decimal,
            day_gain_dollar: Decimal,
            day_gain_percent: Decimal,
            total_gain_dollar: Decimal,
            total_gain_percent: Decimal
        ):

        self.portfolio_id = portfolio_id
        self.symbol = symbol
        self.quantity = quantity
        self.description = description
        self.purchase_price = purchase_price
        self.market_value = market_value
        self.day_gain_dollar = day_gain_dollar
        self.day_gain_percent = day_gain_percent
        self.total_gain_dollar = total_gain_dollar
        self.total_gain_percent = total_gain_percent
        self.current_price = self.market_value / self.quantity



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
        return self._quote_fn()

    def sell(self, **trade_kwargs):
        trade_kwargs['symbol'] = self.symbol
        trade_kwargs.setdefault('quantity', self.quantity)
        trade_kwargs['transaction_type'] = TransactionType.SELL
        trade_kwargs['portfolio_id'] = self.portfolio_id
        sell_trade = StockTrade(**trade_kwargs)
        sell_trade.validate()
        sell_trade.execute()
        return sell_trade


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
        return self._quote_fn()
    

    def cover(self, **trade_kwargs):
        trade_kwargs['symbol'] = self.symbol
        trade_kwargs.setdefault('quantity', self.quantity)
        trade_kwargs['transaction_type'] = TransactionType.BUY_TO_COVER
        trade_kwargs['portfolio_id'] = self.portfolio_id
        cover_trade = StockTrade(**trade_kwargs)
        cover_trade.validate()
        cover_trade.execute()
        return cover_trade


class OptionPosition(Position):
    stock_type_assertion = 'option'

    @coerce_method_params
    def __init__(
            self,
            is_put: bool,
            last: Decimal,
            expiration_date: int,
            strike_price: Decimal,
            underlying_symbol: str,
            quote_fn: object,
            stock_type: str,
            **kwargs: object):
        super().__init__(**kwargs)
        assert stock_type == self.stock_type_assertion
        self.stock_type = stock_type
        self.is_put = is_put
        self.current_price = last
        self.expiration_date = datetime.fromtimestamp(expiration_date/1000)
        self.strike_price = strike_price
        self._quote_fn = quote_fn
        self.underlying_symbol = underlying_symbol
        self._contract = None

    @property
    def contract(self):
        if self._contract is None:
            self._contract = self._quote_fn()
        return self._contract

    @property
    def quote(self):
        self._contract = self._quote_fn()
        return self.contract

    def close(self, **trade_kwargs):
        trade_kwargs['symbol'] = self.symbol
        trade_kwargs.setdefault('quantity', self.quantity)
        trade_kwargs['transaction_type'] = TransactionType.SELL
        close_trade = OptionTrade(**trade_kwargs)
        close_trade.validate()
        close_trade.execute()


class StockQuote(object):
    @coerce_method_params
    def __init__(
        self: object,
        symbol: str,
        name: str,
        exchange: str,
        previous_close: Decimal,
        bid: Decimal,
        ask: Decimal,
        volume: int,
        day_high: Decimal,
        day_low: Decimal

    ):
        self.symbol = symbol
        self.name = name
        self.last = ask
        self.exchange = exchange
        self.volume = volume
        self.day_high = day_high
        self.day_low = day_low
        self.previous_close = previous_close
        self.bid = bid
        self.ask = ask
        self.last = self.ask
        self.change = self.ask - self.previous_close
        self.change_percent = round(self.change / self.last * 100,2)
