import re
from urllib import parse
import datetime
from IPython import embed
import json

from utils import Util, UrlHelper
from constants import *
from session_singleton import Session
from stock_trade import *
import itertools

class Game(object):
    def __init__(self,name,url):
        query_params = UrlHelper.get_query_params(url)
        self.game_id = query_params['gameid']
        self.name=name
        self.url=url

    def __repr__(self):
        return "\n---------------------\nGame: %s\nid: %s\nurl: %s" % (self.name, self.game_id, self.url)

class GameList(list):
    def __init__(self,*games,active_id=None):
        self.active_id = active_id
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

        session = Session()
        resp = session.get(url)
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

class Position(object):
    def __init__(self,portfolio_id,symbol,quantity,purchase_price,current_price,total_value):
        self.portfolio_id = portfolio_id
        self.symbol = symbol
        self.quantity = quantity
        self.purchase_price = purchase_price
        self.current_price = current_price
        self.total_value = total_value
    
    @classmethod
    def from_tr_element(cls, tr):
        pass


            

class StockPosition(Position):
    def __init__(self,stock,quantity,current=None,start=None, today_change=None,is_active=False):
        if type(stock) != Stock:
            raise InvalidPositionException("StockPositions must hold stocks.  Got %s instead" % type(stock))
        super().__init__(stock,quantity,current,start,today_change,is_active)
        self.symbol = stock.symbol

       
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

class OptionPosition(Position):
    def __init__(self,option,quantity,current,start=None, today_change=None,is_active=False):
        if type(option) != Option:
            raise InvalidPositionException("OptionPositions must hold options.  Got %s instead." % type(option))
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

    @classmethod 
    def initialize(self):
        session = Session()

class StockPortfolio(list):
    def __init__(self,long_positions):
        for position in long_positions:

            


class StockPortfolio(Portfolio):
    def __init__(self,account_value,buying_power,cash,annual_return_pct, positions):
        super().__init__(account_value,buying_power,cash,annual_return_pct)
        self.net_return = 0
        self.total_value = 0
        
        for h in positions:
            if h.is_active:
                self.net_return += h.net_return
                self.total_value += h.total_value
            elif not h.is_active:
                if h.current is not None:
                    self.pending_total_value += h.total_value
            self.append(h)
            self.security_set.add(h.security.symbol)

    def find_by_symbol(self,symbol,return_pending=True):
        symbol = symbol.upper()
        if symbol not in self.security_set:
            return []
        positions_to_return = []
        for position in list(self):
            if position.security.symbol.upper() == symbol.upper():
                positions_to_return.append(position)

        return positions_to_return

    def total_positions(self,include_pending=True):
        if include_pending:
            return len(self)
        else:
            cnt = 0
            for position in list(self):
                if position.is_active:
                    cnt += 1
            return cnt

        

class OptionPortfolio(Portfolio):
    def __init__(self,account_value, buying_power, cash, annual_return_pct, positions):
        super().__init__(account_value,buying_power,cash,annual_return_pct)

'''
formToken	732b889d629872bb7b7c843574b53d74
symbolTextbox	GOOGL
symbolTextbox_mi_1_value	GOOGL
selectedValue	GOOGL
transactionTypeDropDown	1 # buy, sell, sell_short, buy_to_cover
quantityTextbox	25
isShowMax	0
Price	Limit
limitPriceTextBox	1116
stopPriceTextBox	
tStopPRCTextBox	
tStopVALTextBox	
durationTypeDropDown	2
sendConfirmationEmailCheckBox	on
'''



class OptionChainLookup(dict):
    def __init__(self,stock,calls,puts):
        self.calls = calls
        self.puts = puts

        for contract in self.calls + self.puts:
            self[contract.symbol] = contract


class OptionChain(list):
    def __init__(self,contracts):
        for contract in contracts:
            if type(contract) != OptionContract:
                raise InvalidOptionChainException("A non OptionContract object was passed to OptionChain")
            self.append(contract)
    
    @classmethod
    def parse(cls,html):
        pass

class OptionContract(object):
    def __init__(self,option_dict=None,contract_name=None):
        if option_dict is not None:
            self.raw = option_dict
            self.contract_name = option_dict['Symbol']
            self.base_symbol = option_dict['BaseSymbol']
            self.contract_type = option_dict['Type']
            self.expiration = datetime.datetime.strptime(option_dict['ExpirationDate'],'%m/%d/%Y')
            self.strike_price = option_dict['StrikePrice']
            self._last = option_dict['Last']
            self._bid = option_dict['Bid']
            self._ask = option_dict['Ask']
            self._volume = option_dict['Volume']
            self._open_int = option_dict['OpenInterest']

        elif contract_name is not None:
            re_search = re.search(r'^(\D+)(\d\d)(\d\d)([A-X])([\d\.]+$')
            if re_search is None or len(re_searc.groups() != 5):
                raise InvalidOptionException("Could not parse option symbol '%s'" % symbol)
            self.base_symbol = re_search.group(1)
            exp_year = int(int(re_search.group(2)) + 2000)
            exp_day = int(re_search.group(3))
            month_code = re_search.group(4)
            if month_code not in Constants.OPTION_MONTH_CODES:
                raise InvalidOptionException("Invalid month code '%s'" % month_code)
            self.strike_price = float(re_search.group(5))

            month_and_type_info = Constants.OPTION_MONTH_CODES[month_code]
            exp_month = month_and_type_info['month']

            self.contract_type = month_and_type_info['type']
            self.expiration = datetime.date(exp_year,exp_month,exp_day)
            self.contract_name = contract_name
            

            self._bid = None
            self._ask = None
            self._volume = None
            self._open_int = None

    @staticmethod
    def option_chain_lookup(token,token_userid,symbol):
        pass


    def do_quote_lookup(self):
        pass

    

    @property
    def bid(self):
        if self._bid is None:
            self.do_quote_lookup()
        return self._bid

    @property
    def last(self):
        if self._last is None:
            self.do_quote_lookup()
        return self._last

    @property
    def ask(self):
        if self._ask is None:
            self.do_quote_lookup()
        return self._ask

    @property
    def volume(self):
        if self._volume is None:
            self.do_quote_lookup()
        return self._volume

    @property
    def open_int(self):
        if self._open_int is None:
            self.do_quote_lookup()
        return self._open_int


    @property
    def current(self):
        return self.last

    @property
    def symbol(self):
        return self.contract_name


                

                

            
class OptionTrade(object):
    pass



        
