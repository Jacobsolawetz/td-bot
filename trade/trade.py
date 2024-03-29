from authentication import refresh_auth
from emailer import send_message
from account import Account
from market import Market
#from utils import desired_current_allocation
from strategy import Strategy


if __name__ == '__main__':
    try:
        headers = refresh_auth()
    except:
        print('auth failed')
        message = "Subject: Error in Auth! \n\n" \
            + "Authentication failed. You probably need to refresh your refresh key. https://colab.research.google.com/drive/13KdhhOhDh5M1rr4Bcw9daJ1RSCSK8D06#scrollTo=UdtBy0v4a4Y7."

        to_email = "jacob@roboflow.ai"
        send_message(to_email, message)

    #set up main classes
    current_account = Account(headers)
    current_market = Market(headers)

    if current_market.is_trading_day:
        liquidation_value = current_account.get_liquidation_value()
        spy_price = current_market.quote_symbol(symbol='SPY')['lastPrice']
        vixy_price = current_market.quote_symbol(symbol='$VIX.X')['lastPrice']
        trading_days_until_current_expir = current_market.trading_days_until_current_expir

        current_positions = current_account.get_positions()
        current_var, current_var_by_expir = current_account.value_at_risk(current_positions)
        current_num_contracts, current_num_contracts_by_expir = current_account.get_num_contracts(current_positions)

        portion_risked = current_var / liquidation_value

        strat = Strategy(trading_days_until_current_expir, current_var, current_var_by_expir, liquidation_value, current_market.current_options_friday, current_market.next_options_friday, spy_price, vixy_price, headers)

        #this is where trade execution happens
        recommendation = strat.recommend_action(int(trading_days_until_current_expir))

        message = "Subject: Trading Update \n\n" \
            + "Your current account's liquidation value is : " + str(liquidation_value) + "\n\n" \
            + "The SPY is trading at : " + str(spy_price) + ". The VIXY is trading at : " + str(vixy_price) + "\n\n" \
            + "The current monthly options contract will expire in this many trading days: " + str(trading_days_until_current_expir) + "\n\n" \
            + "Your current put exposure is allocated accordingly " + str(current_var_by_expir) +  "\n\n" \
            + "You currently have this many contracts open to the current expiration: " + str(strat.num_open_contracts_current) + " and you have closed this many to the current contract: " + str(strat.num_closed_contracts_current) + "\n\n" \
            + "Your current put exposure is allocated accordingly " + str(current_var_by_expir) +  "\n\n" \
            + "Based on your current exposures the strategy recommends and executes: " + str(recommendation) +  "\n\n" \
            + "Sincerely,\n" \
            + "K.M.T."

        to_email = "jacob@roboflow.ai"
        send_message(to_email, message)
    else:
        message = "Subject: Not a Trading Day \n\n" \
            + "Kick back and relax and chill." + "\n\n" \
            + "Sincerely,\n" \
            + "K.M.T."

        to_email = "jacob@roboflow.ai"
        send_message(to_email, message)
