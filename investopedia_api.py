from api_models import *
from constants import *
from utils import UrlHelper, Util
from session_singleton import Session

from IPython import embed
import requests
from lxml import html
import json
import re
from urllib import parse
import warnings
import logging
import copy
logging.basicConfig(level=logging.INFO)


class InvestopediaSimulatorAPI(object):
    def __init__(self, auth_cookie):
        self._auth_cookie = None
        self.auth_cookie = auth_cookie

        
        self._stock_portfolio = None
        self._option_portfolio = None
        self._games = None
        self._active_game = None

        self._user_id = None

        self.option_token = None
        self.option_user_id = None

    @property
    def auth_cookie(self):
        return self._auth_cookie

    @auth_cookie.setter
    def auth_cookie(self,ac):
        if ac is None:
            raise InvestopediaAuthException("Why are you setting the auth cookie to None?  Don't do that.")
        
        if ac != self._auth_cookie:
            print("Logging in as new user")
        
        if not Session.is_logged_in() or Session().cookies.get('UI4') != ac:
            Session.login(ac)

        self._auth_cookie = ac
        

    def route(self,page_name):
        return UrlHelper.route(page_name)
    

    def get_quote(self, symbol):
        url = self.route('lookup')
        resp = self.session.post(url, data={'symbol': symbol})
        if resp.status_code == 200 and int(resp.headers['content-length']) > 0:
            tree = html.fromstring(resp.text)
            xpath_map = {
                'name': '//h3[@class="companyname"]/text()',
                'symbol': '//table[contains(@class,"table3")]/tbody/tr[1]/td[1]/h3[contains(@class,"pill")]/text()',
                'exchange': '//table[contains(@class,"table3")]//div[@class="marketname"]/text()',
                'last': '//table[@id="Table2"]/tbody/tr[1]/th[contains(text(),"Last")]/following-sibling::td/text()',
                'change': '//table[@id="Table2"]/tbody/tr[2]/th[contains(text(),"Change")]/following-sibling::td/text()',
                'change_percent': '//table[@id="Table2"]/tbody/tr[3]/th[contains(text(),"% Change")]/following-sibling::td/text()'
            }
            try:
                stock_quote_data = {
                    k: str(tree.xpath(v)[0]).strip() for k, v in xpath_map.items()}
            except IndexError:
                print("Could not get quote for %s" % symbol)
                return

            exchange_matches = re.search(
                r'^\(([^\)]+)\)$', stock_quote_data['exchange'])
            if exchange_matches:
                stock_quote_data['exchange'] = exchange_matches.group(1)

            quote = StockQuote(**stock_quote_data)
            return quote

    @property
    def option_portfolio(self):
        if self._option_portfolio is None:
            self._get_option_portfolio()
        return self._option_portfolio

    def _get_option_portfolio(self):
        resp = self.session.get(self.route('portfolio'))
        tree = html.fromstring(resp.content.decode())

        pending_rows = tree.xpath('//table[@id="option-portfolio-table"]//tr[contains(@style,"italic")]')
        active_rows = tree.xpath('//table[@id="option-portfolio-table"]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@style,"italic"))]')


        active_contracts = self._get_active_option_portfolio(active_rows)
        pending_contracts = self._get_pending_option_portfolio(tree)

        embed()

        all_contracts = active_contracts + pending_contracts
        #self._option_portfolio = StockPortfolio(**portfolio_metadata, positions=all_positions)

    def _get_active_option_portfolio(self,rows):
        pass

    def _get_pending_option_portfolio(self,tree):
        pass

    @property
    def stock_portfolio(self):
        if self._stock_portfolio is None:
            self._get_stock_portfolio()
        return self._stock_portfolio

    def _get_active_stock_portfolio(self, rows):
        stock_td_map = {
            'name': 'td[4]/text()|td[3]/a[2]/text()',
            'symbol': 'td[3]/a[2]/text()',
            'url': 'td[3]/a[2]/@href',
        }
        position_td_map = {
            'quantity': 'td[5]/text()',
            'start': 'td[6]/text()',
            'current': 'td[7]/text()',
            'today_change': 'td[9]/text()'
        }

        positions = []
        for tr in rows:
            try:
                stock_data = {field: tr.xpath(
                    xpr)[0] for field, xpr in stock_td_map.items()}
                position_data = {field: tr.xpath(
                    xpr)[0] for field, xpr in position_td_map.items()}
            except IndexError as e:
                raise(e)

            stock = Stock(**stock_data)
            position = StockPosition(
                stock=stock, **position_data, is_active=True)

            positions.append(position)

        return positions

    def _get_pending_stock_portfolio(self, portfolio_tree):
        open_trades_resp = self.session.get(self.route('opentrades'))
        ot_tree = html.fromstring(open_trades_resp.text)

        rows = ot_tree.xpath(
            '//table[@class="table1"]/tbody/tr[@class="table_data"]/td[2]/a/parent::td/parent::tr')
        # //table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]

        pending_positions = []

        for tr in rows:

            buy_or_sell = re.search(
                r'(Buy|Sell)', tr.xpath('td[4]/text()')[0]).group(1)
            symbol = tr.xpath('td[5]/a/text()')[0]
            url = tr.xpath('td[5]/a/@href')[0]
            stock = Stock(name=symbol, symbol=symbol, url=url)
            current = None

            if buy_or_sell == 'Buy':
                # will only assign a "current price" to pending Buy market / stop / limit orders
                current = tr.xpath('td[7]/text()')[0]
                cmatch = re.search(
                    r'(?:Stop|Limit)[\s?\-]+\$([\d\.]+)', current)
                if cmatch and current != 'n/a':
                    current = cmatch.group(1)
                else:
                    try:
                        order_id = tr.xpath('td[1]/text()')[0]
                        current_price = portfolio_tree.xpath(
                            '//table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]//span[contains(@id,"%s")]/ancestor::tr/td[5]/span/text()' % order_id)[0]
                        current = re.sub(r'[^\d\.]+', '', current_price)
                    except IndexError as e:
                        current = self.get_quote(symbol).last

            quantity = int(tr.xpath('td[6]/text()')[0])

            position_data = {
                'stock': stock,
                'quantity': quantity,
                'start': None,
                'today_change': None,
                'is_active': False,
                'current': current
            }

            pending_positions.append(StockPosition(**position_data))

        return pending_positions

    def _get_stock_portfolio(self):

        resp = self.session.get(self.route('portfolio'))
        tree = html.fromstring(resp.content.decode())

        xpath_prefix = '//div[@id="infobar-container"]/div[@class="infobar-title"]/p'

        xpath_map = {
            'account_value': '/strong[contains(text(),"Account Value")]/following-sibling::span/text()',
            'buying_power':  '/strong[contains(text(),"Buying Power")]/following-sibling::span/text()',
            'cash':          '/strong[contains(text(),"Cash")]/following-sibling::span/text()',
            'annual_return_pct': '/strong[contains(text(),"Annual Return")]/following-sibling::span/text()',
        }

        portfolio_metadata = {k: str(tree.xpath("%s%s" % (xpath_prefix, v))[
                                     0]) for k, v in xpath_map.items()}

        pending_rows = tree.xpath(
            '//table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]')
        active_rows = tree.xpath(
            '//table[@id="stock-portfolio-table"]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@style,"italic"))]')

        active_positions = self._get_active_stock_portfolio(active_rows)
        pending_positions = self._get_pending_stock_portfolio(tree)

        all_positions = active_positions + pending_positions
        self._stock_portfolio = StockPortfolio(
            **portfolio_metadata, positions=all_positions)

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
        rows = tree.xpath(
            '//table[contains(@class,"table1")]//tr[position()>1]')
        for row in rows:
            url = row.xpath('td[1]/a/@href')[0]
            name = row.xpath('td[1]/a/text()')[0]
            game = Game(name, url)
            status = row.xpath('td[2]/a')
            if len(status) < 1:
                active = game.game_id

            games.append(game)

        self._games = GameList(*games, session=self.session, active_id=active)

    def _get_option_trade_form_token(self):
        resp = self.session.get(self.route('tradeoption'))
        tree = html.fromstring(resp.text)
        token = tree.xpath(
            '//div[@class="group"]//form[@id="orderForm"]/input[@name="formToken"]/@value')[0]
        return

    def trade_stock(self, trade_object):
        pass
        #form_data = trade_object.prepare()

    def option_lookup(self, symbol):

        if self.option_token is None or self.option_user_id is None:
            resp = self.session.get(self.route('tradeoption'))
            tree = html.fromstring(resp.text)

            token = None
            user_id = None
            param_script = tree.xpath(
                '//script[contains(text(),"quoteOptions")]/text()')[0]
            param_search = re.search(
                r'\#get\-quote\-options\'\)\,\s*\'(.+)\'\s*\,\s*(\d+)\s*\)\;', param_script)
            if param_search:
                self.option_token = param_search.group(1)
                self.option_user_id = param_search.group(2)

        option_quote_qp = {
            'IdentifierType': 'Symbol',
            'Identifier': symbol,
            'SymbologyType': 'DTNSymbol',
            'OptionExchange': None,
            '_token': self.option_token,
            '_token_userid': self.option_user_id
        }

        url = UrlHelper.set_query(Constants.OPTIONS_QUOTE_URL, option_quote_qp)

        resp = requests.get(url)
        option_chain = json.loads(resp.text)
        calls = []
        puts = []
        stock = self.get_quote(symbol)

        for e in option_chain['Expirations']:
            for call in e['Calls']:
                calls.append(OptionContract(call))
            for put in e['Puts']:
                puts.append(OptionContract(put))

        call_option_chain = OptionChain(calls)
        put_option_chain = OptionChain(puts)
        option_chain_lookup = OptionChainLookup(
            stock=stock, calls=call_option_chain, puts=put_option_chain)
        return option_chain_lookup
