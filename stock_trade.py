from session_singleton import Session
from constants import *
from utils import UrlHelper

from titlecase import titlecase
import re
from lxml import html
from IPython import embed
from ratelimit import limits, sleep_and_retry




class TradeType(object):
    TRADE_TYPES = {
        'BUY': 1,
        'SELL': 2,
        'SELL_SHORT': 3,
        'BUY_TO_COVER': 4,
    }

    def __init__(self, trade_type):
        self._trade_type = None
        self.form_data = None
        self.trade_type = trade_type

    @property
    def trade_type(self):
        return self._trade_type

    @trade_type.setter
    def trade_type(self, trade_type):
        self.form_data = None
        trade_type = trade_type.upper()
        try:
            form_arg = self.__class__.TRADE_TYPES[trade_type]
            self.form_data = {'transactionTypeDropDown': form_arg}
            self._trade_type = trade_type
        except KeyError:
            err = "Invalid stock transaction type '%s'.\n" % trade_type
            err += "  Valid stock transaction types are:\n"
            err += "\t%s\n" % ", ".join(self.__class__.TRADE_TYPES.keys())
            raise InvalidTradeTransactionException(err)

    def __repr__(self):
        return self._trade_type

    def __str__(self):
        return self._trade_type

    @classmethod
    def BUY(cls):
        return cls('BUY')

    @classmethod
    def SELL(cls):
        return cls('SELL')

    @classmethod
    def SELL_SHORT(cls):
        return cls('SELL_SHORT')

    @classmethod
    def BUY_TO_COVER(cls):
        return cls('BUY_TO_COVER')


class OrderType(object):

    ORDER_TYPES = {
        'Market': lambda val1, val2: {},
        'Limit': lambda val1, val2: {'limitPriceTextBox': val1},
        'Stop': lambda val1, val2: {'stopPriceTextBox': val1},
        'TrailingStop': lambda pct=None, dlr=None:
            {
                'tStopPRCTextBox': pct,
                'tStopVALTextBox': dlr
        }
    }

    def __init__(self, order_type, price=None, pct=None):
        self._order_type = None

        if re.search(r'trailingstop', order_type.lower()):
            order_type = 'TrailingStop'
        else:
            order_type = titlecase(order_type)
        self.form_data = {
            'Price': order_type,
            'limitPriceTextBox': None,
            'stopPriceTextBox': None,
            'tStopPRCTextBox': None,
            'tStopVALTextBox': None
        }

        try:
            self.form_data.update(
                self.__class__.ORDER_TYPES[order_type](price, pct))
            self._order_type = order_type
            self._price = price
            self._pct = pct
        except KeyError:
            err = "Invalid order type '%s'\n" % order_type
            err += "  Valid order types are:\n\t"
            err += ", ".join(self.__class__.ORDER_TYPES.keys()) + "\n"
            raise InvalidOrderTypeException(err)

    # read-only
    @property
    def order_type(self):
        return self._order_type

    def __repr__(self):
        pod = ''
        if self._pct:
            pod = '%s %%' % self._pct
        elif self._price:
            pod = '$%s' % self._price

        return "%s %s" % (self.order_type, pod)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def MARKET(cls):
        return cls('Market')

    @classmethod
    def LIMIT(cls, price):
        return cls('Limit', price)

    @classmethod
    def STOP(cls, price):
        return cls('Stop', price)

    @classmethod
    def TRAILING_STOP(cls, price=None, pct=None):
        if price and pct:
            raise InvalidOrderTypeException(
                "Must only pick either percent or dollar amount for trailing stop.")
        if price is None and pct is None:
            raise InvalidOrderTypeException(
                "Must enter either a percent or dollar amount for traling stop.")
        return cls('TrailingStop', price, pct)


