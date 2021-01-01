import math
from scipy.stats import norm
import pandas as pd
from datetime import date
import numpy as np
from emailer import send_message
from execution import Execution
from utils import calculate_strike

class Strategy:
    def __init__(self, trading_days_until_current_expir, current_var, current_var_by_expir, liquidation_value, current_options_friday, next_options_friday, spy_price, vix_price, headers):

        self.max_loss = 0.7
        self.leverage = 12
        self.z_score = 2.0

        #the distance between a put spread, is a function of where the spy is, the leverage you want to take, and the max loss
        #leverage calculated against sold put strike
        self.options_spread = (spy_price/self.leverage) * self.max_loss
        self.var_per_contract = self.options_spread * 100

        #current_var: current valuation at risk, float
        #current_var_by_expir: {expir (datetime): value at risk}
        #liquidationValue, value of portoflio at given snapshot, float
        self.trading_days_until_current_expir = trading_days_until_current_expir
        self.current_var = current_var
        self.current_var_by_expir = current_var_by_expir
        self.liquidation_value = liquidation_value
        self.current_options_friday = current_options_friday
        self.next_options_friday = next_options_friday
        self.spy_price = spy_price
        self.vix_price = vix_price

        #check to make sure market calendar logic is working
        for expir in current_var_by_expir.keys():
            if expir not in [current_options_friday, next_options_friday]:
                #we got trouble
                message = "Subject: Trading FAILED \n\n" \
                    + "Trading execution script failed because market calendar logic did not match up. " + "\n\n" \
                    + "The position expiration keys  " + str(current_var_by_expir.keys()) + " did not match the market calendar keys " + str([current_options_friday, next_options_friday]) + "\n\n" \
                    + "The current monthly options contract will expire in this many trading days: " + str(trading_days_until_current_expir) + "\n\n" \
                    + "This might have to do with pandas mcal or the way the positions are set. Happy debugging  "  "\n\n" \
                    + "Sincerely,\n" \
                    + "K.M.T."
                to_email = "jacob@roboflow.ai"
                send_message(to_email, message)

                raise Exception("market calendar logic failed we sent you a failure email")

        self.execution = Execution(headers)

        self.num_open_contracts_current = self.execution.get_num_open_contracts_current(self.current_options_friday)
        self.num_opened_contracts_current = self.execution.get_num_opened_contracts_current(self.current_options_friday)
        self.num_closed_contracts_current = self.num_opened_contracts_current - self.num_open_contracts_current

        self.var_opened_to_next = self.execution.get_var_opened_to_next(self.next_options_friday)

        print('printing new variables ', self.num_open_contracts_current, self.num_opened_contracts_current, self.num_closed_contracts_current, self.var_opened_to_next)

        print('initializing short vol strategy')

    def recommend_action(self, trading_days_until_current_expir):
        recommendations = []

        if trading_days_until_current_expir > 20:
            recommendations.append('nothing to do, more than 20 trading days from current expir')
            return recommendations

        elif trading_days_until_current_expir > 5:
            ##roll logic
            #close logic
            num_to_close = round(float((self.num_open_contracts_current / (trading_days_until_current_expir - 5))))
            if num_to_close > 0:
                recommendations.append(self.close(num_to_close, self.current_options_friday))
            #open logic
            pct_current_closed = float((num_to_close + self.num_closed_contracts_current) / self.num_opened_contracts_current)
            #we should have this much value at risk on the next contract
            var_to_open = float((pct_current_closed * self.max_loss * self.liquidation_value) - self.var_opened_to_next)

            num_to_open = round(float(var_to_open / self.var_per_contract))
            if num_to_open > 0:
                recommendations.append(self.open(num_to_open, self.next_options_friday))
        else:
            #next roll health check, in the few days before current contracts would expire
            if self.num_open_contracts_current > 0:
                recommendations.append(self.close(self.num_open_contracts_current, self.current_options_friday))

            target_var = float((self.max_loss * self.liquidation_value))
            var_difference_from_target = (self.var_opened_to_next) - target_var
            if (float(var_difference_from_target / target_var)) > 0.05:
                ##too much exposure
                num_to_close = round(float(var_difference_from_target / self.var_per_contract))
            elif (float(var_difference_from_target / target_var)) < -0.05:
                ##too little exposure
                num_to_open = 0
                num_to_open = round(float(-var_difference_from_target / self.var_per_contract))
                recommendations.append(self.open(num_to_open, self.next_options_friday))
            else:
                recommendations.append('there is 5 or less trading days to expiration and all is well.')

        return recommendations

    def open(self, num_contracts, target_expir):

        strike1 = calculate_strike('P', self.spy_price, self.vix_price, self.z_score)
        strike2 = strike1 - self.options_spread
        strike1 = int(strike1)
        strike2 = int(strike2)
        #trade execution
        self.execution.short(num_contracts, target_expir, strike1, strike2)

        return 'short ' + str(num_contracts) + ' contracts, expiring on ' + str(target_expir) + ' struck at ' + str(strike1) + ' and ' + str(strike2)

    def close(self, num_contracts, target_expir):
        #trade execution
        self.execution.close(num_contracts, target_expir)

        return 'close_var: ' + 'buy back ' + str(num_contracts) + ' contracts, expiring on ' + str(self.current_options_friday)
