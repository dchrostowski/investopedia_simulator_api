## Description
A simple Python API for Investopedia's stock simulator games.  I initially released this project around 2018/2019, but since then Investopedia made some significant changes which rendered this API useless.  I'm currently working on overhauling it in 2024 and have some functionality restored.

## Features
Currently you can programmatically:
* Read all positions in your stock, and short portfolios and get quotes for each position
* Fetch and cancel pending/open trades


Coming soon:
* Buy/Sell long positions
* Short sell/cover short positions
* Buy/sell options
* Perform option chain lookups
* Buy/sell options

## Dependencies
To use this API, there are a few dependencies that you will need to install.  See the below sections for an explanation of each.

### Python
This API is intended to be used for writing Python programs to automate trades in the Investopedia Stock Simulator, therefore you should have Python installed on your system.  I recommend using Python 3.12.2 or later to avoid running into issues or other problems.  You can download Python [here](https://www.python.org/downloads/).

### Git (optional)
This API is not currently hosted as a package anywhere, so you'll need to download the code directly from GitHub to use it.  [Download and install the latest version of Git](https://git-scm.com/downloads) on your system and run the following in a terminal to download a copy of this repository:

`git clone https://github.com/dchrostowski/investopedia_simulator_api.git/`

Alternatively, you can just download a zipped archive of the source code directly from this project's GitHub page and unzip it somewhere on your filesystem.  To do this, click on the green Code button and select Download ZIP.

### Node.js
Node.js is utilized to facilitate logging in to the simulator with a virtual web browser and fetching authentication tokens.  [Download and install the latest version of Node.js on your system here.](https://nodejs.org/en/download).


## Usage

Once all dependencies are installed, you will need to use pip to install supplementary Python packages to run your code with the API.  Open a terminal on your system and navigate to where you downloaded this code:

```cd path/to/investopedia_simulator_api```

Next run the following command to install the supplementary packages:

```pip install -r ./requirements.txt```

Once all the required packages are installed, you will need to provide your login credentials for the Investopedia Stock Simulator.  Rename the ```credentials_example.json``` file to ```credentials.json```, open it, and replace the username and password values with your actual username and password for logging in to Investopedia.  Make sure you leave the double quotes intaact.

Finally, try running the provided `example.py` file.  This `example.py` file is a usage example of the API.  Feel free to modify it as you see fit for your needs:

```python example.py```

## Example
### code
```
from investopedia_api import InvestopediaApi, TradeExceedsMaxSharesException
import json
import datetime

credentials = {}
with open('credentials.json') as ifh:
    credentials = json.load(ifh)
# look at credentials_example.json
# credentials = {"username": "you@example.org", "password": "yourpassword" }
client = InvestopediaApi(credentials)

p = client.portfolio
print("\nPortfolio Details")
print("-------------------------------------------------")
print("Portfolio Value: %s" % p.account_value)
print("Cash: %s" % p.cash)
print("Buying Power: %s" % p.buying_power)
print("Annual Return Percent: %s" % p.annual_return_pct)
print("-------------------------------------------------")


print("\nOpen Orders:")
for open_order in p.open_orders:
    print("-------------------------------------------------")
    print("Trade Type: %s" % open_order.trade_type)
    print("Symbol: %s" % open_order.symbol)
    print("Quantity: %s" % open_order.quantity)
    print("Price: %s" % open_order.order_price)
    print("-------------------------------------------------")

stock_portfolio = p.stock_portfolio
short_portfolio = p.short_portfolio

print("\nStock Portfolio Details:")
print("-------------------------------------------------")
print("Market Value: %s" % stock_portfolio.market_value)
print("Today's Gain: %s (%s%%)" % (stock_portfolio.day_gain_dollar, stock_portfolio.day_gain_percent))
print("Total Gain: %s (%s%%)" % (stock_portfolio.total_gain_dollar, stock_portfolio.total_gain_percent))
print("-------------------------------------------------")

print("\nLong Positions:")
for position in stock_portfolio:
    print("-------------------------------------------------")
    print("Company: %s (%s)" % (position.description, position.symbol))
    print("Shares: %s" % position.quantity)
    print("Purchase Price: %s" % position.purchase_price)
    print("Current Price: %s" % position.current_price)
    print("Today's Gain: %s (%s%%)" % (position.day_gain_dollar, position.day_gain_percent))
    print("Total Gain: %s (%s%%)" % (position.total_gain_dollar, position.total_gain_percent))
    print("Market/Total Value: %s" % position.market_value)
    print("\t------------------------------")
    print("\tQuote")
    print("\t------------------------------")
    quote = position.quote
    for k,v in quote.__dict__.items():
        print("\t%s: %s" % (k,v))
    print("\t------------------------------")
    print("-------------------------------------------------")


print("\nShort Positions:")
for position in short_portfolio:
    print("-------------------------------------------------")
    print("Company: %s (%s)" % (position.description, position.symbol))
    print("Shares: %s" % position.quantity)
    print("Purchase Price: %s" % position.purchase_price)
    print("Current Price: %s" % position.current_price)
    print("Today's Gain: %s (%s%%)" % (position.day_gain_dollar, position.day_gain_percent))
    print("Total Gain: %s (%s%%)" % (position.total_gain_dollar, position.total_gain_percent))
    print("Market/Total Value: %s" % position.market_value)
    print("\t------------------------------")
    print("\tQuote")
    print("\t------------------------------")
    quote = position.quote
    for k,v in quote.__dict__.items():
        print("\t%s: %s" % (k,v))
    print("\t------------------------------")
    print("-------------------------------------------------")

    ```