from authentication import refresh_auth
from emailer import send_message
from account import Account
from market import Market
#from utils import desired_current_allocation
from strategy import Strategy


if __name__ == '__main__':
    headers = refresh_auth()
    #set up main classes
    current_account = Account(headers)
    current_market = Market(headers)


    #example fields
    liquidation_value = current_account.get_liquidation_value()
    spy_price = current_market.quote_symbol(symbol='SPY')['lastPrice']
    vixy_price = current_market.quote_symbol(symbol='$VIX.X')['lastPrice']
    trading_days_until_current_expir = current_market.trading_days_until_current_expir

    current_positions = current_account.get_positions()
    current_var, current_var_by_expir = current_account.value_at_risk(current_positions)
    current_num_contracts, current_num_contracts_by_expir = current_account.get_num_contracts(current_positions)

    portion_risked = current_var / liquidation_value


    strat = Strategy(trading_days_until_current_expir, current_var, current_var_by_expir, liquidation_value, current_market.current_options_friday, current_market.next_options_friday, spy_price, vixy_price, headers)

    desired_allocation_pct = strat.desired_current_allocation(int(trading_days_until_current_expir))
    #need to think through rebalance routine
    #is it based on notional or market value. What happens when liquidation_value tanks, do you still roll, how to calculate algorithmically.
    #back tester is just rolling a single put, returns multiply on portfolio base value, so it would roll "less of a put"
    current_allocation_ratio = strat.calculate_current_allocation_ratio()
    recommendation = strat.recommend_action(desired_allocation_pct, current_allocation_ratio)



    message = "Subject: Trading Update \n\n" \
        + "Your current account's liquidation value is : " + str(liquidation_value) + "\n\n" \
        + "The SPY is trading at : " + str(spy_price) + ". The VIXY is trading at : " + str(vixy_price) + "\n\n" \
        + "The current monthly options contract will expire in this many trading days: " + str(trading_days_until_current_expir) + "\n\n" \
        + "You should have this much of the portfolio on current contract : " + str(desired_allocation_pct) + "\n\n" \
        + "You currently have this percentage of portfolio risked: " + str(portion_risked) + " in comparison with the target of 60%" + "\n\n" \
        + "Your current put exposure is allocated accordingly " + str(current_var_by_expir) +  "\n\n" \
        + "Based on your current exposures the strategy recommends : " + str(recommendation) +  "\n\n" \
        + "Sincerely,\n" \
        + "K.M.T."


    to_email = "jacob@roboflow.ai"
    send_message(to_email, message)

    #to_email = "hannahclingan@gmail.com"
    #send_message(to_email, message)
