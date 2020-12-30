import requests
from datetime import datetime
from dateutil import parser

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

    def get_close_orders(self, symbol_start, num_contracts):
        ####
        #returns list of positions to close for symbol number of contracts
        ####

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

        opening = []
        closing = []
        for t in transactions:
            if 'instrument' in t['transactionItem']:
                if 'symbol' in t['transactionItem']['instrument']:
                    if t['transactionItem']['instrument']['symbol'].startswith(symbol_start):
                        if t['transactionItem']['positionEffect'] == 'OPENING':
                            opening.append(t)
                        if t['transactionItem']['positionEffect'] == 'CLOSING':
                            closing.append(t)

        #subtract closing trades from the open contracts
        for o in opening:
            for c in closing:
                if o['transactionItem']['instrument']['symbol'] == c['transactionItem']['instrument']['symbol']:
                    if o['transactionItem']['instruction'] != c['transactionItem']['instruction']:
                        #need some date logic
                        #then the position has been closed by some amount
                        o_date = parser.parse(o['transactionDate'])
                        c_date = parser.parse(c['transactionDate'])

                        o_strike = o['transactionItem']['instrument']['symbol'].split('P')[-1]
                        c_strike = c['transactionItem']['instrument']['symbol'].split('P')[-1]

                        o_amount = o['transactionItem']['amount']
                        c_amount = c['transactionItem']['amount']

                        if (c_date > o_date) & (o_strike == c_strike) & (o_amount > 0) & (c_amount > 0):
                          if c_amount > o_amount:
                            o['transactionItem']['amount'] -= o_amount
                            c_date['transactionItem']['amount'] -= o_amount
                          else:
                            o['transactionItem']['amount'] -= c_amount
                            c['transactionItem']['amount'] -= c_amount

        still_open = []

        for o in opening:
          if o['transactionItem']['amount'] > 0:
            still_open.append(o)

        #oldest listed first
        still_open = sorted(still_open, key=lambda k: parser.parse(k['transactionDate']))

        #return list of triples with strike1, strike2, and num_contracts to close

        current_order = {
            "strike1": "",
            "strike2": "",
            "num_contracts": 0
        }

        close_list = []

        #assumtpiton, spread orders will always be ordered in pairs, as execution logic executes sequentially by day
        for o in still_open:

            if num_contracts == 0:
                break

            o_strike = o['transactionItem']['instrument']['symbol'].split('P')[-1]
            o_instruction = o['transactionItem']['instruction']
            o_amount = o['transactionItem']['amount']
            o_symbol = o['transactionItem']['instrument']['symbol']

            if o_instruction == 'SELL':
                current_order['strike1'] = o_symbol
                #add and subtract amounts on the put
                amount_to_close = 0
                if num_contracts > o_amount:
                    amount_to_close = o_amount
                else:
                    amount_to_close = num_contracts
                current_order['num_contracts'] = amount_to_close
                num_contracts -= amount_to_close

                if ((current_order['strike1'] != "") & (current_order['strike2'] != "")):
                    close_list.append(current_order)
                    current_order = {
                        "strike1": "",
                        "strike2": "",
                        "num_contracts": 0
                    }
            elif o_instruction == 'BUY':
                current_order['strike2'] = o_symbol

                if ((current_order['strike1'] != "") & (current_order['strike2'] != "")):
                    close_list.append(current_order)
                    current_order = {
                        "strike1": "",
                        "strike2": "",
                        "num_contracts": 0
                    }

        return close_list




    def close(self, num_contracts, target_expir):

        target_expir_str = target_expir.strftime("%m%d%y")
        close_symbol_start = 'SPY_' + target_expir_str + 'P'
        #get transaction history for trades made on this contract
        close_orders = self.get_close_orders(close_symbol_start, num_contracts)

        for close_order in close_orders:
            strike1_symbol = close_order['strike1']
            strike2_symbol = close_order['strike2']
            num_close_contracts = close_order['num_contracts']

            if int(strike1_symbol.split('P')[-1]) < int(strike2_symbol.split('P')[-1]):
                message = "Subject: Malformed Close \n\n" \
                    + strike1_symbol + " is less than " + strike2_symbol + ". You should review the close order logic. Close routine aborted." + "\n\n" \
                    + "Sincerely,\n" \
                    + "K.M.T."
                to_email = "jacob@roboflow.ai"
                send_message(to_email, message)
                break

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
                                  "instruction": "BUY_TO_CLOSE",
                                  "quantity": num_close_contracts,
                                  "instrument": {
                                    "symbol": strike1_symbol,
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
                                      "instruction": "SELL_TO_CLOSE",
                                      "quantity": num_close_contracts,
                                      "instrument": {
                                        "symbol": strike2_symbol,
                                        "assetType": "OPTION"
                                      }
                                    }
                                  ]
                                }

                    sell_result = self.place_order(payload)
                    if buy_result.status_code in [200, 201]:
                        print('close successful')
                        return 'success'

            return 'failure'

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
                    return 'success'

            return 'failure'
