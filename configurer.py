import re
import configparser
import spotipy.util as util
import os

music_dir = ''
spotify_user = ''
gpm_user = ''
gpm_pw = ''

config = configparser.ConfigParser()

print('This script only needs to be run once, before your first run of the program')
print('It will generate config.txt in this directory, a file required to run the PlaylistGenerator')
print('This script will remove any config.txt in this directory, resetting all options before asking for new input')
input('Press Enter to continue...')

if os.path.isfile('config.txt'):
    os.remove('config.txt')

resp = input('Do you want to make m3u playlists from a local music directory? [Y/N]: ')
if re.match('[Yy]', resp):
    music_dir = input('Type the directory of your local music directory: ')
    playlist_dir = input('Type the directory to store your playlist m3u files: ')

resp = input('Do you want to make spotify playlists? [Y/N]: ')
if re.match('[Yy]', resp):
    spotify_user = input('Type your spotify username: ')
    print('A browser will launch a tab, allow the app access and copy the return url here')
    scope = 'playlist-read-private playlist-modify-public playlist-modify-private'
    util.prompt_for_user_token(spotify_user, scope, '892896528c1c4849bab75b493377d83e',
                               '287db3f1e9c64d6aa8de0724a3b09573', 'https://example.com/callback/')

resp = input('Do you want to make google music playlists? [Y/N]: ')
if re.match('[Yy]', resp):
    gpm_user = input('Type your google music username (email): ')
    print('app-specific password suggested! google api has no authentication like spotify, '
          'so the app-specific password is stored in the config file')
    gpm_pw = input('Type your google app-specific password: ')

config['Local'] = {'Music Directory': music_dir, 'Playlist Directory': playlist_dir}
config['Spotify'] = {'Username': spotify_user}
config['Google Music'] = {'Username': gpm_user, 'Password': gpm_pw}

with open('config.txt', 'w') as configfile:
    config.write(configfile)
