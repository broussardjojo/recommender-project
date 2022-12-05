import asyncio
import pathlib
from typing import List, Optional
from urllib.parse import urlencode

import pandas as pd
import requests
import spotipy
import spotipy.oauth2
from aiohttp import ClientSession, ContentTypeError
import base64
import api_setup
import encoding
import webbrowser

env_vars = api_setup.parse_api_kvs("../api-keys")
EXPECTED_COLUMN_ORDER = ['track_id', 'artist_name', 'track_name', 'duration_ms', 'danceability', 'energy', 'key',
                         'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence',
                         'tempo', 'time_signature', 'genres', 'artist_popularity']
REPO_ROOT = pathlib.Path.cwd().parent


def auth_args():
    env_vars = api_setup.parse_api_kvs(REPO_ROOT / "api-keys")
    auth_manager = spotipy.SpotifyClientCredentials(env_vars['client_id'], env_vars['client_secret'])
    spotify = spotipy.Spotify(client_credentials_manager=auth_manager, backoff_factor=2)
    given_auth_args = [spotify, env_vars['client_id'], env_vars['client_secret']]
    return given_auth_args


def oauth_args(scope: List[str] = ['playlist-modify-public', 'playlist-modify-private']):
    env_vars = api_setup.parse_api_kvs(REPO_ROOT / "api-keys")
    oauth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=env_vars['client_id'],
        client_secret=env_vars['client_secret'],
        redirect_uri='https://localhost:8888/callback', scope=scope)
    return oauth_manager.get_access_token()


def get_header_with_oauth_token(token: str):
    return {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"
            }


def get_token(client_id: str, client_secret: str, redirect_uri: str, scope: List[str]):
    auth_endpoint = "https://accounts.spotify.com/authorize"
    auth_headers = {
        "response_type": "code",
        "client_id": client_id,
        "scope": " ".join(scope),
        "redirect_uri": redirect_uri
    }
    token = requests.get(auth_endpoint, headers=auth_headers)
    #webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))

    # message = base64.b64encode(f"{client_id}:{client_secret}".encode('ascii')).decode('ascii')
    # #token = requests.get(auth_endpoint,
    #                      data={
    #                          'grant_type': 'authorization_code',
    #                      },
    #                      headers={'message':message})
    return token


def get_songs_from_playlist(spotify_client: spotipy.Spotify, playlist_uri: str) -> List[str]:
    """
    Return a list of strings of the URIs of the tracks in this playlist.
    """
    tracks_json = spotify_client.playlist_items(playlist_uri)
    return [track['track']['uri'].split(":")[-1] for track in tracks_json['items']]


async def get_audio_features(session: ClientSession, track_uri: str) -> dict:
    """
    Return the audio features of the song with the given uri.
    """
    uri = track_uri.split(":")[-1]
    endpoint = f"https://api.spotify.com/v1/audio-features/{uri}"

    async with session.get(endpoint) as response:
        response = await(response.json())
    return response


async def get_artist(session: ClientSession, artist_uri: str) -> dict:
    """
    Given an artist's URI, return their info.
    """
    uri = artist_uri.split(":")[-1]
    endpoint = f"https://api.spotify.com/v1/artists/{uri}"

    async with session.get(endpoint) as response:
        response = await(response.json())

    return response

def sync_get_artist_from_track_uri(spotify: spotipy.Spotify, track_uri: str) -> dict:
    spotify.track
async def get_artist_from_track_uri(session: ClientSession, track_uri: str) -> dict:
    """
    Given a track URI, return its artist's name and their popularity.
    """
    uri = track_uri.split(":")[-1]
    endpoint = f"https://api.spotify.com/v1/tracks/{uri}"

    async with session.get(endpoint) as response:
        try:
            response_json = await(response.json(content_type=None))
            track_name = response_json['name']
            artist_uri = response_json['artists'][0]['uri']
            artist_info = await(get_artist(session, artist_uri))
            artist_name, artist_popularity, artist_genres = artist_info['name'], artist_info['popularity'], artist_info[
                'genres']
            return {'track_uri': uri, 'artist_name': artist_name, 'artist_popularity': artist_popularity,
                    'artist_genres': artist_genres, 'track_name': track_name}
        except ContentTypeError:
            print(response)


