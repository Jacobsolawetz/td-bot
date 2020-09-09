import requests
from datetime import datetime

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

    def get_positions(self):

        ####get account ID####
        # define an endpoint with a stock of your choice, MUST BE UPPER
        endpoint = r"https://api.tdameritrade.com/v1/accounts"
        #payload = {'fields':'positions'}
        # make a request
        content = requests.get(url = endpoint, headers = self.headers)
        # convert it dictionary object
        data = content.json()
        account_id = data[0]['securitiesAccount']['accountId']

        ###now get positions####
        endpoint = r"https://api.tdameritrade.com/v1/accounts/" + str(account_id) + "?fields=positions"

        payload = {'fields':'positions,orders'}
        # make a request
        content = requests.get(url = endpoint, headers = self.headers, json=payload)

        # convert it dictionary object
        data = content.json()
        positions = data['securitiesAccount']['positions']
        #get position expirs from put symbol
        for p in positions:
            pos_date_str = p['instrument']['symbol'].split('_')[1][0:6]
            pos_date_str = pos_date_str[0:2] + '-' + pos_date_str[2:4] + '-' + '20' + pos_date_str[4:6]
            format_str = '%m-%d-%Y'
            pos_date = datetime.strptime(pos_date_str, format_str)
            p['expir_date'] = pos_date
        #get strike from symbol
        for p in positions:
            strike = int(p['instrument']['symbol'].split('P')[2])
            p['strike'] = strike
        return positions

    def value_at_risk(self, positions):
        expirs = []
        for pos in positions:
            #print(pos)
            expirs.append(pos['expir_date'])
        unique_expirs = list(set(expirs))

        var_by_expir = {}
        total_var = 0
        for expir in unique_expirs:
            pos_expir = [p for p in positions if p['expir_date'] == expir]
            risked = 0
            hedged = 0
            for expir_p in pos_expir:
                risked += (expir_p['shortQuantity'] * expir_p['strike'] * 100)
                hedged += (expir_p['longQuantity'] * expir_p['strike'] * 100)
            var_by_expir[expir] = risked - hedged
            total_var += risked - hedged
        return total_var, var_by_expir

    def get_num_contracts(self, positions):
        expirs = []
        for pos in positions:
            #print(pos)
            expirs.append(pos['expir_date'])
        unique_expirs = list(set(expirs))

        contracts_by_expir = {}
        total_contracts = 0
        for expir in unique_expirs:
            pos_expir = [p for p in positions if p['expir_date'] == expir]
            short = 0
            for expir_p in pos_expir:
                short += expir_p['shortQuantity']
            contracts_by_expir[expir] = short
            total_contracts += short
        return total_contracts, contracts_by_expir
