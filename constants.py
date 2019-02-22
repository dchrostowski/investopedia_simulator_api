
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

class InvalidHoldingException(Exception):
    pass

class InvalidOptionException(Exception):
    pass

class Constants(object):
    BASE_URL = 'https://www.investopedia.com/simulator'
    PATHS = {
        'portfolio': '/portfolio/',
        'games': '/game',
        'home': '/home.aspx',
        'lookup': '/stocks/symlookup.aspx',
    }