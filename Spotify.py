from __future__ import unicode_literals

import spotify
import logging
import threading
import platform
import Settings

log = logging.getLogger('root')

class Spotify:

    def __init__(self, settings):

        self.logged_in = threading.Event()
        self.logged_out = threading.Event()
        self.logged_out.set()

        self.session = spotify.Session()
        self.session.on(
            spotify.SessionEvent.CONNECTION_STATE_UPDATED,
            self.on_connection_state_changed)
        self.session.on(
            spotify.SessionEvent.END_OF_TRACK, self.on_end_of_track)

        try:
            if platform.system() == 'Linux':
                self.audio_driver = spotify.AlsaSink(self.session)
            else:
                self.audio_driver = spotify.PortAudioSink(self.session)
        except ImportError:
            log.warning(
                'No audio sink found; audio playback unavailable.')

        self.config = spotify.Config()
        self.config.user_agent = 'Alarm Clock'
        self.settings = settings

    def on_connection_state_changed(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in.set()
            self.logged_out.clear()
        elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
            self.logged_in.clear()
            self.logged_out.set()

    def on_end_of_track(self, session):
        self.session.player.play(False)

    def login(self):
        self.session.login(self.settings.get("spotify_user"), self.settings.get("spotify_pass"), remember_me=True)
        self.logged_in.wait()

    def relogin(self, line):
        "relogin -- login as the previous logged in user"
        try:
            self.session.relogin()
            self.logged_in.wait()
        except spotify.Error as e:
            log.error(e)

    def forget_me(self, line):
        "forget_me -- forget the previous logged in user"
        self.session.forget_me()

    def logout(self, line):
        "logout"
        self.session.logout()
        self.logged_out.wait()

    def whoami(self, line):
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
        self.session.player.load(track)
        log.info('Playing track')
        self.session.player.play()

    def pause(self, line):
        log.info('Pausing track')
        self.session.player.play(False)

    def resume(self, line):
        log.info('Resuming track')
        self.session.player.play()

    def stop(self, line):
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
        for playlist in self.session.playlist_container:
            playlist_uri = playlist.load()
            log.info("Name: {0} URI: {1}".format(playlist.name, playlist_uri))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    settings = Settings.Settings()
    settings.setup()
    spotify = Spotify()
    spotify.login()
    spotify.get_playlists()

    #Commander().cmdloop()