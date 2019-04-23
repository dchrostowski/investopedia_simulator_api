import re
from constants import OPTION_MONTH_CODES
import datetime
import calendar
from typing import List

class InvalidOptionChainException(Exception):
    pass

class InvalidOptionException(Exception):
    pass





class OptionChainLookup(dict):
    def __init__(self,symbol,*option_chains):
        self.expirations = {}
        for oc in option_chains:
            for contract in oc.calls + oc.puts:
                self.update({contract.contract_name: contract})
            self.expirations.update({
                oc.expiration_date: oc
            })
        self.symbol = symbol

    def search_by_month_and_year(self,month,year):
        last_day = calendar.monthrange(year,month)[1]
        start_date = datetime.datetime(year,month,1)
        end_date = datetime.datetime(year,month,last_day)
        return self.search_by_daterange(start_date,end_date)

    def search_by_daterange(self,start_date,end_date):
        for exp_date in self.expirations.keys():
            if exp_date >= start_date and exp_date <= end_date:
                yield self.expirations[exp_date]


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

    def lazy_values(self):
        return (self.last,self.bid,self.ask,self.volume,self.open_int)

    def __repr__(self):
        return str({
            'strike_price': self.strike_price,
            'contract_name': self.contract_name,
            'last': self.last,
            'bid': self.bid,
            'ask': self.ask,
            'volume': self.volume,
            'open_int': self.open_int
        })

# for type hinting
OptionContractList = List[OptionContract]

class OptionChain(object):
    def __init__(self,expiration_date: str,calls: OptionContractList, puts: OptionContractList):
        self.expiration_date = datetime.datetime.strptime(expiration_date,"%m/%d/%Y")
        self.expiration_date_str = expiration_date
        self.calls = calls
        self.puts = puts