import asyncio
import json
from typing import List
import spotipy
import spotipy.util

import api_setup
import featurizing
from aiohttp import ClientSession
from pprint import PrettyPrinter

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


async def create_playlist(oauth_token: str, playlist_name: str, track_uris: List[str], playlist_description: str = "A robot made this :)",
                          public: bool = True, collaborative: bool = False):
    """
    Creates a playlist with the given name and adds the tracks with given URIs to it.

    :param playlist_name: The name of the playlist to create.
    :param track_uris: The tracks to add to the playlist.
    :param playlist_description: Optional description of the playlist.
    :param public: Whether the playlist is public or not; defaults to True.
    :param collaborative: Whether the playlist is collaborative or not; defaults to False.
    :return:
    """
    headers = featurizing.get_header_with_oauth_token(oauth_token)
    pp = PrettyPrinter()

    track_uris_as_sublists = split_into_sublists(track_uris)

    async with ClientSession(headers=headers) as session:
        # Get current user ID
        get_current_user_endpoint = 'https://api.spotify.com/v1/me'
        async with session.get(get_current_user_endpoint) as response:
            user_id = await response.read()
            user_id = user_id.decode()
            user_id = json.loads(user_id, strict=False)
        user_id = user_id['id']

        # Create playlist
        create_playlist_endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        create_playlist_data = {
            'name': playlist_name,
            'description': playlist_description,
            'public': public,
            'collaborative': collaborative
        }
        async with session.post(create_playlist_endpoint, json=create_playlist_data) as response:
            playlist_id = await response.read()
            playlist_id = playlist_id.decode()
            playlist_id = json.loads(playlist_id, strict=False)
        playlist_id = playlist_id['id']

        # Add tracks to playlist
        add_songs_to_playlist_endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        resp = await session.post(add_songs_to_playlist_endpoint, json={'uris': ['spotify:track:' + uri for uri in track_uris_as_sublists[0]]})
        pp.pprint(resp)

