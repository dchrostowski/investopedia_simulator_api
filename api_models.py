import re
from urllib import parse
import datetime
from IPython import embed

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

class Security(object):
    def __init__(self,symbol,name,security_type):
        self.symbol = symbol
        self.name = name
        self.security_type = security_type

class Option(Security):
    def __init__(self,symbol,name):
        super().__init__(symbol,name,Option)
        option_type_match = re.search(r'\d+([A-Z])[\d\.]+$',symbol)
        if not option_type_match:
            raise InvalidOptionException("Could not determine if the option is a call or a put, check symbol")
        
        option_code = option_type_match.group(1)
        if re.search(r'^([A-L])$',option_code):
            self.option_type = 'call'
        else:
            self.option_type = 'put'

class Stock(Security):
    def __init__(self, symbol, name, url, exchange=None):
        # only want to do this for stocks because we derive info about options from the unadulterated name
        name = re.sub(r'(?:\.|\,)','',name).upper()
        super().__init__(symbol,name,Stock)
        self.url = url
        self.exchange = exchange
    
    def __repr__(self):
        return "%s" % self.symbol

class Holding(object):
    def __init__(self,security,quantity,current,start=None, today_change=None, is_active=False):
        if not issubclass(type(security),Security):
            raise InvalidHoldingException("Must be a security (option or stock)")
        self.security = security
        self.quantity = int(quantity)
        self.current = Util.sanitize_number(current)
        today_change_percent = None
        if start is not None and today_change is not None:
            is_active = True
        if is_active:
            start = Util.sanitize_number(start)
            change_match = re.search(r'^\$([\d\.]+)\(([\d\.]+)\s?\%\)\s*?$',today_change)
            if change_match:
                today_change = float(change_match.group(1))
                today_change_percent = float(change_match.group(2))
        
        self.is_active = is_active
        self.start = start
        self.today_change = today_change
        self.today_change_percent = today_change_percent

        self.total_value = self.current * self.quantity
            
        if self.security.security_type == Option:
            self.total_value = self.total_value * 100
            

class StockHolding(Holding):
    def __init__(self,stock,quantity,current,start=None, today_change=None,is_active=False):
        if type(stock) != Stock:
            raise InvalidHoldingException("StockHoldings must hold stocks.  Got %s instead" % type(stock))
        super().__init__(stock,quantity,current,start,today_change,is_active)
       
    @property
    def net_return(self):
        if not self.is_active:
            return 0
        net = self.current - self.start
        net *= self.quantity
        return round(net,2)

    def __repr__(self):
        if self.is_active:
            return "\n  %s shares of %s\n  start: $%s\n  current: $%s\n  net: $%s\n" % (self.quantity,self.security.symbol, self.start, self.current, self.net_return)
        else:
            return "\n  %s shares of %s (PENDING)\n  current: %s\n" % (self.quantity, self.security.symbol, self.current)

class OptionHolding(Holding):
    def __init__(self,option,quantity,current,start=None, today_change=None,is_active=False):
        if type(option) != Option:
            raise InvalidHoldingException("OptionHoldings must hold options.  Got %s instead." % type(option))
        super().__init__(option,quantity,current,start,today_change,is_active)

        date_strike_match = re.search(r'^(\d{4}\/\d{2}\/\d{2})[^\$]+\$([\d\.]+)$',self.security.name)
        if date_strike_match:
            self.expiration = datetime.strptime(date_strike_match.group(1),'%Y/%m/%d')
            self.strike_price = float(date_strike_match.group(2))
        else:
            raise InvalidOptionException("Could not parse expiration date and/or strike price from name")
        


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
        self.security_set = set()

class StockPortfolio(Portfolio):
    def __init__(self,account_value,buying_power,cash,annual_return_pct, holdings):
        super().__init__(account_value,buying_power,cash,annual_return_pct)
        self.net_return = 0
        self.total_value = 0
        for h in holdings:
            if h.is_active:
                self.net_return += h.net_return
                self.total_value += h.total_value
            self.append(h)
            self.security_set.add(h.security.symbol)

    def find_by_symbol(self,symbol):
        symbol = symbol.upper()
        if symbol not in self.security_set:
            return None
        holdings_to_return = []
        for holding in list(self):
            if holding.security.symbol == symbol:
                holdings_to_return.append(holding)

        if len(holdings_to_return) < 2:
            return holdings_to_return[0]
        
        return holdings_to_return
        

class OptionPortfolio(Portfolio):
    def __init__(self,account_value, buying_power, cash, annual_return_pct, holdings):
        super().__init__(account_value,buying_power,cash,annual_return_pct)