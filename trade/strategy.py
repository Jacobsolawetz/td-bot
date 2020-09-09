import math
from scipy.stats import norm
import pandas as pd
from datetime import date
import numpy as np
from emailer import send_message


class Strategy:
    def __init__(self, trading_days_until_current_expir, current_var, current_var_by_expir, liquidation_value, current_options_friday, next_options_friday, spy_price, vix_price):

        self.max_loss = 0.6
        self.leverage = 10

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

    ####REVISIT####
    ####probably want to introduce the concept of a "reduced roll" rather than just close

    def recommend_action(self, desired_current_allocation, current_allocation_ratio):
        recommendations = []
        if self.current_var / self.liquidation_value < self.max_loss:
            recommendations.append('increase_var_to_current: ' + self.increase_var_to_current(amt=0.05))

        if current_allocation_ratio > desired_current_allocation:
            #roll more if we're more out of wack with schedule
            if current_allocation_ratio - desired_current_allocation > 0.1:
                amt_to_roll = 0.08
                amt_to_close = 0.05
            else:
                amt_to_roll = 0.05
                amt_to_close = 0.05

            #decide between roll or close
            #10% buffer
            if self.current_var / self.liquidation_value > (self.max_loss + .1):
                #too much exposure, cut losses and de-risk
                recommendations.append(self.close_var_to_current(amt=amt_to_close))
            else:
                recommendations.append(self.roll_var_to_next(amt=amt_to_roll))
        return recommendations

    def increase_var_to_current(self, amt=0.05):
        if int(self.trading_days_until_current_expir) > 10:
            target_expir = self.current_options_friday
        else:
            target_expir = self.next_options_friday
        target_var_to_increase = self.liquidation_value*amt
        num_contracts = round(float(target_var_to_increase / self.var_per_contract))

        return 'short ' + str(num_contracts) + ' conracts, expiring on ' + str(target_expir) + ' with spread ' + str(self.options_spread)

    def close_var_to_current(self, amt=0.05):
        #close 5% var in current expir
        #need a notion of trade date from order history to close the last contract
        #could use spy direction to infer
        target_var_to_close = self.current_var*amt
        num_contracts = int(target_var_to_increase / self.var_per_contract)

        return 'close_var_to_current: ' + 'buy back ' + str(num_contracts) + ' contracts, expiring on ' + str(self.current_options_friday)

    def roll_var_to_next(self, amt=0.05):
        #close 5% var in current expir
        #open 5% var in next expir
        target_var_to_roll = self.liquidation_value * amt
        num_contracts = round(float(target_var_to_roll / self.var_per_contract))


        return 'roll_var_to_next: ' + 'roll ' + str(num_contracts) + ' number of contracts to the next month with spread ' + str(self.options_spread)
