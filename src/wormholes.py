import cmd
import yaml
import spotipy
import uuid
import requests
import time
import spotipy.util as util

from random import randint
from spotipy.oauth2 import SpotifyOauthError

global CONFIG


class User(object):

    def __init__(self, spotify_conn):
        self.spotify = spotify_conn
        user_info = self.spotify.current_user()
        self.id = user_info['id']
        self.name = user_info['display_name']


class Wormholes(cmd.Cmd):
    """
Welcome to Spotify-Wormholes!		 
-----------------------------

I specialise in creating "Wormhole" playlists.
Give me one of your favourite artists to start
and I will come back with a lengthy playist of 
unique tracks from recursively chosen related 
artists.

Type help or ? to list commands.
    """

    def __init__(self, user=None):
        cmd.Cmd.__init__(self)
        self.set_prompt()
        self._user = user

    def set_prompt(self, user=None):
        if user is None:
            self.prompt = 'Wormholes: '
        else:
            self.prompt = 'Wormholes(%s): ' % user

    def do_login(self, line=''):
        """
Initiates mandatory oauth2 login process for
Spotify-Wormholes.
        """

        credentials = CONFIG['CREDENTIALS']
        token = util.prompt_for_user_token(
            uuid.uuid4().hex[:7],
            credentials['SCOPE'],
            credentials['CLIENT_ID'],
            credentials['CLIENT_SECRET'],
            credentials['REDIRECT_URL']
        )
        try:
            spotify_conn = spotipy.Spotify(auth=token)
            self._user = User(spotify_conn)
            self.set_prompt(self._user.name)
        except SpotifyOauthError:
            print "Botched login!"

    def do_create(self, origin_artist):
        """
Creates a wormhole playlist given an origin
artist name.

Example: create "R Kelly"
        """

        if self._user is None:
            print('\nNot logged in, try "help" for more info.\n')
            return

        worm_name = 'Wormhole - %s' % origin_artist
        worm_tracklist = []
        worm_artistlist = []
        depth = CONFIG['WORM_DEPTH']
        rand_artist_coef = CONFIG['RANDOM_COEFFICIENTS']['ARTIST']

        worm_artist_id = self.get_artist_id(origin_artist)
        worm_artistlist.append(worm_artist_id)

        for i in xrange(depth):
            self.select_worm_track(worm_artist_id, worm_tracklist)
            related_artists = self.get_related_artists(worm_artist_id)

            while worm_artist_id in worm_artistlist:
                worm_artist_id = self.random_select(
                    related_artists, rand_artist_coef)

            worm_artistlist.append(worm_artist_id)

        wormhole = self.create_wormhole_playlist(
            worm_name, worm_tracklist)

        print '\nCreated "%s"\n' % worm_name

    def do_exit(self, line):
        """
Closes Spotify-Wormholes.
        """
        return True

    def create_wormhole_playlist(self, worm_name, worm_tracklist):
        wormhole = self._user.spotify.user_playlist_create(
            self._user.id, worm_name)
        wormhole_id = wormhole['id']

        self._user.spotify.user_playlist_add_tracks(
            self._user.id, wormhole_id, worm_tracklist)

        return wormhole

    def get_artist_id(self, artist):
        results = self._user.spotify.search(
            q='artist:' + artist, type='artist'
        )
        artist = results['artists']['items'][0]
        artist_id = artist['id']

        return artist_id

    def get_related_artists(self, artist_id):
        results = self._user.spotify.artist_related_artists(artist_id)
        related_artists = [
            artist['id'] for artist in results['artists']
        ]

        return related_artists

    def get_top_tracks(self, artist_id):
        results = self._user.spotify.artist_top_tracks(
            artist_id,  country='US')
        top_tracks = [
            track['id'] for track in results['tracks']
        ]

        return top_tracks

    def select_worm_track(self, worm_artist_id, worm_tracklist):
        rand_track_coef = CONFIG['RANDOM_COEFFICIENTS']['TRACK']

        worm_artist_tracks = self.get_top_tracks(worm_artist_id)
        worm_track = self.random_select(
            worm_artist_tracks,
            rand_track_coef
        )
        worm_tracklist.append(worm_track)

    def random_select(self, collection, coefficient):
        if len(collection) < coefficient:
            return collection[randint(0, len(collection) - 1)]
        else:
            return collection[randint(0, coefficient - 1)]


if __name__ == '__main__':
    CONFIG = yaml.load(open('conf/credentials.yaml'))
    Wormholes().cmdloop(intro=Wormholes.__doc__)
