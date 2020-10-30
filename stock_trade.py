from trade_common import TradeType, OrderType, Duration, Trade
from lxml import html
from ratelimit import limits, sleep_and_retry
from utils import UrlHelper
from session_singleton import Session
import warnings
import re


class StockTrade(Trade):
    def __init__(
            self,
            symbol,
            quantity,
            trade_type,
            order_type=OrderType.MARKET(),
            duration=Duration.GOOD_TILL_CANCELLED(),
            send_email=True):

        self.security_type = 'stock'
        self.base_url = UrlHelper.route('tradestock')
        self.submit_url = UrlHelper.route('tradestock_submit')
        super().__init__(symbol, quantity,
                         trade_type, order_type, duration, send_email)

    @sleep_and_retry
    @limits(calls=6, period=20)
    def _get_max_shares(self):
        uri = self.base_url
        form_data = {
            'isShowMax': 1,
            'symbolTextbox': self.symbol,
            'action': 'showMax'
        }
        # should not refresh token here because reasons.
        resp = Session().post(uri, data=form_data)
        try:
            shares_match = re.search(
                r'maximum\s*of\s*(\d+)\s*(?:shares|option)', resp.text)
            return int(shares_match.group(1))
        except Exception as e:
            warnings.warn("Unable to determine max shares: %s" % e)

        warnings.warn("Could not determine max shares.")
        return 0

    def go_to_preview(self):
        session = Session()
        uri = UrlHelper.set_query(self.base_url, self.query_params)
        self.form_data.update({'isShowMax': 0})
        return session.post(uri, data=self.form_data)
