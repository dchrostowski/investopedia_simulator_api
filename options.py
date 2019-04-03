import re
from IPython import embed
from constants import OPTION_MONTH_CODES
import datetime

class InvalidOptionChainException(Exception):
    pass

class InvalidOptionException(Exception):
    pass





class OptionChainLookup(dict):
    def __init__(self,stock,calls,puts):
        self.calls = calls
        self.puts = puts
        for contract in self.calls + self.puts:
            self[contract.contract_name] = contract


class OptionChain(list):
    def __init__(self,contracts):
        for contract in contracts:
            if type(contract).__name__ != 'OptionContract':
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
            self.last = option_dict['Last']
            self.bid = option_dict['Bid']
            self.ask = option_dict['Ask']
            self.volume = option_dict['Volume']
            self.open_int = option_dict['OpenInterest']

        elif contract_name is not None:
            re_search = re.search(r'^(\D+)(\d\d)(\d\d)([A-X])([\d\.]+)$',contract_name)
            if re_search is None or len(re_search.groups()) != 5:
                raise InvalidOptionException("Could not parse option symbol '%s'" % symbol)
            self.base_symbol = re_search.group(1)
            exp_year = int(int(re_search.group(2)) + 2000)
            exp_day = int(re_search.group(3))
            month_code = re_search.group(4)
            if month_code not in OPTION_MONTH_CODES:
                raise InvalidOptionException("Invalid month code '%s'" % month_code)
            self.strike_price = float(re_search.group(5))

            month_and_type_info = OPTION_MONTH_CODES[month_code]
            exp_month = month_and_type_info['month']

            self.contract_type = month_and_type_info['type']
            self.expiration = datetime.date(exp_year,exp_month,exp_day)
            self.contract_name = contract_name
            
            self.last = None
            self.bid = None
            self.ask = None
            self.volume = None
            self.open_int = None
