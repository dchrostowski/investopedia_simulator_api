from stock_trade import TradeType, OrderType, Duration

class OptionTradeType(TradeType):
    TRADE_TYPES = {
        'BUY_TO_OPEN': 1,
        'SELL_TO_CLOSE': 2
    }

    @property
    def form_data(self):
        self._form_data['ddlAction'] = self._form_data.pop('transactionTypeDropDown')
        return self._form_data

    @classmethod
    def BUY(cls):
        return cls.BUY_TO_OPEN()
    
    @classmethod
    def SELL(cls):
        return cls.SELL_TO_CLOSE()

    @classmethod
    def BUY_TO_OPEN(cls):
        return cls('BUY_TO_OPEN')

    @classmethod
    def SELL_TO_CLOSE(cls):
        return cls('SELL_TO_CLOSE')


class OptionTrade(object):
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
            trade_type = OptionTradeType(trade_type)

        if type(order_type) == str:
            order_type = self._order_type_validator(order_type)

        if type(duration) == str:
            duration = Duration(duration)

        try:
            assert type(trade_type).__name__ == 'OptionTradeType'
            assert type(order_type).__name__ == 'OptionOrderType'
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

    