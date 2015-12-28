import cmd
import yaml
import spotipy
import uuid
import requests
import spotipy.util as util

from random import randint
from spotipy.oauth2 import SpotifyOauthError

global CONFIG


class User(object):

    def __init__(self, spotify_conn):
        user_info = spotify_conn.current_user()
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

    def __init__(self, spotify_conn=None):
        cmd.Cmd.__init__(self)
        if spotify_conn:
            self.sp = spotify_conn
            self.user = User(self.sp)
        else:
            self.sp = None
            self.user = None
        self.set_prompt()
        
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
            self.sp = spotify_conn
            self.user = User(self.sp)
            self.set_prompt(self.user.name)
        except SpotifyOauthError:
            print "Botched login!"

    def do_create(self, origin_artist):
        """
Creates a wormhole playlist given an origin
artist name.

Example: create "R Kelly"
        """

        if self.user is None:
            print('\nNot logged in, try "help" for more info.\n')
            return

        worm_name = 'Wormhole - %s' % origin_artist
        worm_tracklist = []
        worm_artistlist = []
        depth = CONFIG['WORM_DEPTH']

        worm_artist_id = self.get_artist_id(origin_artist)
        worm_artistlist.append(worm_artist_id)

        for i in xrange(depth):
            worm_track = self.get_worm_track(worm_artist_id)
            worm_tracklist.append(worm_track)
            worm_artist_id = self.get_worm_artist(
                worm_artist_id, worm_artistlist)

        wormhole = self.create_wormhole_playlist(
            worm_name, worm_tracklist)

        print '\nCreated "%s"\n' % worm_name

    def do_exit(self, line):
        """
Closes Spotify-Wormholes.
        """
        return True

    def create_wormhole_playlist(self, worm_name, worm_tracklist):
        wormhole = self.sp.user_playlist_create(
            self.user.id, worm_name)
        wormhole_id = wormhole['id']

        self.sp.user_playlist_add_tracks(
            self.user.id, wormhole_id, worm_tracklist)

        return wormhole

    def get_artist_id(self, artist):
        results = self.sp.search(
            q='artist:' + artist, type='artist'
        )
        artist = results['artists']['items'][0]
        artist_id = artist['id']

        return artist_id

    def get_related_artists(self, artist_id):
        results = self.sp.artist_related_artists(artist_id)
        related_artists = [
            artist['id'] for artist in results['artists']
        ]

        return related_artists

    def get_top_tracks(self, artist_id):
        results = self.sp.artist_top_tracks(
            artist_id,  country='US')
        top_tracks = [
            track['id'] for track in results['tracks']
        ]

        return top_tracks

    def get_worm_track(self, worm_artist_id):
        rand_track_coef = CONFIG['RANDOM_COEFFICIENTS']['TRACK']

        worm_artist_tracks = self.get_top_tracks(worm_artist_id)
        worm_track = self.random_select(
            worm_artist_tracks,
            rand_track_coef
        )

        return worm_track

    def get_worm_artist(self, worm_artist_id, worm_artistlist):
        rand_artist_coef = CONFIG['RANDOM_COEFFICIENTS']['ARTIST']
        related_artists = self.get_related_artists(worm_artist_id)

        while worm_artist_id in worm_artistlist:
            try:
                related_artists.remove(worm_artist_id)
            except ValueError:
                pass
            worm_artist_id = self.random_select(
                related_artists, rand_artist_coef)

        worm_artistlist.append(worm_artist_id)

        return worm_artist_id

    def random_select(self, collection, coefficient):
        if len(collection) < coefficient:
            return collection[randint(0, len(collection) - 1)]
        else:
            return collection[randint(0, coefficient - 1)]


if __name__ == '__main__':
    CONFIG = yaml.load(open('conf/credentials.yaml'))
    Wormholes().cmdloop(intro=Wormholes.__doc__)
