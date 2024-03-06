from api_models import Portfolio
from parsers import Parsers, option_lookup, stock_quote
from trade_common import Expiration, OrderLimit, TransactionType, Trade, StockTrade
from trade_common import TradeExceedsMaxSharesException, TradeNotValidatedException, InvalidOrderDurationException, InvalidOrderTypeException, InvalidTradeTypeException
from options import OptionChain
from option_trade import OptionTrade
# from stock_trade import StockTrade
from session_singleton import Session
from utils import TaskQueue, validate_and_execute_trade
import warnings


class InvestopediaApi(object):
    def __init__(self, credentials,game_name=None, portfolio_id=None,game_id=None):
        Session.login(credentials)
        self.portfolios = Parsers.get_portfolios()
        self.portfolio = self.portfolios[0]
        if game_name is not None or portfolio_id is not None or game_id is not None:
            self.change_portfolio(game_name,game_id,portfolio_id)
        print("Initialized portfolio ID %s in game %s" % (self.portfolio.portfolio_id, self.portfolio.game_name))
        #self.open_orders = self.portfolio.open_orders

    def change_portfolio(self,game_name=None, game_id=None, portfolio_id=None):
        if game_name is not None:
            for portfolio in self.portfolios:
                if portfolio.game_name == game_name:
                    self.portfolio = portfolio
                    print("changed portfolio to portfolio ID %s in game %s" % (self.portfolio.portfolio_id, self.portfolio.game_name))
                    return
            warnings.warn("Portfolio not changed, could not find portfolio with game_name %s" % game_name)
            return

        elif game_id is not None:
             for portfolio in self.portfolios:
                if portfolio.game_id == game_id:
                    self.portfolio = portfolio
                    print("changed portfolio to portfolio ID %s in game %s" % (self.portfolio.portfolio_id, self.portfolio.game_name))
                    return
                warnings.warn("Portfolio not changed, could not find portfolio with game_id %s" % game_id)
                return
                
        elif portfolio_id is not None:
            for portfolio in self.portfolios:
                if portfolio.game_id == game_id:
                    self.portfolio = portfolio
                    print("changed portfolio to portfolio ID %s in game %s" % (self.portfolio.portfolio_id, self.portfolio.game_name))
                    return
            warnings.warn("Portfolio not changed, could not find portfolio with portfolio_id %s" % portfolio_id)
            return
        else:
            warnings.warn("Portfolio not changed, specify a valid game_name, game_id, or portfolio_id")




    class TradeQueue(TaskQueue):
        def __init__(self):
            super().__init__(default_task_function=validate_and_execute_trade)


    class StockTrade(StockTrade):
        pass

    class OptionTrade(OptionTrade):
        pass

    class TradeProperties:
        class Expiration(Expiration):
            pass

        class OrderLimit(OrderLimit):
            pass

        class TransactionType(TransactionType):
            pass

    @staticmethod
    def get_option_chain(symbol):
        return OptionChain(symbol)

    @staticmethod
    def get_stock_quote(symbol):
        return stock_quote(symbol)

    def refresh_portfolio(self):
        current_portfolio_id = self.portfolio.portfolio_id
        self.portfolios = Parsers.get_portfolios()

        for portfolio in self.portfolios:
            if current_portfolio_id == portfolio.portfolio_id:
                self.portfolio = portfolio
        
        self.open_orders = self.portfolio.open_orders