import spotipy
import spotipy.util as util
from more_itertools import unique_everseen
import re
import logging


class SpotifyGenerator():
    def __init__(self, options, username):
        self.options = options
        self.spotify_instance = None
        self.username = username
        self.playlist = None

    def create_spotipy_instance(self):
        scope = 'playlist-read-private playlist-modify-public playlist-modify-private'
        self.token = util.prompt_for_user_token(self.username, scope, '892896528c1c4849bab75b493377d83e',
                                                '287db3f1e9c64d6aa8de0724a3b09573', 'https://example.com/callback/')
        if not self.token:
            return('Failed', 'Login failed, run configurer.exe :(')
        self.spotify_instance = spotipy.Spotify(auth=self.token)
        self.get_create_playlist(self.options['playlist_name'])
        return('Working', '')

    def get_create_playlist(self, playlist_name):
        existing_playlists = self.spotify_instance.user_playlists(self.username)
        for playlist in existing_playlists['items']:
            if playlist['name'].lower() == playlist_name.lower():
                self.playlist = playlist
                return
        self.playlist = self.spotify_instance.user_playlist_create(self.username, playlist_name)

    def add_all(self, bands):
        for band in bands:
            try:
                artist_id = self.spotify_instance.search(q='artist:' + band, type='artist')['artists']['items'][0]['id']
            except:
                logging.info('Cannot find ' + band + ' on spotify')
            try:

                results = self.spotify_instance.artist_albums(artist_id, album_type='album', country='US')
                albums = results['items']
                while results['next']:
                    results = self.spotify_instance.next(results)
                    albums.extend(results['items'])

                unique_albums = []
                unique_album_names = []
                for album in albums:
                    album_name = album['name']
                    if 'edited' in album_name.lower():
                        continue
                    if album_name not in unique_album_names:
                        if 'deluxe' not in album_name.lower():
                            skip = False
                            for alb in albums:
                                if re.search(album_name + '.*(Deluxe|Explicit)', alb['name']):
                                    skip = True
                                    break
                            if skip:
                                continue
                    else:
                        continue
                    unique_albums.append(album)
                    unique_album_names.append(album_name)

            except:
                logging.info('Error finding albums for ' + band)
            tracks_to_add = []
            for album in unique_albums:
                album_id = album['id']
                tracks = self.spotify_instance.album_tracks(album_id)['items']
                for track in tracks:
                    tracks_to_add.append(track['id'])

            self.add_track_ids(tracks_to_add)

    def add_set(self, songs_to_add):
        track_ids = []
        for song_dict in songs_to_add:
            search_query = 'track:' + song_dict['Title']

            search_query += ' AND artist:' + song_dict['Artist']
            if song_dict['Album']:
                search_query += ' AND album:' + song_dict['Album']
            trackID = None
            try:
                results = self.spotify_instance.search(q=search_query, type='track', limit=5)['tracks']['items']
                for result in results:
                    title = song_dict['Title'].replace(',', '').split('(')[0]
                    if re.match(title, result['name'], re.IGNORECASE) or re.match(song_dict['Title'], result['name'], re.IGNORECASE):
                        trackID = result['id']
                        track_ids.append(trackID)
                        break
            except:
                logging.info('Error on ' + song_dict['Title'] + ' by ' + song_dict['Artist'])
        self.add_track_ids(track_ids)

    def get_playlist_track_ids(self):
        results = self.spotify_instance.user_playlist_tracks(self.username, self.playlist['id'])
        tracks = results['items']
        while results['next']:
            results = self.spotify_instance.next(results)
            tracks.extend(results['items'])
        track_ids = [track['track']['id'] for track in tracks]
        return track_ids

    def add_track_ids(self, tracks):
        '''
        Add all trackIDs in tracks into a playlist, ensuring no duplicates with tracks already in the playlist.
        '''
        existing_tracks = self.get_playlist_track_ids()
        tracks_to_add = list(unique_everseen(tracks))
        tracks_to_add = [track for track in tracks_to_add if track not in existing_tracks]
        # split track ids into groups of 50
        for tracks_split in [tracks_to_add[i:i+50] for i in range(0, len(tracks_to_add), 50)]:
            self.spotify_instance.user_playlist_add_tracks(self.username, self.playlist['id'], tracks_split)
