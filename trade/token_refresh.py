import os
import requests

#access token is also a refresh token valid for 90 days
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

#API Endpoints

#More endpoints https://developer.tdameritrade.com/account-access/apis

# define an endpoint with a stock of your choice, MUST BE UPPER
endpoint = r"https://api.tdameritrade.com/v1/accounts"


#payload = {'fields':'positions'}
# make a request
content = requests.get(url = endpoint, headers = headers)

# convert it dictionary object
data = content.json()

# grab the account id
liquidation_value = data[0]['securitiesAccount']['currentBalances']['liquidationValue']

print(liquidation_value)
