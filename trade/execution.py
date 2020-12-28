import requests
from datetime import datetime

from emailer import send_message


class Execution:
    def __init__(self, headers):
        self.headers = headers
        print('execution class initialized ')

    def get_quote(self, symbol):
        endpoint = r"https://api.tdameritrade.com/v1/marketdata/"+ symbol + "/quotes"
        # make a request
        content = requests.get(url = endpoint, headers = self.headers)

        # convert it dictionary object
        data = content.json()

        return data[symbol]

    def place_order(self, order_specs):
        endpoint = r"https://api.tdameritrade.com/v1/accounts"
        #payload = {'fields':'positions'}
        # make a request
        content = requests.get(url = endpoint, headers = self.headers)
        # convert it dictionary object
        data = content.json()
        account_id = data[0]['securitiesAccount']['accountId']

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(account_id)

        content = requests.post(url = endpoint, json = order_specs, headers = self.headers)

        return content

    def get_transactions(self, smybol_start):
        endpoint = r"https://api.tdameritrade.com/v1/accounts"
        #payload = {'fields':'positions'}
        # make a request
        content = requests.get(url = endpoint, headers = self.headers)
        # convert it dictionary object
        data = content.json()
        # grab the account id
        account_id = data[0]['securitiesAccount']['accountId']

        endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/transactions".format(account_id)

        # define the payload, in JSON format
        payload = {
          "type": "TRADE"
        }


        # make a post, NOTE WE'VE CHANGED DATA TO JSON AND ARE USING POST
        content = requests.get(url = endpoint, json = payload, headers = header)
        transactions = content.json()




    def close(self, num_contracts, target_expir):

        target_expir_str = target_expir.strftime("%m%d%y")
        close_symbol_start = 'SPY_' + target_expir_str + 'P'
        #get transaction history for trades made on this contract



        strike1_quote = self.get_quote(strike1_symbol)
        strike2_quote = self.get_quote(strike2_symbol)

        if (strike1_quote['askPrice'] - strike1_quote['askPrice'] > .02) or (strike2_quote['askPrice'] - strike2_quote['askPrice'] > .02):
            #lack of liquidity
            message = "Subject: Lack of Liquidity \n\n" \
                + "Bid ask spread for one of the contracts to be traded exceeded .02, aborting trade for now" + "\n\n" \
                + "target_expir " + str(target_expir) + 'strike ' + str(strike1) + ' strike2 ' + str(strike2) + "\n\n" \
                + "If this is the first time this happened, you should check your account and make sure everything is working well" + "\n\n" \
                + "Sincerely,\n" \
                + "K.M.T."
            to_email = "jacob@roboflow.ai"
            send_message(to_email, message)
            return None
        else:
            #liquidity is there place a market order
            #first buy the put part of the leg
            payload = {
                          "orderType": "MARKET",
                          "session": "NORMAL",
                          "duration": "DAY",
                          "orderStrategyType": "SINGLE",
                          "orderLegCollection": [
                            {
                              "instruction": "BUY_TO_OPEN",
                              "quantity": num_contracts,
                              "instrument": {
                                "symbol": strike2_symbol,
                                "assetType": "OPTION"
                              }
                            }
                          ]
                        }
            buy_result = self.place_order(payload)
            if buy_result.status_code in [200, 201]:
                #if success, then place sale part of the leg
                payload = {
                              "orderType": "MARKET",
                              "session": "NORMAL",
                              "duration": "DAY",
                              "orderStrategyType": "SINGLE",
                              "orderLegCollection": [
                                {
                                  "instruction": "SELL_TO_OPEN",
                                  "quantity": num_contracts,
                                  "instrument": {
                                    "symbol": strike1_symbol,
                                    "assetType": "OPTION"
                                  }
                                }
                              ]
                            }

                sell_result = self.place_order(payload)
                if buy_result.status_code in [200, 201]:
                    print('short successful')

            return None




    def short(self, num_contracts, target_expir, strike1, strike2):
        target_expir_str = target_expir.strftime("%m%d%y")
        strike1_symbol = 'SPY_' + target_expir_str + 'P' + str(strike1)
        strike2_symbol = 'SPY_' + target_expir_str + 'P' + str(strike2)

        strike1_quote = self.get_quote(strike1_symbol)
        strike2_quote = self.get_quote(strike2_symbol)

        if (strike1_quote['askPrice'] - strike1_quote['askPrice'] > .02) or (strike2_quote['askPrice'] - strike2_quote['askPrice'] > .02):
            #lack of liquidity
            message = "Subject: Lack of Liquidity \n\n" \
                + "Bid ask spread for one of the contracts to be traded exceeded .02, aborting trade for now" + "\n\n" \
                + "target_expir " + str(target_expir) + 'strike ' + str(strike1) + ' strike2 ' + str(strike2) + "\n\n" \
                + "If this is the first time this happened, you should check your account and make sure everything is working well" + "\n\n" \
                + "Sincerely,\n" \
                + "K.M.T."
            to_email = "jacob@roboflow.ai"
            send_message(to_email, message)
            return None
        else:
            #liquidity is there place a market order
            #first buy the put part of the leg
            payload = {
                          "orderType": "MARKET",
                          "session": "NORMAL",
                          "duration": "DAY",
                          "orderStrategyType": "SINGLE",
                          "orderLegCollection": [
                            {
                              "instruction": "BUY_TO_OPEN",
                              "quantity": num_contracts,
                              "instrument": {
                                "symbol": strike2_symbol,
                                "assetType": "OPTION"
                              }
                            }
                          ]
                        }
            buy_result = self.place_order(payload)
            if buy_result.status_code in [200, 201]:
                #if success, then place sale part of the leg
                payload = {
                              "orderType": "MARKET",
                              "session": "NORMAL",
                              "duration": "DAY",
                              "orderStrategyType": "SINGLE",
                              "orderLegCollection": [
                                {
                                  "instruction": "SELL_TO_OPEN",
                                  "quantity": num_contracts,
                                  "instrument": {
                                    "symbol": strike1_symbol,
                                    "assetType": "OPTION"
                                  }
                                }
                              ]
                            }

                sell_result = self.place_order(payload)
                if buy_result.status_code in [200, 201]:
                    print('short successful')

            return None
