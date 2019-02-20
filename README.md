# investopedia simulator api

## Description
A simple Python API for Investopedia's stock simulator games.  

## Features
This is a work-in-progress.  I am actively developing as of 2019-02-15.  Currently you can basically read your stock portfolio.  I'm planning on adding support for trading stocks and options and whatever else others or myself would find useful.

## Authentication
Investopedia put a recaptcha puzzle thing on their login page so that **every 3 months you will need to manually get a new session cookie value for this to work.**.  Fortunately, that's pretty easy, doesn't take much time, and wasn't often enough to deter me from starting this project.  I am currently looking to find a way to refresh the session cookie so that the session can live indefinitely.  Anyway this is what you need to do every three months:

1. Go to investopedia.com login screen
2. Solve recaptcha
3. Login
4. Inspect cookies with your browser's dev tools
5. Find the cookie called UI4, copy the value only
6. Pass it to the InvestopediaSimulatorAPI constructor
7. Don't worry about it for 3 months.

### Security considerations
**Don't fork this repo and publish your cookie for the whole world to see.  Anyone with that string can access your account.**  For your convenience I added auth_cooke.json to .gitignore.  If you plan on forking this to a publicly accessible repository then you should probably put your cookie in that untracked file and read from it.
  
## Example
### code
 ```
# good for 3 months
cookie_val = 'ce271b7c5db3b7f999bf35a75c8cb6a9a9c113e8b6daae75a25fad9bd836936e318e6f5cf68b2415ca65b42abcdb97a9471bb4d98a53f8db43d14cf7a9f76f2cea315c8aa6a977986693fa9aa3be8a6ba3f5eabfd39b598f357afa6a83a887b89c6e54f9d3b1e298'

client = InvestopediaSimulatorAPI(auth_cookie=cookie_val)
portfolio = client.stock_portfolio

print("Default (active) game: %s" % client.active_game)
print("Portfolio total value: %s" % portfolio.total_value)
for holding in portfolio:
    stock = holding.stock
    print("\nStock symbol: %s (%s)" % (stock.symbol, stock.url))
    print("Start price: %s" % holding.start)
    print("Current price: %s" % holding.current)
    print("Net return: %s\n" % holding.net_return)
 ```
 ### output
```
Game: Investopedia Game 2019 No End
id: 394100
url: https://www.investopedia.com/simulator/portfolio/?gameid=394100
Portfolio total value: 115827.59

Stock symbol: ERIE (https://www.investopedia.com/markets/stocks/erie/)
Start price: 165.24
Current price: 167.14
Net return: 76.0


Stock symbol: FOX (https://www.investopedia.com/markets/stocks/fox/)
Start price: 49.9
Current price: 50.17
Net return: 36.18


Stock symbol: EGAN (https://www.investopedia.com/markets/stocks/egan/)
Start price: 11.27
Current price: 11.61
Net return: 204.0
```

## More Info / Documentation ##
This is a work in progress.  I'll add more documentation as I continue developing.  I also plan on making this a module and publishing to pip.
