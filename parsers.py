from api_models import Position,LongPosition, ShortPosition, OptionPosition
from api_models import Portfolio,StockPortfolio,ShortPortfolio,OptionPortfolio,OpenOrder
from api_models import StockQuote
from queries import Queries
from constants import OPTIONS_QUOTE_URL, API_URL
from options import OptionChain, OptionContract, OptionScope
from session_singleton import Session
from utils import UrlHelper, coerce_value
from lxml import html
import json
import re
from warnings import warn
import requests
import datetime
from ratelimit import limits,sleep_and_retry
from decimal import Decimal
import logging
import warnings
from IPython import embed

@sleep_and_retry
@limits(calls=10,period=20)
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
        return oc.chain.get(self.symbol,None)

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
        # TO DO
        #Parsers.parse_and_sort_positions(portfolio_tree,stock_portfolio,short_portfolio,option_portfolio)

        portfolio_args['open_orders'] = Parsers.get_open_trades(portfolio_id)

        #portfolio_args = {k: xpath_get(v)  for k,v in xpath_map.items()}
        
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

            qw = QuoteWrapper(option_data['symbol'],stock_data['symbol'])
            position_kwargs['quote_fn'] = qw.wrap_option_quote
            position = OptionPosition(**position_kwargs)
            embed()



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