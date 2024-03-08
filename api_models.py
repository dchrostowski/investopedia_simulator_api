from constants import *
from datetime import datetime, timedelta
from decimal import Decimal
from utils import subclass_method, coerce_method_params
from trade_common import StockTrade, TransactionType, OptionTrade
from queries import Queries
from session_singleton import Session
from constants import API_URL
import json
import warnings
from warnings import warn
import requests
from ratelimit import limits,sleep_and_retry
import logging


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
            if hasattr(p,'underlying_symbol'):
                if symbol.upper() == p.underlying_symbol:
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
    
    def refresh(self):
        new_portfolio = Parsers.generate_portfolio(self.portfolio_id,self.game_id,self.game_name)
        self._stock_portfolio = new_portfolio._stock_portfolio
        self._short_portfolio = new_portfolio._short_portfolio
        self._option_portfolio = new_portfolio._option_portfolio
        self._open_orders = new_portfolio._open_orders
        self.account_value = new_portfolio.account_value
        self.buying_power = new_portfolio.buying_power
        self.cash = new_portfolio.cash
        self.annual_return_pct = new_portfolio.annual_return_pct

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
        trade_kwargs['portfolio_id'] = self.portfolio_id
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

class OptionScope(object):
    IN_THE_MONEY = 'IN_THE_MONEY'
    NEAR_THE_MONEY = 'NEAR_THE_MONEY'
    OUT_OF_THE_MONEY = 'OUT_OF_THE_MONEY'
    ALL = 'ALL'


class OptionChain(object):
    def __init__(self,symbol):
        self.expirations = []
        self.options = {}
        self.chain = {}
        symbol = symbol.upper()

        session = Session()
        exp_resp = session.post(API_URL,data=Queries.option_expiration_dates(symbol))
        exp_resp.raise_for_status()


        exp_json = json.loads(exp_resp.text)
        for expiration in exp_json['data']['readOptionsExpirationDates']['expirationDates']:
            self.expirations.append(expiration)

        for expiration in self.expirations:
            self.chain[expiration] = {}
            option_scopes = [OptionScope.IN_THE_MONEY, OptionScope.OUT_OF_THE_MONEY, OptionScope.NEAR_THE_MONEY]
            for os in option_scopes:
                self.chain[expiration][os] = {'calls': [], 'puts': []}
                options_resp = session.post(API_URL, data=Queries.options_by_expiration(symbol,expiration,os))
                options_resp.raise_for_status()
                options = json.loads(options_resp.text)['data']['readStock']['options']
                call_options = options['callOptions']['list']
                put_options = options['putOptions']['list']
                for co_kwargs in call_options:
                    co_kwargs['expiration'] = expiration
                    co_kwargs['is_put'] = False
                    call_option = OptionContract(**co_kwargs)
                    self.options[call_option.symbol] = call_option
                    self.chain[expiration][os]['calls'].append(call_option.symbol)

                for po_kwargs in put_options:
                    po_kwargs['expiration'] = expiration
                    po_kwargs['is_put'] = True
                    put_option = OptionContract(**po_kwargs)
                    self.options[put_option.symbol] = put_option
                    self.chain[expiration][os]['puts'].append(put_option.symbol)

    def search(
        self,
        after=datetime.now() - timedelta(days=365),
        before=datetime.now() + timedelta(days=365),
        scope=OptionScope.ALL,
        calls=True,
        puts=True
        ):

        eligible_expirations = []
        eligible_scopes = []
        eligible_types = []


        after_ts = after.timestamp()
        before_ts = before.timestamp()

        
        for exp in self.expirations:
            if exp/1000 >= after_ts and exp/1000 <= before_ts:
                eligible_expirations.append(exp)
        
        if scope == OptionScope.ALL:
            eligible_scopes = [OptionScope.IN_THE_MONEY, OptionScope.OUT_OF_THE_MONEY, OptionScope.NEAR_THE_MONEY]
        else:
            eligible_scopes = [scope]

        if calls:
            eligible_types.append('calls')
        
        if puts:
            eligible_types.append('puts')

        filtered_options = []
        for exp in eligible_expirations:
            filtered_expirations = self.chain[exp]
            for esc in eligible_scopes:
                filtered_scopes = filtered_expirations[esc]
                for ety in eligible_types:
                    filtered_option_symbols = filtered_scopes[ety]
                    for opt_symbol in filtered_option_symbols:
                        filtered_options.append(self.options[opt_symbol])

        return filtered_options
    

    def all(self):
        return [v for v in self.options.values()]
    
    def lookup_by_symbol(self,symbol):
        return self.options.get(symbol,None)

