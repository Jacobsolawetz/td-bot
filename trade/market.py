import requests
import pandas_market_calendars as mcal
import pandas as pd
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from utils import is_third_friday



class Market:
    def __init__(self, headers):
        self.headers = headers
        print('current_market_intialized')
        ######routine to calculate date based variables#####
        today = datetime.today()#.strftime('%Y-%m-%d')
        two_month = today + relativedelta(months=2)
        today_str = today.strftime('%Y-%m-%d')
        two_month_str = two_month.strftime('%Y-%m-%d')
        cme = mcal.get_calendar('CME')
        start_day = today_str
        end_day = two_month_str
        schedule = cme.schedule(start_date = start_day, end_date = end_day).reset_index().rename(index=str, columns={"index": "date"})
        third_friday = schedule[schedule['date'].apply(is_third_friday)].reset_index()
        current_options_friday = list(third_friday['date'])[0].to_pydatetime()
        next_options_friday = list(third_friday['date'])[1].to_pydatetime()

        self.is_trading_day = today in list(schedule['date'])

        trading_days_until_current_expir = list(third_friday['index'])[0]

        self.current_options_friday = current_options_friday
        self.next_options_friday = next_options_friday

        self.trading_days_until_current_expir = trading_days_until_current_expir



    def quote_symbol(self, symbol):
        endpoint = r"https://api.tdameritrade.com/v1/marketdata/"+ symbol + "/quotes"

        content = requests.get(url = endpoint, headers = self.headers)

        # convert it dictionary object
        data = content.json()

        # grab the account id
        #account_id = data[0]['securitiesAccount']['accountId']
        return data[symbol]

    def get_put_symbol(self, date, strike):
        return None
