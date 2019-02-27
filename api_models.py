import re
from urllib import parse
import datetime
from IPython import embed
import json

from utils import Util, UrlHelper
from titlecase import titlecase
from constants import *

class Game(object):
    def __init__(self,name,url):
        query_params = UrlHelper.get_query_params(url)
        self.game_id = query_params['gameid']
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

class Position(object):
    def __init__(self,security,quantity,current=None,start=None, today_change=None, is_active=True):
        if not issubclass(type(security),Security):
            raise InvalidPositionException("Must be a security (option or stock)")
        self.security = security
        quantity = int(quantity)
        total_value = None
        today_change_percent = None

        if current is not None:
            current = Util.sanitize_number(current)
            total_value = float(current * quantity)

        if start is None or today_change is None or current is None:
            is_active = False

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
        self.current = current
        self.quantity = quantity
        self.total_value = total_value
            
        if self.security.security_type == Option:
            self.total_value = self.total_value * 100
            

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
        self.security_set = set()

class StockPortfolio(Portfolio):
    def __init__(self,account_value,buying_power,cash,annual_return_pct, positions):
        super().__init__(account_value,buying_power,cash,annual_return_pct)
        self.net_return = 0
        self.total_value = 0
        self.pending_total_value = 0
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

class TransactionType(object):
    def __init__(self,ttype):
        ttype = ttype.upper()
        type_val = None

        if ttype in Constants.STOCK_TRADE_TRANSACTION_TYPES:
            self.security_type = Stock
            type_val = Constants.STOCK_TRADE_TRANSACTION_TYPES[ttype]

        elif ttype in Constants.OPTION_TRADE_TRANSACTION_TYPES:
            self.security_type = Option
            type_val = Constants.OPTION_TRADE_TRANSACTION_TYPES[ttype]
        else:
            err = "Invalid transaction type '%s'.\n" % ttype
            err += "  Valid stock transaction types are:\n"
            err += "\t%s\n" % ", ".join(Constants.STOCK_TRADE_TRANSACTION_TYPES.keys())
            err += "  Valid option transaction types are:\n"
            err += "\t%s\n" % ", ".join(Constants.OPTION_TRADE_TRANSACTION_TYPES.keys())
            raise InvalidTradeTransactionException(err)

        self.form_data = {'transactionTypeDropDown': type_val}

    def __repr__(self):
        return json.dumps(self.form_data)

    
    @classmethod
    def STOCK_BUY(cls):
        return cls('BUY')
    
    @classmethod
    def STOCK_SELL(cls):
        return cls('SELL')
    
    @classmethod
    def STOCK_SELL_SHORT(cls):
        return cls('SELL_SHORT')
    
    @classmethod
    def STOCK_BUY_TO_COVER(cls):
        return cls('BUY_TO_COVER')

    @classmethod
    def OPTION_BUY_TO_OPEN(cls):
        return cls('BUY_TO_OPEN')
    
    @classmethod
    def OPTION_SELL_TO_CLOSE(cls):
        return cls('SELL_TO_CLOSE')


class OrderType(object):
    def __init__(self,order_type,price=None, pct=None):
        order_type = titlecase(order_type)

        self.form_data = {
            'Price': order_type,
            'limitPriceTextBox': None,
            'stopPriceTextBox': None,
            'tStopPRCTextBox':None,
            'tStopVALTextBox':None 
        }

        if re.search(r'trailingstop', order_type.lower()):
            order_type = 'TrailingStop'

        try:
            self.form_data.update(Constants.ORDER_TYPES[order_type](price,pct))
        except KeyError:
            err = "Invalid order type '%s'\n" % order_type
            err += "  Valid order types are:\n\t"
            err += ", ".join(Constants.ORDER_TYPES.keys()) + "\n"
            raise InvalidOrderTypeException(err)

    def __repr__(self):
        return json.dumps(self.form_data)

    @classmethod
    def MARKET(cls):
        return cls('Market')
    
    @classmethod
    def LIMIT(cls,price):
        return cls('Limit',price)
    
    @classmethod
    def STOP(cls,price):
        return cls('Stop',price)

    @classmethod
    def TRAILING_STOP(cls,price=None,pct=None):
        if price and pct:
            raise InvalidOrderTypeException("Must only pick either percent or dollar amount for trailing stop.")
        if price is None and pct is None:
            raise InvalidOrderTypeException("Must enter either a percent or dollar amount for traling stop.")
        return cls('TrailingStop',price,pct)

class OrderDuration(object):
    def __init__(self,duration):
        duration = duration.upper()
        form_val = None
        try:
            form_val = Constants.ORDER_DURATIONS[duration]
            self.duration = duration
        except KeyError:
            err = "Invalid order duration '%s'.\n" % duration
            err += "  Valid order durations are:\n\t"
            err += ", ".join(Constants.ORDER_DURATIONS.keys()) + "\n"
            raise InvalidOrderDurationException(err)

        self.form_data = {'durationTypeDropDown': form_val}

    def __repr__(self):
        return json.dumps(self.form_data)

    @classmethod
    def DAY_ORDER(cls):
        return cls('DAY_ORDER')

    @classmethod
    def GOOD_TILL_CANCELLED(cls):
        return cls('GOOD_TILL_CANCELLED')

class OptionTrade(object):
    pass

class StockTrade(object):
    def __init__(
        self,
        stock,
        quantity,
        transaction_type,
        order_type=OrderType.MARKET(),
        order_duration=OrderDuration.GOOD_TILL_CANCELLED(),
        sendEmail=True):

        try:
            assert type(transaction_type) == TransactionType
            assert type(order_type) == OrderType
            assert type(quantity) == int
        except AssertionError:
            err = "Invalid trade.  Ensure all paramaters are properly typed."
            raise InvalidTradeException(err)
        
        self._form_token = None
        self.symbol = stock.symbol
        self.quantity = quantity


        if sendEmail:
            sendEmail=1
        else:
            sendEmail=0

        self.form_data = {
            'symbolTextbox': self.symbol,
            'selectedValue': None,
            'quantityTextbox': self.quantity,
            'isShowMax': 0,
            'sendConfirmationEmailCheckBox':sendEmail
        }

        self.form_data.update(transaction_type.form_data)
        self.form_data.update(order_type.form_data)
        self.form_data.update(order_duration.form_data)

    @property
    def form_token(self):
        return self._form_token

    @form_token.setter
    def form_token(self,token):
        self.form_data.update({'formToken': token})
        self._form_token = token

    def show_max(self):
        return {
            'isShowMax': 1,
            'symbolTextbox': self.symbol,
            'action': 'showMax'
        }

    def prepare(self):
        if self._form_token is None:
            raise TradeTokenNotSetException("Must set the csrf token for the trade first")
        return self.form_data

class PreparedTrade(dict):
    def __init__(self,session,url,form_data, **kwargs):
        self.session = session
        self.url = url
        self.form_data = form_data
        self.update(kwargs)

    def execute(self):
        resp = self.session.post(self.url,data=self.form_data)
        return resp

        
