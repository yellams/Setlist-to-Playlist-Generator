from gmusicapi import Mobileclient
from more_itertools import unique_everseen
import logging
import re


class GoogleMusicGenerator():
    def __init__(self, options, username, password):
        self.options = options
        self.username = username
        self.password = password
        self.playlist = None
        self.api = Mobileclient()
        self.logged_in = self.api.login(username, password, Mobileclient.FROM_MAC_ADDRESS)
        self.playlist_name = self.options['playlist_name']
        self.get_create_playlist()

    def get_status(self):
        if not self.logged_in:
            logging.error('Google music login failed :(')
            return('Failed', 'Login failed, run configurer.exe :(')
        return('Working', '')

    def get_create_playlist(self):
        existing_playlists = self.api.get_all_playlists()
        for playlist in existing_playlists:
            if playlist['name'].lower() == self.playlist_name.lower():
                self.playlist = playlist['id']
                self.new_playlist = False
                return
        self.playlist = self.api.create_playlist(self.playlist_name)
        self.new_playlist = True
        logging.info('Got a playlist!')

    def add_all(self, bands):
        for band in bands:
            try:
                artist_id = self.api.search(band, max_results=1)['artist_hits']['artistId']
            except:
                logging.info('Cannot find ' + band + ' on google music')
            try:
                tracks_to_add = []
                albums = self.api.get_artist_info(artist_id, include_albums=True, max_top_tracks=0, max_rel_artist=0)['albums']
                for album in albums:
                    if 'commentary' in album['name']:
                        continue
                    tracks = self.api.get_album_info(album['albumId'], include_tracks=True)['tracks']
                    for track in tracks:
                        tracks_to_add.append(track['trackId'])

            except:
                logging.info('Error finding albums for ' + band)
            self.add_track_ids(tracks_to_add)

    def add_set(self, songs_to_add):
        track_ids = []
        for song_dict in songs_to_add:
            search_query = song_dict['Title']

            search_query += ' ' + song_dict['Artist']
            if song_dict['Album']:
                search_query += ' ' + song_dict['Album']
            trackID = trackEPID = None
            try:
                results = self.api.search(search_query, max_results=5)['song_hits']
                for result in results:
                    title = song_dict['Title'].replace(',', '').split('(')[0]
                    if re.match(title, result['track']['title'], re.IGNORECASE) or re.match(song_dict['Title'], result['track']['title'], re.IGNORECASE):
                        if 'EP' in result['track']['album']:
                            trackEPID = result['track']['storeId']
                        else:
                            trackID = result['track']['storeId']
                            break
                if trackID:
                    track_ids.append(trackID)
                elif trackEPID:
                    track_ids.append(trackEPID)
            except:
                logging.info('Error on ' + song_dict['Title'] + ' by ' + song_dict['Artist'])
        self.add_track_ids(track_ids)

    def get_playlist_track_ids(self):
        results = self.api.get_all_user_playlist_contents()
        tracks = []
        for playlist in results:
            if playlist['id'] == self.playlist:
                for track in playlist['tracks']:
                    tracks.append(track['track']['storeId'])
        return tracks

    def add_track_ids(self, tracks):
        '''
        Add all trackIDs in tracks into a playlist, ensuring no duplicates with tracks already in the playlist.
        '''

        existing_tracks = self.get_playlist_track_ids()
        tracks_to_add = list(unique_everseen(tracks))
        tracks_to_add = [track for track in tracks_to_add if track not in existing_tracks]
        # split track ids into groups of 50

        added = len(existing_tracks)
        first_additional = True
        nr = 1
        for tracks_split in [tracks_to_add[i:i+50] for i in range(0, len(tracks_to_add), 50)]:
            added += 50
            self.api.add_songs_to_playlist(self.playlist, tracks_split)
            if added > 950:
                added = 0
                if first_additional:
                    self.api.edit_playlist(self.playlist, self.playlist_name + '-' + str(nr))
                    nr += 1
                    first_additional = False
                self.playlist = self.api.create_playlist(self.playlist_name + '-' + str(nr))
                nr += 1
