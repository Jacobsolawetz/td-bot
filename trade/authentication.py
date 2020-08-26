import os
import requests

def refresh_auth():
    # THE AUTHENTICATION ENDPOINT

    # define the endpoint
    url = r"https://api.tdameritrade.com/v1/oauth2/token"

    # define the headers
    headers = {"Content-Type":"application/x-www-form-urlencoded"}

    # define the payload
    payload = {'grant_type': 'refresh_token',
               'refresh_token': os.environ['REFRESH_TOKEN'],
               'client_id': os.environ['CLIENT_ID'] }

    # post the data to get the token
    authReply = requests.post(r'https://api.tdameritrade.com/v1/oauth2/token', data=payload)

    # convert it to a dictionary
    decoded_content = authReply.json()

    access_token = decoded_content['access_token']
    headers = {'Authorization': "Bearer {}".format(access_token)}
    return headers
