import spotipy
from concurrent import futures
import api_setup
import pathlib

def get_artist_top_track_uris(spotify_client: spotipy.Spotify, artist_uri: str):
    top_tracks_json = spotify_client.artist_top_tracks(artist_uri)
    print([track['id'] for track in top_tracks_json['tracks']])
    return [track['id'] for track in top_tracks_json['tracks']]

if __name__ == '__main__':
    env_vars = api_setup.parse_api_kvs(pathlib.Path.cwd().parent / "api-keys")
    auth_manager = spotipy.SpotifyClientCredentials(env_vars['client_id'], env_vars['client_secret'])
    sp = spotipy.Spotify(client_credentials_manager=auth_manager, backoff_factor=2, retries=1)

    print("Reading data...")
    with open("./data/artists/artist_uris.txt", "r") as artist_data:
        artist_uris = [uri.strip() for uri in artist_data.readlines()]

    print("Beginning requests...")
    track_ids = []
    for uri in artist_uris:
        track_ids.extend(get_artist_top_track_uris(sp, uri))
    # with futures.ThreadPoolExecutor(max_workers=16) as executor:
    #     for result in executor.map(get_artist_top_track_uris, [sp]*len(artist_uris), artist_uris):
    #         print(result)
    #         track_ids.extend(result)

    with open("./data/tracks/track_uris.txt", "a") as track_data:
        track_data.writelines([uri + '\n' for uri in track_ids])
