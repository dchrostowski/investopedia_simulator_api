import re
from urllib import parse

from util import Util, UrlHelper

class Game(object):
    def __init__(self,name,url):
        query_str = parse.urlsplit(url).query
        query_params = parse.parse_qs(query_str)
        self.game_id = query_params['gameid'][0]
        self.name=name
        self.url=url

    def __repr__(self):
        return "\n---------------------\nGame: %s\nid: %s\nurl: %s" % (self.name, self.game_id, self.url)

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
    def __init__(self,stock,quantity,current,start=None, today_change=None,is_active=False):
        if type(stock) != Stock:
            raise InvalidStockHoldingException("stock param must be a Stock")
        self.stock = stock
        self.quantity = int(quantity)
        self.current = Util.sanitize_number(current)
        if start is not None and today_change is not None:
            is_active = True
        if is_active:
            self.start = Util.sanitize_number(start)
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
    def __init__(self, symbol, name, url, exchange=None):
        name = re.sub(r'(?:\.|\,)','',name)
        self.symbol = symbol
        self.name = name
        self.url = url
    
    def __repr__(self):
        return "%s" % self.symbol

class StockQuote(Stock):
    def __init__(self,symbol,name,last,change,change_percent,exchange=None):
        super().__init__(symbol,name,exchange)
        self.last = Util.sanitize_number(last)
        self.change = Util.sanitize_number(change)
        self.open = self.last - self.change
        self.change_percent = Util.sanitize_number(change_percent)
    
    def as_dict(self):
        return self.__dict__

    def __repr__(self):
        reprstr = "Quote for %s (%s):\n" % (self.name, self.symbol)
        if self.change_percent < 0:
            reprstr += "  down "
        elif self.change_percent > 0:
            reprstr += "  up "
        else:
            reprstr += "  flat "
        reprstr += "%s %% to $%s per share\n" % (round(self.change_percent,2), self.last)
        return reprstr

class Portfolio(list):
    def __init__(self,account_value,buying_power,cash,annual_return_pct):
        self.account_value = Util.sanitize_number(account_value)
        self.buying_power = Util.sanitize_number(buying_power)
        self.cash = Util.sanitize_number(cash)
        self.annual_return_pct = Util.sanitize_number(annual_return_pct)
        self.securities_loaded = False

    @property
    def security_map(self):
        if not self.securities_loaded:
            return {}
        else:
            for holding in self:



class StockPortfolio(Portfolio):
    def __init__(self,account_value,buying_power,cash,annual_return_pct, holdings):
        super().__init__(account_value,buying_power,cash,annual_return_pct)
        self.net_return = 0
        self.stocks_shares = {}
        self.total_value = 0
        for h in holdings:
            self.stocks_shares[h.stock.symbol] = h.quantity
            if h.is_active:
                self.net_return += h.net_return
                self.total_value += h.total_value
            self.append(h)
        
        self.securities_loaded = True

    def find_by_symbol(self,symbol):
        if symbol not in self.stocks_shares:
            return []
        holdings_to_return = []
        for holding in list(self):
            if holding.stock.symbol == symbol:
                holdings_to_return.append(holding)
        return holdings_to_return

class OptionPortfolio(Portfolio):
    def __init__(self,account_value, buying_power, cash, annual_return_pct, holdings):
        super().__init__(account_value,buying_power,cash,annual_return_pct)