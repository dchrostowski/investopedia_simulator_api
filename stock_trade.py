from trade_common import TradeType, OrderType, Duration, Trade
from lxml import html
from ratelimit import limits, sleep_and_retry
from utils import UrlHelper
from session_singleton import Session
import warnings


class StockTrade(Trade):
    def __init__(
            self,
            contract,
            quantity,
            trade_type,
            order_type=OrderType.MARKET(),
            duration=Duration.GOOD_TILL_CANCELLED(),
            send_email=True):

        self.security_type = 'stock'
        self.base_url = UrlHelper.route('tradestock')
        self.submit_url = UrlHelper.route('tradestock_submit')
        super().__init__(contract.base_symbol, quantity,
                         trade_type, order_type, duration, send_email)

    @sleep_and_retry
    @limits(calls=6, period=30)
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
