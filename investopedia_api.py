from api_models import Portfolio
from parsers import Parsers, option_lookup, stock_quote
from stock_trade import StockTrade, TradeType, Duration, OrderType
from session_singleton import Session

class InvestopediaApi(object):
    def __init__(self,auth_cookie):
        Session.login(auth_cookie)
        self.portfolio = Parsers.get_portfolio()

    class StockTrade(StockTrade):
        class Trade(StockTrade):
            pass
        class TradeType(TradeType):
            pass
        class Duration(Duration):
            pass
        class OrderType(OrderType):
            pass
    
    @staticmethod
    def get_option_chain(symbol):
        return option_lookup(symbol)

    @staticmethod
    def get_stock_quote(symbol):
        return stock_quote(symbol)



