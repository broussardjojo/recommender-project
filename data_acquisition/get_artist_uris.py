import spotipy
from aiohttp import ClientSession

import api_setup
import pathlib

env_vars = api_setup.parse_api_kvs("./../api-keys")
client_id = env_vars['client_id']
client_secret = env_vars['client_secret']


async def get_artist_top_tracks(session: ClientSession, artist_uri: str) -> dict:
    """
    Given an artist's URI, return their info.
    """
    uri = artist_uri.split(":")[-1]
    endpoint = f"https://api.spotify.com/v1/artists/{uri}/top-tracks"

    async with session.get(endpoint, data={"country": 'US'}) as response:
        print(response.request_info.headers)
        response = await(response.json())

    return response


def recursively_get_related_artists(track_uri, call_depth= 50, explored= set()):
    # TODO: Make async or multithread
    # Create a Spotify client
    env_vars = api_setup.parse_api_kvs(pathlib.Path.cwd().parent / "api-keys")
    auth_manager = spotipy.SpotifyClientCredentials(env_vars['client_id'], env_vars['client_secret'])
    sp = spotipy.Spotify(client_credentials_manager=auth_manager, backoff_factor=2)

    # Get the track information for the given URI
    track_info = sp.track(track_uri)

    # Get the artist ID from the track information
    artist_ids = {artist['id'] for artist in track_info['artists']}

    # Search through related artists in a random order
    frontier = artist_ids
    while frontier and len(explored) < call_depth:
        artist_id = frontier.pop()
        if artist_id not in explored:
            explored.add(artist_id)
            if len(explored) % 50 == 0:
                print(f"Explored {len(explored)} / {call_depth}")
            related_artists = sp.artist_related_artists(artist_id)
            frontier.update([artist['id'] for artist in related_artists['artists']])

    return explored, frontier

# Example usage
if __name__ == '__main__':
    track_uri = 'spotify:track:7yCPwWs66K8Ba5lFuU2bcx'
    token = 'BQArc8jEq5yWjuHeWpKdPIix0Lbm2OPq6U_mxnqh3V3QX3jRnaiQiCioaBGLFolXFv1dXJfZ5kvBABaB4KQNhYVdNxNI45whzJtvw32tvMxU9JdbETKn_EDv33YQK4UVY-zneAX13cSwGpLVGzAW2FMX0q6bXT5DKVJtLCRdCHMcdx2yuq8LdEUkFsAfacjNIVU'
    explored, frontier = recursively_get_related_artists(track_uri, 1500)
    seen = explored
    seen.update(frontier)
    seen = {uri + '\n' for uri in explored}
    with open("data/artists/artist_uris.txt", 'a') as f:
        f.writelines(seen)
