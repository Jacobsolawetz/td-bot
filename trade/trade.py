from authentication import refresh_auth
from emailer import send_message
from account import Account
from market import Market
from utils import desired_current_allocation


if __name__ == '__main__':
    headers = refresh_auth()
    #set up main classes
    current_account = Account(headers)
    current_market = Market(headers)


    #example fields
    liquidation_value = current_account.get_liquidation_value()
    spy_price = current_market.quote_symbol(symbol='SPY')['lastPrice']
    vixy_price = current_market.quote_symbol(symbol='VIXY')['lastPrice']
    trading_days_until_current_expir = current_market.trading_days_until_current_expir
    desired_allocation_pct = desired_current_allocation(int(trading_days_until_current_expir))


    message = "Subject: Trading Update \n\n" \
        + "Your current account's liquidation value is : " + str(liquidation_value) + "\n\n" \
        + "The SPY is trading at : " + str(spy_price) + ". The VIXY is trading at : " + str(vixy_price) + "\n\n" \
        + "The current monthly options contract will expire in this many trading days: " + str(trading_days_until_current_expir) + "\n\n" \
        + "You should have this much of the portfolio on current contract : " + str(desired_allocation_pct) + "\n\n" \
        + "Sincerely,\n" \
        + "K.M.T."


    to_email = "jacob@roboflow.ai"
    send_message(to_email, message)
