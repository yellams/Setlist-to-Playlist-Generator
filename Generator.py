import configparser
import requests
import re
import os
import mutagen
import shutil
import SpotifyGenerator
import GoogleMusicGenerator
import logging


class Generator():
    def __init__(self, items, options):
        logging.basicConfig(filename='log.txt', level=logging.INFO)
        logging.info('Generator starting')
        logging.getLogger('requests').setLevel(logging.WARNING)
        self.items = items
        self.options = options
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read('config.txt')
        self.songsToAdd = []
        self.runningDir = os.getcwd()
        self.playlistDir = self.config['Local']['playlist directory']
        self.logContents = []
        self.status = 'Working'
        self.message = ''
        self.spotifyGenerator = None
        self.googleGenerator = None

        # error returns when no items/options/config.

    def run(self):
        # Need to determine if self.items is band names or urls, easy check
        self.status, self.message = self.errorHandling()
        if self.status == 'Failed':
            return self.status, self.message
        if self.options['spotify']:
            spotify_username = self.config['Spotify']['Username']
            self.spotifyGenerator = SpotifyGenerator.SpotifyGenerator(self.options, spotify_username)
            self.status, self.message = self.spotifyGenerator.create_spotipy_instance()
            if self.status == 'Failed':
                return self.status, self.message
        if self.options['google_music']:
            google_username = self.config['Google Music']['Username']
            google_password = self.config['Google Music']['Password']
            self.googleGenerator = GoogleMusicGenerator.GoogleMusicGenerator(self.options, google_username, google_password)
            self.status, self.message = self.googleGenerator.get_status()
            if self.status == 'Failed':
                return self.status, self.message

        self.itemsAreBands = False if self.items[0].startswith('http://') else True

        if self.options['playlist_type'] == 2:
            if self.options['spotify']:
                self.spotifyGenerator.add_all(self.items)
            if self.options['google_music']:
                self.googleGenerator.add_all(self.items)
            if self.options['local']:
                for item in self.items:
                    self.generateAllSongs(item)
                self.writeM3U()

        else:
            for item in self.items:
                self.generateFromSetlist(item)
            if self.options['spotify']:
                self.spotifyGenerator.add_set(self.songsToAdd)
            if self.options['google_music']:
                self.googleGenerator.add_set(self.songsToAdd)
            if self.options['local']:
                self.findFiles()
                self.writeM3U()

        logging.info('Finished generating')
        self.status = 'Finished'
        return self.status, self.message

    def errorHandling(self):
        if not self.items:
            return 'Failed', 'No entries in the list'
        if not self.options['local'] and not self.options['google_music'] and not self.options['spotify']:
            return 'Failed', 'No playlist type selected'
        if self.options['local'] and not self.config['Local']['Music Directory']:
            return 'Failed', 'No local music directory'
        return 'Working', ''

    def generateAllSongs(self, item):
        self.addAll(item)

    def generateFromSetlist(self, item):
        if self.itemsAreBands:
            self.findSetlistAndAdd(item)
        else:
            self.addFromSetlistURL(item)

    def findSetlistAndAdd(self, band):
        # This will return a url with more than x songs
        # but then parsing it again to get songs..?
        search_url = 'http://www.setlist.fm/search?query=' + band.replace(' ', '+')
        specific = self.options['specific_set']
        if specific is not None and specific != 'Optional search phrase':
            search_url += '+'
            search_url += specific.replace(' ', '+')
        r = requests.get(search_url).text
        for row in r.split('\n'):
            if '<h2><a href=' in row:
                link_suffix = re.match(r'<h2><a href="(.*)" title', row).group(1)
                final_url = 'http://www.setlist.fm/' + link_suffix
                full_set = self.addFromSetlistURL(final_url, band)
                if full_set:
                    break

    def addFromSetlistURL(self, url, band=None):
        temporary_list_to_count = []
        r = requests.get(url).text

        for row in r.split('\n'):
            if not band:
                if 'meta name="keywords" content=' in row:
                    temp = row.split('=')[2]
                    temp = temp.split(',')[0]
                    band = temp[1:]
            if 'a class="songLabel' in row:
                temp = row.split('=')[3]
                temp = temp.split('"')[0]
                song_title = temp.replace('+', ' ')
                song_title = song_title.replace('%26', '&')
                song_title = song_title.replace('%27', '\'')
                song_title = song_title.replace('%28', '(')
                song_title = song_title.replace('%29', ')')
                song_dict = {}
                song_dict['Title'] = song_title
                song_dict['Album'] = None
                song_dict['Artist'] = band
                song_dict['Location'] = None

                temporary_list_to_count.append(song_dict)
        if len(temporary_list_to_count) < 7:
            return False
        else:
            self.songsToAdd.extend(temporary_list_to_count)
            return True

    def findFiles(self):
        music_dir = self.config['Local']['Music Directory']
        os.chdir(music_dir)

        for song_dict in self.songsToAdd:
            artist = song_dict['Artist']
            title = song_dict['Title']
            try:
                os.chdir(artist)
            except OSError:
                logging.info('No music by ' + artist)
                continue
            found = False
            for root, dirs, files in os.walk('.'):
                if found:
                    break
                for f in files:
                    if re.match('.*.(mp3|wma|mp4|flac|wav|wmp)$', f):
                        if re.search(title, f, re.IGNORECASE):
                            if 'TALB' in mutagen.File(os.path.join(root, f)).tags.keys():
                                song_dict['Album'] = mutagen.File(os.path.join(root, f)).tags['TALB'].text[0]
                            song_dict['Location'] = os.path.abspath(os.path.join(root, f))
                            found = True
                            break
            if not song_dict['Location']:
                logging.info('Could not find ' + title + ' by ' + artist + ' locally')
            os.chdir(music_dir)

    def addAll(self, artist):
        if self.itemsAreBands:
            music_dir = self.config['Local']['Music Directory']
            try:
                os.chdir(music_dir + '/' + artist)
                for root, dirs, files in os.walk('.'):
                    try:
                        for f in files:
                            song = {}
                            if re.match('.*.(mp3|wma|mp4|flac|wav|wmp)$', f):
                                song['Title'] = mutagen.File(os.path.join(root, f)).tags['TIT2'].text[0]
                                song['Album'] = mutagen.File(os.path.join(root, f)).tags['TALB'].text[0]
                                song['Artist'] = mutagen.File(os.path.join(root, f)).tags['TPE1'].text[0]
                                song['Location'] = os.path.abspath(os.path.join(root, f))
                                self.songsToAdd.append(song)
                    except KeyError:
                        logging.info(os.path.join(root, f) + ' tags are not present/readable')
            except OSError:
                logging.info('No music by ' + artist)
            os.chdir(music_dir)

    def writeM3U(self):
        os.chdir(self.playlistDir)
        songs_in_list = []
        if os.path.isfile(self.options['playlist_name'] + '.m3u'):
            with open(self.options['playlist_name'] + '.m3u', 'r') as read_file:
                for line in read_file:
                    songs_in_list.append(line.strip())

        with open(self.options['playlist_name'] + '.m3u', 'a+') as local_file:
            for song in self.songsToAdd:
                if song['Location'] and song['Location'] not in songs_in_list:
                    local_file.write(song['Location'])
                    local_file.write('\n')

    def copyFiles(self, destination):
        for song in self.songsToAdd:
            if song['Location']:
                shutil.copy(song['Location'], destination)
