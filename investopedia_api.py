from api_models import Portfolio
from parsers import Parsers
from stock_trade import StockTrade, TransactionType, OrderDuration, OrderType
from session_singleton import Session

class InvestopediaApi(object):
    def __init__(self,auth_cookie):
        Session.login(auth_cookie)
        self.portfolio = Parsers.get_portfolio()

    class StockTrade(object):
        class Trade(StockTrade):
            pass
        class TransactionType(TransactionType):
            pass
        class OrderDuration(OrderDuration):
            pass
        class OrderType(OrderType):
            pass




