from api_models import Position,LongPosition, ShortPosition, OptionPosition
from api_models import Portfolio,StockPortfolio,ShortPortfolio,OptionPortfolio,OpenOrder
from api_models import StockQuote
from queries import Queries
from constants import OPTIONS_QUOTE_URL, API_URL
from options import OptionChainLookup, OptionChain, OptionContract
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
from IPython import embed
import warnings

@sleep_and_retry
@limits(calls=6,period=20)
def option_lookup(symbol,strike_price_proximity=3):
    logging.debug("OPTION LOOKUP FOR %s" % symbol)
    def filter_contracts(olist,stock_price,spp):
        if olist is None:
            return []
        middle_index = 0
        for i in range(len(olist)):
            if stock_price < olist[i]['StrikePrice']:
                middle_index += 1
                break
        start = middle_index - spp
        end = middle_index + spp
        if start < 0:
            start = 0
        if end > len(olist) - 1:
            end = len(olist) - 1

        return olist[start:end]


    session = Session()
    resp = session.get(UrlHelper.route('optionlookup'))
    tree = html.fromstring(resp.text)

    option_token = None
    option_user_id = None

    token = None
    user_id = None
    param_script = tree.xpath('//script[contains(text(),"quoteOptions")]/text()')[0]
    param_search = re.search(r'\#get\-quote\-options\'\)\,\s*\'(.+)\'\s*\,\s*(\d+)\s*\)\;', param_script)
    try:
        option_token = param_search.group(1)
        option_user_id = param_search.group(2)
    except Exception:
        raise Exception("Unable to get option lookup token")

    option_quote_qp = {
        'IdentifierType': 'Symbol',
        'Identifier': symbol,
        'SymbologyType': 'DTNSymbol',
        'OptionExchange': None,
        '_token': option_token,
        '_token_userid': option_user_id
    }

    url = UrlHelper.set_query(OPTIONS_QUOTE_URL, option_quote_qp)

    resp = requests.get(url)
    option_data = json.loads(resp.text)

    quote = option_data['Quote']
    if quote is None:
        logging.debug(option_data)
        raise Exception("No option quote data for %s" % symbol)


    try:
        last_price = option_data['Quote']['Last']
    except Exception as e:
        logging.debug(option_data)
        logging.debug(e)
    option_chains = []
    for e in option_data['Expirations']:
        expiration = e['ExpirationDate']
        filtered_calls = filter_contracts(e['Calls'],last_price,strike_price_proximity)
        filtered_puts = filter_contracts(e['Puts'],last_price,strike_price_proximity)
        

        calls = [OptionContract(o) for o in filtered_calls]
        puts = [OptionContract(o) for o in filtered_puts]
        option_chains.append(OptionChain(expiration,calls=calls,puts=puts))

        
    option_chain_lookup = OptionChainLookup(symbol,*option_chains)
    return option_chain_lookup


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
    def __init__(self,symbol):
        self.symbol = symbol

    def wrap_quote(self):
        return stock_quote(self.symbol)

class OptionLookupWrapper(object):
    def __init__(self,underlying,contract_symbol,contract):
        self.underlying = underlying
        self.contract_symbol = contract_symbol
        self.contract = contract

    def wrap_quote(self):
        # check if contract is expired here before doing a lookup
        if datetime.date.today() > self.contract.expiration:
            return self.contract
        return option_lookup(self.underlying)[self.contract_symbol]

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

        print("Order cancelled")
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
        option_portfolio = OptionPortfolio()

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



    @staticmethod
    def parse_and_sort_positions(tree,stock_portfolio,short_portfolio, option_portfolio):        
        trs = tree.xpath('//table[contains(@class,"table1")]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@class,"no-border"))]')
        xpath_map = {
            'portfolio_id': 'td[1]/div/@data-portfolioid',
            # stock_type': 'td[1]/div/@data-stocktype',
            'symbol': 'td[1]/div/@data-symbol',
            'description': 'td[4]/text()',
            'quantity': 'td[5]/text()',
            'purchase_price': 'td[6]/text()',
            'current_price': 'td[7]/text()',
            'total_value': 'td[8]/text()',
        }

        for tr in trs:
            # <div class="detailButton btn-expand close" id="PS_LONG_0" data-symbol="TMO" data-portfolioid="5700657" data-stocktype="long"></div>
            fon = lambda x: x[0] if len(x)> 0 else None
            position_data = {k: fon(tr.xpath(v)) for k, v in xpath_map.items()}

            stock_type = fon(tr.xpath('td[1]/div/@data-stocktype'))
            trade_link = fon(tr.xpath('td[2]/a[2]/@href'))

            if stock_type is None or trade_link is None:
                continue

            elif stock_type == 'long':
                qw = QuoteWrapper(position_data['symbol']).wrap_quote
                long_pos = LongPosition(qw, stock_type, **position_data)
                stock_portfolio.append(long_pos)
            elif stock_type == 'short':
                qw = QuoteWrapper(position_data['symbol']).wrap_quote
                short_pos = ShortPosition(qw,stock_type, **position_data)
                short_portfolio.append(short_pos)
            elif stock_type == 'option':
                contract_symbol = position_data['symbol']
                oc = OptionContract(contract_name=position_data['symbol'])
                underlying = oc.base_symbol
                quote_fn = OptionLookupWrapper(underlying,contract_symbol,oc).wrap_quote
                option_pos = OptionPosition(oc,quote_fn,stock_type, **position_data)

                option_portfolio.append(option_pos)
