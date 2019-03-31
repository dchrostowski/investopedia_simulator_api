
from IPython import embed
from api_models import LongPosition, ShortPosition
from api_models import Portfolio,StockPortfolio,ShortPortfolio
from session_singleton import Session
from utils import UrlHelper
from lxml import html
"""
<tr>
                <td>
                    <div class="detailButton btn-expand close" id="PS_LONG_0" data-symbol="TMO" data-portfolioid="5700657" data-stocktype="long"></div>
                </td>
                <td><a href="#"></a><a href="https://www.investopedia.com/simulator/trade/tradestock.aspx?too=2&amp;Sym=TMO&amp;Qty=4">Sell</a></td>
                <td><a href="#"></a><a href="https://www.investopedia.com/markets/stocks/tmo/" target="_blank">TMO</a></td>
                <td>THERMO FISHER SCIENTIFIC INC.</td>
                <td class="num">4</td>
                <td class="num">$269.75</td>
                <td class="num">$269.74</td>
                <td class="num">$1,078.96</td>
                <td class="num up">$133.48(14.12 %)</td>
                <td class="num dn">- $0.04(-0.00 %)                </td>
            </tr>
            """


class Parsers(object):
    
    @staticmethod
    def get_portfolio():
        session = Session()
        portfolio_response = session.get(UrlHelper.route('portfolio'))
        portfolio_tree = html.fromstring(portfolio_response.text)

        stock_portfolio = StockPortfolio()
        short_portfolio = ShortPortfolio()

        Parsers.parse_and_sort_positions(portfolio_tree,stock_portfolio,short_portfolio)

        xpath_prefix = '//div[@id="infobar-container"]/div[@class="infobar-title"]/p'

        xpath_map = {
            'account_value': '/strong[contains(text(),"Account Value")]/following-sibling::span/text()',
            'buying_power':  '/strong[contains(text(),"Buying Power")]/following-sibling::span/text()',
            'cash':          '/strong[contains(text(),"Cash")]/following-sibling::span/text()',
            'annual_return_pct': '/strong[contains(text(),"Annual Return")]/following-sibling::span/text()',
        }

        xpath_get = lambda xpth: portfolio_tree.xpath("%s%s" % (xpath_prefix,xpth))[0]

        portfolio_args = {k: xpath_get(v)  for k,v in xpath_map.items()}
        portfolio_args['stock_portfolio'] = stock_portfolio
        portfolio_args['short_portfolio'] = short_portfolio

        return Portfolio(**portfolio_args)

    @staticmethod
    def parse_and_sort_positions(tree,stock_portfolio,short_portfolio):        

        trs = tree.xpath('//table[contains(@class,"table1")]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@class,"no-border"))]')
        

        xpath_map = {
            'portfolio_id': 'td[1]/div/@data-portfolioid',
            # stock_type': 'td[1]/div/@data-stocktype',
            'symbol': 'td[1]/div/@data-symbol',
            'description': 'td[4]/text()',
            'quantity': 'td[5]/text()',
            'purchase_price': 'td[6]/text()',
            'current_price': 'td[7]/text()',
            'total_value': 'td[8]/text()',

        }
        

        for tr in trs:
            # <div class="detailButton btn-expand close" id="PS_LONG_0" data-symbol="TMO" data-portfolioid="5700657" data-stocktype="long"></div>
            position_data = {k: tr.xpath(v)[0] for k, v in xpath_map.items()}

            stock_type = tr.xpath('td[1]/div/@data-stocktype')[0]
            trade_link = tr.xpath('td[2]/a[2]/@href')[0]
            print(trade_link)

            if stock_type == 'long':
                long_pos = LongPosition(trade_link, stock_type, **position_data)
                stock_portfolio.append(long_pos)
            if stock_type == 'short':
                short_pos = ShortPosition(trade_link,stock_type, **position_data)
                short_portfolio.append(short_pos)
