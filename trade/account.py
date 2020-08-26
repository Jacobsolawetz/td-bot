import requests

class Account:
    def __init__(self, headers):
        self.headers = headers
        print('current_account_intialized')


    def get_liquidation_value(self):
        # define an endpoint with a stock of your choice, MUST BE UPPER
        endpoint = r"https://api.tdameritrade.com/v1/accounts"
        #payload = {'fields':'positions'}
        # make a request
        content = requests.get(url = endpoint, headers = self.headers)
        # convert it dictionary object
        data = content.json()
        # grab the account id
        liquidation_value = data[0]['securitiesAccount']['currentBalances']['liquidationValue']
        return liquidation_value