class OptionContract(object):
    def __init__(self,**kwargs):
        self.symbol = kwargs['symbol']
        self.strike_price = kwargs['strikePrice']
        self.last = kwargs['lastPrice']
        self.day_change = kwargs['dayChangePrice']
        self.day_change_percent = kwargs['dayChangePercent']
        self.day_low = kwargs['dayLowPrice']
        self.day_high = kwargs['dayHighPrice']
        self.bid = kwargs['bidPrice']
        self.ask = kwargs['askPrice']
        self.volume = kwargs['volume']
        self.open_interest = kwargs['openInterest']
        self.in_the_money = kwargs['isInTheMoney']
        self.expiration = datetime.fromtimestamp(kwargs['expiration']/1000)
        self.is_put = kwargs['is_put']

@sleep_and_retry
@limits(calls=6,period=20)
def stock_quote(symbol):
    session = Session()
    search_resp = session.post(API_URL,data=Queries.stock_search(symbol))
    search_resp.raise_for_status()

    search_data_list = json.loads(search_resp.text)['data']['searchStockSymbols']['list']
    name = ''
    for sd in search_data_list:
        if sd['symbol'] == symbol.upper():
            name = sd['description']
            symbol = sd['symbol']
            break

    exchange_resp = session.post(API_URL, data=Queries.stock_exchange(symbol))
    exchange_resp.raise_for_status()

    exchange_data = json.loads(exchange_resp.text)['data']['readStock']
    exchange = exchange_data['exchange']

    quote_resp = session.post(API_URL, data=Queries.stock_quote(symbol))
    quote_resp.raise_for_status()

    quote_data = json.loads(quote_resp.text)['data']['readStock']['technical']

    yahoo_url = "https://query1.finance.yahoo.com/v8/finance/chart/%s" % symbol
    yahoo_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    yahoo_resp = requests.get(yahoo_url,headers=yahoo_headers)
    yahoo_resp.raise_for_status()
    yahoo_data = json.loads(yahoo_resp.text)
    prev_close = yahoo_data['chart']['result'][0]['meta']['previousClose']

    stock_quote_data = {
        'symbol': symbol,
        'name': name,
        'exchange': exchange,
        'previous_close': prev_close,
        'bid': quote_data['bidPrice'],
        'ask': quote_data['askPrice'],
        'volume': quote_data['volume'],
        'day_high': quote_data['dayHighPrice'],
        'day_low': quote_data['dayLowPrice']
    }

    quote = StockQuote(**stock_quote_data)
    return quote

class QuoteWrapper(object):
    def __init__(self,symbol, underlying=None):
        self.symbol = symbol
        self.underlying = underlying

    def wrap_quote(self):
        return stock_quote(self.symbol)
    
    def wrap_option_quote(self):
        oc = OptionChain(self.underlying)
        return oc.options.get(self.symbol,None)

