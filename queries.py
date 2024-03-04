import json
from urllib.parse import urlencode



class Queries(object):

    @staticmethod
    def read_user_id():
        return json.dumps({"operationName":"ReadUserId","variables":{},"query":"query ReadUserId {\n  readUser {\n    ... on UserErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on User {\n      id\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def read_user_portfolios():
        return json.dumps({"operationName":"MyActiveGames","variables":{},"query":"query MyActiveGames {\n  readUserPortfolios(input: {filter: ACTIVE}) {\n    ... on UserDoesNotExistError {\n      errorMessages\n      __typename\n    }\n    ... on UserPortfoliosError {\n      errorMessages\n      __typename\n    }\n    ... on PagedPortfolioList {\n      list {\n        id\n        game {\n          id\n          gameDetails {\n            ... on GameDetails {\n              active\n              description\n              endDate\n              gameType\n              id\n              name\n              numberOfPlayers\n              ownerId\n              rules {\n                allowLateEntry\n                allowMargin\n                allowOptionTrading\n                allowPortfolioResetting\n                allowPortfolioViewing\n                allowShortSelling\n                cashInterestPercent\n                commissionDollars\n                commissionPerContractDollars\n                dailyVolumePercent\n                diversificationOptionsPercent\n                diversificationPercent\n                marginInterestPercent\n                marketDelayMinutes\n                minStockForMarginDollars\n                minimumPriceDollars\n                minimumPriceToShortDollars\n                quickSellDurationMinutes\n                startingCashDollars\n                __typename\n              }\n              startDate\n              owner {\n                ... on UserResponse {\n                  id\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def portfolio_summary_query(portfolio_id):
        return json.dumps({"operationName":"PortfolioSummary","variables":{"portfolioId":portfolio_id},"query":"query PortfolioSummary($portfolioId: String!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on Portfolio {\n      summary {\n        accountValue\n        annualReturn\n        buyingPower\n        cash\n        dayGainDollar\n        dayGainPercent\n        __typename\n      }\n      __typename\n    }\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def open_stock_trades(portfolio_id):
        return json.dumps({"operationName":"PendingStockTrades","variables":{"portfolioId":portfolio_id,"holdingType":"STOCKS"},"query":"query PendingStockTrades($portfolioId: String!, $holdingType: HoldingType!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: $holdingType) {\n        ... on CategorizedStockHoldings {\n          pendingTrades {\n            stock {\n              ... on Stock {\n                description\n                technical {\n                  lastPrice\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            symbol\n            transactionTypeDescription\n            orderPriceDescription\n            tradeId\n            action\n            cancelDate\n            quantity\n            quantityType\n            transactionType\n            limit {\n              limit\n              stop\n              trailingStop {\n                percentage\n                price\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def open_option_trades(portfolio_id):
        return json.dumps({"operationName":"PendingOptionTrades","variables":{"portfolioId":portfolio_id,"holdingType":"OPTIONS"},"query":"query PendingOptionTrades($portfolioId: String!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: OPTIONS) {\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedOptionHoldings {\n          pendingTrades {\n            option {\n              ... on Option {\n                isPut\n                expirationDate\n                lastPrice\n                strikePrice\n                stock {\n                  ... on Stock {\n                    symbol\n                    technical {\n                      lastPrice\n                      __typename\n                    }\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            symbol\n            transactionTypeDescription\n            orderPriceDescription\n            tradeId\n            action\n            cancelDate\n            quantity\n            quantityType\n            transactionType\n            limit {\n              limit\n              stop\n              trailingStop {\n                percentage\n                price\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def open_short_trades(portfolio_id):
        return json.dumps({"operationName":"PendingStockTrades","variables":{"portfolioId":portfolio_id,"holdingType":"SHORTS"},"query":"query PendingStockTrades($portfolioId: String!, $holdingType: HoldingType!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: $holdingType) {\n        ... on CategorizedStockHoldings {\n          pendingTrades {\n            stock {\n              ... on Stock {\n                description\n                technical {\n                  lastPrice\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            symbol\n            transactionTypeDescription\n            orderPriceDescription\n            tradeId\n            action\n            cancelDate\n            quantity\n            quantityType\n            transactionType\n            limit {\n              limit\n              stop\n              trailingStop {\n                percentage\n                price\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def cancel_order(order_id):
        return json.dumps({"operationName":"CancelTrade","variables":{"input":order_id},"query":"mutation CancelTrade($input: String!) {\n  submitCancelTrade(tradeId: $input) {\n    ... on CancelTradeErrorResponse {\n      errorMessages\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def refresh_token(refresh_token):
        return urlencode({'grant_type': 'refresh_token', 'refresh_token': refresh_token, 'client_id': 'finance-simulator'})

    @staticmethod
    def stock_holdings(portfolio_id):
        return json.dumps({"operationName":"StockHoldings","variables":{"portfolioId":portfolio_id,"holdingType":"STOCKS"},"query":"query StockHoldings($portfolioId: String!, $holdingType: HoldingType!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: $holdingType) {\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedStockHoldings {\n          holdingsSummary {\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          executedTrades {\n            stock {\n              ... on Stock {\n                symbol\n                description\n                technical {\n                  lastPrice\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            symbol\n            quantity\n            purchasePrice\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def option_holdings(portfolio_id):
        return json.dumps({"operationName":"OptionHoldings","variables":{"portfolioId":portfolio_id,"holdingType":"OPTIONS"},"query":"query OptionHoldings($portfolioId: String!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: OPTIONS) {\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedOptionHoldings {\n          holdingsSummary {\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          executedTrades {\n            option {\n              ... on SymbolNotFoundResponse {\n                errorMessages\n                __typename\n              }\n              ... on InvalidSymbolResponse {\n                errorMessages\n                __typename\n              }\n              ... on Option {\n                symbol\n                isPut\n                lastPrice\n                expirationDate\n                strikePrice\n                stock {\n                  ... on Stock {\n                    symbol\n                    description\n                    technical {\n                      lastPrice\n                      __typename\n                    }\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            quantity\n            purchasePrice\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def short_holdings(portfolio_id):
        return json.dumps({"operationName":"StockHoldings","variables":{"portfolioId":portfolio_id,"holdingType":"SHORTS"},"query":"query StockHoldings($portfolioId: String!, $holdingType: HoldingType!) {\n  readPortfolio(portfolioId: $portfolioId) {\n    ... on PortfolioErrorResponse {\n      errorMessages\n      __typename\n    }\n    ... on Portfolio {\n      holdings(type: $holdingType) {\n        ... on HoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedHoldingsErrorResponse {\n          errorMessages\n          __typename\n        }\n        ... on CategorizedStockHoldings {\n          holdingsSummary {\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          executedTrades {\n            stock {\n              ... on Stock {\n                symbol\n                description\n                technical {\n                  lastPrice\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            symbol\n            quantity\n            purchasePrice\n            marketValue\n            dayGainDollar\n            dayGainPercent\n            totalGainDollar\n            totalGainPercent\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def stock_search(symbol):
        return json.dumps({"operationName":"StockSearch","variables":{"input":{"term":symbol}},"query":"query StockSearch($input: StockSearchInput!) {\n  searchStockSymbols(input: $input) {\n    list {\n      symbol\n      description\n      __typename\n    }\n    totalSize\n    __typename\n  }\n}\n"})

    @staticmethod
    def stock_exchange(symbol):
        return json.dumps({"operationName":"stockExchange","variables":{"symbol":symbol},"query":"query stockExchange($symbol: String!) {\n  readStock(symbol: $symbol) {\n    ... on Stock {\n      exchange\n      __typename\n    }\n    __typename\n  }\n}\n"})

    @staticmethod
    def stock_quote(symbol):
        return json.dumps({"operationName":"CompanyProfile","variables":{"symbol":symbol},"query":"query CompanyProfile($symbol: String!) {\n  readStock(symbol: $symbol) {\n    ... on Stock {\n      technical {\n        volume\n        dayHighPrice\n        dayLowPrice\n        askPrice\n        bidPrice\n        __typename\n      }\n      fundamental {\n        lowestPriceLast52Weeks\n        highestPriceLast52Weeks\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"})
                          
    @staticmethod
    def validate_stock_trade(trade):
        # portfolio_id, expiry, limit, quantity, symbol, transaction_type
        expiry = trade.expiration
        limit = trade.order_limit
        portfolio_id = trade.portfolio_id
        quantity = trade.quantity
        symbol = trade.symbol
        transaction_type = trade.transaction_type

        return json.dumps({"operationName":"PreviewStockTrade","variables":{"input":{"expiry":expiry,"limit":limit,"portfolioId":portfolio_id,"quantity":quantity,"symbol":symbol,"transactionType":transaction_type}},"query":"query PreviewStockTrade($input: TradeEntityInput!) {\n  previewStockTrade(stockTradeEntityInput: $input) {\n    ... on TradeDetails {\n      bill {\n        commission\n        price\n        quantity\n        total\n        __typename\n      }\n      __typename\n    }\n    ... on TradeInvalidEntity {\n      errorMessages\n      __typename\n    }\n    ... on TradeInvalidTransaction {\n      errorMessages\n      __typename\n    }\n    __typename\n  }\n}\n"})
    
    @staticmethod
    def execute_stock_trade(trade):
        expiry = trade.expiration
        limit = trade.order_limit
        portfolio_id = trade.portfolio_id
        quantity = trade.quantity
        symbol = trade.symbol
        transaction_type = trade.transaction_type
        
        return json.dumps({"operationName":"StockTrade","variables":{"input":{"expiry":expiry,"limit":limit,"portfolioId":portfolio_id,"quantity":quantity,"symbol":symbol,"transactionType":transaction_type}},"query":"mutation StockTrade($input: TradeEntityInput!) {\n  submitStockTrade(stockTradeEntityInput: $input) {\n    ... on TradeInvalidEntity {\n      errorMessages\n      __typename\n    }\n    ... on TradeInvalidTransaction {\n      errorMessages\n      __typename\n    }\n    __typename\n  }\n}\n"}
)
