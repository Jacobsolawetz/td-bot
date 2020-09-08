import math
from scipy.stats import norm
import pandas as pd
from datetime import date
import numpy as np
from emailer import send_message


class Strategy:
    def __init__(self, current_var, current_var_by_expir, liquidation_value, current_options_friday, next_options_friday):

        self.max_loss = 0.6

        #current_var: current valuation at risk, float
        #current_var_by_expir: {expir (datetime): value at risk}
        #liquidationValue, value of portoflio at given snapshot, float
        self.current_var = current_var
        self.current_var_by_expir = current_var_by_expir
        self.liquidation_value = liquidation_value
        self.current_options_friday = current_options_friday
        self.next_options_friday = next_options_friday

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


        print('initializing short vol strategy')

    def desired_current_allocation(self, trading_days_until_current_expir):
        #roll 1/20 of the portfolio from trade days 25 to day 5
        if trading_days_until_current_expir >= 25:
            return 1.0
        elif trading_days_until_current_expir < 5:
            return 0.0
        else:
            return float((trading_days_until_current_expir - 5) / 20)

    def calculate_current_allocation_ratio(self):
        #calculates based on the currrent value at risk for each of the next expirations

        if self.current_options_friday in self.current_var_by_expir.keys():
            current_options_var = self.current_var_by_expir[self.current_options_friday]
        else:
            current_options_var = 0

        if self.next_options_friday in self.current_var_by_expir.keys():
            next_options_var = self.current_var_by_expir[self.next_options_friday]
        else:
            next_options_var = 0

        return current_options_var / (current_options_var + next_options_var)

    def recommend_action(self, desired_current_allocation, current_allocation_ratio):
        recommendations = []
        if self.current_var / self.liquidation_value < self.max_loss:
            recommendations.append('increase_var_to_current')

        if current_allocation_ratio > desired_current_allocation:
            #decide between roll or close
            #10% buffer
            if self.current_var / self.liquidation_value > (self.max_loss + .1):
                #too much exposure, cut losses and de-risk
                recommendations.append('close_var_to_current')
            else:
                recommendations.append('roll_var_to_next')
        return recommendations

    def increase_var_to_current(self, amt=.05):
        #if days to expir > 10: add 5% var to current options contract
        #else: add 5% var to next contract
        return None

    def close_var_to_current(self, amt=.05):
        #close 5% var in current expir
        #need a notion of trade date from order history to close the last contract
        #could use spy direction to infer
        return None

    def roll_var_to_next(self, amt=.05):
        #close 5% var in current expir
        #open 5% var in next expir
        return None
