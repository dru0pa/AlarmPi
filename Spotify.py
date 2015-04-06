from __future__ import unicode_literals

import spotify
import logging
import threading
import platform
import Settings
import sys
import random

log = logging.getLogger('root')

log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)
#
# logging.basicConfig(level=logging.INFO)

class Spotify(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.end_of_track = threading.Event()
        self.logged_in = threading.Event()
        self.logged_out = threading.Event()
        self.logged_out.set()

        log.debug("Spawning spotify.Session()")
        self.session = spotify.Session()
        self.session.on(
            spotify.SessionEvent.CONNECTION_STATE_UPDATED,
            self.on_connection_state_changed)
        self.session.on(
            spotify.SessionEvent.END_OF_TRACK, self.on_end_of_track)

        myPlatform = platform.system()

        log.debug("Detecting platform")
        try:
            if myPlatform == 'Linux':
                log.info("{0} platform detected; using ALSA".format(myPlatform))
                self.audio_driver = spotify.AlsaSink(self.session)
            else:
                log.info("{0} platform detected; using PortAudio".format(myPlatform))
                self.audio_driver = spotify.PortAudioSink(self.session)
        except ImportError as e:
            log.warning('No audio sink found; audio playback unavailable. Exception: {0}'.format(e.args))

        # log.debug("spotify.Config()")
        # self.config = spotify.Config()
        # self.config.user_agent = 'Alarm Clock'
        # #self.settings = settings

        log.debug("Spotify event loop")
        self.event_loop = spotify.EventLoop(self.session)
        self.event_loop.start()

    def on_connection_state_changed(self, session):
        log.debug("on_connection_state_changed: ")
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            log.debug("LOGGED_IN")
            self.logged_in.set()
            self.logged_out.clear()
        elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
            log.debug("LOGGED_OUT")
            self.logged_in.clear()
            self.logged_out.set()

    def on_end_of_track(self, session):
        log.debug("on_end_of_track: ")
        #self.session.player.play(False)
        self.end_of_track.set()

    def login(self, username, password):
        log.debug("login")
        #username=self.settings.get("spotify_user"), password=self.settings.get("spotify_pass")
        self.session.login(username,password, remember_me=True)
        self.logged_in.wait()

    def relogin(self):
        log.debug("relogin")
        "relogin -- login as the previous logged in user"
        try:
            self.session.relogin()
            self.logged_in.wait()
        except spotify.Error as e:
            log.error(e)

    def forget_me(self):
        log.debug("forget_me")
        "forget_me -- forget the previous logged in user"
        self.session.forget_me()

    def logout(self):
        log.debug("logout")
        "logout"
        self.session.logout()
        self.logged_out.wait()

    def whoami(self):
        log.debug("whoami")
        "whoami"
        if self.logged_in.is_set():
            log.info(
                'I am %s aka %s. You can find me at %s',
                self.session.user.canonical_name,
                self.session.user.display_name,
                self.session.user.link)
        else:
            log.info(
                'I am not logged in, but I may be %s',
                self.session.remembered_user)

    def play_uri(self, line):
        log.debug("play_uri: {0}".format(line))
        "play <spotify track uri>"
        if not self.logged_in.is_set():
            log.warning('You must be logged in to play')
            return
        try:
            track = self.session.get_track(line)
            track.load()
        except (ValueError, spotify.Error) as e:
            log.warning(e)
            return
        log.info('Loading track into player')
        try:
            self.session.player.load(track)
        except spotify.error.LibError as e:
            log.error("Exception: {0}".format(e.args))
            return
        log.info('Playing track')
        self.session.player.play()

    def pause(self):
        log.info('Pausing track')
        self.session.player.play(False)

    def resume(self):
        log.info('Resuming track')
        self.session.player.play()

    def stop(self):
        log.info('Stopping track')
        self.session.player.play(False)
        self.session.player.unload()

    def seek(self, seconds):
        "seek <seconds>"
        if not self.logged_in.is_set():
            log.warning('You must be logged in to seek')
            return
        if self.session.player.state is spotify.PlayerState.UNLOADED:
            log.warning('A track must be loaded before seeking')
            return
        self.session.player.seek(int(seconds) * 1000)

    def search(self, query):
        "search <query>"
        if not self.logged_in.is_set():
            log.warning('You must be logged in to search')
            return
        try:
            result = self.session.search(query)
            result.load()
        except spotify.Error as e:
            log.warning(e)
            return
        log.info(
            '%d tracks, %d albums, %d artists, and %d playlists found.',
            result.track_total, result.album_total,
            result.artist_total, result.playlist_total)
        log.info('Top tracks:')
        for track in result.tracks:
            log.info(
                '[%s] %s - %s', track.link, track.artists[0].name, track.name)

    def get_playlists(self):
        log.debug("Number of playlists: {0}".format(len(self.session.playlist_container)))
        for playlist in self.session.playlist_container:
            try:
                playlist_uri = playlist.load()
                log.info("Name: {0} URI: {1}".format(playlist.name, playlist_uri))
            except AttributeError as e:
                log.info("Oops, encountered a folder of platlists.  Not sure howto handle, so moving on: {0}".format(e.args))

    def play_playlist(self, uri):
        log.debug("play_playlist: {0}".format(uri))
        playlist = self.session.get_playlist(uri)
        playlist.load()
        log.debug("{0} tracks loaded".format(len(playlist.tracks)))

        for i in sorted(range(1, len(playlist.tracks) + 1), key=lambda k: random.random()):
            log.info("Fetching {0} from playlist and sending to player".format(playlist.tracks[i].name))
            self.play_uri(str(playlist.tracks[i].link))
            while not self.end_of_track.wait(0.1):
                pass




if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    # settings = Settings.Settings()
    # settings.setup()
    mySpotify = Spotify()
    mySpotify.login("joel_roberts","p@ssw0rd")
    #mySpotify.get_playlists()
    mySpotify.play_playlist('spotify:user:spotify:playlist:0186RkeoJsHWEQy0ssDAus')
    #mySpotify.play_playlist('spotify:user:joel_roberts:playlist:1lDfZAjJG7TP5zNs0vNlL2')
    mySpotify.play_uri("spotify:track:14CsUVcoKztExH6aSgfrfb")
    mySpotify.logout()

    #Commander().cmdloop()