import asyncio
import base64
import json
from typing import List

import requests
import spotipy
from aiohttp import ClientSession
import api_setup

env_vars = api_setup.parse_api_kvs("../api-keys")

def get_header_with_token(client_id: str, client_secret: str):
    creds = f"{env_vars['client_id']}:{env_vars['client_secret']}"
    creds_b64 = base64.b64encode(creds.encode())
    headers= {"Authorization": f"Basic {creds_b64.decode()}"}
    data= {"grant_type": "client_credentials"}
    token = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    token = token.json()['access_token']
    return {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}

async def get_audio_features(session: ClientSession, track_uris: str) -> dict:
    """
    Return the audio features of the song with the given uri.
    """
    sublist = [uri.split(":")[-1] for uri in track_uris]
    endpoint = f"https://api.spotify.com/v1/audio-features/"

    async with session.request("get", endpoint, data={'ids': ",".join(sublist)}) as response:
        response = await(response.json())
    return response


async def featurize_song_list(client_id:str, client_secret: str, song_uris: List[List[str]]) -> List[dict]:
    # TODO: This can be chunked >.>
    # https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features
    request_headers = get_header_with_token(client_id, client_secret)
    async with ClientSession(headers=request_headers) as session:
        tasks = [asyncio.ensure_future(get_audio_features(session, uri)) for uri in song_uris]
        features = await(asyncio.gather(*tasks))
    return features

def split_into_sublists(input_list, chunk_size=50):
    upto = 0
    output_lists = []
    while True:
        if upto + chunk_size >= len(input_list):
            output_lists.append(input_list[upto:-1])
            break
        else:
            output_lists.append(input_list[upto:upto+chunk_size])
            upto += chunk_size
    return output_lists


if __name__ == '__main__':
    print("Reading data...")
    with open("./data/tracks/track_uris.txt", "r") as artist_data:
        track_uris = [uri.strip() for uri in artist_data.readlines()]

    env_vars = api_setup.parse_api_kvs("./../api-keys")
    auth_manager = spotipy.SpotifyClientCredentials(env_vars['client_id'], env_vars['client_secret'])
    sp = spotipy.Spotify(client_credentials_manager=auth_manager, backoff_factor=2)

    #track_uris = track_uris[:300] # Don't do the whole thing at once
    track_uris_sublist = split_into_sublists(track_uris, 100)

    data_file_path = "./data/tracks/track_features.txt"
    for sublist in track_uris_sublist:
        results = sp.audio_features(sublist)
        with open(data_file_path, "a") as f:
            json.dump(results, f)