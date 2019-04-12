class TradeType(object):
    TRADE_TYPES = {}
    def __init__(self, trade_type, **form_data):
        self._trade_type = trade_type.upper()
        self._form_data = form_data

    @property
    def form_data(self):
        return self._form_data

    @form_data.setter
    def form_data(self,form_data):


    @property
    def trade_type(self):
        self._trade_type

    @trade_type.setter
    def trade_type(self,trade_type):
        if trade_type not in self.__class__.TRADE_TYPES:
            raise InvalidTradeTypeException("Trade type %s was not defined in TRADE_TYPES.")
        
    def __repr__(self):
        return self._trade_type

    def __str__(self):
        return self._trade_type

