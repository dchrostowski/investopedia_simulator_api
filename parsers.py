
from IPython import embed
from api_models2 import LongPosition

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
    def positions(tree):

        xpath_map = {
            'portfolio_id': 'td[1]/div/@data-portfolioid',
            'stock_type': 'td[1]/div/@data-stocktype',
            'symbol': 'td[1]/div/@data-symbol',
            'description': 'td[4]/text()',
            'quantity': 'td[5]/text()',
            'purchase_price': 'td[6]/text()',
            'current_price': 'td[7]/text()',
            'total_value': 'td[8]/text()',
            'total_change': 'td[9]/text()',

        }
        trs = tree.xpath(
            '//table[contains(@class,"table1")]/tbody/tr[not(contains(@class,"expandable")) and not(contains(@class,"no-border"))]')
        for tr in trs:
            # <div class="detailButton btn-expand close" id="PS_LONG_0" data-symbol="TMO" data-portfolioid="5700657" data-stocktype="long"></div>
            position_data = {k: tr.xpath(v)[0] for k, v in xpath_map.items()}
            if position_data['stock_type'] == 'long':
                del position_data['stock_type']
                long_pos = LongPosition(**position_data)
                print(long_pos)
                embed()
