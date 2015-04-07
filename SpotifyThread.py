from __future__ import unicode_literals

import spotify
import logging
import threading
import platform
import Settings
import sys
import random
import time
import Spotify

log = logging.getLogger('root')

log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

logging.basicConfig(level=logging.INFO)

LOOP_TIME = float(0.1)

class SpotifyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopping = False
        self.spotify = Spotify.Spotify()

    def stop(self):
        self.stopping = True

    def run(self):
        while (not self.stopping):
            time.sleep(LOOP_TIME)

    def play(self):
        self.spotify.login("joel_roberts","p@ssw0rd")

        #self.spotify.get_playlists()
        self.spotify.play_playlist('spotify:user:spotify:playlist:0186RkeoJsHWEQy0ssDAus')

    def pause(self):
        self.spotify.pause()


if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    # settings = Settings.Settings()
    # settings.setup()
    #mySpotifySession = spotify.Session()
    mySpotify = SpotifyThread()
    mySpotify.start()
    #mySpotify.login("joel_roberts","p@ssw0rd")

    #mySpotify.get_playlists()
    #mySpotify.play_playlist('spotify:user:spotify:playlist:0186RkeoJsHWEQy0ssDAus')
    #mySpotify.join()

    #mySpotify.play_playlist('spotify:user:joel_roberts:playlist:1lDfZAjJG7TP5zNs0vNlL2')
    #mySpotify.play_uri("spotify:track:14CsUVcoKztExH6aSgfrfb")
    mySpotify.join()
    mySpotify.stop()

    #Commander().cmdloop()