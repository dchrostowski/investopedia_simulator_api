import re
from constants import OPTION_MONTH_CODES
from datetime import datetime, timedelta
import calendar
from typing import List
from queries import Queries
from session_singleton import Session
from constants import API_URL
import json

class InvalidOptionChainException(Exception):
    pass

class InvalidOptionException(Exception):
    pass

class OptionScope(object):
    IN_THE_MONEY = 'IN_THE_MONEY'
    NEAR_THE_MONEY = 'NEAR_THE_MONEY'
    OUT_OF_THE_MONEY = 'OUT_OF_THE_MONEY'
    ALL = 'ALL'

    
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
        start_date = datetime(year,month,1)
        end_date = datetime(year,month,last_day)
        return self.search_by_daterange(start_date,end_date)

    def search_by_daterange(self,start_date,end_date):
        for exp_date in self.expirations.keys():
            if exp_date >= start_date and exp_date <= end_date:
                yield self.expirations[exp_date]


class OptionChain(object):
    def __init__(self,symbol):
        self.expirations = []
        self.options = {}
        self.chain = {}
        symbol = symbol.upper()

        session = Session()
        exp_resp = session.post(API_URL,data=Queries.option_expiration_dates(symbol))
        exp_resp.raise_for_status()


        exp_json = json.loads(exp_resp.text)
        for expiration in exp_json['data']['readOptionsExpirationDates']['expirationDates']:
            self.expirations.append(expiration)

        for expiration in self.expirations:
            self.chain[expiration] = {}
            option_scopes = [OptionScope.IN_THE_MONEY, OptionScope.OUT_OF_THE_MONEY, OptionScope.NEAR_THE_MONEY]
            for os in option_scopes:
                self.chain[expiration][os] = {'calls': [], 'puts': []}
                options_resp = session.post(API_URL, data=Queries.options_by_expiration(symbol,expiration,os))
                options_resp.raise_for_status()
                options = json.loads(options_resp.text)['data']['readStock']['options']
                call_options = options['callOptions']['list']
                put_options = options['putOptions']['list']
                for co_kwargs in call_options:
                    co_kwargs['expiration'] = expiration
                    co_kwargs['is_put'] = False
                    call_option = OptionContract(**co_kwargs)
                    self.options[call_option.symbol] = call_option
                    self.chain[expiration][os]['calls'].append(call_option.symbol)

                for po_kwargs in put_options:
                    po_kwargs['expiration'] = expiration
                    po_kwargs['is_put'] = True
                    put_option = OptionContract(**po_kwargs)
                    self.options[put_option.symbol] = put_option
                    self.chain[expiration][os]['puts'].append(put_option.symbol)

    def search(
        self,
        after=datetime.now() - timedelta(days=365),
        before=datetime.now() + timedelta(days=365),
        scope=OptionScope.ALL,
        calls=True,
        puts=True
        ):

        eligible_expirations = []
        eligible_scopes = []
        eligible_types = []


        after_ts = after.timestamp()
        before_ts = before.timestamp()

        
        for exp in self.expirations:
            if exp/1000 >= after_ts and exp/1000 <= before_ts:
                eligible_expirations.append(exp)
        
        if scope == OptionScope.ALL:
            eligible_scopes = [OptionScope.IN_THE_MONEY, OptionScope.OUT_OF_THE_MONEY, OptionScope.NEAR_THE_MONEY]
        else:
            eligible_scopes = [scope]

        if calls:
            eligible_types.append('calls')
        
        if puts:
            eligible_types.append('puts')

        filtered_options = []
        for exp in eligible_expirations:
            filtered_expirations = self.chain[exp]
            for esc in eligible_scopes:
                filtered_scopes = filtered_expirations[esc]
                for ety in eligible_types:
                    filtered_option_symbols = filtered_scopes[ety]
                    for opt_symbol in filtered_option_symbols:
                        filtered_options.append(self.options[opt_symbol])

        return filtered_options
    

    def all(self):
        return [v for v in self.options.values()]
    
    def lookup_by_symbol(self,symbol):
        return self.options.get(symbol,None)

class OptionContract(object):
    def __init__(self,**kwargs):
        self.symbol = kwargs['symbol']
        self.strike_price = kwargs['strikePrice']
        self.last = kwargs['lastPrice']
        self.day_change = kwargs['dayChangePrice']
        self.day_change_percent = kwargs['dayChangePercent']
        self.day_low = kwargs['dayLowPrice']
        self.day_high = kwargs['dayHighPrice']
        self.bid = kwargs['bidPrice']
        self.ask = kwargs['askPrice']
        self.volume = kwargs['volume']
        self.open_interest = kwargs['openInterest']
        self.in_the_money = kwargs['isInTheMoney']
        self.expiration = datetime.fromtimestamp(kwargs['expiration']/1000)
        self.is_put = kwargs['is_put']



# for type hinting
OptionContractList = List[OptionContract]