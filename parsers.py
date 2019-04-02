
from IPython import embed
from api_models import Position,LongPosition, ShortPosition, OptionPosition
from api_models import Portfolio,StockPortfolio,ShortPortfolio,OptionPortfolio,OpenOrder
from api_models import StockQuote
from constants import *
from options import OptionChainLookup, OptionChain, OptionContract
from session_singleton import Session
from utils import UrlHelper, coerce_value
from lxml import html
import json
import re
from warnings import warn
import requests
import datetime

def option_lookup(symbol):
    session = Session()
    resp = session.get(UrlHelper.route('tradeoption'))
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

    url = UrlHelper.set_query(Constants.OPTIONS_QUOTE_URL, option_quote_qp)

    resp = requests.get(url)
    option_chain = json.loads(resp.text)
    calls = []
    puts = []
    

    for e in option_chain['Expirations']:
        for call in e['Calls']:
            calls.append(OptionContract(call))
        for put in e['Puts']:
            puts.append(OptionContract(put))

    call_option_chain = OptionChain(calls)
    put_option_chain = OptionChain(puts)
    option_chain_lookup = OptionChainLookup(
        stock=symbol, calls=call_option_chain, puts=put_option_chain)
    return option_chain_lookup



def stock_quote(symbol):
    
    url = UrlHelper.route('lookup')
    session = Session()
    resp = session.post(url, data={'symbol': symbol})
    resp.raise_for_status()
    with open('/home/dan/quotebox.html','w') as ofh:
        ofh.write(resp.text)
    
    tree = html.fromstring(resp.text)
    xpath_map = {
        'name': '//h3[@class="companyname"]/text()',
        'symbol': '//table[contains(@class,"table3")]/tbody/tr[1]/td[1]/h3[contains(@class,"pill")]/text()',
        'exchange': '//table[contains(@class,"table3")]//div[@class="marketname"]/text()',
        'last': '//table[@id="Table2"]/tbody/tr[1]/th[contains(text(),"Last")]/following-sibling::td/text()',
        'change': '//table[@id="Table2"]/tbody/tr[2]/th[contains(text(),"Change")]/following-sibling::td/text()',
        'change_percent': '//table[@id="Table2"]/tbody/tr[3]/th[contains(text(),"% Change")]/following-sibling::td/text()',
        'volume': '//table[@id="Table2"]/tbody/tr[4]/th[contains(text(),"Volume")]/following-sibling::td/text()'
    }
    try:
        stock_quote_data = {
            k: str(tree.xpath(v)[0]).strip() for k, v in xpath_map.items()}
    except IndexError:
        warn("Unable to parse quote ")
        

    exchange_matches = re.search(
        r'^\(([^\)]+)\)$', stock_quote_data['exchange'])
    if exchange_matches:
        stock_quote_data['exchange'] = exchange_matches.group(1)

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



class Parsers(object):
    
    @staticmethod
    def get_open_trades(portfolio_tree):
        session = Session()
        open_trades_resp = session.get(UrlHelper.route('opentrades'))
        open_tree = html.fromstring(open_trades_resp.text)
        open_trade_rows = open_tree.xpath('//table[@class="table1"]/tbody/tr[@class="table_data"]/td[2]/a/parent::td/parent::tr')

        ot_xpath_map = {
            'order_id': 'td[1]/text()',
            'symbol': 'td[5]/a/text()',
            'cancel_link': 'td[2]/a/@href',
            'order_date': 'td[3]/text()',
            'quantity': 'td[6]/text()',
            'order_price': 'td[7]/text()',
        
        }

        open_orders = []

        for tr in open_trade_rows:
            fon = lambda x: x[0] if len(x)> 0 else None
            open_order_dict = {k:fon(tr.xpath(v)) for k,v in ot_xpath_map.items()}
            if open_order_dict['order_price'] == 'n/a':
                oid = open_order_dict['order_id']
                quantity = int(open_order_dict['quantity'])
                pxpath = '//table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]//span[contains(@id,"%s")]/ancestor::tr/td[5]/span/text()' % oid
                current_price = coerce_value(fon(portfolio_tree.xpath(pxpath)),float)
                open_order_dict['order_price'] = current_price * quantity
            
            print(open_order_dict)
            open_orders.append(OpenOrder(**open_order_dict))
        
        return open_orders

    @staticmethod
    def get_portfolio():
        session = Session()
        portfolio_response = session.get(UrlHelper.route('portfolio'))
        portfolio_tree = html.fromstring(portfolio_response.text)

        stock_portfolio = StockPortfolio()
        short_portfolio = ShortPortfolio()
        option_portfolio = OptionPortfolio()

        Parsers.parse_and_sort_positions(portfolio_tree,stock_portfolio,short_portfolio,option_portfolio)

        xpath_prefix = '//div[@id="infobar-container"]/div[@class="infobar-title"]/p'

        xpath_map = {
            'account_value': '/strong[contains(text(),"Account Value")]/following-sibling::span/text()',
            'buying_power':  '/strong[contains(text(),"Buying Power")]/following-sibling::span/text()',
            'cash':          '/strong[contains(text(),"Cash")]/following-sibling::span/text()',
            'annual_return_pct': '/strong[contains(text(),"Annual Return")]/following-sibling::span/text()',
        }

        xpath_get = lambda xpth: portfolio_tree.xpath("%s%s" % (xpath_prefix,xpth))[0]

        portfolio_args = {k: xpath_get(v)  for k,v in xpath_map.items()}
        portfolio_args['stock_portfolio'] = stock_portfolio
        portfolio_args['short_portfolio'] = short_portfolio
        portfolio_args['option_portfolio'] = option_portfolio
        open_orders = Parsers.get_open_trades(portfolio_tree)
        for order in open_orders:
            print(order.__dict__)
        return Portfolio(**portfolio_args)

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
            position_data = {k: tr.xpath(v)[0] for k, v in xpath_map.items()}

            stock_type = tr.xpath('td[1]/div/@data-stocktype')[0]
            trade_link = tr.xpath('td[2]/a[2]/@href')[0]

            if stock_type == 'long':
                qw = QuoteWrapper(position_data['symbol']).wrap_quote
                long_pos = LongPosition(qw, stock_type, **position_data)
                stock_portfolio.append(long_pos)
            if stock_type == 'short':
                qw = QuoteWrapper(position_data['symbol']).wrap_quote
                short_pos = ShortPosition(qw,stock_type, **position_data)
                short_portfolio.append(short_pos)
            if stock_type == 'option':
                contract_symbol = position_data['symbol']
                oc = OptionContract(contract_name=position_data['symbol'])
                underlying = oc.base_symbol
                quote_fn = OptionLookupWrapper(underlying,contract_symbol,oc).wrap_quote
                option_pos = OptionPosition(oc,quote_fn,stock_type, **position_data)

                option_portfolio.append(option_pos)                

    
    @staticmethod 
    def parse_trade(link):
        session = Session()
        resp = session.get(link)
        with open('/home/dan/trade.html') as ofh:
            ofh.write(resp.text)