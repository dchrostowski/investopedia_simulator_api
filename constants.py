
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

class InvalidOptionChainException(Exception):
    pass

class InvalidOptionTypeException(Exception):
    pass

class NotLoggedInException(Exception):
    pass

class TradeExceedsMaxSharesException(Exception):
    def __init__(self, message, max_shares):
        super().__init__(message)

        self.max_shares = max_shares
        
    


class Constants(object):
    BASE_URL = 'https://www.investopedia.com/simulator'
    PATHS = {
        'portfolio': '/portfolio/',
        'games': '/game',
        'home': '/home.aspx',
        'lookup': '/ajax/quotebox.aspx',
        'tradestock': '/trade/tradestock.aspx',
        'tradestock_submit': '/trade/tradestockpreview.aspx',
        'tradeoption': '/trade/getquote.aspx',
        'opentrades': '/trade/showopentrades.aspx'
    }

    OPTIONS_QUOTE_URL = 'https://globaloptions.xignite.com/xglobaloptions.json/GetAllEquityOptionChain'


   
   

    

    

    OPTION_MONTH_CODES = {
        'A': {
            'type': 'Call',
            'month': 1
        },
        'B': {
            'type': 'Call',
            'month': 2
        },
        'C': {
            'type': 'Call',
            'month': 3
        },
        'D': {
            'type': 'Call',
            'month': 4
        },
        'E': {
            'type': 'Call',
            'month': 5
        },
        'F': {
            'type': 'Call',
            'month': 6
        },
        'G': {
            'type': 'Call',
            'month': 7
        },
        'H': {
            'type': 'Call',
            'month': 8
        },
        'i': {
            'type': 'Call',
            'month': 9
        },
        'j': {
            'type': 'Call',
            'month': 10
        },
        'k': {
            'type': 'Call',
            'month': 11
        },
        'L': {
            'type': 'Call',
            'month': 12
        },
         'M': {
            'type': 'Put',
            'month': 1
        },
        'N': {
            'type': 'Put',
            'month': 2
        },
        'O': {
            'type': 'Put',
            'month': 3
        },
        'P': {
            'type': 'Put',
            'month': 4
        },
        'Q': {
            'type': 'Put',
            'month': 5
        },
        'R': {
            'type': 'Put',
            'month': 6
        },
        'S': {
            'type': 'Put',
            'month': 7
        },
        'T': {
            'type': 'Put',
            'month': 8
        },
        'U': {
            'type': 'Put',
            'month': 9
        },
        'V': {
            'type': 'Put',
            'month': 10
        },
        'W': {
            'type': 'Put',
            'month': 11
        },
        'X': {
            'type': 'Put',
            'month': 12
        }
    }

    OPTION_MONTH_CODES = {
        'A': {
            'type': 'Call',
            'month': 1
        },
        'B': {
            'type': 'Call',
            'month': 2
        },
        'C': {
            'type': 'Call',
            'month': 3
        },
        'D': {
            'type': 'Call',
            'month': 4
        },
        'E': {
            'type': 'Call',
            'month': 5
        },
        'F': {
            'type': 'Call',
            'month': 6
        },
        'G': {
            'type': 'Call',
            'month': 7
        },
        'H': {
            'type': 'Call',
            'month': 8
        },
        'i': {
            'type': 'Call',
            'month': 9
        },
        'j': {
            'type': 'Call',
            'month': 10
        },
        'k': {
            'type': 'Call',
            'month': 11
        },
        'L': {
            'type': 'Call',
            'month': 12
        },
         'M': {
            'type': 'Put',
            'month': 1
        },
        'N': {
            'type': 'Put',
            'month': 2
        },
        'O': {
            'type': 'Put',
            'month': 3
        },
        'P': {
            'type': 'Put',
            'month': 4
        },
        'Q': {
            'type': 'Put',
            'month': 5
        },
        'R': {
            'type': 'Put',
            'month': 6
        },
        'S': {
            'type': 'Put',
            'month': 7
        },
        'T': {
            'type': 'Put',
            'month': 8
        },
        'U': {
            'type': 'Put',
            'month': 9
        },
        'V': {
            'type': 'Put',
            'month': 10
        },
        'W': {
            'type': 'Put',
            'month': 11
        },
        'X': {
            'type': 'Put',
            'month': 12
        }
    }

