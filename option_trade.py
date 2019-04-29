from trade_common import TradeType, OrderType, Duration, Trade
from lxml import html
from ratelimit import limits, sleep_and_retry
from utils import UrlHelper
from session_singleton import Session
import warnings
import re

class OptionTrade(Trade):
    def __init__(
            self,
            contract,
            quantity,
            trade_type,
            order_type=OrderType.MARKET(),
            duration=Duration.GOOD_TILL_CANCELLED(),
            send_email=True):

        self.security_type = 'option'
        self.base_url = UrlHelper.route('tradeoption')
        self.submit_url = UrlHelper.route('tradeoption_submit')
        super().__init__(contract.base_symbol, quantity,
                         trade_type, order_type, duration, send_email)

        self.contract = contract
        self.prepared_trade = None

    @property
    def contract(self):
        return self._contract

    @contract.setter
    def contract(self, contract):
        tt = 's'
        if self.trade_type == 'BUY_TO_OPEN':
            tt = 'b'
        self.query_params.update({
            'ap': contract.ask,
            'bid': contract.bid,
            'sym': contract.contract_name,
            't': contract.contract_type.lower()[0],
            's': contract.strike_price,
            'msym': contract.raw['Month'],
            'tt': tt
        })

        self._contract = contract

    @sleep_and_retry
    @limits(calls=6, period=30)
    def _get_max_shares(self):
        if self.form_token is None:
            self.refresh_form_token()
        uri = UrlHelper.set_query(self.base_url, self.query_params)
        self.form_data['isShowMax'] = 1
        resp = Session().post(uri, data=self.form_data)
        tree = html.fromstring(resp.text)
        self.form_data['isShowMax'] = 0
        self.refresh_form_token(tree)
        fon = lambda x: x[0] if len(x)> 0 else None

        try:
            xpath1 = '//div[@id="limitDiv"]/span[@id="limitationLabel"]/text()'
            xpath2 = '//div[@id="limitDiv"]/span/text()'
            text = fon(tree.xpath(xpath1)) or fon(tree.xpath(xpath2))
            shares_match = re.search(
                r'maximum\s*of\s*(\d+)\s*(?:shares|option)', text)
            return int(shares_match.group(1))

        except Exception as e:
            error = e
            warnings.warn("Unable to determine max shares: %s" % e)
            return
        return 0

    def go_to_preview(self):
        session = Session()
        self.form_data.update({'btnReview': 'Preview+Order', 'isShowMax': 0})
        uri = UrlHelper.set_query(UrlHelper.route(
            'tradeoption'), self.query_params)
        return session.post(uri, data=self.form_data)