def get_header_with_token(client_id: str, client_secret: str):
    creds = f"{env_vars['client_id']}:{env_vars['client_secret']}"
    creds_b64 = base64.b64encode(creds.encode())
    headers = {"Authorization": f"Basic {creds_b64.decode()}"}
    data = {"grant_type": "client_credentials"}
    token = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    token = token.json()['access_token']
    return {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}


async def featurize_song_list(client_id: str, client_secret: str, song_uris: List[str]) -> List[dict]:
    # TODO: This can be chunked >.>
    # https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features
    request_headers = get_header_with_token(client_id, client_secret)
    async with ClientSession(headers=request_headers) as session:
        tasks = [asyncio.ensure_future(get_audio_features(session, uri)) for uri in song_uris]
        features = await(asyncio.gather(*tasks))
    return features


async def get_playlist_song_features(spotify_client: spotipy.Spotify, client_id: str, client_secret: str,
                                     playlist_uri: str) -> dict:
    song_uris = get_songs_from_playlist(spotify_client, playlist_uri)
    playlist_song_features = await(featurize_song_list(client_id, client_secret, song_uris))
    return playlist_song_features


async def dataframe_from_playlist(spotify_client: spotipy.Spotify, client_id: str, client_secret: str,
                                  playlist_uri: str) -> pd.DataFrame:
    # Get the song features and URIs from a playlist
    playlist_song_features = await(get_playlist_song_features(spotify_client, client_id, client_secret, playlist_uri))
    playlist_song_uris = [features['uri'] for features in playlist_song_features]
    # Get those songs' artists and their popularity
    async with ClientSession(headers=get_header_with_token(client_id, client_secret)) as session:
        tasks = [asyncio.ensure_future(get_artist_from_track_uri(session, uri)) for uri in playlist_song_uris]
        artist_info = await(asyncio.gather(*tasks))

    # Create the dataframe we expect >:(
    song_features_df = pd.DataFrame.from_records(playlist_song_features)
    track_uri_artist_popularity_df = pd.DataFrame.from_records(artist_info).set_index('track_uri')

    song_features_df = song_features_df.join(track_uri_artist_popularity_df, on='id')
    song_features_df = song_features_df.drop(columns=["type", "uri", "track_href", "analysis_url"])

    song_features_df = song_features_df.rename(mapper={"artist_genres": "genres", "id": "track_id"}, axis=1)

    song_features_df = song_features_df[EXPECTED_COLUMN_ORDER]

    return song_features_df


async def get_playlist_vector_from_uri(spotify_client: spotipy.Spotify, client_id: str, client_secret: str,
                                       playlist_uri: str, scalers_and_encoders: Optional[dict] = None) -> pd.DataFrame:
    playlist_features = await dataframe_from_playlist(spotify_client, client_id, client_secret, playlist_uri)
    if not scalers_and_encoders:
        scalers_and_encoders = encoding.fit_scalers_and_encoders(playlist_features)
    playlist_features = encoding.encode_dataframe_given_scalers(playlist_features, scalers_and_encoders)

    # For now, we don't care about genre - this may change in the future
    playlist_features = playlist_features.drop(columns=[*encoding.UNUSED_COLUMNS, 'track_id'])
    playlist_feature_vector = playlist_features.sum(axis=0, numeric_only=False)
    return playlist_feature_vector


if __name__ == '__main__':
    print(get_token(env_vars['client_id'], env_vars['client_secret'], env_vars['redirect_uri'], ['playlist-modify-public', 'playlist-modify-private']).content)