class CancelOrderWrapper(object):
    def __init__(self,order_id):
        self.order_id = order_id
    @sleep_and_retry
    @limits(calls=3,period=20)
    def wrap_cancel(self):
        session = Session()
        resp = session.post(API_URL,Queries.cancel_order(self.order_id))
        resp.raise_for_status()

        resp_json = json.loads(resp.text)
        if resp_json['data']['submitCancelTrade'].get('errorMessages',None) is not None:
            errors = resp_json['data']['submitCancelTrade']['errorMessages']
            for error in errors:
                warnings.warn(error)

            return False

        return True

class Parsers(object):
    @staticmethod
    @sleep_and_retry
    @limits(calls=6,period=20)
    def get_open_trades(portfolio_id):
        open_orders = []
        session = Session()

        
        open_stock_trades_response = json.loads(session.post(API_URL, data=Queries.open_stock_trades(portfolio_id)).text)
        open_option_trades_response = json.loads(session.post(API_URL, data=Queries.open_option_trades(portfolio_id)).text)
        open_short_trades_response = json.loads(session.post(API_URL, data=Queries.open_short_trades(portfolio_id)).text)

        all_open_trades_responses = [open_stock_trades_response, open_option_trades_response, open_short_trades_response]

        for open_trade_resp in all_open_trades_responses:

            open_trades = open_trade_resp['data']['readPortfolio']['holdings']['pendingTrades']
            
            for open_trade in open_trades:
                
                if open_trade['cancelDate'] is not None:
                    continue
                order_dict = {
                    'order_id': open_trade['tradeId'],
                    'symbol': open_trade['symbol'],
                    'quantity': open_trade['quantity'],
                    'order_price': open_trade['orderPriceDescription'],
                    'trade_type': open_trade['transactionTypeDescription']  
                }

                

                if order_dict['order_price'] == 'n/a':
                    try:
                        order_dict['order_price'] = open_trade['stock']['technical']['lastPrice'] * -1
                    except KeyError as e:
                        order_dict['order_price'] = open_trade['option']['lastPrice'] * -1

                wrapper = CancelOrderWrapper(order_dict['order_id'])
                order_dict['cancel_fn'] = wrapper.wrap_cancel


                open_orders.append(OpenOrder(**order_dict))
        return open_orders

    @staticmethod
    @sleep_and_retry
    @limits(calls=6,period=20)
    def generate_portfolio(portfolio_id,game_id,game_name):
        session = Session()
        resp = session.post(API_URL,Queries.portfolio_summary_query(portfolio_id))
        portfolio_response = json.loads(resp.text)
        portfolio_data = portfolio_response['data']['readPortfolio']['summary']
        
        portfolio_args = {'portfolio_id': portfolio_id, 'game_id':game_id, 'game_name':game_name}
        portfolio_args['account_value'] = portfolio_data['accountValue']
        portfolio_args['buying_power'] = portfolio_data['buyingPower']
        portfolio_args['cash'] = portfolio_data['cash']
        portfolio_args['annual_return_pct'] = portfolio_data['annualReturn']

        stock_portfolio = Parsers.generate_stock_portfolio(portfolio_id)
        short_portfolio = Parsers.generate_stock_portfolio(portfolio_id, short=True)
        option_portfolio = Parsers.generate_option_portfolio(portfolio_id)

        portfolio_args['open_orders'] = Parsers.get_open_trades(portfolio_id)
        portfolio_args['stock_portfolio'] = stock_portfolio
        portfolio_args['short_portfolio'] = short_portfolio
        portfolio_args['option_portfolio'] = option_portfolio

        return Portfolio(**portfolio_args)

    def get_portfolios():
        session = Session()
        resp = json.loads(session.post(API_URL,Queries.read_user_portfolios()).text)

        portfolio_list = resp['data']['readUserPortfolios']['list']
        portfolios = []

        for portfolio in portfolio_list:
            portfolio_id = portfolio['id']
            game_id = portfolio['game']['id']
            game_name = portfolio['game']['gameDetails']['name']
            portfolios.append(Parsers.generate_portfolio(portfolio_id,game_id,game_name))


        return portfolios

    @staticmethod
    def make_subportfolio_dict(portfolio_id, data):
        return {
            'portfolio_id': portfolio_id,
            'market_value': data['marketValue'],
            'day_gain_dollar': data['dayGainDollar'],
            'day_gain_percent': data['dayGainPercent'],
            'total_gain_dollar': data['totalGainDollar'],
            'total_gain_percent': data['totalGainPercent']
        }

    @staticmethod
    def generate_option_portfolio(portfolio_id):
        session = Session()
        resp = session.post(API_URL,data=Queries.option_holdings(portfolio_id))
        resp_data = json.loads(resp.text)
        option_data = resp_data['data']['readPortfolio']['holdings']
        summary_data = option_data['holdingsSummary']
        position_data = option_data['executedTrades']
        sub_portfolio_dict = Parsers.make_subportfolio_dict(portfolio_id,summary_data)
        positions = []
        stock_type = 'option'

        for data in position_data:
            
            option_data = data['option']
            stock_data = option_data['stock']

            position_kwargs = {
                'portfolio_id': portfolio_id,
                'symbol': option_data['symbol'],
                'is_put': option_data['isPut'],
                'last': option_data['lastPrice'],
                'expiration_date': option_data['expirationDate'],
                'strike_price': option_data['strikePrice'],
                'underlying_symbol': stock_data['symbol'],
                'description': stock_data['description'],
                'quantity': data['quantity'],
                'purchase_price': data['purchasePrice'],
                'market_value': data['marketValue'],
                'day_gain_dollar': data['dayGainDollar'],
                'day_gain_percent': data['dayGainPercent'],
                'total_gain_dollar': data['totalGainDollar'],
                'total_gain_percent': data['totalGainPercent'],
                'stock_type': stock_type
            }

            qw = QuoteWrapper(option_data['symbol'],underlying=stock_data['symbol'])
            position_kwargs['quote_fn'] = qw.wrap_option_quote
            position = OptionPosition(**position_kwargs)
            positions.append(position)

        return OptionPortfolio(positions=positions,**sub_portfolio_dict)

    @staticmethod
    def generate_stock_portfolio(portfolio_id, short=False):
        session = Session()
        resp = None
        stock_type = None
        if short:
            stock_type = 'short'
            resp = session.post(API_URL,data=Queries.short_holdings(portfolio_id))
        else:
            stock_type = 'long'
            resp = session.post(API_URL,data=Queries.stock_holdings(portfolio_id))

        resp.raise_for_status()
        resp_data = json.loads(resp.text)
        
        stock_data = resp_data['data']['readPortfolio']['holdings']
        summary_data = stock_data['holdingsSummary']
        position_data = stock_data['executedTrades']

        sub_portfolio_dict = Parsers.make_subportfolio_dict(portfolio_id,summary_data)
        positions = []

        for data in position_data:
            position_kwargs = {
                'symbol': data['symbol'],
                'portfolio_id': portfolio_id,
                'quantity': data['quantity'],
                'description': data['stock']['description'],
                'purchase_price': data['purchasePrice'],
                'market_value': data['marketValue'],
                'day_gain_dollar': data['dayGainDollar'],
                'day_gain_percent': data['dayGainPercent'],
                'total_gain_dollar': data['totalGainDollar'],
                'total_gain_percent': data['totalGainPercent'],
                'stock_type': stock_type
            }

            qw = QuoteWrapper(data['symbol'])
            position_kwargs['quote_fn'] = qw.wrap_quote
            stock_position = None

            if short:
                stock_position = ShortPosition(**position_kwargs)
            else:
                stock_position = LongPosition(**position_kwargs)
            
            positions.append(stock_position)
        
        if short:
            stock_portfolio = ShortPortfolio(positions=positions,**sub_portfolio_dict)

        else:
            stock_portfolio = StockPortfolio(positions=positions,**sub_portfolio_dict)

        return stock_portfolio