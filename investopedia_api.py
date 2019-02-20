from IPython import embed
import requests
from lxml import html
import json
import re
from urllib import parse
import warnings
import logging
logging.basicConfig(level=logging.DEBUG)

from util import UrlHelper, Util
from constants import *
from api_models import Game, GameList, StockPortfolio, Stock, StockHolding, StockQuote

class InvestopediaSimulatorAPI(object):
    def __init__(self,auth_cookie):
        # auth cookie is UI4
        self.auth_cookie_value = auth_cookie
        self._session=None
        self._stock_portfolio = None
        self._games = None
        
        self._active_game = None
        self.login()
    
    @property
    def session(self):
        if self._session is None:
            self.login()
        return self._session

    def route(self,page_name):
        return UrlHelper.append_path(Constants.BASE_URL,self.routes[page_name])

    @property
    def routes(self):
        return Constants.PATHS

    def get_quote(self,symbol):
        url = self.route('lookup')
        url = UrlHelper.set_query(url,{'s':symbol})
        resp = self.session.get(url)
        if resp.status_code == 200:
            tree = html.fromstring(resp.text)
            xpath_map = {
                'name': '//section[@id="Overview"]/div[@class="inner"]//span[@id="quoteName"]/text()',
                'symbol': '//section[@id="Overview"]/div[@class="inner"]//span[@id="quoteSymbol"]/text()',
                'exchange': '//section[@id="Overview"]/div[@class="inner"]//span[@id="quoteExchange"]/text()',
                'last': '//section[@id="Overview"]//table[@class="ticker"]//tr/td[@id="quotePrice"]/text()',
                'change': '//section[@id="Overview"]//table[@class="ticker"]//tr/td[@class="value-change"]/span[@id="quoteChange"]/text()',
                #'change_percent': '//table[@id="Table2"]/tbody/tr/th[text()="% Change"]/following-sibling::td/text()',
                #'high': '//table[@id="Table2"]/tbody/tr/th[text()="Day\'s High"]/following-sibling::td/text()',
                #'low': '//table[@id="Table2"]/tbody/tr/th[text()="Day\'s Low"]/following-sibling::td/text()',
                #'volume': '//table[@id="Table2"]/tbody/tr/th[text()="Volume"]/following-sibling::td/text()',
            }
            stock_quote_data = {k: str(tree.xpath(v)[0]).strip() for k,v in xpath_map.items()}
            
            
            matches = re.search(r'^\(([^\)]+)\)$', stock_quote_data['exchange'])
            if matches:
                stock_quote_data['exchange'] = matches.group(1)
            
            change_matches = re.search(r'(-?\d+?\.?\d+)\s*\((-?\d+?\.\d+)\%\)',stock_quote_data['change'])
            if change_matches:
                stock_quote_data['change'] = change_matches.group(1)
                stock_quote_data['change_percent'] = change_matches.group(2)

            quote = StockQuote(**stock_quote_data)
            return quote

    def login(self):
        url = self.route('portfolio')
        self._session = requests.Session()

        auth_cookie = {
            "version":0,
            "name":'UI4',
            "value":self.auth_cookie_value,
            "port":None,
            # "port_specified":False,
            "domain":'www.investopedia.com',
            # "domain_specified":False,
            # "domain_initial_dot":False,
            "path":'/',
            # "path_specified":True,
            "secure":False,
            "expires":None,
            "discard":True,
            "comment":None,
            "comment_url":None,
            "rest":{},
            "rfc2109":False
        }

        self.session.cookies.set(**auth_cookie)
        self.auth_cookie = auth_cookie

        resp = self.session.get(self.route('home'))
        if resp.status_code != 200:
            raise InvestopediaAuthException("Got status code %s when fetching home %s" % (resp.status_code,self.route('home')))
        tree = html.fromstring(resp.text)
        sign_out_link = tree.xpath('//div[@class="left-nav"]//ul/li/a[text()="Sign Out"]')
        if len(sign_out_link) < 1:
            raise InvestopediaAuthException("Could not authenticate with cookie")

    @property
    def stock_portfolio(self):
        if self._stock_portfolio is None:
            self._get_stock_portfolio()
        return self._stock_portfolio

    def _get_active_stock_portfolio(self,rows):
        stock_td_map = {
            'name': 'td[4]/text()',
            'symbol': 'td[3]/a[2]/text()',
            'url': 'td[3]/a[2]/@href',
        }
        holding_td_map = {
            'quantity': 'td[5]/text()',
            'start': 'td[6]/text()',
            'current': 'td[7]/text()',
            'today_change': 'td[9]/text()'
        }
        holdings = []
        for tr in rows:
            stock_data = {field: tr.xpath(xpr)[0] for field, xpr in stock_td_map.items()}
            holding_data = {field: tr.xpath(xpr)[0] for field, xpr in holding_td_map.items()}

            stock = Stock(**stock_data)
            holding = StockHolding(stock=stock,**holding_data, is_active=True)

            holdings.append(holding)
        
        return holdings

    def _get_pending_stock_portfolio(self,rows):
        portfolio_data = []

        td_map_stock = {
            'url': 'td[2]/span/a/@href',
            'symbol': 'td[2]/span/a/text()',
            'name': 'td[2]/span/text()',
        }

        td_map_holding = {
            #'id': 'td[1]/span/span/@id',
            #'cancel_href': 'td[1]/span/span/a[1]/@href',
            #'edit_href': 'td[1]/span/span/a[2]/@href',
            #'symbol': 'td[2]/span/a/text()',
            #'url': 'td[2]/span/a/@href',
            #'company_name': 'td[2]/span/text()',
            'quantity': 'td[3]/span/text()',
            #'info': 'td[4]/span/text()',
            #'start': 'td[5]/span/text()',
            'current': 'td[5]/span/text()'
        }

        pending_holdings = []
        for tr in rows:
            stock_data = {k:tr.xpath(v)[0] for k,v in td_map_stock.items()}

            #stock,quantity,start,current,today_change
            holding_data = {k:tr.xpath(v)[0] for k,v, in td_map_holding.items()}
            holding_data['quantity'] = re.sub('Qty:\xa0','',holding_data['quantity']).strip()
            holding_data['current'] = re.sub('Current Price:\xa0','', holding_data['current']).strip()
            
            missing = {
                'stock': Stock(**stock_data),
                'today_change': None
            }
            holding_data.update(missing)
            
            pending_holdings.append(StockHolding(**holding_data))

        
        return pending_holdings


    def _get_stock_portfolio(self):

        resp = self.session.post(self.route('portfolio'))
        tree = html.fromstring(resp.content.decode())

        xpath_prefix = '//div[@id="infobar-container"]/div[@class="infobar-title"]/p'

        xpath_map = {
            'account_value': '/strong[contains(text(),"Account Value")]/following-sibling::span/text()',
            'buying_power':  '/strong[contains(text(),"Buying Power")]/following-sibling::span/text()',
            'cash':          '/strong[contains(text(),"Cash")]/following-sibling::span/text()',
            'annual_return_pct': '/strong[contains(text(),"Annual Return")]/following-sibling::span/text()', 
        }

        portfolio_metadata = {k: str(tree.xpath("%s%s" % (xpath_prefix, v))[0]) for k,v in xpath_map.items()}

        pending_rows = tree.xpath('//table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]')
        active_rows = tree.xpath('//table[@id="stock-portfolio-table"]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@style,"italic"))]')
        
        pending_holdings = self._get_pending_stock_portfolio(pending_rows)
        active_holdings = self._get_active_stock_portfolio(active_rows)
        all_holdings = active_holdings + pending_holdings
        self._stock_portfolio = StockPortfolio(**portfolio_metadata, holdings=all_holdings)

        

    @property
    def active_game(self):
        return self.games.active
    
    @property
    def games(self):
        if self._games is None:
            self._get_games()
        return self._games

    def _get_games(self):
        games = []
        resp = self.session.get(self.route('games'))
        tree = html.fromstring(resp.content.decode())
        rows = tree.xpath('//table[contains(@class,"table1")]//tr[position()>1]')
        for row in rows:
            url = row.xpath('td[1]/a/@href')[0]
            name = row.xpath('td[1]/a/text()')[0]
            game = Game(name,url)
            status = row.xpath('td[2]/a')
            if len(status) < 1:
                active = game.game_id

            games.append(game)
        
        self._games = GameList(*games,session=self.session,active_id=active)
