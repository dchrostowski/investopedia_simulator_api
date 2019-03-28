from session_singleton import Session
from constants import *
from utils import UrlHelper

from titlecase import titlecase
import re
from lxml import html


class TransactionType(object):
    TRANSACTION_TYPES = {
        'BUY': 1,
        'SELL': 2,
        'SELL_SHORT': 3,
        'BUY_TO_COVER': 4,
    }

    def __init__(self, transaction_type):
        self._transaction_type = None
        self.form_data = None
        self.transaction_type = transaction_type

    @property
    def transaction_type(self):
        return self._transaction_type

    @transaction_type.setter
    def transaction_type(self, ttype):
        self.form_data = None
        ttype = ttype.upper()
        try:
            form_arg = self.__class__.TRANSACTION_TYPES[ttype]
            self.form_data = {'transactionTypeDropDown': form_arg}
            self._transaction_type = ttype
        except KeyError:
            err = "Invalid stock transaction type '%s'.\n" % ttype
            err += "  Valid stock transaction types are:\n"
            err += "\t%s\n" % ", ".join(self.__class__.TRANSACTION_TYPES.keys())
            raise InvalidTradeTransactionException(err)

    def __repr__(self):
        return self._transaction_type

    def __str__(self):
        return self._transaction_type

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


class OrderDuration(object):
    ORDER_DURATIONS = {
        'DAY_ORDER': 1,
        'GOOD_TILL_CANCELLED': 2,
    }

    def __init__(self, duration):
        self._order_duration = None
        self.form_data = None
        self.order_duration = duration

        duration = duration.upper()

    @property
    def order_duration(self):
        return self._order_duration

    @order_duration.setter
    def order_duration(self, duration):
        try:
            duration = duration.upper()
            form_arg = self.__class__.ORDER_DURATIONS[duration]
            self.form_data = {'durationTypeDropDown': form_arg}
            self._order_duration = duration
        except KeyError:
            err = "Invalid order duration '%s'.\n" % duration
            err += "  Valid order durations are:\n\t"
            err += ", ".join(Constants.ORDER_DURATIONS.keys()) + "\n"
            raise InvalidOrderDurationException(err)

    def __repr__(self):
        return self._order_duration

    def __str__(self):
        return self._order_duration

    @classmethod
    def DAY_ORDER(cls):
        return cls('DAY_ORDER')

    @classmethod
    def GOOD_TILL_CANCELLED(cls):
        return cls('GOOD_TILL_CANCELLED')


class StockTrade(object):
    def __init__(
            self,
            stock,
            quantity,
            transaction_type,
            order_type=OrderType.MARKET(),
            order_duration=OrderDuration.GOOD_TILL_CANCELLED(),
            sendEmail=True):

        if type(transaction_type) == str:
            transaction_type = TransactionType(transaction_type)

        if type(order_type) == str:
            if order_type.lower() != 'market':
                raise InvalidTradeException(
                    "Can only pass order_type as string for simple market orders.  For stop/limit orders pass something like OrderType.LIMIT(10.00) Or OrderType.STOP(20.00)")
            else:
                order_type = OrderType(order_type)

        if type(order_duration) == str:
            order_duration = OrderDuration(order_duration)

        try:
            assert type(transaction_type) == TransactionType
            assert type(order_type) == OrderType
            assert type(quantity) == int
        except AssertionError:
            err = "Invalid trade.  Ensure all paramaters are properly typed."
            raise InvalidTradeException(err)

        symbol = None
        if type(stock) == str:
            symbol = stock
        else:
            symbol = stock.symbol

        self._form_token = None
        self._symbol = symbol
        self._quantity = quantity
        self._transaction_type = transaction_type
        self._order_type = order_type
        self._order_duration = order_duration
        self._sendEmail = sendEmail

        if sendEmail:
            sendEmail = 1
        else:
            sendEmail = 0

        self.form_data = {
            'symbolTextbox': self._symbol,
            'selectedValue': None,
            'quantityTextbox': self._quantity,
            'isShowMax': 0,
            'sendConfirmationEmailCheckBox': sendEmail
        }

        self.form_data.update(transaction_type.form_data)
        self.form_data.update(order_type.form_data)
        self.form_data.update(order_duration.form_data)

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
    def transaction_type(self):
        return str(self._transaction_type)

    @transaction_type.setter
    def transaction_type(self, ttype):
        if type(ttype) == str:
            ttype = TransactionType(ttype)

        if type(ttype) == TransactionType:
            self.form_data.update(ttype.form_data)
            self._transaction_type = ttype
        else:
            raise InvalidTradeException(
                "transaction_type must be either str or TransactionType")

    @property
    def order_duration(self):
        return str(self._order_duration)

    @order_duration.setter
    def order_duration(self, od):
        if type(od) == str:
            od = OrderDuration(od)
        if type(od) == OrderDuration:
            self.form_data.update(od.form_data)
            self._order_duration = od
        else:
            raise InvalidTradeException(
                "order_duration must be either str or OrderDuraton")

    @property
    def order_type(self):
        return str(self._order_type)

    @order_type.setter
    def order_type(self, ot):
        if type(ot) == str and ot.lower() == 'market':
            ot = OrderType.MARKET()
            self.form_data.update(ot.form_data)
            self._order_type = ot
        elif type(ot) == OrderType:
            self.form_data.update(ot.form_data)
            self._order_type = ot
        else:
            err = "order_type property must be either a str of value 'market' or OrderType object.  Examples:\n"
            err += "\tOrderType.MARKET()\n"
            err += "\tOrderType.LIMIT(40.00)\n"
            raise InvalidTradeException(err)

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

    def _get_form_token(self):
        session = Session()
        resp = session.get(UrlHelper.route('tradestock'))
        tree = html.fromstring(resp.text)
        token = tree.xpath(
            '//div[@class="group"]//form[@id="orderForm"]/input[@name="formToken"]/@value')[0]
        return token

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
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'duration': self.order_duration,
            'price/limit': self.order_type
        })

    def __str__(self):
        return "%s" % self.__repr__()


class PreparedTrade(dict):
    def __init__(self, url, form_data, **kwargs):
        self.url = url
        self.form_data = form_data
        self.update(kwargs)

    def execute(self):
        session = Session()
        resp = session.post(self.url, data=self.form_data)
        return resp
