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

        self.max_loss = 0.6
        self.leverage = 10
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
            #our portfolio has gone up in value, add some exposure
            recommendations.append('increase_var_to_current: ' + self.increase_var_to_current(amt=0.05))

        if current_allocation_ratio > desired_current_allocation:
            #roll if we're behind schedule
            if current_allocation_ratio - desired_current_allocation > 0.1:
                #roll a bit more if we're definitively behind
                amt_to_roll = 0.08
                amt_to_close = 0.05
            else:
                amt_to_roll = 0.05
                amt_to_close = 0.05

            #decide between roll or close
            #10% buffer
            if self.current_var / self.liquidation_value > (self.max_loss + .1):
                #too much exposure, cut losses and de-risk
                message = "Subject: Too Much Exposure! \n\n" \
                    + "Trading execution script found too much exposure and recommend close. " + "\n\n" \
                    + "If this is the first time this happened, you should check your account and make sure everything is working well. Nothing was executed in the strategy. " + "\n\n" \
                    + "This recommendation occurs when VAR / liquidation_value > (max_loss + 10%) " + "\n\n" \
                    + "You considered it an edge case and thought leaving it to manual would be better. " + "\n\n" \
                    + "Sincerely,\n" \
                    + "K.M.T."
                to_email = "jacob@roboflow.ai"
                send_message(to_email, message)
                recommendations.append(self.close_var_to_current(amt=amt_to_close))
            else:
                recommendations.append(self.roll_var_to_next(amt=amt_to_roll))
        return recommendations

    def increase_var_to_current(self, amt=0.05):
        if int(self.trading_days_until_current_expir) > 15:
            target_expir = self.current_options_friday
        else:
            target_expir = self.next_options_friday
        target_var_to_increase = self.liquidation_value*amt
        num_contracts = round(float(target_var_to_increase / self.var_per_contract))

        strike1 = calculate_strike('P', self.spy_price, self.vix_price, self.z_score)
        strike2 = strike1 - self.options_spread
        strike1 = int(strike1)
        strike2 = int(strike2)
        #trade execution
        #self.execution.short(num_contracts, target_expir, strike1, strike2)

        return 'short ' + str(num_contracts) + ' contracts, expiring on ' + str(target_expir) + ' struck at ' + str(strike1) + ' and ' + str(strike2)

    def close_var_to_current(self, amt=0.05):
        #close 5% var in current expir
        #need a notion of trade date from order history to close the last contract
        #could use spy direction to infer
        target_var_to_close = self.current_var*amt
        num_contracts = int(target_var_to_increase / self.var_per_contract)

        #trade execution
        #self.execution.close(num_contracts, self.current_options_friday)

        return 'close_var_to_current: ' + 'buy back ' + str(num_contracts) + ' contracts, expiring on ' + str(self.current_options_friday)

    def roll_var_to_next(self, amt=0.05):
        #close 5% var in current expir
        #open 5% var in next expir
        target_var_to_roll = self.liquidation_value * amt
        num_contracts = round(float(target_var_to_roll / self.var_per_contract))

        #self.execution.close(num_contracts, self.current_options_friday)
        target_expir = self.next_options_friday
        strike1 = calculate_strike('P', self.spy_price, self.vix_price, self.z_score)
        strike2 = strike1 - self.options_spread
        strike1 = int(strike1)
        strike2 = int(strike2)

        #self.execution.short(num_contracts, target_expir, strike1, strike2)

        return 'roll_var_to_next: ' + 'roll ' + str(num_contracts) + ' number of contracts from ' + str(self.current_options_friday) + ' to ' + str(self.next_options_friday) + ' with spread ' + str(self.options_spread)
