from api_models2 import *
from IPython import embed


mp = Portfolio(1,2,3,4)
positions = [Position(5.3,6.0), Position(5.4,7.5), Position(4,6)]
sp = StockPortfolio(positions)

sp.total_gain()
sp.total_value()


embed()