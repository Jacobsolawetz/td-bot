from authentication import refresh_auth
from emailer import send_message
from account import Account
from market import Market


if __name__ == '__main__':
    headers = refresh_auth()
    #set up main classes
    current_account = Account(headers)
    current_market = Market(headers)


    #example fields
    liquidation_value = current_account.get_liquidation_value()
    spy_price = current_market.quote_symbol(symbol='SPY')['lastPrice']
    vixy_price = current_market.quote_symbol(symbol='VIXY')['lastPrice']



    message = "Subject: Trading Update \n\n" \
        + "Your current account's liquidation value is : " + str(liquidation_value) + "\n\n" \
        + "The SPY is trading at : " + str(spy_price) + ". The VIXY is trading at : " + str(vixy_price) + "\n\n" \
        + "Sincerely,\n" \
        + "K.M.T."


    to_email = "jacob@roboflow.ai"
    send_message(to_email, message)
