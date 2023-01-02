import streamlit as st
import json
import pandas as pd

STRATEGY_DIR = "./"


def app():
    st.title("Short Volatility Theta Decayer")
    
    st.write("This strategy is based on the studies contained in: https://github.com/Jacobsolawetz/options_backtester")
    
    #read bot status from bot_status.txt
    with open(STRATEGY_DIR + "bot_status.txt", "r") as f:
        status = f.read()
        
    st.write("Bot Status: " + status)
    
    stats = pd.read_csv(STRATEGY_DIR + "stats.csv")
    stats = stats.rename(columns={'trading_day':'index'}).set_index('index')
    
    previous_day_pnl = stats["pnl"].iloc[-1]
    previous_day_portfolio_value = stats["portfolio_value"].iloc[-1]
    
    st.write("Previous Day PNL: " + str(previous_day_pnl))
    st.write("Portfolio Value: " + str(previous_day_portfolio_value))
    
    st.bar_chart(stats["pnl"])
    st.bar_chart(stats["portfolio_value"])
    #st.bar_chart(stats["portfolio_value"].pct_change())
    st.bar_chart(stats["spy"])
    st.bar_chart(stats["vix"])
    
    #date.today().strftime("%b-%d-%Y")
    
    st.subheader("Tune Strategy Parameters")
    st.write("Strategy will be rebalanced piecemeal, daily, according to desired parameters.")
    with st.form("my_form"):
        
        #read strategy parameters from json file
        
        with open(STRATEGY_DIR + "strategy_params.json", "r") as f:
            strat_params = json.load(f)
            max_loss_val = strat_params["max_loss"]
            num_scores_out_val = strat_params["num_scores_out"]
            put_spread_distance_val = strat_params["put_spread_distance"]
        
        #max loss param
        st.write("The maximum monthly loss you are willing to accept on the portfolio")
        max_loss_val = st.slider("Max Loss", min_value=0.0, max_value=1.0, value=float(max_loss_val))
        
        #num scores out param
        st.write("The number of standard deviations from the SPY mean to sell PUT options")
        num_scores_out_val = st.slider("Num Scores Out", min_value=0.0, max_value=3.0, value=float(num_scores_out_val))
        
        st.write("The wideness of the put spread")
        put_spread_distance_val = st.slider("Put Spread Distance", min_value=0.0, max_value=20.0, value=put_spread_distance_val, step=1.0)
        
        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write("Set strategy parameters: max_loss: ", max_loss_val, " num_scores_out: ", num_scores_out_val, " put_spread_distance: ", put_spread_distance_val)
            
            #write parameters to json file in STRATEGY_DIR
            #the cron job will read this file and update the strategy
            strat_params = {"max_loss": max_loss_val, "num_scores_out": num_scores_out_val, "put_spread_distance": put_spread_distance_val}
            with open(STRATEGY_DIR + "strategy_params.json", "w") as f:
                json.dump(strat_params, f)
                


app()
