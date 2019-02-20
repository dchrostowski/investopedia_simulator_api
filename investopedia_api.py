from IPython import embed
import requests
from lxml import html
import json
import re
from urllib import parse
import warnings
import logging
logging.basicConfig(level=logging.INFO)

class InvestopediaAuthException(Exception):
    pass

class InvalidActiveGameException(Exception):
    pass

class DuplicateGameException(Exception):
    pass

class SetActiveGameException(Exception):
    pass

class InvalidGameException(Exception):
    pass

class InvalidStockHoldingException(Exception):
    pass

class InvalidStockHoldingException(Exception):
    pass

class Constants(object):
    BASE_URL = 'https://www.investopedia.com/simulator'
    PATHS = {
        'portfolio': '/portfolio/',
        'games': '/game',
        'home': '/home.aspx',
    }

class Game(object):
    def __init__(self,name,url):
        query_str = parse.urlsplit(url).query
        query_params = parse.parse_qs(query_str)
        self.game_id = query_params['gameid'][0]
        self.name=name
        self.url=url

    def __repr__(self):
        return "\n---------------------\nGame: %s\nid: %s\nurl: %s" % (self.name, self.game_id, self.url)

# Needed this because urllib is a bit clunky/confusing
class UrlHelper(object):
    @staticmethod
    def append_path(url,path):
        parsed = parse.urlparse(url)
        existing_path = parsed._asdict()['path']
        new_path = "%s%s" % (existing_path,path)
        return UrlHelper.set_field(url,'path',new_path)

    @staticmethod
    def set_path(url,path):
        return UrlHelper.set_field(url,'path',path)

    @staticmethod
    def set_query(url,query_dict):
        query_string = parse.urlencode(query_dict)
        return UrlHelper.set_field(url,'query',query_string)
    
    @staticmethod
    def set_field(url,field,value):
        parsed = parse.urlparse(url)
        # is an ordered dict
        parsed_dict = parsed._asdict()
        parsed_dict[field] = value
        return parse.urlunparse(tuple(v for k,v in parsed_dict.items()))

class GameList(list):
    def __init__(self,*games,session,active_id=None):
        self.active_id = active_id
        self.session=session
        self.games = {}
        for game in games:
            if type(game) != Game:
                raise InvalidGameException("Object is not a game")
            if game.game_id in self.games:
                raise DuplicateGameException("Duplicate game '%s' (id=%s)" % (game.name,game.game_id))
            
            self.games.update({game.game_id: game})
            self.append(game)

        if self.active_id is None:
            warnings.warn("No active game in game list")
        elif self.active_id not in self.games:
            raise InvalidActiveGameException("Invalid active game id '%s' specified" % self.active_id)
    
    def __repr__(self):
        rpr =  ",\n".join([game.__repr__() for game in list(self)])
        return "[\n%s\n]" % rpr

    def route(self,page_name):
        return UrlHelper.append_path(Constants.BASE_URL,self.routes[page_name])

    @property
    def routes(self):
        return Constants.PATHS

    @property
    def active(self):
        if self.active_id is None:
            return None
        return self.games[self.active_id]

    @active.setter
    def active(self,game_or_gid):
        active_id = None
        if type(game_or_gid) == Game:
            active_id = str(game_or_gid.game_id)
        else:
            active_id = str(game_or_gid)
        if active_id not in self.games:
            raise InvalidActiveGameException("Invalid active game id on set")
        query_params = {'SDGID':active_id}
        
        url = self.route('games')
        url = UrlHelper.set_query(url,{'SDGID':active_id})
        resp = self.session.get(url)
        if resp.status_code == 200:
            self.active_id = active_id
        else:
            raise SetActiveGameException("Server returned back error: %s" % resp.status_code)

class StockHolding(object):
    @staticmethod
    def strip_dollars(amt):
        match = re.search(r'^\$(\d+\.\d+)',amt)
        if match:
            return float(match.group(1))
        else:
            try:
                return float(amt)
            except ValueError:
                raise InvalidStockHoldingException("Unable to parse %s as a number" % amt)


    def __init__(self,stock,quantity,current,start=None, today_change=None,is_active=False):
        if type(stock) != Stock:
            raise InvalidStockHoldingException("stock param must be a Stock")
        self.stock = stock
        self.quantity = int(quantity)
        self.current = StockHolding.strip_dollars(current)
        if start is not None and today_change is not None:
            is_active = True
        if is_active:
            self.start = StockHolding.strip_dollars(start)
            self.today_change = today_change
        else:
            self.start = None
            self.today_change = None

        self.is_active=is_active

    @property
    def net_return(self):
        if not self.is_active:
            return 0
        net = self.current - self.start
        net *= self.quantity
        return round(net,2)

    @property
    def total_value(self):
        return round(self.current * self.quantity,2)

    def __repr__(self):
        if self.is_active:
            return "\n[%s shares of %s]\n  start: $%s\n  current: $%s\n  net: $%s\n" % (self.quantity,self.stock.symbol, self.start, self.current, self.net_return)
        else:
            return "\n[%s shares of %s] (PENDING)\n  current: %s\n" % (self.quantity, self.stock.symbol, self.current)

class Stock(object):
    def __init__(self, symbol, name, url):
        name = re.sub(r'(?:\.|\,)','',name)
        self.symbol = symbol
        self.name = name
        self.url = url
    
    def __repr__(self):
        return "%s" % self.symbol

class StockPortfolio(list):
    def __init__(self,*holdings):
        self.net_return = 0
        self.stocks_shares = {}
        self.total_value = 0
        for h in holdings:
            self.stocks_shares[h.stock.symbol] = h.quantity
            if h.is_active:
                self.net_return += h.net_return
                self.total_value += h.total_value
            self.append(h)

    def find_by_symbol(self,symbol):
        if symbol not in self.stocks_shares:
            return []
        holdings_to_return = []
        for holding in list(self):
            if holding.stock.symbol == symbol:
                holdings_to_return.append(holding)
        return holdings_to_return

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
    
    # lookup: POST https://www.investopedia.com/simulator/stocks/symlookup.aspx
    # body: asbDescription=FCAP&selectedValue=&btnLookup=Lookup+Symbol 

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

            stock_data['name'] = re.sub(r'(?:\.|\,)','',stock_data['name'])

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

        pending_rows = tree.xpath('//table[@id="stock-portfolio-table"]//tr[contains(@style,"italic")]')
        active_rows = tree.xpath('//table[@id="stock-portfolio-table"]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@style,"italic"))]')
        
        pending_holdings = self._get_pending_stock_portfolio(pending_rows)
        active_holdings = self._get_active_stock_portfolio(active_rows)
        all_holdings = active_holdings + pending_holdings
        self._stock_portfolio = StockPortfolio(*all_holdings)

        

    @property
    def active_game(self):
        return self.games.active
    
    @property
    def games(self):
        if self._games is None:
            self._get_games()
        return self._games

    def _get_games(self):
        self._games = []
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

            games.append(Game(name,url))
        
        self._games = GameList(*games,session=self.session,active_id=active)
            

