import requests


class Market:
    def __init__(self, headers):
        self.headers = headers
        print('current_market_intialized')

    def quote_symbol(self, symbol):
        endpoint = r"https://api.tdameritrade.com/v1/marketdata/"+ symbol + "/quotes"

        content = requests.get(url = endpoint, headers = self.headers)

        # convert it dictionary object
        data = content.json()

        # grab the account id
        #account_id = data[0]['securitiesAccount']['accountId']
        return data[symbol]
