import time

import requests
from urllib.parse import urlencode
import api_setup

ENV_VARS = api_setup.parse_api_kvs("./../api-keys")

# Replace these with your own client ID and secret
client_id = ENV_VARS['client_id']
client_secret = ENV_VARS['client_secret']

# Replace this with the redirect URI you registered with Spotify
redirect_uri = ENV_VARS['redirect_uri']

# Set up the parameters for the authorization request
params = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "scope": "playlist-modify-public",  # Request permission to edit playlists
}

# Generate the authorization URL by encoding the parameters
auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)

# Send the user to the authorization URL
print("Go to the following URL in your browser:")
print(auth_url)

# Once the user has granted your app access to their Spotify account,
# they will be redirected to the redirect URI you specified, with
# an authorization code included as a query parameter
# (e.g. http://localhost:8000/callback?code=AQDs...
time.sleep(15)
# Use the requests library to extract the authorization code from the URL
response = requests.get(redirect_uri)
auth_code = response.url.split("=")[1]

# The authorization code is now stored in the "auth_code" variable
# You can use it to get an authorization token (as shown in the previous answer)