class Duration(object):
    DURATIONS = {
        'DAY_ORDER': 1,
        'GOOD_TILL_CANCELLED': 2,
    }

    def __init__(self, duration):
        self._duration = None
        self.form_data = None
        self.duration = duration

        duration = duration.upper()

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        try:
            duration = duration.upper()
            form_arg = self.__class__.DURATIONS[duration]
            self.form_data = {'durationTypeDropDown': form_arg}
            self._duration = duration
        except KeyError:
            err = "Invalid order duration '%s'.\n" % duration
            err += "  Valid order durations are:\n\t"
            err += ", ".join(self.__class__.DURATIONS.keys()) + "\n"
            raise InvalidOrderDurationException(err)

    def __repr__(self):
        return self._duration

    def __str__(self):
        return self._duration

    @classmethod
    def DAY_ORDER(cls):
        return cls('DAY_ORDER')

    @classmethod
    def GOOD_TILL_CANCELLED(cls):
        return cls('GOOD_TILL_CANCELLED')


class StockTrade(object):
    def __init__(
            self,
            symbol,
            quantity,
            trade_type,
            order_type=OrderType.MARKET(),
            duration=Duration.GOOD_TILL_CANCELLED(),
            send_email=True):

        if send_email:
            send_email=1
        else:
            send_email=0

        if type(trade_type) == str:
            trade_type = TradeType(trade_type)

        if type(order_type) == str:
            order_type = self._order_type_validator(order_type)
            #if order_type.lower() != 'market':
            #    raise InvalidTradeException(
            #        "Can only pass order_type as string for simple market orders.  For stop/limit orders pass something like OrderType.LIMIT(10.00) Or OrderType.STOP(20.00)")
            #else:
            #    order_type = OrderType(order_type)

        if type(duration) == str:
            duration = Duration(duration)

        try:
            assert type(trade_type).__name__ == 'TradeType'
            assert type(order_type).__name__ == 'OrderType'
            assert type(quantity) == int
        except AssertionError:
            err = "Invalid trade.  Ensure all paramaters are properly typed."
            raise InvalidTradeException(err)

        self._form_token = None
        self._symbol = symbol
        self._quantity = quantity
        self._trade_type = trade_type
        self._order_type = order_type
        self._duration = duration
        self._send_email = send_email

        self.form_data = {
            'symbolTextbox': self._symbol,
            'selectedValue': None,
            'quantityTextbox': self._quantity,
            'isShowMax': 0,
            'sendConfirmationEmailCheckBox': self._send_email
        }

        self.form_data.update(trade_type.form_data)
        self.form_data.update(order_type.form_data)
        self.form_data.update(duration.form_data)

    def _order_type_validator(self,order_type_str):
        ots_fn, *ots_args = order_type_str.split()
        try:
            ots_fn = getattr(OrderType,ots_fn.upper())
            order_type = ots_fn(*ots_args)
            return order_type
        except Exception as e:
            raise InvalidOrderDurationException("str %s is invalid for OrderType" % order_type)
        


    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, symbol):
        self.form_data['symbolTextbox'] = symbol
        self._symbol = symbol

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, q):
        self.form_data['quantityTextbox'] = q
        self._quantity = q

    @property
    def trade_type(self):
        return str(self._trade_type)

    @trade_type.setter
    def trade_type(self, trade_type):
        if type(trade_type) == str:
            trade_type = TradeType(trade_type)

        assert type(trade_type).__name__ == 'TradeType', "Could not validate transaction type"
        
        self.form_data.update(trade_type.form_data)
        self._trade_type = trade_type

    @property
    def duration(self):
        return str(self._duration)

    @duration.setter
    def duration(self, duration):
        if type(duration) == str:
            duration = Duration(duration)
        assert type(duration).__name__ == 'Duration', "Could not validate Duration"
        
        self.form_data.update(duration.form_data)
        self._duration = duration
        

    @property
    def order_type(self):
        return str(self._order_type)

    @order_type.setter
    def order_type(self, order_type):
        if type(order_type) == str:
            order_type = self._order_type_validator(order_type)

            
        
        assert type(order_type).__name__ == 'OrderType', 'Could not validate OrderType'
        self.form_data.update(order_type.form_data)
        self._order_type = order_type

    @property
    def form_token(self):
        return self._form_token

    @form_token.setter
    def form_token(self, token):
        self.form_data.update({'formToken': token})
        self._form_token = token

    def show_max(self):
        return {
            'isShowMax': 1,
            'symbolTextbox': self.symbol,
            'action': 'showMax'
        }

    @sleep_and_retry
    @limits(calls=6,period=30)
    def _get_form_token(self):
        session = Session()
        resp = session.get(UrlHelper.route('tradestock'))
        tree = html.fromstring(resp.text)
        token = tree.xpath(
            '//div[@class="group"]//form[@id="orderForm"]/input[@name="formToken"]/@value')[0]
        return token
    @sleep_and_retry
    @limits(calls=6,period=30)
    def _check_max_shares(self):
        session = Session()
        resp = session.post(UrlHelper.route(
            'tradestock'), data=self.show_max())
        shares_match = re.search(
            r'^A\s*maximum\s*of\s*(\d+)\s*shares', resp.text)
        if shares_match:
            max_shares = int(shares_match.group(1))
            if self.quantity > max_shares:
                raise TradeExceedsMaxSharesException(
                    "Quantity of trade exceeds maximum of %s" % max_shares, max_shares)

    def _get_trade_info(self, tree):

        trade_info_tables = tree.xpath(
            '//div[@class="box-table"]/table[contains(@class,"table1")]')
        tt1 = trade_info_tables[0]
        tt2 = trade_info_tables[1]

        trade_info = {
            'Description': tt1.xpath('tbody/tr[2]/td[1]/text()')[0],
            'Transaction': tt1.xpath('tbody/tr[2]/td[2]/text()')[0],
            'StopLimit': tt1.xpath('tbody/tr[2]/td[3]/text()')[0],
            'Duration': tt1.xpath('tbody/tr[2]/td[4]/text()')[0],
            'Price': tt2.xpath('tbody/tr[1]/td[3]/text()')[0],
            'Quantity': tt2.xpath('tbody/tr[2]/td[2]/text()')[0],
            'Commision': tt2.xpath('tbody/tr[3]/td[2]/text()')[0],
            'Est_Total': tt2.xpath('tbody/tr[4]/td[2]/text()')[0],
        }

        return trade_info

    @sleep_and_retry
    @limits(calls=6,period=30)
    def validate(self):
        session = Session()
        self.form_token = self._get_form_token()
        self._check_max_shares()
        resp = session.post(UrlHelper.route('tradestock'), data=self.form_data)

        url_token = None
        if resp.history:
            redirect_url = resp.history[0].headers['Location']
            redirect_qp = UrlHelper.get_query_params(redirect_url)
            url_token = redirect_qp['urlToken']

        tree = html.fromstring(resp.text)
        trade_info = self._get_trade_info(tree)

        change_onclick = tree.xpath('//input[@id="changeOrder"]/@onclick')[0]
        matches = re.search(r'href=\'([^\']+)\'$', change_onclick)

        change_url = None
        if matches:
            change_url = matches.group(1)
        submit_query_params = UrlHelper.get_query_params(change_url)
        submit_query_params.update({'urlToken': url_token})
        submit_form = tree.xpath(
            '//div[@class="group"]/form[@name="simTradePreview"]')[0]
        submit_token = submit_form.xpath('input[@name="formToken"]/@value')[0]
        submit_order_val = submit_form.xpath(
            'input[@name="submitOrder"]/@value')[0]

        submit_data = {
            'submitOrder': submit_order_val,
            'formToken': submit_token
        }

        submit_url = UrlHelper.set_query(UrlHelper.route(
            'tradestock_submit'), submit_query_params)

        return PreparedTrade(submit_url, submit_data, **trade_info)

    def __repr__(self):
        return str({
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'quantity': self.quantity,
            'duration': self.duration,
            'price/limit': self.order_type
        })

    def __str__(self):
        return "%s" % self.__repr__()


class PreparedTrade(dict):
    def __init__(self, url, form_data, **kwargs):
        self.url = url
        self.form_data = form_data
        self.update(kwargs)
    
    @sleep_and_retry
    @limits(calls=6,period=30)
    def execute(self):
        session = Session()
        resp = session.post(self.url, data=self.form_data)
        return resp
