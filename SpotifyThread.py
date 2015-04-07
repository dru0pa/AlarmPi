from __future__ import unicode_literals

import logging
import threading
import time
import Spotify

log = logging.getLogger('root')
#
# log.setLevel(logging.DEBUG)
#
# stream = logging.StreamHandler(sys.stdout)
# stream.setLevel(logging.DEBUG)
#
# formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
# stream.setFormatter(formatter)
#
# log.addHandler(stream)
#
#logging.basicConfig(level=logging.INFO)

LOOP_TIME = float(0.1)

class SpotifyThread(threading.Thread):
    def __init__(self, settings):
        threading.Thread.__init__(self)
        self.stopping = False
        self.settings = settings
        self.spotify = Spotify.Spotify()
        self.spotify.login(settings.get("spotify_user"), settings.get("spotify_pass"))

    def stop(self):
        self.spotify.stop()
        self.stopping = True

    def run(self):

        while (not self.stopping):
            time.sleep(LOOP_TIME)

    def play(self):

        #self.spotify.get_playlists()
        self.spotify.play_playlist(self.settings.get("spotify_uri"))

    # def pause(self):
    #     self.spotify.pause()
    #
    # def get_playlists(self):
    #     self.spotify.get_playlists()


if __name__ == '__main__':

    mySpotify = SpotifyThread()
    mySpotify.start()
    mySpotify.play()
    mySpotify.stop()