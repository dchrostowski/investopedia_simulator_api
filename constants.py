
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

class InvalidStockPositionException(Exception):
    pass

class InvalidStockPositionException(Exception):
    pass

class InvalidPositionException(Exception):
    pass

class InvalidOptionException(Exception):
    pass

class InvalidTradeTransactionException(Exception):
    pass

class InvalidOrderTypeException(Exception):
    pass

class InvalidOrderDurationException(Exception):
    pass
class InvalidTradeException(Exception):
    pass

class TradeTokenNotSetException(Exception):
    pass

class Constants(object):
    BASE_URL = 'https://www.investopedia.com/simulator'
    PATHS = {
        'portfolio': '/portfolio/',
        'games': '/game',
        'home': '/home.aspx',
        'lookup': '/stocks/symlookup.aspx',
        'tradestock': '/trade/tradestock.aspx',
        'tradestock_submit': '/trade/tradestockpreview.aspx',
        'tradeoption': '/trade/TradeOptions.aspx',
        'opentrades': '/trade/showopentrades.aspx'
    }


    STOCK_TRADE_TRANSACTION_TYPES = {
        'BUY': 1,
        'SELL': 2,
        'SELL_SHORT': 3,
        'BUY_TO_COVER': 4,
    }

    OPTION_TRADE_TRANSACTION_TYPES = {
        'BUY_TO_OPEN': 1,
        'SELL_TO_CLOSE': 2
    }

    ORDER_TYPES = {
        'Market': lambda val1,val2: {},
        'Limit': lambda val1,val2: {'limitPriceTextBox': val1},
        'Stop': lambda val1,val2: {'stopPriceTextBox': val1},
        'TrailingStop': lambda pct=None, dlr=None: 
            {
                'tStopPRCTextBox':pct,
                'tStopVALTextBox':dlr 
            }
    }

    ORDER_DURATIONS = {
        'DAY_ORDER': 1,
        'GOOD_TILL_CANCELLED' : 2,
    }

