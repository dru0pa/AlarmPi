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
#logging.basicConfig(level=logging.DEBUG)

LOOP_TIME = float(0.1)

class SpotifyThread(threading.Thread):
    def __init__(self, settings):
        log.debug("__init__")
        threading.Thread.__init__(self)
        self.stopping = False
        self.settings = settings
        self.spotify = Spotify.Spotify()
        self.spotify.login(settings.get("spotify_user"), settings.get("spotify_pass"))
        self.play_thread = None
        self.pause_thread = None
        self.resume_thread = None
        self.stop_thread = None

    def stop(self):
        log.debug("stop")
        #self.spotify.stop()
        self.stop_thread = threading.Thread(target=self.spotify.stop())
        self.stopping = True

    def run(self):
        log.debug("run loop")
        while (not self.stopping):
            time.sleep(LOOP_TIME)

    def play(self):
        log.debug("play")
        #self.spotify.get_playlists()
        self.spotify.play_playlist(self.settings.get("spotify_uri"))
        #self.play_thread = threading.Thread(target=self.spotify.play_playlist, args=self.settings.get("spotify_uri"))
        #log.debug(self.play_thread.is_alive())

    def resume(self):
        log.debug("resume")
        #self.spotify.resume()
        self.resume_thread = threading.Thread(target=self.spotify.resume())

    def pause(self):
        log.debug("pause")
        #self.spotify.pause()
        self.pause_thread = threading.Thread(target=self.spotify.pause())
    #
    # def get_playlists(self):
    #     self.spotify.get_playlists()


if __name__ == '__main__':

    import Settings

    settings = Settings.Settings()
    settings.setup()
    mySpotify = SpotifyThread(settings)
    mySpotify.start()
    mySpotify.play()
    time.sleep(20)
    mySpotify.pause()
    time.sleep(10)
    mySpotify.resume()
    time.sleep(10)
    mySpotify.stop()