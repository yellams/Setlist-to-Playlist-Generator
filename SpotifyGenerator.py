import spotipy
import spotipy.util as util
import operator
from more_itertools import unique_everseen


class SpotifyGenerator():
    def __init__(self, options, username):
        self.options = options
        self.spotify_instance = None
        self.username = username
        self.playlist = None

    def create_spotipy_instance(self):
        scope = 'playlist-read-private playlist-modify-public playlist-modify-private'
        # TODO modifiy this function with a tkinter pop up window. want this to all be runnable with no console.
        self.token = util.prompt_for_user_token(self.username, scope, '892896528c1c4849bab75b493377d83e',
                                                '287db3f1e9c64d6aa8de0724a3b09573', 'https://example.com/callback/')
        if not self.token:
            return('Failed', 'Login failed :(')
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
                print('Cannot find ' + band + ' on spotify')
            try:

                results = self.spotify_instance.artist_albums(artist_id, album_type='album', country='US')
                albums = results['items']
                while results['next']:
                    results = self.spotify_instance.next(results)
                    albums.extend(results['items'])
                unique_albums = []
                # Preference for deluxe...?
                # track ids might be the same anyway?
                # look at eminem relapse versions.
                for album in albums:
                    if not album['name'] in map(operator.itemgetter('name'), unique_albums):
                        unique_albums.append(album)

            except:
                print('Error finding albums for ' + band)
            for album in unique_albums:
                get_all_songs

        pass
        # For each band in list of bands get all albums and add songs to playlist called options['playlist_name']

    def add_set(self, songs_to_add):
        track_ids = []
        for song_dict in songs_to_add:
            search_query = 'track:' + song_dict['Title']
            print(song_dict['Title'])

            search_query += ' AND artist:' + song_dict['Artist']
            if song_dict['Album']:
                search_query += ' AND album:' + song_dict['Album']
                # TODO musicbrainz lookup?
            try:
                # TODO if return more than 1 => multiple albums with song. musicbrainz api get first release - use as album param
                trackID = self.spotify_instance.search(q=search_query, type='track', limit=1)['tracks']['items'][0]['id']
            except:
                print('Error on ' + song_dict['Title'] + ' by ' + song_dict['Artist'])
            if trackID:
                track_ids.append(trackID)
        # get track ids already in playlist
        existing_tracks = self.get_playlist_track_ids()
        # Just in case, check against itself for duplicates
        tracks_to_add = list(unique_everseen(track_ids))

        # remove any tracks from track_ids if they exist in existing_tracks (i.e. adding to a playlist)
        tracks_to_add = [track for track in tracks_to_add if track not in existing_tracks]
        # split track ids into groups of 50
        for track_ids_split in [tracks_to_add[i:i+50] for i in range(0, len(tracks_to_add), 50)]:
            self.spotify_instance.user_playlist_add_tracks(self.username, self.playlist['id'], track_ids_split)

    def get_playlist_track_ids(self):
        results = self.spotify_instance.user_playlist_tracks(self.username, self.playlist['id'])
        tracks = results['items']
        while results['next']:
            results = self.spotify_instance.next(results)
            tracks.extend(results['items'])
        track_ids = [track['track']['id'] for track in tracks]
        return track_ids
